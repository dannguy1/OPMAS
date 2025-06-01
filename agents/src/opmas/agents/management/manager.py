"""Agent manager for managing agent lifecycle and communication."""

import asyncio
import json
import os
import subprocess
import sys
import logging
from datetime import datetime, timedelta
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
from opmas.core.nats import NATSClient

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
    """Manager for agent lifecycle and communication."""

    def __init__(self, nats_url: str, db_session, heartbeat_timeout: int = 300):
        """Initialize the agent manager."""
        self._nats = NATSClient(nats_url)
        self._discovery = AgentDiscovery()
        self._registry = AgentRegistry(db_session)
        self._heartbeat_timeout = heartbeat_timeout
        self._running = False
        self._monitor_task = None
        logger.info(f"Initialized agent manager with heartbeat timeout: {heartbeat_timeout}s")

    async def start(self) -> None:
        """Start the agent manager."""
        if self._running:
            return

        try:
            # Connect to NATS
            await self._nats.connect()
            logger.info("Connected to NATS server")

            # Start discovery and registry
            await self._discovery.start()
            await self._registry.start()
            logger.info("Started discovery and registry services")

            # Load registered agents from database
            agents = await self._registry.get_all_agents()
            logger.info(f"Loaded {len(agents)} agents from database")

            # Discover agents
            discovered_agents = await self._discovery.discover_agents()
            logger.info(f"Discovered {len(discovered_agents)} agents")

            # Register newly discovered agents
            for agent_data in discovered_agents:
                try:
                    agent = await self._registry.register_agent(agent_data)
                    if agent:
                        logger.info(f"Registered agent: {agent.name} ({agent.agent_type})")
                    else:
                        logger.error(f"Failed to register agent: {agent_data.get('name')}")
                except Exception as e:
                    logger.error(f"Error registering agent {agent_data.get('name')}: {e}")

            # Remove agents that are no longer present
            for agent in agents:
                agent_path = agent.agent_metadata.get('path')
                if agent_path and not any(a.get('path') == agent_path for a in discovered_agents):
                    logger.info(f"Agent {agent.name} not found in discovery, removing...")
                    if await self._registry.remove_agent(agent.id):
                        logger.info(f"Successfully removed agent {agent.name}")
                    else:
                        logger.error(f"Failed to remove agent {agent.name}")

            # Start monitoring task
            self._monitor_task = asyncio.create_task(self._monitor_agents())
            logger.info("Started agent monitoring task")

            # Subscribe to agent heartbeats
            await self._nats.subscribe("agent.heartbeat", self._handle_heartbeat)
            logger.info("Subscribed to agent heartbeats")

            self._running = True
            logger.info("Agent manager started successfully")

        except Exception as e:
            logger.error(f"Error starting agent manager: {e}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the agent manager."""
        if not self._running:
            return

        try:
            # Stop monitoring task
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
                self._monitor_task = None

            # Stop discovery and registry
            await self._discovery.stop()
            await self._registry.stop()

            # Disconnect from NATS
            await self._nats.disconnect()

            self._running = False
            logger.info("Agent manager stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping agent manager: {e}")
            raise

    async def _monitor_agents(self) -> None:
        """Monitor agent health and status."""
        while self._running:
            try:
                agents = await self._registry.get_all_agents()
                now = datetime.utcnow()

                for agent in agents:
                    last_heartbeat = self._registry.get_agent_heartbeat(agent.id)
                    if last_heartbeat:
                        time_since_heartbeat = (now - last_heartbeat).total_seconds()
                        if time_since_heartbeat > self._heartbeat_timeout:
                            logger.warning(
                                f"Agent {agent.name} heartbeat timeout: "
                                f"{time_since_heartbeat:.1f}s since last heartbeat"
                            )
                            await self._registry.update_status(agent.id, "inactive")
                    else:
                        logger.warning(f"Agent {agent.name} has no heartbeat record")
                        await self._registry.update_status(agent.id, "inactive")

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in agent monitoring: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _handle_heartbeat(self, msg) -> None:
        """Handle agent heartbeat messages."""
        try:
            data = msg.data.decode()
            agent_id = data.get('agent_id')
            if agent_id:
                if await self._registry.update_heartbeat(agent_id):
                    logger.debug(f"Updated heartbeat for agent {agent_id}")
                else:
                    logger.warning(f"Received heartbeat for unknown agent {agent_id}")
        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}")

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        return await self._registry.get_agent(agent_id)

    async def get_all_agents(self) -> List[Agent]:
        """Get all registered agents."""
        return await self._registry.get_all_agents()

    async def update_agent_status(self, agent_id: str, status: str) -> bool:
        """Update an agent's status."""
        return await self._registry.update_status(agent_id, status)

    async def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the registry."""
        return await self._registry.remove_agent(agent_id)

    async def _run_discovery(self) -> None:
        """Run agent discovery and process results."""
        try:
            agents = await self._discovery.discover_agents()
            logger.info(f"Discovered {len(agents)} agents during discovery")
            
            for agent in agents:
                logger.info(f"Processing agent: {agent}")
                registered_agent = await self._registry.register_agent(agent)
                if registered_agent:
                    logger.info(f"Registered agent: {registered_agent.name} ({registered_agent.agent_type})")
                    
                    if registered_agent.status == 'active':
                        logger.info(f"Auto-launching discovered agent: {registered_agent.name}")
                        try:
                            await self.start_agent(str(registered_agent.id))
                            logger.info(f"Successfully launched agent: {registered_agent.name}")
                        except Exception as e:
                            logger.error(f"Failed to launch agent {registered_agent.name}: {e}")
                    else:
                        logger.info(f"Skipping launch of agent {registered_agent.name} - status is {registered_agent.status}")
        except Exception as e:
            logger.error(f"Error during discovery: {e}")

    async def _handle_discovery(self, msg) -> None:
        """Handle agent discovery request."""
        await self._run_discovery()

    async def _handle_command(self, msg) -> None:
        """Handle agent command."""
        try:
            data = json.loads(msg.data.decode())
            command = data.get("command")
            agent_id = data.get("agent_id")

            if not command or not agent_id:
                return

            if command == "start":
                await self.start_agent(agent_id)
            elif command == "stop":
                await self.stop_agent(agent_id)
            elif command == "restart":
                await self.stop_agent(agent_id)
                await self.start_agent(agent_id)
        except Exception as e:
            logger.error(f"Error handling command: {e}")

    async def start_agent(self, agent_id: str) -> None:
        """Start an agent."""
        try:
            agent = await self._registry.get_agent(agent_id)
            if not agent:
                logger.error(f"Agent {agent_id} not found")
                return

            if agent_id in self._running_agents:
                logger.warning(f"Agent {agent_id} already running")
                return

            # Get agent script path from metadata
            agent_path = agent.agent_metadata.get('path')
            if not agent_path:
                logger.error(f"Agent {agent_id} has no path in metadata")
                return

            agent_dir = Path(agent_path).resolve()  # Convert to absolute path
            agent_script = agent_dir / "run.py"
            
            if not agent_script.exists():
                logger.error(f"Agent script not found: {agent_script}")
                return

            # Prepare environment
            env = os.environ.copy()
            env.update({
                "AGENT_ID": str(agent.id),
                "NATS_URL": self._nats_url,
                "AGENT_TYPE": agent.agent_type,
                "AGENT_NAME": agent.name,
                "PYTHONPATH": f"{agent_dir.parent.parent.parent}:{agent_dir.parent.parent}:{agent_dir.parent}"
            })

            # Start process
            process = subprocess.Popen(
                [sys.executable, str(agent_script)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,  # Use text mode for easier reading
                cwd=str(agent_dir),  # Set working directory to agent directory
                bufsize=1,  # Line buffered
                universal_newlines=True  # Use universal newlines
            )
            
            # Start background tasks to read output
            async def read_output(stream, prefix):
                while True:
                    line = stream.readline()
                    if not line:
                        break
                    line = line.strip()
                    if line:
                        if prefix == "ERROR":
                            logger.error(f"Agent {agent_id} {prefix}: {line}")
                        else:
                            logger.info(f"Agent {agent_id} {prefix}: {line}")

            # Create tasks to read stdout and stderr
            stdout_task = asyncio.create_task(read_output(process.stdout, "OUTPUT"))
            stderr_task = asyncio.create_task(read_output(process.stderr, "ERROR"))
            
            # Wait a bit to see if process starts successfully
            try:
                await asyncio.sleep(2)
                if process.poll() is not None:
                    logger.error(f"Agent {agent_id} failed to start (exit code: {process.returncode})")
                    await self._registry.update_status(agent_id, "error")
                    return
            except Exception as e:
                logger.error(f"Error checking agent {agent_id} startup: {e}")
                await self._registry.update_status(agent_id, "error")
                return
            
            self._running_agents[agent_id] = process
            await self._registry.update_status(agent_id, "running")
            logger.info(f"Started agent: {agent.name} ({agent.agent_type})")

        except Exception as e:
            logger.error(f"Error starting agent {agent_id}: {e}")
            await self._registry.update_status(agent_id, "error")

    async def stop_agent(self, agent_id: str) -> None:
        """Stop an agent."""
        try:
            process = self._running_agents.get(agent_id)
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                
                del self._running_agents[agent_id]
                await self._registry.update_status(agent_id, "stopped")
                logger.info(f"Stopped agent: {agent_id}")

        except Exception as e:
            logger.error(f"Error stopping agent {agent_id}: {e}")

    async def _handle_agent_termination(self, agent_id: str, return_code: int) -> None:
        """Handle agent process termination."""
        try:
            await self._registry.update_status(
                agent_id,
                "error" if return_code != 0 else "stopped",
                {
                    "exit_code": return_code,
                    "terminated_at": datetime.utcnow().isoformat()
                }
            )
            self._registry.unregister_agent(agent_id)
            logger.info(f"Agent {agent_id} terminated with code {return_code}")
        except Exception as e:
            logger.error(f"Error handling agent termination: {e}") 