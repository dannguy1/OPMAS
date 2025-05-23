# OPMAS Orchestrator Agent
# Consumes findings, consults playbooks, and dispatches actions.

import asyncio
import logging
import signal
import time
import json
import jinja2 # Using Jinja2 for command templating
from dataclasses import asdict
from collections import defaultdict
from typing import Dict, Any, Optional, Tuple, List
import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError
import uuid
from datetime import datetime
import os # <<< Add import
from pathlib import Path # <<< Add import
import atexit # <<< Add import

# OPMAS Imports
from .config import get_config # Still needed for NATS URL
from .logging_config import setup_logging
from .data_models import AgentFinding, ActionResult
from .mq import get_shared_nats_client
# Database imports
from .db_utils import get_db_session
from .db_models import Playbook, PlaybookStep, Finding as FindingModel, IntendedAction as IntendedActionModel, Agent as AgentModel # Alias DB models
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("OrchestratorAgent")

# --- Path Definitions ---
ORCH_FILE = Path(__file__).resolve()
OPMAS_DIR = ORCH_FILE.parent
CORE_SRC_DIR = OPMAS_DIR.parent
CORE_DIR = CORE_SRC_DIR.parent
PIDS_DIR = CORE_DIR / 'pids'
ORCHESTRATOR_PID_FILE = PIDS_DIR / "OrchestratorAgent.pid"
# -----------------------

# --- PID File Cleanup Function ---
def _remove_orchestrator_pid_file():
    """Ensures the Orchestrator PID file is removed on exit."""
    try:
        if ORCHESTRATOR_PID_FILE.is_file():
            # Use logger if available (might not be if startup failed early)
            log_func = logger.info if 'logger' in globals() and logger else print
            log_func(f"Removing PID file: {ORCHESTRATOR_PID_FILE}")
            ORCHESTRATOR_PID_FILE.unlink()
        # else: logger.debug("PID file removal skipped: File not found.")
    except Exception as e:
        log_func = logger.error if 'logger' in globals() and logger else print
        log_func(f"Error removing PID file {ORCHESTRATOR_PID_FILE}: {e}")
# -----------------------------

