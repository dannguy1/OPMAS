"""Actions endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from opmas_mgmt_api.api.deps import get_current_user, get_db
from opmas_mgmt_api.schemas.action import Action, ActionCreate, ActionUpdate
from opmas_mgmt_api.schemas.auth import User
from opmas_mgmt_api.services.action import ActionService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/actions", response_model=List[Action])
async def get_actions(
    search: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = "due_date",
    sort_direction: str = "asc",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all actions with optional filtering and sorting."""
    try:
        service = ActionService(db)
        actions = await service.get_actions(
            search=search,
            priority=priority,
            status=status,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
        return actions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve actions: {str(e)}",
        )


@router.post("/actions", response_model=Action, status_code=status.HTTP_201_CREATED)
async def create_action(
    action: ActionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new action."""
    try:
        service = ActionService(db)
        return await service.create_action(action)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create action: {str(e)}",
        )


@router.get("/actions/{action_id}", response_model=Action)
async def get_action(
    action_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific action by ID."""
    try:
        service = ActionService(db)
        action = await service.get_action(action_id)
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action {action_id} not found",
            )
        return action
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve action: {str(e)}",
        )


@router.put("/actions/{action_id}", response_model=Action)
async def update_action(
    action_id: str,
    action: ActionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing action."""
    try:
        service = ActionService(db)
        updated_action = await service.update_action(action_id, action)
        if not updated_action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action {action_id} not found",
            )
        return updated_action
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update action: {str(e)}",
        )


@router.delete("/actions/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action(
    action_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an action."""
    try:
        service = ActionService(db)
        if not await service.delete_action(action_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action {action_id} not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete action: {str(e)}",
        )
