"""Agent manager for handling agent lifecycle."""
import asyncio
import logging
import os
from typing import Dict, List, Optional

from .base_agent_package.agent import BaseAgent
from .example_agent.agent import ExampleAgent

logger = logging.getLogger(__name__)

class AgentManager:
    """Manager for handling agent lifecycle."""

    def __init__(self):
        """Initialize the agent manager."""
        self.agents: Dict[str, BaseAgent] = {}
        self.tasks: Dict[str, asyncio.Task] = {}

    async def start_agent(self, agent_type: str, config: dict) -> Optional[str]:
        """Start an agent of the specified type."""
        try:
            # Create agent instance based on type
            if agent_type == "example":
                agent = ExampleAgent(
                    name=config.get("name", "example-agent"),
                    version=config.get("version", "0.1.0"),
                    description=config.get("description", "Example agent for monitoring system resources"),
                    capabilities=config.get("capabilities", ["resource_monitoring", "finding_generation"]),
                    management_api_url=os.getenv("MANAGEMENT_API_URL", "http://localhost:8000"),
                    nats_url=os.getenv("NATS_URL", "nats://localhost:4222")
                )
            else:
                logger.error(f"Unknown agent type: {agent_type}")
                return None

            # Start the agent
            await agent.start()
            self.agents[agent.id] = agent

            # Start monitoring task
            task = asyncio.create_task(self._monitor_agent(agent))
            self.tasks[agent.id] = task

            logger.info(f"Started agent {agent.id} of type {agent_type}")
            return agent.id

        except Exception as e:
            logger.error(f"Error starting agent: {e}")
            return None

    async def stop_agent(self, agent_id: str) -> bool:
        """Stop an agent."""
        try:
            agent = self.agents.get(agent_id)
            if not agent:
                logger.error(f"Agent {agent_id} not found")
                return False

            # Stop the agent
            await agent.stop()
            del self.agents[agent_id]

            # Cancel monitoring task
            task = self.tasks.get(agent_id)
            if task:
                task.cancel()
                del self.tasks[agent_id]

            logger.info(f"Stopped agent {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Error stopping agent {agent_id}: {e}")
            return False

    async def get_agent_status(self, agent_id: str) -> Optional[dict]:
        """Get agent status."""
        agent = self.agents.get(agent_id)
        if not agent:
            return None

        return {
            "id": agent.id,
            "name": agent.name,
            "type": agent.__class__.__name__,
            "status": "running" if agent.is_running else "stopped",
            "last_heartbeat": agent.last_heartbeat,
            "metrics": agent.metrics
        }

    async def list_agents(self) -> List[dict]:
        """List all running agents."""
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "type": agent.__class__.__name__,
                "status": "running" if agent.is_running else "stopped",
                "last_heartbeat": agent.last_heartbeat
            }
            for agent in self.agents.values()
        ]

    async def _monitor_agent(self, agent: BaseAgent):
        """Monitor agent health and restart if needed."""
        try:
            while True:
                await asyncio.sleep(60)  # Check every minute
                if not agent.is_running:
                    logger.warning(f"Agent {agent.id} is not running, attempting restart")
                    await agent.stop()
                    await agent.start()
        except asyncio.CancelledError:
            logger.info(f"Monitoring task for agent {agent.id} cancelled")
        except Exception as e:
            logger.error(f"Error monitoring agent {agent.id}: {e}")

# Create global agent manager instance
agent_manager = AgentManager() 