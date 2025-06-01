"""Agent registry for managing agent instances."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from opmas.agents.management.models import Agent

logger = logging.getLogger(__name__)

class AgentRegistry:
    """Registry for managing agent instances."""

    def __init__(self, db_session: AsyncSession):
        """Initialize the registry."""
        self._agents: Dict[str, Agent] = {}
        self._db = db_session
        self._running = False
        self._heartbeats: Dict[str, datetime] = {}
        logger.info("Starting agent registry")

    async def start(self) -> None:
        """Start the agent registry."""
        if self._running:
            return

        logger.info("Starting agent registry")
        self._running = True

    async def stop(self) -> None:
        """Stop the agent registry."""
        if not self._running:
            return

        logger.info("Stopping agent registry")
        self._running = False
        self._agents.clear()
        self._heartbeats.clear()

    async def register_agent(self, agent_data: dict) -> Optional[Agent]:
        """Register a new agent in the registry and database."""
        try:
            # Get or generate agent ID
            agent_id = agent_data.get('agent_id')
            if not agent_id:
                agent_id = f"{agent_data['name']}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                logger.info(f"Generated new agent ID: {agent_id}")

            # Check if agent already exists
            existing_agent = await self.get_agent(agent_id)
            if existing_agent:
                logger.info(f"Agent {agent_id} already exists, updating...")
                # Update existing agent
                existing_agent.name = agent_data['name']
                existing_agent.agent_type = agent_data['type']
                existing_agent.status = agent_data.get('status', 'inactive')
                existing_agent.agent_metadata = agent_data.get('metadata', {})
                existing_agent.updated_at = datetime.utcnow()
                await self._db.commit()
                await self._db.refresh(existing_agent)
                logger.info(f"Updated existing agent: {agent_id}")
                return existing_agent

            # Ensure path is stored in metadata
            metadata = agent_data.get('metadata', {})
            if 'path' in agent_data:
                metadata['path'] = agent_data['path']

            # Create agent instance
            agent = Agent(
                id=agent_id,
                name=agent_data['name'],
                agent_type=agent_data['type'],
                version=agent_data.get('version', '1.0.0'),
                status=agent_data.get('status', 'inactive'),
                enabled=str(agent_data.get('enabled', True)).lower(),  # Convert boolean to string
                config=agent_data.get('config', {}),
                agent_metadata=metadata,
                capabilities=agent_data.get('capabilities', []),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Save to database
            self._db.add(agent)
            await self._db.commit()
            await self._db.refresh(agent)

            # Store in memory
            self._agents[str(agent.id)] = agent
            self._heartbeats[str(agent.id)] = datetime.utcnow()

            logger.info(f"Registered new agent: {agent.name} ({agent.agent_type}) with ID: {agent.id}")
            return agent

        except SQLAlchemyError as e:
            logger.error(f"Database error registering agent: {e}")
            await self._db.rollback()
            return None
        except Exception as e:
            logger.error(f"Error registering agent: {e}")
            await self._db.rollback()
            return None

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        try:
            # First check in-memory registry
            if agent_id in self._agents:
                return self._agents[agent_id]
            
            # If not in memory, check database
            query = select(Agent).where(Agent.id == agent_id)
            result = await self._db.execute(query)
            agent = result.scalar_one_or_none()
            
            if agent:
                # Add to in-memory registry
                self._agents[str(agent.id)] = agent
                self._heartbeats[str(agent.id)] = agent.last_heartbeat or datetime.utcnow()
                logger.debug(f"Loaded agent {agent_id} from database")
            
            return agent
        except Exception as e:
            logger.error(f"Error getting agent {agent_id}: {e}")
            return None

    async def get_all_agents(self) -> List[Agent]:
        """Get all registered agents."""
        try:
            # Get from database
            query = select(Agent)
            result = await self._db.execute(query)
            agents = result.scalars().all()
            
            # Update in-memory registry
            for agent in agents:
                self._agents[str(agent.id)] = agent
                self._heartbeats[str(agent.id)] = agent.last_heartbeat or datetime.utcnow()
            
            logger.debug(f"Loaded {len(agents)} agents from database")
            return list(agents)
        except Exception as e:
            logger.error(f"Error getting all agents: {e}")
            return list(self._agents.values())

    def get_agents(self) -> Dict[str, Agent]:
        """Get all registered agents as a dictionary."""
        return self._agents

    def get_agent_heartbeat(self, agent_id: str) -> Optional[datetime]:
        """Get agent's last heartbeat timestamp."""
        return self._heartbeats.get(agent_id)

    async def update_status(self, agent_id: str, status: str, metadata: Optional[Dict] = None) -> bool:
        """Update agent status and metadata."""
        try:
            agent = await self.get_agent(agent_id)
            if agent:
                agent.status = status
                if metadata:
                    agent.agent_metadata = metadata
                agent.updated_at = datetime.utcnow()
                await self._db.commit()
                logger.info(f"Updated agent {agent_id} status to {status}")
                return True
            logger.warning(f"Agent {agent_id} not found for status update")
            return False
        except Exception as e:
            logger.error(f"Error updating agent status: {e}")
            await self._db.rollback()
            return False

    async def update_agent_status(self, agent_id: str, status: str) -> bool:
        """Update an agent's status."""
        return await self.update_status(agent_id, status)

    async def update_heartbeat(self, agent_id: str) -> bool:
        """Update an agent's last heartbeat timestamp."""
        try:
            agent = await self.get_agent(agent_id)
            if agent:
                now = datetime.utcnow()
                agent.last_heartbeat = now
                self._heartbeats[str(agent.id)] = now
                await self._db.commit()
                logger.debug(f"Updated heartbeat for agent {agent_id}")
                return True
            logger.warning(f"Agent {agent_id} not found for heartbeat update")
            return False
        except Exception as e:
            logger.error(f"Error updating agent heartbeat: {e}")
            await self._db.rollback()
            return False

    async def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the registry."""
        try:
            # First try to get agent from database
            query = select(Agent).where(Agent.id == agent_id)
            result = await self._db.execute(query)
            agent = result.scalar_one_or_none()
            
            if agent:
                # Delete from database
                await self._db.delete(agent)
                await self._db.commit()
                
                # Clean up in-memory state
                if agent_id in self._agents:
                    del self._agents[agent_id]
                if agent_id in self._heartbeats:
                    del self._heartbeats[agent_id]
                    
                logger.info(f"Successfully removed agent {agent_id} from registry and database")
                return True
                
            logger.warning(f"Agent {agent_id} not found in database")
            return False
            
        except Exception as e:
            logger.error(f"Error removing agent {agent_id}: {e}")
            await self._db.rollback()
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the registry."""
        return await self.remove_agent(agent_id) 