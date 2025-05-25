# OPMAS Base Agent Class

import asyncio
import json
import logging
import os
import signal
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import nats
from dotenv import load_dotenv
from nats.errors import ConnectionClosedError, NoServersError, TimeoutError

# OPMAS Imports
from ..config import get_config, load_yaml_file
from ..data_models import AgentFinding, ParsedLogEvent
from ..logging_config import setup_logging
from ..mq import publish_message  # Reusing publish utility

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all OPMAS Domain Agents."""

    def __init__(
        self,
        agent_name: str,
        subscribed_topics: List[str],
        findings_topic: str,
        queue_group: str = "",
        load_rules_from_config: bool = True,
    ):
        """Initialize the agent.

        Args:
            agent_name: The name of this agent (e.g., "WiFiAgent").
            subscribed_topics: List of NATS topics to subscribe to (e.g., ["logs.wifi"]).
            findings_topic: NATS topic to publish findings on (e.g., "findings.wifi").
            queue_group: Optional NATS queue group name for load balancing.
            load_rules_from_config: If True (default), load rules using _load_agent_rules(). Set to False if rules are loaded differently (e.g., from DB by subclass).
        """
        self.agent_name = agent_name
        self.subscribed_topics = subscribed_topics
        self.findings_topic = findings_topic
        self.queue_group = queue_group or self.agent_name  # Default queue group to agent name
        self.config = get_config()
        self.nats_url = self.config.get("nats", {}).get("url", "nats://localhost:4222")
        self.nc: Optional[nats.NATS] = None  # NATS client connection
        self.subscriptions: List[nats.Subscription] = []
        self.running = False
        self.shutdown_event = asyncio.Event()

        # --- Assign logger BEFORE calling methods that might use it ---
        logger = logging.getLogger(self.agent_name)  # Get logger specific to the agent instance
        self.logger = logger

        # Now load rules and initialize state
        self.agent_rules = {}
        if load_rules_from_config:
            # First try to load package-specific .env file
            package_env_path = self._find_package_env()
            if package_env_path:
                load_dotenv(package_env_path)
                self.logger.info(f"Loaded environment from package: {package_env_path}")

            # Then load rules from YAML config
            self.agent_rules = self._load_agent_rules()

            # Finally load rules from environment variables
            self._load_env_rules()
        else:
            self.logger.info(
                "Skipping default rule loading based on 'load_rules_from_config=False'. Subclass should load rules."
            )

        # Initialize agent-specific state if needed
        self._initialize_state()

    def _find_package_env(self) -> Optional[Path]:
        """Find the package's .env file."""
        try:
            # Get the directory of the actual agent implementation
            agent_dir = Path(self.__class__.__module__.replace(".", "/")).parent
            if not agent_dir.is_absolute():
                agent_dir = Path.cwd() / agent_dir

            # Look for .env file
            env_file = agent_dir / ".env"
            example_env = agent_dir / "example.env"

            if env_file.exists():
                return env_file
            elif example_env.exists():
                self.logger.warning(
                    f"Found example.env but no .env in {agent_dir}. Using example.env."
                )
                return example_env

            return None
        except Exception as e:
            self.logger.error(f"Error finding package .env file: {e}", exc_info=True)
            return None

    def _initialize_state(self):
        """Placeholder for subclasses to initialize their specific state variables."""
        pass

    def _load_agent_rules(self) -> Dict[str, Any]:
        """Load agent rules from YAML config file."""
        # Get rules path from config or use default
        rules_path = self.config.get("rules_path", "config/rules.yaml")
        if isinstance(rules_path, str):
            rules_path = Path(rules_path)

        if not rules_path.is_absolute():
            # Make path absolute relative to project root
            project_root = (
                Path(__file__).resolve().parents[4]
            )  # Go up one more level to project root
            rules_path = project_root / rules_path

        self.logger.debug(f"Loading YAML rules from: {rules_path}")

        try:
            all_rules = load_yaml_file(rules_path)
            if not all_rules:
                self.logger.warning("No rules found in YAML rules file.")
                return {}

            # Filter rules for this agent
            agent_rules = {
                rule_name: rule_config
                for rule_name, rule_config in all_rules.items()
                if rule_config.get("agent") == self.agent_name
            }

            if not agent_rules:
                self.logger.warning(f"No rules found for agent: {self.agent_name}")
            else:
                self.logger.info(f"Loaded {len(agent_rules)} rules from YAML for {self.agent_name}")
                self.logger.debug(f"YAML rules: {list(agent_rules.keys())}")

            return agent_rules

        except Exception as e:
            self.logger.error(f"Error loading YAML rules: {e}", exc_info=True)
            return {}

    def _load_env_rules(self):
        """Load classification rules from environment variables as initial rules."""
        env_rules = os.getenv("RULES")
        if not env_rules:
            self.logger.debug("No RULES environment variable found.")
            return

        try:
            # Split rules by comma and clean up whitespace
            patterns = [p.strip() for p in env_rules.split(",") if p.strip()]
            if not patterns:
                self.logger.debug("No valid patterns found in RULES environment variable.")
                return

            # Create a classification rule for each pattern
            rules_before = set(self.agent_rules.keys())

            for i, pattern in enumerate(patterns):
                # Create a more descriptive rule name based on the pattern
                rule_name = f"default_{pattern.lower().replace(' ', '_')}"
                self.agent_rules[rule_name] = {
                    "type": "classification",
                    "patterns": [pattern],
                    "enabled": True,
                    "agent": self.agent_name,
                    "description": f"Default classification rule for pattern: {pattern}",
                    "is_default": True,  # Mark as a default rule
                    "created_ts": datetime.utcnow().isoformat(),
                    "modified_ts": datetime.utcnow().isoformat(),
                }

            rules_after = set(self.agent_rules.keys())
            new_rules = rules_after - rules_before

            self.logger.info(
                f"Loaded {len(patterns)} default classification rules from package environment"
            )
            self.logger.debug(f"Default patterns: {patterns}")
            self.logger.debug(f"New default rules added: {list(new_rules)}")
            self.logger.debug(f"Total rules now: {len(self.agent_rules)}")

            # Log complete rules summary
            self.logger.info("=== Initial Agent Rules Summary ===")
            for rule_name, rule in self.agent_rules.items():
                self.logger.info(f"Rule: {rule_name}")
                self.logger.info(f"  Type: {rule.get('type')}")
                self.logger.info(f"  Patterns: {rule.get('patterns')}")
                self.logger.info(f"  Enabled: {rule.get('enabled')}")
                self.logger.info(f"  Default: {rule.get('is_default', False)}")
            self.logger.info("=======================")

        except Exception as e:
            self.logger.error(
                f"Error loading default rules from package environment: {e}", exc_info=True
            )

    async def get_rules(self) -> Dict[str, Any]:
        """Get all agent rules including metadata about default status."""
        return {
            name: {
                **rule,
                "is_default": rule.get("is_default", False),
                "can_delete": not rule.get("is_default", False),  # Default rules can't be deleted
            }
            for name, rule in self.agent_rules.items()
        }

    async def update_rule(self, rule_name: str, rule_config: Dict[str, Any]) -> bool:
        """Update an existing rule, preserving its default status if applicable."""
        if rule_name not in self.agent_rules:
            self.logger.warning(f"Attempted to update non-existent rule: {rule_name}")
            return False

        # Preserve default status and created timestamp if it's a default rule
        if self.agent_rules[rule_name].get("is_default"):
            rule_config["is_default"] = True
            rule_config["created_ts"] = self.agent_rules[rule_name]["created_ts"]

        rule_config["modified_ts"] = datetime.utcnow().isoformat()
        self.agent_rules[rule_name] = rule_config
        self.logger.info(f"Updated rule: {rule_name}")
        return True

    async def add_rule(self, rule_name: str, rule_config: Dict[str, Any]) -> bool:
        """Add a new custom rule."""
        if rule_name in self.agent_rules:
            self.logger.warning(f"Rule {rule_name} already exists")
            return False

        # Ensure new rules are marked as non-default
        rule_config["is_default"] = False
        rule_config["created_ts"] = datetime.utcnow().isoformat()
        rule_config["modified_ts"] = datetime.utcnow().isoformat()

        self.agent_rules[rule_name] = rule_config
        self.logger.info(f"Added new rule: {rule_name}")
        return True

    async def delete_rule(self, rule_name: str) -> bool:
        """Delete a rule if it's not a default rule."""
        if rule_name not in self.agent_rules:
            self.logger.warning(f"Attempted to delete non-existent rule: {rule_name}")
            return False

        if self.agent_rules[rule_name].get("is_default"):
            self.logger.warning(f"Cannot delete default rule: {rule_name}")
            return False

        del self.agent_rules[rule_name]
        self.logger.info(f"Deleted rule: {rule_name}")
        return True

    async def connect_nats(self):
        """Establish NATS connection."""
        if self.nc and self.nc.is_connected:
            self.logger.info("Already connected to NATS.")
            return
        try:
            self.nc = await nats.connect(
                self.nats_url,
                name=self.agent_name,
                disconnected_cb=self._nats_disconnected_cb,
                reconnected_cb=self._nats_reconnected_cb,
                error_cb=self._nats_error_cb,
                closed_cb=self._nats_closed_cb,
            )
            self.logger.info(f"Connected to NATS at {self.nats_url}")
        except NoServersError as e:
            self.logger.error(f"Could not connect to any NATS server: {e}")
            # Implement retry logic or fail gracefully
            raise
        except Exception as e:
            self.logger.error(f"Error connecting to NATS: {e}", exc_info=True)
            raise

    async def _nats_disconnected_cb(self):
        self.logger.warning("NATS connection lost. Attempting to reconnect...")

    async def _nats_reconnected_cb(self):
        self.logger.info(f"Reconnected to NATS at {self.nc.connected_url.netloc}...")
        # Resubscribe upon reconnection if needed (nats-py might handle this automatically for basic subs)
        # If using JetStream or more complex subs, manual handling might be required.
        # For simple subs, check if they are still valid or re-create.
        # self.logger.info("Re-establishing subscriptions...")
        # await self.subscribe()

    async def _nats_error_cb(self, e):
        self.logger.error(f"NATS Error: {e}", exc_info=isinstance(e, Exception))

    async def _nats_closed_cb(self):
        self.logger.warning("NATS connection is permanently closed.")
        # Trigger shutdown or attempt a full reconnect sequence if desired.
        self.shutdown_event.set()  # Signal agent to shutdown if NATS closes

    async def _check_classification_rules(self, event: ParsedLogEvent):
        """Check if the event matches any classification rules."""
        for rule_name, rule_config in self.agent_rules.items():
            if not isinstance(rule_config, dict) or not rule_config.get("enabled", False):
                continue

            if rule_config.get("type") != "classification":
                continue

            patterns = rule_config.get("patterns", [])
            if not patterns:
                continue

            for pattern in patterns:
                if pattern.lower() in event.message.lower():
                    # Store the classification in the event's structured fields
                    if not event.structured_fields:
                        event.structured_fields = {}
                    event.structured_fields["classifications"] = event.structured_fields.get(
                        "classifications", []
                    )
                    event.structured_fields["classifications"].append(
                        {
                            "rule_name": rule_name,
                            "pattern": pattern,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                    self.logger.info(
                        f"Event {event.event_id} matched classification rule '{rule_name}' with pattern '{pattern}'"
                    )

    @abstractmethod
    async def process_log_event(self, event: ParsedLogEvent):
        """Process a parsed log event. Must be implemented by subclasses."""
        # Check classification rules first
        await self._check_classification_rules(event)
        # Let subclasses handle their specific processing
        await self._process_agent_specific_rules(event)

    @abstractmethod
    async def _process_agent_specific_rules(self, event: ParsedLogEvent):
        """Process agent-specific rules. Must be implemented by subclasses."""
        pass

    async def _message_handler(self, msg):
        """Generic handler for messages received from NATS subscriptions."""
        subject = msg.subject
        data_str = msg.data.decode()
        # +++ Log Entry & Raw Data +++
        self.logger.debug(
            f"[{self.agent_name}] _message_handler received message on '{subject}'. Raw data: {data_str[:150]}..."
        )
        # ++++++++++++++++++++++++++++
        try:
            data_dict = json.loads(data_str)
            # +++ Log Parsed Dict +++
            self.logger.debug(f"[{self.agent_name}] Parsed data dict: {data_dict}")
            # +++++++++++++++++++++++
            # TODO: Add validation here (e.g., using Pydantic if added)
            log_event = ParsedLogEvent(**data_dict)  # Convert dict to dataclass
            # +++ Log Instantiated Event +++
            self.logger.debug(
                f"[{self.agent_name}] Instantiated ParsedLogEvent: ID={log_event.event_id}, Type={log_event.log_source_type}, Msg='{log_event.message[:50]}...'"
            )
            # ++++++++++++++++++++++++++++++
            await self.process_log_event(log_event)
        except json.JSONDecodeError:
            self.logger.error(f"Failed to decode JSON from '{subject}': {data_str[:100]}...")
        except TypeError as e:
            self.logger.error(
                f"Failed to instantiate ParsedLogEvent from '{subject}' data: {e}. Data: {data_dict}"
            )
        except Exception as e:
            self.logger.error(f"Error processing message from '{subject}': {e}", exc_info=True)

    async def subscribe(self):
        """Subscribe to the NATS topics defined in self.subscribed_topics."""
        if not self.nc or not self.nc.is_connected:
            self.logger.error(f"[{self.agent_name}] Cannot subscribe, NATS client not connected.")
            return
        # Clear existing subs
        for sub in self.subscriptions:
            try:
                await sub.unsubscribe()
            except Exception as e:
                self.logger.warning(
                    f"[{self.agent_name}] Error unsubscribing previous subscription: {e}"
                )
        self.subscriptions = []

        for topic in self.subscribed_topics:
            # +++ Add Subscription Attempt Log +++
            self.logger.debug(f"[{self.agent_name}] Attempting to subscribe to topic: '{topic}'")
            # ++++++++++++++++++++++++++++++++++++
            try:
                # Use queue group based on agent name for potential load balancing
                queue_group = self.agent_name
                sub = await self.nc.subscribe(topic, queue=queue_group, cb=self._message_handler)
                self.subscriptions.append(sub)
                # +++ Add Subscription Success Log +++
                self.logger.info(
                    f"[{self.agent_name}] Successfully subscribed to topic: '{topic}' with queue '{queue_group}'"
                )
                # ++++++++++++++++++++++++++++++++++++
            except Exception as e:
                # +++ Add Subscription Failure Log +++
                self.logger.error(
                    f"[{self.agent_name}] Failed to subscribe to topic '{topic}': {e}",
                    exc_info=True,
                )
                # ++++++++++++++++++++++++++++++++++++
                # Decide if agent should stop/retry on subscription failure

    async def publish_finding(self, finding: AgentFinding):
        """Publish a finding object to the designated NATS topic."""
        if not self.nc or not self.nc.is_connected:
            self.logger.error("Cannot publish finding, NATS client not connected.")
            # Optionally queue findings temporarily? For now, just log.
            return

        try:
            finding.agent_name = self.agent_name  # Ensure agent name is set
            finding_dict = asdict(finding)
            await publish_message(self.findings_topic, finding_dict, nats_client=self.nc)
            self.logger.info(f"Published finding ({finding.finding_type}) to {self.findings_topic}")
            self.logger.debug(f"Finding details: {finding_dict}")
        except Exception as e:
            self.logger.error(f"Failed to publish finding: {e}", exc_info=True)

    def _handle_shutdown_signal(self, sig, frame):
        """Handle OS signals for graceful shutdown."""
        self.logger.warning(f"Received signal {sig}, initiating shutdown...")
        self.shutdown_event.set()

    async def run(self):
        """Main execution loop for the agent."""
        # --- Get Logger ---
        try:
            agent_logger = getattr(self, "logger", logging.getLogger())
        except Exception as log_init_e:
            print(
                f"CRITICAL ERROR getting logger for {getattr(self, 'agent_name', 'UnknownAgent')}: {log_init_e}",
                flush=True,
            )
            return  # Cannot proceed

        # --- Initial Startup ---
        try:
            agent_logger.info(f"Attempting to start {self.agent_name}...")
            setup_logging()  # Ensure logging is configured (might be redundant if called elsewhere)
            agent_logger.info(f"Starting {self.agent_name}...")
            self.running = True
        except Exception as start_e:  # <<< Except for initial startup
            agent_logger.critical(
                f"Error during initial startup of {self.agent_name}: {start_e}", exc_info=True
            )
            self.running = False
            return  # Stop if startup fails

        # --- Signal Handler Setup ---
        # <<< Temporarily commenting out agent-level signal handler setup >>>
        # try:
        #     agent_logger.debug(f"Setting up signal handlers for {self.agent_name}...")
        #     loop = asyncio.get_running_loop()
        #     for sig in (signal.SIGINT, signal.SIGTERM):
        #         loop.add_signal_handler(sig, self._handle_shutdown_signal, sig, None)
        #     agent_logger.debug(f"Signal handlers set for {self.agent_name}.")
        # except Exception as sig_e:
        #     agent_logger.critical(f"Error setting up signal handlers for {self.agent_name}: {sig_e}", exc_info=True)
        #     self.running = False
        #     return # Stop if signals fail

        # --- Main Run Loop ---
        try:  # <<< Main try block >>>
            agent_logger.info(f"Attempting NATS connection for {self.agent_name}...")
            await self.connect_nats()
            connection_status = self.nc.is_connected if self.nc else False
            agent_logger.info(
                f"NATS connection attempt complete for {self.agent_name}. Connected: {connection_status}"
            )

            agent_logger.info(f"Attempting NATS subscription(s) for {self.agent_name}...")
            await self.subscribe()
            agent_logger.info(f"NATS subscription attempt complete for {self.agent_name}.")

            agent_logger.info(
                f"{self.agent_name} started successfully. Waiting for events or shutdown signal."
            )
            await self.shutdown_event.wait()

        except Exception as e:  # <<< Except for main try block >>>
            agent_logger.critical(
                f"{self.agent_name} encountered a critical error during run: {e}", exc_info=True
            )
        finally:  # <<< Finally for main try block >>>
            agent_logger.info(f"Shutting down {self.agent_name}...")
            self.running = False
            # Clean up NATS subscriptions
            for sub in self.subscriptions:
                try:
                    if self.nc and self.nc.is_connected:
                        await sub.unsubscribe()
                        agent_logger.debug(f"Unsubscribed from {sub.subject}")  # Use agent_logger
                except Exception as unsub_e:
                    agent_logger.warning(f"Error during unsubscribe: {unsub_e}")  # Use agent_logger
            # Close NATS connection
            if self.nc and self.nc.is_connected:
                await self.nc.close()
                agent_logger.info("NATS connection closed.")  # Use agent_logger
            agent_logger.info(f"{self.agent_name} has shut down.")  # Use agent_logger

    async def disconnect(self):
        """Gracefully disconnect from NATS."""
        if self.nc and not self.nc.is_closed:
            try:
                await self.nc.drain()
                self.logger.info(f"{self.agent_name} disconnected from NATS")
            except Exception as e:
                self.logger.error(f"Error disconnecting from NATS: {e}", exc_info=True)


# Note: This base class is not meant to be run directly.
# Subclasses will implement process_log_event and be run.
