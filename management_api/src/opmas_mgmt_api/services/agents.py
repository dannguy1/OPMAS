"""Agent management service."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from opmas_mgmt_api.core.exceptions import OPMASException
from opmas_mgmt_api.core.nats import NATSManager, nats_manager
from opmas_mgmt_api.models.agents import Agent
from opmas_mgmt_api.schemas.agents import AgentCreate, AgentStatus, AgentUpdate
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class AgentService:
    """Agent management service."""

    def __init__(self, db: Session, nats: Optional[NATSManager] = None):
        """Initialize service with database session and NATS manager."""
        self.db = db
        self._nats = nats or nats_manager

    async def list_agents(
        self,
        skip: int = 0,
        limit: int = 100,
        agent_type: Optional[str] = None,
        status: Optional[str] = None,
        enabled: Optional[bool] = None,
        device_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """List agents with pagination and filtering."""
        query = select(Agent)

        if agent_type:
            query = query.where(Agent.agent_type == agent_type)
        if status:
            query = query.where(Agent.status == status)
        if enabled is not None:
            query = query.where(Agent.enabled == enabled)
        if device_id:
            query = query.where(Agent.device_id == device_id)

        # Get total count
        count_query = select(Agent.id).select_from(query.subquery())
        result = await self.db.execute(count_query)
        total = len(result.scalars().all())

        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        agents = result.scalars().all()

        return {"items": agents, "total": total, "skip": skip, "limit": limit}

    async def create_agent(self, agent: AgentCreate) -> Agent:
        """Create a new agent."""
        db_agent = Agent(
            **agent.model_dump(),
            status="inactive",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        try:
            self.db.add(db_agent)
            await self.db.commit()
            await self.db.refresh(db_agent)

            # Publish agent creation event
            await self.nats.publish(
                "agent.created",
                {
                    "agent_id": str(db_agent.id),
                    "agent_type": db_agent.agent_type,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            return db_agent
        except IntegrityError as e:
            await self.db.rollback()
            raise OPMASException(status_code=400, detail=f"Agent creation failed: {str(e)}")

    async def get_agent(self, agent_id: UUID) -> Optional[Agent]:
        """Get agent by ID."""
        query = select(Agent).where(Agent.id == agent_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_agent(self, agent_id: UUID, agent: AgentUpdate) -> Optional[Agent]:
        """Update agent details."""
        query = (
            update(Agent)
            .where(Agent.id == agent_id)
            .values(**agent.model_dump(exclude_unset=True), updated_at=datetime.utcnow())
            .returning(Agent)
        )

        try:
            result = await self.db.execute(query)
            await self.db.commit()
            updated_agent = result.scalar_one_or_none()

            if updated_agent:
                # Publish agent update event
                await self.nats.publish(
                    "agent.updated",
                    {
                        "agent_id": str(agent_id),
                        "agent_type": updated_agent.agent_type,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

            return updated_agent
        except IntegrityError as e:
            await self.db.rollback()
            raise OPMASException(status_code=400, detail=f"Agent update failed: {str(e)}")

    async def delete_agent(self, agent_id: UUID) -> bool:
        """Delete an agent."""
        query = delete(Agent).where(Agent.id == agent_id)
        result = await self.db.execute(query)
        await self.db.commit()

        if result.rowcount > 0:
            # Publish agent deletion event
            await self.nats.publish(
                "agent.deleted",
                {"agent_id": str(agent_id), "timestamp": datetime.utcnow().isoformat()},
            )
            return True
        return False

    async def get_agent_status(self, agent_id: UUID) -> Optional[AgentStatus]:
        """Get agent status."""
        agent = await self.get_agent(agent_id)
        if not agent:
            return None

        return AgentStatus(
            status=agent.status,
            timestamp=agent.updated_at,
            details={
                "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None
            },
            metrics=agent.capabilities.get("metrics", {}) if agent.capabilities else {},
        )

    async def update_agent_status(
        self, agent_id: UUID, status: AgentStatus
    ) -> Optional[AgentStatus]:
        """Update agent status."""
        query = (
            update(Agent)
            .where(Agent.id == agent_id)
            .values(
                status=status.status, last_heartbeat=datetime.utcnow(), updated_at=datetime.utcnow()
            )
            .returning(Agent)
        )

        result = await self.db.execute(query)
        await self.db.commit()

        agent = result.scalar_one_or_none()
        if not agent:
            return None

        # Publish status update event
        await self.nats.publish(
            f"agent.status.{agent_id}",
            {
                "agent_id": str(agent_id),
                "status": status.status,
                "timestamp": datetime.utcnow().isoformat(),
                "details": status.details,
                "metrics": status.metrics,
            },
        )

        return AgentStatus(
            status=agent.status,
            timestamp=agent.updated_at,
            details=status.details,
            metrics=status.metrics,
        )

    async def discover_agents(self) -> List[Dict[str, Any]]:
        """Discover available agents."""
        # Publish discovery request
        await self.nats.publish("agent.discovery", {"timestamp": datetime.utcnow().isoformat()})

        # Return currently registered agents
        query = select(Agent).where(Agent.status == "active")
        result = await self.db.execute(query)
        agents = result.scalars().all()

        return [
            {
                "id": str(agent.id),
                "name": agent.name,
                "agent_type": agent.agent_type,
                "status": agent.status,
                "last_heartbeat": agent.last_heartbeat.isoformat()
                if agent.last_heartbeat
                else None,
            }
            for agent in agents
        ]
