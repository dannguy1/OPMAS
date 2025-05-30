"""Action management endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from opmas_mgmt_api.api.deps import get_db, get_nats
from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.schemas.actions import ActionCreate, ActionResponse, ActionUpdate
from opmas_mgmt_api.services.actions import ActionService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=List[ActionResponse])
async def get_actions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    finding_id: Optional[UUID] = None,
    search: Optional[str] = None,
    sort_by: str = "due_date",
    sort_direction: str = "asc",
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats),
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
        db: Database session
        nats: NATS manager

    Returns:
        List of actions
    """
    service = ActionService(db, nats)
    return await service.list_actions(
        skip=skip,
        limit=limit,
        status=status,
        finding_id=finding_id,
        search=search,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )


@router.post("/", response_model=ActionResponse)
async def create_action(
    action: ActionCreate,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats),
) -> ActionResponse:
    """Create a new action.

    Args:
        action: Action data
        db: Database session
        nats: NATS manager

    Returns:
        Created action

    Raises:
        HTTPException: If action data is invalid
    """
    service = ActionService(db, nats)
    try:
        return await service.create_action(action)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{action_id}", response_model=ActionResponse)
async def get_action(
    action_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats),
) -> ActionResponse:
    """Get action by ID.

    Args:
        action_id: Action ID
        db: Database session
        nats: NATS manager

    Returns:
        Action data

    Raises:
        HTTPException: If action not found
    """
    service = ActionService(db, nats)
    try:
        return await service.get_action(action_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{action_id}", response_model=ActionResponse)
async def update_action(
    action_id: UUID,
    action: ActionUpdate,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats),
) -> ActionResponse:
    """Update an action.

    Args:
        action_id: Action ID
        action: Updated action data
        db: Database session
        nats: NATS manager

    Returns:
        Updated action

    Raises:
        HTTPException: If action not found or data is invalid
    """
    service = ActionService(db, nats)
    try:
        return await service.update_action(action_id, action)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{action_id}")
async def delete_action(
    action_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats),
) -> None:
    """Delete an action.

    Args:
        action_id: Action ID
        db: Database session
        nats: NATS manager

    Raises:
        HTTPException: If action not found
    """
    service = ActionService(db, nats)
    try:
        await service.delete_action(action_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
