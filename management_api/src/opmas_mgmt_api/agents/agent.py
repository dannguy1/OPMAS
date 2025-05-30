"""Agent management service."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from opmas_mgmt_api.core.exceptions import OPMASException
from opmas_mgmt_api.core.nats import NATSManager, nats_manager
from opmas_mgmt_api.models.agents import Agent, AgentRule
from opmas_mgmt_api.schemas.agents import (
    AgentCreate,
    AgentDiscovery,
    AgentList,
    AgentResponse,
    AgentRuleCreate,
    AgentRuleUpdate,
    AgentStatus,
    AgentUpdate,
)
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class AgentService:
    """Agent management service."""

    def __init__(self, db: AsyncSession, nats: Optional[NATSManager] = None):
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
    ) -> AgentList:
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

        return AgentList(
            agents=agents,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit,
        )

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
            await self._nats.publish(
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
                await self._nats.publish(
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
            await self._nats.publish(
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
                status=status.status,
                last_heartbeat=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            .returning(Agent)
        )

        result = await self.db.execute(query)
        await self.db.commit()

        agent = result.scalar_one_or_none()
        if not agent:
            return None

        # Publish status update event
        await self._nats.publish(
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

    async def discover_agents(self) -> List[AgentDiscovery]:
        """Discover available agents."""
        # Publish discovery request
        await self._nats.publish("agent.discovery", {"timestamp": datetime.utcnow().isoformat()})

        # Return currently registered agents
        query = select(Agent).where(Agent.status == "active")
        result = await self.db.execute(query)
        agents = result.scalars().all()

        return [
            AgentDiscovery(
                name=agent.name,
                agent_type=agent.agent_type,
                hostname=agent.hostname,
                ip_address=agent.ip_address,
                port=agent.port,
                confidence=1.0,  # High confidence for registered agents
                agent_metadata=agent.agent_metadata,
            )
            for agent in agents
        ]

    async def get_agent_rules(
        self, agent_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[AgentRule]:
        """Get agent rules."""
        query = select(AgentRule).where(AgentRule.agent_id == agent_id)
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_agent_rule(self, agent_id: UUID, rule_id: UUID) -> Optional[AgentRule]:
        """Get agent rule by ID."""
        query = select(AgentRule).where(
            AgentRule.agent_id == agent_id, AgentRule.id == rule_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_agent_rule(
        self, agent_id: UUID, rule: AgentRuleCreate
    ) -> Optional[AgentRule]:
        """Create new agent rule."""
        db_agent = await self.get_agent(agent_id)
        if not db_agent:
            return None

        db_rule = AgentRule(
            agent_id=agent_id,
            name=rule.name,
            description=rule.description,
            condition=rule.condition,
            action=rule.action,
            priority=rule.priority,
            enabled=rule.enabled,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        try:
            self.db.add(db_rule)
            await self.db.commit()
            await self.db.refresh(db_rule)

            # Publish rule creation event
            await self._nats.publish(
                "agent.rule.created",
                {
                    "agent_id": str(agent_id),
                    "rule_id": str(db_rule.id),
                    "name": db_rule.name,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            return db_rule
        except IntegrityError as e:
            await self.db.rollback()
            raise OPMASException(status_code=400, detail=f"Rule creation failed: {str(e)}")

    async def update_agent_rule(
        self, agent_id: UUID, rule_id: UUID, rule: AgentRuleUpdate
    ) -> Optional[AgentRule]:
        """Update agent rule."""
        query = (
            update(AgentRule)
            .where(AgentRule.agent_id == agent_id, AgentRule.id == rule_id)
            .values(**rule.model_dump(exclude_unset=True), updated_at=datetime.utcnow())
            .returning(AgentRule)
        )

        try:
            result = await self.db.execute(query)
            await self.db.commit()
            updated_rule = result.scalar_one_or_none()

            if updated_rule:
                # Publish rule update event
                await self._nats.publish(
                    "agent.rule.updated",
                    {
                        "agent_id": str(agent_id),
                        "rule_id": str(rule_id),
                        "name": updated_rule.name,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

            return updated_rule
        except IntegrityError as e:
            await self.db.rollback()
            raise OPMASException(status_code=400, detail=f"Rule update failed: {str(e)}")

    async def delete_agent_rule(self, agent_id: UUID, rule_id: UUID) -> bool:
        """Delete agent rule."""
        query = delete(AgentRule).where(
            AgentRule.agent_id == agent_id, AgentRule.id == rule_id
        )
        result = await self.db.execute(query)
        await self.db.commit()

        if result.rowcount > 0:
            # Publish rule deletion event
            await self._nats.publish(
                "agent.rule.deleted",
                {
                    "agent_id": str(agent_id),
                    "rule_id": str(rule_id),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            return True
        return False
