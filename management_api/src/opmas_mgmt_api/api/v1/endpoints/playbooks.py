"""Playbook management endpoints."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from opmas_mgmt_api.api.deps import get_db, get_nats
from opmas_mgmt_api.api.v1.endpoints.route_utils import create_route_builder
from opmas_mgmt_api.core.exceptions import ResourceNotFoundError, ValidationError
from opmas_mgmt_api.schemas.playbooks import (
    PlaybookBase,
    PlaybookCreate,
    PlaybookExecution,
    PlaybookList,
    PlaybookResponse,
    PlaybookStatus,
    PlaybookUpdate,
)
from opmas_mgmt_api.services.playbooks import PlaybookService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
route = create_route_builder(router)


@route.get("", response_model=PlaybookList)
async def list_playbooks(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> PlaybookList:
    """List playbooks with optional filtering."""
    service = PlaybookService(db, nats)
    return await service.list_playbooks(
        skip=skip,
        limit=limit,
        agent_type=agent_type,
        enabled=enabled,
    )


@route.post("", response_model=PlaybookResponse)
async def create_playbook(
    playbook: PlaybookCreate, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> PlaybookResponse:
    """Create a new playbook."""
    service = PlaybookService(db, nats)
    try:
        return await service.create_playbook(playbook)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.get("/{playbook_id}", response_model=PlaybookResponse)
async def get_playbook(
    playbook_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> PlaybookResponse:
    """Get playbook by ID."""
    service = PlaybookService(db, nats)
    try:
        return await service.get_playbook(playbook_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@route.put("/{playbook_id}", response_model=PlaybookResponse)
async def update_playbook(
    playbook_id: UUID,
    playbook: PlaybookUpdate,
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> PlaybookResponse:
    """Update a playbook."""
    service = PlaybookService(db, nats)
    try:
        return await service.update_playbook(playbook_id, playbook)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.delete("/{playbook_id}")
async def delete_playbook(
    playbook_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> None:
    """Delete a playbook."""
    service = PlaybookService(db, nats)
    try:
        await service.delete_playbook(playbook_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@route.get("/{playbook_id}/status", response_model=PlaybookStatus)
async def get_playbook_status(
    playbook_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> PlaybookStatus:
    """Get playbook status."""
    service = PlaybookService(db, nats)
    try:
        return await service.get_playbook_status(playbook_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@route.post("/{playbook_id}/execute", response_model=PlaybookExecution)
async def execute_playbook(
    playbook_id: UUID,
    metadata: Optional[Dict[str, Any]] = Body(None),
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> PlaybookExecution:
    """Execute a playbook."""
    service = PlaybookService(db, nats)
    try:
        return await service.execute_playbook(playbook_id, metadata)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.get("/executions/{execution_id}", response_model=PlaybookExecution)
async def get_execution(
    execution_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> PlaybookExecution:
    """Get playbook execution by ID."""
    service = PlaybookService(db, nats)
    try:
        return await service.get_execution(execution_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@route.patch("/executions/{execution_id}", response_model=PlaybookExecution)
async def update_execution_status(
    execution_id: UUID,
    status: str = Body(...),
    error: Optional[str] = Body(None),
    steps: Optional[List[Dict[str, Any]]] = Body(None),
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> PlaybookExecution:
    """Update playbook execution status."""
    service = PlaybookService(db, nats)
    try:
        return await service.update_execution_status(execution_id, status, error, steps)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
