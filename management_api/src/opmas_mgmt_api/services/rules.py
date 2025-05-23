"""Rule management service."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from opmas_mgmt_api.models.rules import Rule
from opmas_mgmt_api.schemas.rules import RuleCreate, RuleUpdate, RuleStatus
from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.core.exceptions import ResourceNotFoundError, ValidationError

class RuleService:
    """Rule management service."""

    def __init__(self, db: AsyncSession, nats: NATSManager):
        """Initialize service."""
        self.db = db
        self.nats = nats

    async def list_rules(
        self,
        skip: int = 0,
        limit: int = 100,
        agent_type: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> Dict[str, Any]:
        """List rules with optional filtering."""
        query = select(Rule)
        
        if agent_type:
            query = query.where(Rule.agent_type == agent_type)
        if enabled is not None:
            query = query.where(Rule.enabled == enabled)
            
        total = await self.db.scalar(select(Rule).where(query.whereclause))
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        rules = result.scalars().all()
        
        return {
            "items": rules,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    async def get_rule(self, rule_id: UUID) -> Rule:
        """Get rule by ID."""
        query = select(Rule).where(Rule.id == rule_id)
        result = await self.db.execute(query)
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise ResourceNotFoundError(f"Rule not found: {rule_id}")
            
        return rule

    async def create_rule(self, rule_data: RuleCreate) -> Rule:
        """Create a new rule."""
        # Check for duplicate name
        query = select(Rule).where(Rule.name == rule_data.name)
        result = await self.db.execute(query)
        if result.scalar_one_or_none():
            raise ValidationError(f"Rule creation failed: duplicate name: {rule_data.name}")
            
        rule = Rule(**rule_data.dict())
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        
        # Publish rule creation event
        await self.nats.publish(
            "rules.created",
            {
                "rule_id": str(rule.id),
                "agent_type": rule.agent_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return rule

    async def update_rule(self, rule_id: UUID, rule_data: RuleUpdate) -> Rule:
        """Update a rule."""
        rule = await self.get_rule(rule_id)
        
        # Check for duplicate name if name is being updated
        if rule_data.name and rule_data.name != rule.name:
            query = select(Rule).where(Rule.name == rule_data.name)
            result = await self.db.execute(query)
            if result.scalar_one_or_none():
                raise ValidationError(f"Rule update failed: duplicate name: {rule_data.name}")
        
        update_data = rule_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rule, field, value)
            
        rule.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(rule)
        
        # Publish rule update event
        await self.nats.publish(
            "rules.updated",
            {
                "rule_id": str(rule.id),
                "agent_type": rule.agent_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return rule

    async def delete_rule(self, rule_id: UUID) -> None:
        """Delete a rule."""
        rule = await self.get_rule(rule_id)
        
        await self.db.delete(rule)
        await self.db.commit()
        
        # Publish rule deletion event
        await self.nats.publish(
            "rules.deleted",
            {
                "rule_id": str(rule_id),
                "agent_type": rule.agent_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    async def get_rule_status(self, rule_id: UUID) -> RuleStatus:
        """Get rule status."""
        rule = await self.get_rule(rule_id)
        
        return RuleStatus(
            status="active" if rule.enabled else "disabled",
            last_triggered=rule.last_triggered,
            trigger_count=rule.trigger_count,
            details={
                "priority": rule.priority,
                "agent_type": rule.agent_type
            }
        )

    async def update_rule_status(
        self,
        rule_id: UUID,
        status: str,
        error: Optional[str] = None
    ) -> RuleStatus:
        """Update rule status."""
        rule = await self.get_rule(rule_id)
        
        if status == "triggered":
            rule.last_triggered = datetime.utcnow()
            rule.trigger_count += 1
        elif status == "error" and error:
            rule.rule_metadata = rule.rule_metadata or {}
            rule.rule_metadata["last_error"] = error
            
        await self.db.commit()
        await self.db.refresh(rule)
        
        return await self.get_rule_status(rule_id) 