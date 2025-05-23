"""System control service."""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.models.control import ControlAction
from opmas_mgmt_api.schemas.control import (
    ControlActionCreate,
    ControlActionUpdate,
    ControlActionResponse,
    ControlActionStatus
)

logger = logging.getLogger(__name__)

class ControlService:
    """System control service."""

    def __init__(self, db: AsyncSession, nats: NATSManager):
        """Initialize control service."""
        self.db = db
        self.nats = nats

    async def create_control_action(
        self,
        action: str,
        component: Optional[str] = None
    ) -> ControlActionResponse:
        """Create a new control action."""
        # Validate action
        valid_actions = ["start", "stop", "restart", "reload"]
        if action not in valid_actions:
            raise ValueError(f"Invalid action. Must be one of: {', '.join(valid_actions)}")

        # Create action record
        control_action = ControlAction(
            id=str(uuid.uuid4()),
            action=action,
            component=component,
            status=ControlActionStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        self.db.add(control_action)
        await self.db.commit()
        await self.db.refresh(control_action)

        # Publish action event
        await self.nats.publish(
            "system.control.action.created",
            {
                "action_id": control_action.id,
                "action": action,
                "component": component,
                "timestamp": control_action.created_at.isoformat()
            }
        )

        return ControlActionResponse(
            id=control_action.id,
            action=control_action.action,
            component=control_action.component,
            status=control_action.status,
            created_at=control_action.created_at,
            updated_at=control_action.updated_at,
            details=control_action.details
        )

    async def update_control_action(
        self,
        action_id: str,
        status: ControlActionStatus,
        details: Optional[Dict[str, Any]] = None
    ) -> ControlActionResponse:
        """Update control action status."""
        # Get action
        query = select(ControlAction).where(ControlAction.id == action_id)
        result = await self.db.execute(query)
        control_action = result.scalar_one_or_none()
        
        if not control_action:
            raise ValueError(f"Control action not found: {action_id}")

        # Update action
        control_action.status = status
        if details:
            control_action.details = details
        control_action.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(control_action)

        # Publish status update
        await self.nats.publish(
            "system.control.action.updated",
            {
                "action_id": control_action.id,
                "action": control_action.action,
                "component": control_action.component,
                "status": control_action.status,
                "timestamp": control_action.updated_at.isoformat()
            }
        )

        return ControlActionResponse(
            id=control_action.id,
            action=control_action.action,
            component=control_action.component,
            status=control_action.status,
            created_at=control_action.created_at,
            updated_at=control_action.updated_at,
            details=control_action.details
        )

    async def get_control_action(self, action_id: str) -> ControlActionResponse:
        """Get control action by ID."""
        query = select(ControlAction).where(ControlAction.id == action_id)
        result = await self.db.execute(query)
        control_action = result.scalar_one_or_none()
        
        if not control_action:
            raise ValueError(f"Control action not found: {action_id}")

        return ControlActionResponse(
            id=control_action.id,
            action=control_action.action,
            component=control_action.component,
            status=control_action.status,
            created_at=control_action.created_at,
            updated_at=control_action.updated_at,
            details=control_action.details
        )

    async def list_control_actions(
        self,
        component: Optional[str] = None,
        status: Optional[ControlActionStatus] = None,
        limit: int = 100
    ) -> List[ControlActionResponse]:
        """List control actions with optional filtering."""
        query = select(ControlAction)
        
        if component:
            query = query.where(ControlAction.component == component)
        if status:
            query = query.where(ControlAction.status == status)
            
        query = query.order_by(ControlAction.created_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        actions = result.scalars().all()
        
        return [
            ControlActionResponse(
                id=action.id,
                action=action.action,
                component=action.component,
                status=action.status,
                created_at=action.created_at,
                updated_at=action.updated_at,
                details=action.details
            )
            for action in actions
        ]

    async def get_component_status(self, component: str) -> Dict[str, Any]:
        """Get status of a specific component."""
        # Get latest action for component
        query = select(ControlAction).where(
            ControlAction.component == component
        ).order_by(ControlAction.created_at.desc()).limit(1)
        
        result = await self.db.execute(query)
        latest_action = result.scalar_one_or_none()
        
        if not latest_action:
            return {
                "status": "unknown",
                "message": f"No control actions found for component: {component}"
            }
            
        return {
            "status": latest_action.status,
            "action": latest_action.action,
            "last_updated": latest_action.updated_at.isoformat(),
            "details": latest_action.details
        } 