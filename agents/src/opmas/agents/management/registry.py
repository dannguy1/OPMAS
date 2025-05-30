"""Agent registry implementation."""

from typing import Dict, List, Optional
import structlog

from opmas.agents.packages.base.agent import BaseAgent

logger = structlog.get_logger(__name__)

class AgentRegistry:
    """Registry for managing agent instances."""

    def __init__(self) -> None:
        """Initialize the agent registry."""
        self._agents: Dict[str, BaseAgent] = {}

    async def start(self) -> None:
        """Start the agent registry."""
        logger.info("agent_registry_started")

    async def stop(self) -> None:
        """Stop the agent registry."""
        self._agents.clear()
        logger.info("agent_registry_stopped")

    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent instance."""
        self._agents[agent.config.agent_id] = agent
        logger.info(
            "agent_registered",
            agent_id=agent.config.agent_id,
            agent_type=agent.config.agent_type
        )

    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent instance."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info("agent_unregistered", agent_id=agent_id)

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent instance by ID."""
        return self._agents.get(agent_id)

    def get_all_agents(self) -> List[BaseAgent]:
        """Get all registered agent instances."""
        return list(self._agents.values())

    async def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """Get agent status."""
        agent = await self.get_agent(agent_id)
        if not agent:
            return None

        return {
            "agent_id": agent.agent_id,
            "status": agent.status,
            "last_heartbeat": agent.last_heartbeat,
            "metrics": await agent.collect_metrics()
        } 