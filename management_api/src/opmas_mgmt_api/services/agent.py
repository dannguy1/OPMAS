"""Agent management service."""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.models.agent import Agent, AgentRule
from opmas_mgmt_api.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentRuleCreate,
    AgentRuleUpdate,
    AgentDiscovery
)

logger = logging.getLogger(__name__)

class AgentService:
    """Agent management service."""

    def __init__(self, db: AsyncSession, nats: NATSManager):
        """Initialize agent service."""
        self.db = db
        self.nats = nats

    async def get_agents(
        self,
        skip: int = 0,
        limit: int = 100,
        agent_type: Optional[str] = None
    ) -> List[Agent]:
        """Get list of agents."""
        query = select(Agent)
        if agent_type:
            query = query.where(Agent.type == agent_type)
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        query = select(Agent).where(Agent.id == agent_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_agent(self, agent: AgentCreate) -> Agent:
        """Create new agent."""
        db_agent = Agent(
            id=str(uuid4()),
            name=agent.name,
            type=agent.type,
            config=agent.config,
            metadata=agent.metadata,
            status="inactive"
        )
        
        self.db.add(db_agent)
        await self.db.commit()
        await self.db.refresh(db_agent)
        
        # Publish agent creation event
        await self.nats.publish(
            "agent.created",
            {
                "agent_id": db_agent.id,
                "name": db_agent.name,
                "type": db_agent.type,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return db_agent

    async def update_agent(self, agent_id: str, agent: AgentUpdate) -> Optional[Agent]:
        """Update agent."""
        db_agent = await self.get_agent(agent_id)
        if not db_agent:
            return None
            
        update_data = agent.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_agent, field, value)
            
        await self.db.commit()
        await self.db.refresh(db_agent)
        
        # Publish agent update event
        await self.nats.publish(
            "agent.updated",
            {
                "agent_id": db_agent.id,
                "name": db_agent.name,
                "type": db_agent.type,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return db_agent

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete agent."""
        db_agent = await self.get_agent(agent_id)
        if not db_agent:
            return False
            
        await self.db.delete(db_agent)
        await self.db.commit()
        
        # Publish agent deletion event
        await self.nats.publish(
            "agent.deleted",
            {
                "agent_id": agent_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return True

    async def discover_agents(self) -> List[AgentDiscovery]:
        """Discover available agents."""
        # TODO: Implement agent discovery logic
        return []

    async def get_agent_rules(
        self,
        agent_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AgentRule]:
        """Get agent rules."""
        query = select(AgentRule).where(AgentRule.agent_id == agent_id)
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_agent_rule(self, agent_id: str, rule_id: str) -> Optional[AgentRule]:
        """Get agent rule by ID."""
        query = select(AgentRule).where(
            AgentRule.agent_id == agent_id,
            AgentRule.id == rule_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_agent_rule(
        self,
        agent_id: str,
        rule: AgentRuleCreate
    ) -> Optional[AgentRule]:
        """Create new agent rule."""
        db_agent = await self.get_agent(agent_id)
        if not db_agent:
            return None
            
        db_rule = AgentRule(
            id=str(uuid4()),
            agent_id=agent_id,
            name=rule.name,
            description=rule.description,
            condition=rule.condition,
            action=rule.action,
            priority=rule.priority,
            enabled=rule.enabled
        )
        
        self.db.add(db_rule)
        await self.db.commit()
        await self.db.refresh(db_rule)
        
        # Publish rule creation event
        await self.nats.publish(
            "agent.rule.created",
            {
                "agent_id": agent_id,
                "rule_id": db_rule.id,
                "name": db_rule.name,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return db_rule

    async def update_agent_rule(
        self,
        agent_id: str,
        rule_id: str,
        rule: AgentRuleUpdate
    ) -> Optional[AgentRule]:
        """Update agent rule."""
        db_rule = await self.get_agent_rule(agent_id, rule_id)
        if not db_rule:
            return None
            
        update_data = rule.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_rule, field, value)
            
        await self.db.commit()
        await self.db.refresh(db_rule)
        
        # Publish rule update event
        await self.nats.publish(
            "agent.rule.updated",
            {
                "agent_id": agent_id,
                "rule_id": rule_id,
                "name": db_rule.name,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return db_rule

    async def delete_agent_rule(self, agent_id: str, rule_id: str) -> bool:
        """Delete agent rule."""
        db_rule = await self.get_agent_rule(agent_id, rule_id)
        if not db_rule:
            return False
            
        await self.db.delete(db_rule)
        await self.db.commit()
        
        # Publish rule deletion event
        await self.nats.publish(
            "agent.rule.deleted",
            {
                "agent_id": agent_id,
                "rule_id": rule_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return True

    async def update_agent_status(
        self,
        agent_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Agent]:
        """Update agent status."""
        db_agent = await self.get_agent(agent_id)
        if not db_agent:
            return None
            
        db_agent.status = status
        db_agent.last_seen = datetime.utcnow()
        if metadata:
            db_agent.metadata.update(metadata)
            
        await self.db.commit()
        await self.db.refresh(db_agent)
        
        # Publish status update event
        await self.nats.publish(
            "agent.status.updated",
            {
                "agent_id": agent_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return db_agent 