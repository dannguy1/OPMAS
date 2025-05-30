"""Agent manager implementation."""

import asyncio
import json
import os
import subprocess
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import uuid

import structlog
from nats.aio.client import Client as NATS
from sqlalchemy.ext.asyncio import AsyncSession

from .database import AgentDatabase
from .models import Agent
from .registry import AgentRegistry
from .discovery import AgentDiscovery

# Configure structlog with console output
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),  # Set to DEBUG level
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

# Configure standard logging to also show logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = structlog.get_logger(__name__)

class AgentManager:
    """Manages agent lifecycles and coordination."""

    def __init__(
        self,
        db_url: str,
        nats_url: str,
        session: AsyncSession,
        registry: AgentRegistry,
    ) -> None:
        """Initialize the agent manager."""
        self.db = AgentDatabase(session)
        self.registry = registry
        self.discovery = AgentDiscovery()
        self.nats_client = NATS()
        self.nats_url = nats_url
        self._running = False
        self._discovery_interval = 30  # seconds
        self._heartbeat_timeout = 60  # seconds
        self._running_agents: Dict[str, subprocess.Popen] = {}
        logger.info("agent_manager_initialized", nats_url=nats_url)

    async def start(self) -> None:
        """Start the agent manager."""
        try:
            # Connect to NATS
            logger.info("connecting_to_nats", url=self.nats_url)
            await self.nats_client.connect(self.nats_url)
            logger.info("connected_to_nats")

            # Start agent registry and discovery
            await self.registry.start()
            await self.discovery.start()
            logger.info("started_agent_registry_and_discovery")

            # Subscribe to agent events
            logger.info("subscribing_to_nats_topics")
            
            # Subscribe to discovery broadcast
            await self.nats_client.subscribe(
                "agent.discovery",
                cb=self._handle_discovery_request
            )
            logger.info("subscribed_to_discovery")

            # Subscribe to discovery responses
            await self.nats_client.subscribe(
                "agent.discovery.response",
                cb=self._handle_discovery_response
            )
            logger.info("subscribed_to_discovery_response")

            # Subscribe to heartbeats
            await self.nats_client.subscribe(
                "agent.heartbeat",
                cb=self._handle_heartbeat
            )
            logger.info("subscribed_to_heartbeats")

            # Subscribe to status updates
            await self.nats_client.subscribe(
                "agent.status",
                cb=self._handle_status_update
            )
            logger.info("subscribed_to_status_updates")

            self._running = True

            # Start background tasks
            asyncio.create_task(self._health_check_loop())
            asyncio.create_task(self._monitor_agents())

            logger.info("agent_manager_started")
        except Exception as e:
            logger.error("failed_to_start_agent_manager", error=str(e))
            raise

    async def stop(self) -> None:
        """Stop the agent manager."""
        if self._running:
            # Stop all running agents
            for agent_id, process in self._running_agents.items():
                await self.stop_agent(agent_id)
            
            await self.nats_client.close()
            await self.registry.stop()
            self._running = False
            logger.info("agent_manager_stopped")

    async def _monitor_agents(self) -> None:
        """Monitor running agent processes."""
        while self._running:
            try:
                for agent_id, process in list(self._running_agents.items()):
                    if process.poll() is not None:
                        # Process has terminated
                        logger.warning(
                            "agent_process_terminated",
                            agent_id=agent_id,
                            return_code=process.returncode
                        )
                        await self._handle_agent_termination(agent_id, process.returncode)
                        del self._running_agents[agent_id]
            except Exception as e:
                logger.error("agent_monitoring_error", error=str(e))
            
            await asyncio.sleep(1)

    async def _handle_agent_termination(self, agent_id: str, return_code: int) -> None:
        """Handle agent process termination."""
        try:
            # Update agent status
            await self.db.update_agent_status(
                agent_id,
                "error" if return_code != 0 else "stopped",
                {
                    "exit_code": return_code,
                    "terminated_at": datetime.utcnow().isoformat()
                }
            )
            
            # Unregister agent
            self.registry.unregister_agent(agent_id)
            
            logger.info(
                "agent_terminated",
                agent_id=agent_id,
                return_code=return_code
            )
        except Exception as e:
            logger.error(
                "agent_termination_error",
                agent_id=agent_id,
                error=str(e)
            )

    async def _health_check_loop(self) -> None:
        """Periodically check agent health."""
        while self._running:
            try:
                agents = await self.db.get_all_agents()
                for agent in agents:
                    if agent.last_heartbeat:
                        time_since_heartbeat = (
                            datetime.utcnow() - agent.last_heartbeat
                        ).total_seconds()
                        
                        if time_since_heartbeat > self._heartbeat_timeout:
                            # Mark agent as inactive
                            await self.db.update_agent(
                                agent.id,
                                {
                                    "status": "inactive",
                                    "agent_metadata": {
                                        "last_seen": agent.last_heartbeat.isoformat()
                                    }
                                }
                            )
                            logger.warning(
                                "agent_heartbeat_timeout",
                                agent_id=agent.id,
                                time_since_heartbeat=time_since_heartbeat
                            )
            except Exception as e:
                logger.error("health_check_error", error=str(e))
            
            await asyncio.sleep(self._discovery_interval)

    async def _handle_discovery_request(self, msg) -> None:
        """Handle discovery request from management API."""
        print("DEBUG: Discovery request received!")  # Direct print for immediate feedback
        try:
            logger.info("Raw discovery message received", data=msg.data.decode())
            request = json.loads(msg.data.decode())
            logger.info(
                "received_discovery_request",
                request=request,
                timestamp=datetime.utcnow().isoformat(),
                subject=msg.subject
            )
            
            # Scan for new agents using AgentDiscovery
            logger.info("Scanning for new agents...")
            agents = await self.discovery.discover_agents()
            logger.info(
                "discovered_agents",
                count=len(agents),
                agents=[agent["type"] for agent in agents]
            )

            # Register and launch new agents
            for agent in agents:
                try:
                    # Check if agent is already registered by querying all agents
                    all_agents = await self.db.get_all_agents()
                    existing_agent = next(
                        (a for a in all_agents if a.agent_type == agent["type"]),
                        None
                    )
                    
                    if not existing_agent:
                        # Register new agent
                        agent_id = str(uuid.uuid4())
                        new_agent = Agent(
                            id=agent_id,
                            name=agent.get("name", f"{agent['type']}-{agent_id[:8]}"),
                            agent_type=agent["type"],
                            version=agent.get("version", "1.0.0"),
                            status="inactive",
                            enabled="true",
                            config=agent.get("config", {}),
                            agent_metadata=agent,
                            capabilities=agent.get("capabilities", []),
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        await self.db.create_agent(new_agent)
                        logger.info("Registered new agent: %s", agent_id)

                        # Launch the agent
                        success = await self.launch_agent(agent_id)
                        if success:
                            logger.info("Launched new agent: %s", agent_id)
                        else:
                            logger.error("Failed to launch agent: %s", agent_id)
                    else:
                        logger.info("Agent already registered: %s", existing_agent.id)
                except Exception as e:
                    logger.error("Error processing agent %s: %s", agent["type"], str(e))

            logger.info("Discovery and agent launch process complete")
        except Exception as e:
            logger.error("discovery_request_error", error=str(e), exc_info=True)
            print(f"ERROR: {str(e)}")  # Direct print for immediate feedback

    async def _handle_discovery_response(self, msg) -> None:
        """Handle agent discovery response."""
        try:
            response = json.loads(msg.data.decode())
            agent_id = response.get("agent_id")
            agent_type = response.get("agent_type")
            
            if not agent_id or not agent_type:
                logger.warning("invalid_discovery_response", response=response)
                return

            # Register or update agent
            agent = await self.db.get_agent(agent_id)
            if agent:
                # Update existing agent
                await self.db.update_agent(
                    agent_id,
                    {
                        "status": "active",
                        "last_heartbeat": datetime.utcnow(),
                        "agent_metadata": response
                    }
                )
            else:
                # Register new agent
                await self.db.create_agent(
                    Agent(
                        id=agent_id,
                        name=f"{agent_type}-{agent_id}",
                        agent_type=agent_type,
                        version="1.0.0",  # Default version
                        status="active",
                        enabled="true",
                        config={},
                        agent_metadata=response,
                        capabilities=[],
                        last_heartbeat=datetime.utcnow(),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                )
            
            logger.info(
                "agent_registered",
                agent_id=agent_id,
                agent_type=agent_type
            )
        except Exception as e:
            logger.error("discovery_response_error", error=str(e))

    async def _handle_heartbeat(self, msg) -> None:
        """Handle agent heartbeat."""
        try:
            heartbeat = json.loads(msg.data.decode())
            agent_id = heartbeat.get("agent_id")
            
            if not agent_id:
                logger.warning("invalid_heartbeat", heartbeat=heartbeat)
                return

            # Update agent heartbeat
            await self.db.update_agent(
                agent_id,
                {
                    "last_heartbeat": datetime.utcnow(),
                    "status": "active"
                }
            )
            logger.debug(
                "heartbeat_received",
                agent_id=agent_id
            )
        except Exception as e:
            logger.error("heartbeat_error", error=str(e))

    async def _handle_status_update(self, msg) -> None:
        """Handle agent status update."""
        try:
            status = json.loads(msg.data.decode())
            agent_id = status.get("agent_id")
            new_status = status.get("status")
            
            if not agent_id or not new_status:
                logger.warning("invalid_status_update", status=status)
                return

            # Update agent status
            await self.db.update_agent_status(
                agent_id,
                new_status,
                status.get("metadata", {})
            )
            logger.info(
                "agent_status_updated",
                agent_id=agent_id,
                status=new_status
            )
        except Exception as e:
            logger.error("status_update_error", error=str(e))

    async def launch_agent(self, agent_id: str) -> bool:
        """Launch an agent."""
        try:
            agent = await self.db.get_agent(agent_id)
            if not agent:
                logger.error("agent_not_found", agent_id=agent_id)
                return False

            if agent_id in self._running_agents:
                logger.warning("agent_already_running", agent_id=agent_id)
                return False

            # Prepare environment variables
            env = os.environ.copy()
            env.update({
                "AGENT_ID": str(agent.id),
                "NATS_URL": self.nats_url,
                "AGENT_TYPE": agent.agent_type,
                "AGENT_NAME": agent.name,
                "AGENT_VERSION": agent.version
            })

            # Determine agent script path
            agent_script = Path(__file__).parent.parent.parent / "packages" / agent.agent_type / "run_agent.py"
            if not agent_script.exists():
                logger.error("agent_script_not_found", script=str(agent_script))
                return False

            # Start agent process
            process = subprocess.Popen(
                [sys.executable, str(agent_script)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self._running_agents[agent_id] = process
            
            # Update agent status
            await self.db.update_agent_status(
                agent_id,
                "starting",
                {"started_at": datetime.utcnow().isoformat()}
            )
            
            logger.info("agent_launched", agent_id=agent_id)
            return True
        except Exception as e:
            logger.error("agent_launch_error", error=str(e))
            return False

    async def stop_agent(self, agent_id: str) -> bool:
        """Stop an agent."""
        try:
            agent = await self.db.get_agent(agent_id)
            if not agent:
                logger.error("agent_not_found", agent_id=agent_id)
                return False

            process = self._running_agents.get(agent_id)
            if not process:
                logger.warning("agent_not_running", agent_id=agent_id)
                return False

            # Send stop signal
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                process.kill()
                process.wait()
            
            # Update agent status
            await self.db.update_agent_status(
                agent_id,
                "stopped",
                {"stopped_at": datetime.utcnow().isoformat()}
            )
            
            # Clean up
            del self._running_agents[agent_id]
            self.registry.unregister_agent(agent_id)
            
            logger.info("agent_stopped", agent_id=agent_id)
            return True
        except Exception as e:
            logger.error("agent_stop_error", error=str(e))
            return False 