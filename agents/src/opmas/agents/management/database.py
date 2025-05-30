"""Database operations for agent management."""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Agent

class AgentDatabase:
    """Database operations for agent management."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the database handler."""
        self.session = session

    async def create_agent(self, agent: Agent) -> Agent:
        """Create a new agent in the database."""
        self.session.add(agent)
        await self.session.commit()
        await self.session.refresh(agent)
        return agent

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        result = await self.session.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        return result.scalar_one_or_none()

    async def get_all_agents(self) -> List[Agent]:
        """Get all agents."""
        result = await self.session.execute(select(Agent))
        return result.scalars().all()

    async def update_agent(self, agent_id: str, data: Dict) -> Optional[Agent]:
        """Update an agent's information."""
        # Update the agent
        await self.session.execute(
            update(Agent)
            .where(Agent.id == agent_id)
            .values(**data, updated_at=datetime.utcnow())
        )
        await self.session.commit()
        
        # Return the updated agent
        return await self.get_agent(agent_id)

    async def update_agent_status(
        self, agent_id: str, status: str, metadata: Optional[Dict] = None
    ) -> Optional[Agent]:
        """Update an agent's status."""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        if metadata:
            update_data["agent_metadata"] = metadata
            
        return await self.update_agent(agent_id, update_data)

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent."""
        agent = await self.get_agent(agent_id)
        if agent:
            await self.session.delete(agent)
            await self.session.commit()
            return True
        return False 