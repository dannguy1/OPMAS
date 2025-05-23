#!/usr/bin/env python3

"""Contains the core logic for the Orchestrator.
The Orchestrator coordinates agents and manages their findings.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set
from datetime import datetime
import os
from pathlib import Path
import atexit
from dotenv import load_dotenv

from .data_models import AgentFinding, ParsedLogEvent
from .db_utils import get_db_session
from .db_models import Agent as AgentModel, AgentRule, Finding
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Get logger
logger = logging.getLogger(__name__)

# Path Definitions
CORE_DIR = Path(__file__).resolve().parent.parent.parent
PIDS_DIR = CORE_DIR / 'pids'
ORCHESTRATOR_PID_FILE = PIDS_DIR / "Orchestrator.pid"

def _ensure_pids_dir_exists():
    try:
        PIDS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create PID directory {PIDS_DIR}: {e}")

def _remove_orchestrator_pid_file():
    """Ensures the Orchestrator PID file is removed on exit."""
    try:
        if ORCHESTRATOR_PID_FILE.is_file():
            logger.info(f"Removing PID file: {ORCHESTRATOR_PID_FILE}")
            ORCHESTRATOR_PID_FILE.unlink()
    except Exception as e:
        logger.error(f"Error removing PID file {ORCHESTRATOR_PID_FILE}: {e}")

class Orchestrator:
    """Coordinates agents and manages their findings."""

    def __init__(self):
        """Initialize the Orchestrator."""
        self.logger = logging.getLogger(__name__)
        self.nats_client = None
        self.agents: Dict[str, any] = {}  # Map of agent_name to agent instance
        self.active_findings: Dict[str, List[AgentFinding]] = {}  # Map of resource_id to findings
        self.finding_cooldowns: Dict[str, float] = {}  # Map of finding_id to last notification time
        self.running = False
        self._load_configuration()

    def _load_configuration(self):
        """Load configuration from environment and database."""
        # Load environment variables
        load_dotenv()
        
        # Get configuration from environment
        self.notification_cooldown = int(os.getenv("NOTIFICATION_COOLDOWN", "3600"))  # 1 hour
        self.finding_retention = int(os.getenv("FINDING_RETENTION", "86400"))  # 24 hours
        self.cleanup_interval = int(os.getenv("CLEANUP_INTERVAL", "3600"))  # 1 hour

    async def start(self):
        """Start the Orchestrator."""
        self.logger.info("Starting Orchestrator...")
        self.running = True
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_task())
        
        # Load agents from database
        await self._load_agents()
        
        # Subscribe to findings topics
        await self._subscribe_to_findings()

    async def stop(self):
        """Stop the Orchestrator."""
        self.logger.info("Stopping Orchestrator...")
        self.running = False
        
        # Stop all agents
        for agent in self.agents.values():
            await agent.stop()
        
        # Clear agent list
        self.agents.clear()
        
        # Clear findings
        self.active_findings.clear()
        self.finding_cooldowns.clear()

    async def _load_agents(self):
        """Load agents from database."""
        try:
            with get_db_session() as session:
                agents = session.query(AgentModel).filter_by(enabled=True).all()
                
                for agent_model in agents:
                    try:
                        # Import agent class dynamically
                        module_path = f"opmas.agents.{agent_model.package_name}.agent"
                        class_name = f"{agent_model.name}Agent"
                        
                        module = __import__(module_path, fromlist=[class_name])
                        agent_class = getattr(module, class_name)
                        
                        # Create agent instance
                        agent = agent_class(
                            agent_name=agent_model.name,
                            subscribed_topics=agent_model.subscribed_topics,
                            findings_topic=f"findings.{agent_model.name.lower()}"
                        )
                        
                        # Start agent
                        await agent.start()
                        
                        # Add to agents map
                        self.agents[agent_model.name] = agent
                        self.logger.info(f"Loaded and started agent: {agent_model.name}")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to load agent {agent_model.name}: {e}")
                        continue
                        
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while loading agents: {e}")
            raise

    async def _subscribe_to_findings(self):
        """Subscribe to findings topics from all agents."""
        if not self.nats_client:
            self.logger.error("NATS client not initialized")
            return
            
        # Subscribe to findings topic
        await self.nats_client.subscribe(
            "findings.>",
            cb=self._handle_finding
        )
        self.logger.info("Subscribed to findings topics")

    async def _handle_finding(self, msg):
        """Handle a finding from an agent."""
        try:
            # Parse finding
            finding = AgentFinding.from_json(msg.data.decode())
            
            # Add to active findings
            resource_id = finding.resource_id
            if resource_id not in self.active_findings:
                self.active_findings[resource_id] = []
            self.active_findings[resource_id].append(finding)
            
            # Check cooldown
            finding_id = f"{finding.finding_type}:{resource_id}"
            current_time = time.time()
            last_notification = self.finding_cooldowns.get(finding_id, 0)
            
            if current_time - last_notification > self.notification_cooldown:
                # Update cooldown
                self.finding_cooldowns[finding_id] = current_time
                
                # Store finding in database
                await self._store_finding(finding)
                
                # Notify about finding
                await self._notify_finding(finding)
                
        except Exception as e:
            self.logger.error(f"Error handling finding: {e}")

    async def _store_finding(self, finding: AgentFinding):
        """Store a finding in the database."""
        try:
            with get_db_session() as session:
                db_finding = Finding(
                    finding_type=finding.finding_type,
                    agent_name=finding.agent_name,
                    resource_id=finding.resource_id,
                    severity=finding.severity,
                    message=finding.message,
                    details=finding.details,
                    timestamp=datetime.fromtimestamp(time.time())
                )
                session.add(db_finding)
                session.commit()
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while storing finding: {e}")

    async def _notify_finding(self, finding: AgentFinding):
        """Notify about a finding."""
        # TODO: Implement notification system (e.g., email, Slack, etc.)
        self.logger.info(f"New finding: {finding.message}")

    async def _cleanup_task(self):
        """Periodically clean up old findings."""
        while self.running:
            try:
                current_time = time.time()
                
                # Clean up old findings
                for resource_id, findings in list(self.active_findings.items()):
                    # Remove findings older than retention period
                    findings[:] = [
                        f for f in findings
                        if current_time - f.timestamp < self.finding_retention
                    ]
                    
                    # Remove resource if no findings left
                    if not findings:
                        del self.active_findings[resource_id]
                
                # Clean up old cooldowns
                for finding_id, last_time in list(self.finding_cooldowns.items()):
                    if current_time - last_time > self.notification_cooldown:
                        del self.finding_cooldowns[finding_id]
                
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
            
            # Wait for next cleanup
            await asyncio.sleep(self.cleanup_interval)

# --- Main Execution / Entry Point ---
async def main():
    """Main entry point for the Orchestrator process."""
    # Ensure PID directory exists before writing PID file
    _ensure_pids_dir_exists()

    # Check if PID file already exists
    if ORCHESTRATOR_PID_FILE.is_file():
        print(f"ERROR: PID file {ORCHESTRATOR_PID_FILE} already exists. Is another Orchestrator process running? Exiting.", flush=True)
        exit(1)

    # Write PID file
    try:
        with open(ORCHESTRATOR_PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        print(f"Orchestrator started with PID {os.getpid()}. PID file: {ORCHESTRATOR_PID_FILE}", flush=True)
    except IOError as e:
        print(f"ERROR: Failed to write PID file {ORCHESTRATOR_PID_FILE}: {e}. Exiting.", flush=True)
        exit(1)

    # Register cleanup function to remove PID file on exit
    atexit.register(_remove_orchestrator_pid_file)

    # Create and start Orchestrator
    orchestrator = Orchestrator()
    await orchestrator.start()

    # Keep the process running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    # Setup basic logging for standalone execution
    log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Starting Orchestrator in standalone mode...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Orchestrator interrupted by user. Exiting.")
    finally:
        # Ensure cleanup runs even if asyncio loop exits unexpectedly
        _remove_orchestrator_pid_file() 