class OrchestratorAgent:
    """Receives findings, consults playbooks from DB, logs findings & intended actions to DB."""

    AGENT_NAME = "OrchestratorAgent"
    FINDINGS_SUBSCRIPTION = "findings.>" # Subscribe to all findings topics
    # ACTION_RESULTS_SUBSCRIPTION = "actions.results" # Not needed anymore
    # ACTION_DISPATCH_TOPIC = "actions.execute" # Not needed anymore

    def __init__(self):
        logger.debug("ENTERING OrchestratorAgent.__init__")
        self.config = get_config()
        self.nats_url = self.config.get('nats', {}).get('url', 'nats://localhost:4222')
        logger.debug(f"[{self.AGENT_NAME}] Initializing... Attempting to load playbooks from DB.")
        self.playbooks = self._load_playbooks_from_db() # Load from DB
        logger.debug(f"[{self.AGENT_NAME}] Playbooks loaded from DB. Keys: {list(self.playbooks.keys()) if isinstance(self.playbooks, dict) else 'N/A'}")
        # logger.debug(f"[{self.AGENT_NAME}] Loaded playbook data: {self.playbooks}") # Avoid logging potentially large structure
        self.nc = None
        self.running = False
        self.shutdown_event = asyncio.Event()

        # State for action cooldowns (still relevant for logging frequency)
        self.last_action_times: Dict[Tuple[str, str], float] = defaultdict(float)

        # Setup Jinja2 environment for command templating
        self.template_env = jinja2.Environment(loader=jinja2.BaseLoader(), undefined=jinja2.StrictUndefined)

    def _load_playbooks_from_db(self) -> Dict[str, List[Dict[str, Any]]]:
        """Loads playbook definitions and steps from the database."""
        playbooks_structured = {}
        logger.info("Loading playbooks from database...")
        try:
            with get_db_session() as session:
                # Eager load steps to avoid N+1 queries
                db_playbooks = session.query(Playbook).options(joinedload(Playbook.steps)).all()

                for pb in db_playbooks:
                    steps_list = []
                    for step in pb.steps: # Steps are ordered by step_order due to relationship config
                        steps_list.append({
                            'step_db_id': step.step_id, # Store DB ID for linking
                            'action_type': step.action_type,
                            'command_template': step.command_template,
                            'description': step.description,
                            'timeout_seconds': step.timeout_seconds,
                            'step_config': step.step_config
                        })
                    playbooks_structured[pb.finding_type] = steps_list
                    logger.debug(f"Loaded playbook '{pb.name}' for finding type '{pb.finding_type}' with {len(steps_list)} steps.")

            logger.info(f"Successfully loaded {len(playbooks_structured)} playbooks from the database.")
            return playbooks_structured

        except SQLAlchemyError as e:
            logger.critical(f"Database error loading playbooks: {e}", exc_info=True)
        except Exception as e:
            logger.critical(f"Unexpected error loading playbooks from DB: {e}", exc_info=True)

        logger.warning("Returning empty playbook structure due to loading errors.")
        return {} # Return empty dict on failure

    async def _connect_nats(self):
        """Establish NATS connection."""
        if self.nc and self.nc.is_connected:
            return
        try:
            self.nc = await nats.connect(self.nats_url, name=self.AGENT_NAME)
            logger.info(f"Connected to NATS at {self.nats_url}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}", exc_info=True)
            raise

    async def _subscribe_to_findings(self):
        """Subscribe to findings."""
        if not self.nc or not self.nc.is_connected:
            logger.error("Cannot subscribe, NATS client not connected.")
            return
        try:
            sub_find = await self.nc.subscribe(self.FINDINGS_SUBSCRIPTION, cb=self._handle_finding)
            logger.info(f"Subscribed to findings: '{self.FINDINGS_SUBSCRIPTION}'")
        except Exception as e:
            logger.error(f"Failed to subscribe to findings: {e}", exc_info=True)

    async def _handle_finding(self, msg: nats.aio.msg.Msg):
        """Process incoming findings from agents and store them."""
        subject = msg.subject
        data_str = msg.data.decode()
        logger.debug(f"Received finding on '{subject}'")
        finding_data = None
        try:
            finding_data = json.loads(data_str)
            finding_obj = AgentFinding(**finding_data) # Validate Pydantic model

            # --- Store Finding in Database --- 
            agent_id = None
            try:
                with get_db_session() as session:
                    # Find agent DB ID based on agent name from finding
                    agent = session.query(AgentModel).filter_by(name=finding_obj.agent_name).first()
                    if agent:
                         agent_id = agent.agent_id
                    else:
                         logger.warning(f"Agent '{finding_obj.agent_name}' not found in DB. Cannot link finding.")

                    finding_db = FindingModel(
                        finding_id=finding_obj.finding_id, # Use the UUID from the agent
                        agent_id=agent_id, # Link to agent if found
                        timestamp_utc=datetime.fromisoformat(finding_obj.timestamp_utc), # Convert string back to datetime
                        finding_type=finding_obj.finding_type,
                        device_hostname=finding_obj.device_hostname,
                        device_ip=finding_obj.device_ip,
                        details=finding_obj.details # Store details dict as JSONB
                    )
                    session.add(finding_db)
                    # Commit happens automatically via context manager
                logger.info(f"Stored finding '{finding_obj.finding_type}' ({finding_obj.finding_id}) to database.")
            except SQLAlchemyError as db_e:
                 logger.error(f"Database error storing finding {finding_obj.finding_id}: {db_e}", exc_info=True)
                 # Continue to playbook processing even if DB store fails?
                 # Depending on requirements, maybe return here.
            except Exception as e:
                 logger.error(f"Unexpected error storing finding {finding_obj.finding_id}: {e}", exc_info=True)
                 # Continue?
            # --------------------------------

            logger.info(f"Processing finding '{finding_obj.finding_type}' ({finding_obj.finding_id}) from {finding_obj.agent_name} for {finding_obj.device_hostname or finding_obj.device_ip}")
            # Process playbook asynchronously
            asyncio.create_task(self._execute_playbook(finding_obj))

        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON finding from '{subject}': {data_str[:100]}...")
        except TypeError as e:
            logger.error(f"Failed to instantiate AgentFinding Pydantic model from '{subject}' data: {e}. Data: {finding_data}")
        except Exception as e:
            logger.error(f"Error handling finding: {e}", exc_info=True)

    def _render_command(self, template_str: str, finding: AgentFinding) -> Optional[str]:
         """Renders a command template using Jinja2 and finding data."""
         if not template_str:
             return None
         try:
             template = self.template_env.from_string(template_str)
             # Provide finding data to the template context
             context = {'finding': finding} # Access fields like {{ finding.details.client_mac }}
             rendered_command = template.render(context)
             # Basic check for unresolved template variables (heuristic)
             if '{{ ' in rendered_command or ' }} ' in rendered_command:
                  logger.warning(f"Command template '{template_str}' might have unresolved variables: '{rendered_command}'")
                  # Decide whether to proceed or fail - safer to fail initially
                  return None
             return rendered_command
         except jinja2.exceptions.TemplateSyntaxError as e:
             logger.error(f"Template syntax error in '{template_str}': {e}")
             return None
         except Exception as e:
             logger.error(f"Error rendering command template '{template_str}': {e}", exc_info=True)
             return None

    async def _execute_playbook(self, finding: AgentFinding):
        """Finds playbook in loaded structure, logs intended actions to DB."""
        finding_type = finding.finding_type
        device_key = finding.device_hostname or finding.device_ip # For cooldowns
        if not device_key:
             logger.error(f"Finding {finding.finding_id} lacks device identifier. Cannot process playbook.")
             return

        logger.debug(f"Attempting to find playbook for finding type: '{finding_type}'")
        playbook_steps = self.playbooks.get(finding_type)

        if not playbook_steps:
            # TODO: Add default playbook handling if needed, loading from DB
            logger.info(f"No specific playbook found for finding type '{finding_type}'. No action taken.")
            return

        # Playbook steps are already loaded as a list of dicts from _load_playbooks_from_db
        logger.info(f"Processing playbook '{finding_type}' for device {device_key}")
        logger.debug(f"Found {len(playbook_steps)} steps for playbook '{finding_type}'.")

        for i, step in enumerate(playbook_steps):
            logger.debug(f"Processing step {i}: {step}")

            action_type_name = step.get('action_type')
            command_template = step.get('command_template')
            action_description = step.get('description', 'No description')
            step_db_id = step.get('step_db_id') # Get the DB ID stored during loading

            if not action_type_name:
                logger.warning(f"Playbook step {i} missing 'action_type' name. Skipping.")
                continue

            # --- Check Cooldown (for logging frequency control) ---
            cooldown_seconds = 0 # Default to no cooldown for logging
            # TODO: Make cooldown configurable in playbook_steps table/step_config JSON?
            cooldown_key = (device_key, action_type_name)
            last_run_time = self.last_action_times.get(cooldown_key, 0)
            current_time = time.time()
            if current_time - last_run_time < cooldown_seconds:
                logger.debug(f"Intended action '{action_type_name}' for device {device_key} (step {i}) is on cooldown. Skipping logging.")
                continue
            # -----------------------------------------------------

            # --- Render Command Context --- 
            rendered_command = "<No command template defined>"
            if command_template:
                 rendered_command = self._render_command(command_template, finding)
                 if rendered_command is None:
                      logger.error(f"Step {i}: Command rendering failed for playbook '{finding_type}'. Logging action without command context.")
                      rendered_command = "<Command template rendering failed>"
            # -----------------------------

            # --- Log Intended Action to Database --- 
            logger.info(f"Playbook '{finding_type}' triggered for finding {finding.finding_id}. Logging intended action.")
            try:
                with get_db_session() as session:
                    intended_action_db = IntendedActionModel(
                        finding_id=finding.finding_id,
                        playbook_step_id=step_db_id, # Link to the step definition
                        timestamp_utc=datetime.utcnow(), # Log time of determination
                        action_type=action_type_name,
                        rendered_command_context=rendered_command
                    )
                    session.add(intended_action_db)
                    # Commit happens automatically via context manager

                # Update cooldown timestamp *after* successful logging to DB
                self.last_action_times[cooldown_key] = current_time
                logger.info(f"Stored intended action '{action_type_name}' for finding {finding.finding_id} to database.")

            except SQLAlchemyError as db_e:
                 logger.error(f"Database error storing intended action for finding {finding.finding_id}: {db_e}", exc_info=True)
                 # Decide whether to break playbook on DB error
                 break
            except Exception as e:
                 logger.error(f"Unexpected error storing intended action for finding {finding.finding_id}: {e}", exc_info=True)
                 break
            # --------------------------------------

            # Simple sequential execution: Only process the first step for now
            logger.info(f"Completed first action processing (step {i}) for playbook '{finding_type}'. Stopping playbook execution.")
            break # Stop after the first action is logged

    async def run(self):
        """Main execution loop for the orchestrator."""
        setup_logging() # Ensure logging is configured
        logger.info(f"Starting {self.AGENT_NAME}...")
        self.running = True

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._handle_shutdown_signal, sig, None)

        try:
            await self._connect_nats()
            await self._subscribe_to_findings()
            logger.info(f"{self.AGENT_NAME} started. Waiting for findings or shutdown signal.")
            await self.shutdown_event.wait()

        except asyncio.CancelledError:
            logger.info("OrchestratorAgent shutdown requested.")
        except Exception as e:
            logger.critical(f"{self.AGENT_NAME} encountered critical error: {e}", exc_info=True)
        finally:
            logger.info(f"Shutting down {self.AGENT_NAME}...")
            self.running = False
            if self.nc and not self.nc.is_closed:
                logger.info("Draining NATS connection...")
                await self.nc.drain()
                logger.info("NATS connection drained.")
            logger.info(f"{self.AGENT_NAME} has shut down.")

    def _handle_shutdown_signal(self, sig, frame):
        logger.warning(f"Received signal {sig}, initiating shutdown...")
        self.shutdown_event.set()

