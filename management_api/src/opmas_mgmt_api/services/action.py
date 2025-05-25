"""Action service for managing remediation actions."""

import logging
from typing import List, Optional

from opmas_mgmt_api.models.action import Action
from opmas_mgmt_api.schemas.action import ActionCreate, ActionUpdate
from sqlalchemy import asc, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ActionService:
    """Service for managing remediation actions."""

    def __init__(self, db: AsyncSession):
        """Initialize action service."""
        self.db = db

    async def get_actions(
        self,
        search: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "due_date",
        sort_direction: str = "asc",
    ) -> List[Action]:
        """Get actions with optional filtering and sorting.

        Args:
            search: Optional search term to filter by title or description
            priority: Optional priority filter
            status: Optional status filter
            sort_by: Field to sort by
            sort_direction: Sort direction (asc/desc)

        Returns:
            List of actions matching the criteria
        """
        query = select(Action)

        # Apply filters
        if search:
            query = query.where(
                or_(
                    Action.title.ilike(f"%{search}%"),
                    Action.description.ilike(f"%{search}%"),
                )
            )
        if priority:
            query = query.where(Action.priority == priority)
        if status:
            query = query.where(Action.status == status)

        # Apply sorting
        sort_column = getattr(Action, sort_by, Action.due_date)
        if sort_direction.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_action(self, action_id: str) -> Optional[Action]:
        """Get an action by ID.

        Args:
            action_id: ID of the action to retrieve

        Returns:
            Action if found, None otherwise
        """
        query = select(Action).where(Action.id == action_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_action(self, action_data: ActionCreate) -> Action:
        """Create a new action.

        Args:
            action_data: Action data

        Returns:
            Created action
        """
        action = Action(**action_data.model_dump())
        self.db.add(action)
        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def update_action(self, action_id: str, action_data: ActionUpdate) -> Optional[Action]:
        """Update an action.

        Args:
            action_id: ID of the action to update
            action_data: Updated action data

        Returns:
            Updated action if found, None otherwise
        """
        action = await self.get_action(action_id)
        if not action:
            return None

        update_data = action_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(action, field, value)

        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def delete_action(self, action_id: str) -> bool:
        """Delete an action.

        Args:
            action_id: ID of the action to delete

        Returns:
            True if deleted, False if not found
        """
        action = await self.get_action(action_id)
        if not action:
            return False

        await self.db.delete(action)
        await self.db.commit()
        return True
