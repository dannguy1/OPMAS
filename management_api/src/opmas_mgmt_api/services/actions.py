"""Action management service."""

from typing import List, Optional
from uuid import UUID

from opmas_mgmt_api.core.exceptions import ResourceNotFoundError, ValidationError
from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.models.actions import Action
from opmas_mgmt_api.schemas.actions import ActionCreate, ActionList, ActionResponse, ActionUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ActionService:
    """Service for managing actions."""

    def __init__(self, db: AsyncSession, nats: NATSManager):
        """Initialize service.

        Args:
            db: Database session
            nats: NATS manager
        """
        self.db = db
        self.nats = nats

    async def list_actions(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        finding_id: Optional[UUID] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_direction: str = "asc",
    ) -> List[ActionResponse]:
        """List actions with optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by status
            finding_id: Filter by finding ID
            search: Search term
            sort_by: Field to sort by
            sort_direction: Sort direction (asc/desc)

        Returns:
            List of actions
        """
        # Build base query
        query = select(
            Action.id,
            Action.description,
            Action.action_type,
            Action.status,
            Action.priority,
            Action.action_metadata,
            Action.created_at,
            Action.updated_at,
            Action.completed_at,
            Action.finding_id,
            Action.assignee_id,
        )

        # Apply filters
        if status:
            query = query.where(Action.status == status)
        if finding_id:
            query = query.where(Action.finding_id == finding_id)
        if search:
            query = query.where((Action.description.ilike(f"%{search}%")))

        # Map frontend field names to model field names
        field_mapping = {
            "dueDate": "completed_at",
            "createdAt": "created_at",
            "updatedAt": "updated_at",
            "findingId": "finding_id",
            "completedAt": "completed_at",
            "actionType": "action_type",
            "priority": "priority",
            "assignedTo": "assignee_id",
        }
        sort_field = field_mapping.get(sort_by, sort_by)

        # Apply sorting
        sort_column = getattr(Action, sort_field, Action.created_at)
        if sort_direction.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        actions = result.scalars().all()

        return [ActionResponse.model_validate(action) for action in actions]

    async def create_action(self, action: ActionCreate) -> ActionResponse:
        """Create a new action.

        Args:
            action: Action data

        Returns:
            Created action

        Raises:
            ValidationError: If action data is invalid
        """
        try:
            db_action = Action(**action.model_dump())
            self.db.add(db_action)
            await self.db.commit()
            await self.db.refresh(db_action)
            return ActionResponse.model_validate(db_action)
        except Exception as e:
            await self.db.rollback()
            raise ValidationError(f"Failed to create action: {str(e)}")

    async def get_action(self, action_id: UUID) -> ActionResponse:
        """Get action by ID.

        Args:
            action_id: Action ID

        Returns:
            Action data

        Raises:
            ResourceNotFoundError: If action not found
        """
        result = await self.db.execute(select(Action).where(Action.id == action_id))
        action = result.scalar_one_or_none()

        if not action:
            raise ResourceNotFoundError(f"Action {action_id} not found")

        return ActionResponse.model_validate(action)

    async def update_action(self, action_id: UUID, action: ActionUpdate) -> ActionResponse:
        """Update an action.

        Args:
            action_id: Action ID
            action: Updated action data

        Returns:
            Updated action

        Raises:
            ResourceNotFoundError: If action not found
            ValidationError: If action data is invalid
        """
        try:
            result = await self.db.execute(select(Action).where(Action.id == action_id))
            db_action = result.scalar_one_or_none()

            if not db_action:
                raise ResourceNotFoundError(f"Action {action_id} not found")

            update_data = action.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_action, field, value)

            await self.db.commit()
            await self.db.refresh(db_action)
            return ActionResponse.model_validate(db_action)
        except ResourceNotFoundError:
            raise
        except Exception as e:
            await self.db.rollback()
            raise ValidationError(f"Failed to update action: {str(e)}")

    async def delete_action(self, action_id: UUID) -> None:
        """Delete an action.

        Args:
            action_id: Action ID

        Raises:
            ResourceNotFoundError: If action not found
        """
        result = await self.db.execute(select(Action).where(Action.id == action_id))
        action = result.scalar_one_or_none()

        if not action:
            raise ResourceNotFoundError(f"Action {action_id} not found")

        await self.db.delete(action)
        await self.db.commit()