# --- Main execution ---
async def main():
    # --- Modified main --- 
    # Ensure DB is ready before starting agent
    # Load config first using the shared function
    from .config import load_config
    from .db_utils import init_db # Need init_db here potentially
    initial_setup_ok = False
    try:
        load_config()
        setup_logging() # Setup logging after config is loaded
        # Now logger implicitly refers to the module-level logger
        logger.info("Ensuring database schema is initialized...") 
        init_db()
        logger.info("Database schema check/init complete.")
        initial_setup_ok = True
    except Exception as e:
        # Use basic logging setup only if setup_logging failed
        logging.basicConfig(level=logging.INFO)
        logger.critical(f"Failed to load configuration, setup logging, or initialize DB: {e}", exc_info=True)
        print(f"CRITICAL ERROR: {e}", file=sys.stderr)
        return # Exit if prerequisites fail

    # --- PID File Creation (only if initial setup succeeded) --- 
    if initial_setup_ok:
        try:
            logger.info(f"Attempting to create PID file at {ORCHESTRATOR_PID_FILE}")
            PIDS_DIR.mkdir(parents=True, exist_ok=True) # Ensure directory exists
            pid = os.getpid()
            ORCHESTRATOR_PID_FILE.write_text(str(pid))
            logger.info(f"PID file created successfully with PID: {pid}")
            
            # Register cleanup function AFTER successful PID write
            atexit.register(_remove_orchestrator_pid_file)
            logger.info("PID file removal registered for shutdown.")
            
        except Exception as pid_e:
            logger.critical(f"CRITICAL ERROR creating PID file: {pid_e}", exc_info=True)
            _remove_orchestrator_pid_file() # Attempt cleanup
            print(f"CRITICAL ERROR: Failed to create PID file {ORCHESTRATOR_PID_FILE}. Exiting.", file=sys.stderr)
            return # Do not start agent if PID file fails
    # ---------------------------------------------------------
    else:
        # Should not happen due to return above, but defensive check
        logger.error("Initial setup failed, skipping PID file creation and agent start.")
        return 
        
    # --- Start Agent --- 
    agent = OrchestratorAgent()
    try:
        await agent.run()
    except KeyboardInterrupt:
        # Use module-level logger
        logger.info("Ctrl+C detected. Shutting down OrchestratorAgent...")
        # atexit will handle PID cleanup
    except Exception as e:
        # Use module-level logger
        logger.exception("Unhandled exception in Orchestrator main loop") 
        # atexit will handle PID cleanup
    # -------------------

if __name__ == "__main__":
    # print("DEBUG: ENTERING OrchestratorAgent.__main__")
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Fatal error running orchestrator: {e}", exc_info=True)
        print(f"FATAL: {e}", file=sys.stderr) 