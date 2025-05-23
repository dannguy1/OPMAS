"""Playbook management endpoints."""

from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from opmas_mgmt_api.api.deps import get_db, get_nats
from opmas_mgmt_api.services.playbooks import PlaybookService
from opmas_mgmt_api.schemas.playbooks import (
    PlaybookCreate,
    PlaybookUpdate,
    PlaybookResponse,
    PlaybookList,
    PlaybookStatus,
    PlaybookExecution
)
from opmas_mgmt_api.core.nats import NATSManager

router = APIRouter()

@router.get("", response_model=PlaybookList)
async def list_playbooks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    agent_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> PlaybookList:
    """List playbooks with optional filtering."""
    service = PlaybookService(db, nats)
    result = await service.list_playbooks(skip, limit, agent_type, enabled)
    return result

@router.post("", response_model=PlaybookResponse, status_code=201)
async def create_playbook(
    playbook: PlaybookCreate,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> PlaybookResponse:
    """Create a new playbook."""
    service = PlaybookService(db, nats)
    try:
        return await service.create_playbook(playbook)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{playbook_id}", response_model=PlaybookResponse)
async def get_playbook(
    playbook_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> PlaybookResponse:
    """Get playbook by ID."""
    service = PlaybookService(db, nats)
    try:
        return await service.get_playbook(playbook_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/{playbook_id}", response_model=PlaybookResponse)
async def update_playbook(
    playbook_id: UUID,
    playbook: PlaybookUpdate,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> PlaybookResponse:
    """Update a playbook."""
    service = PlaybookService(db, nats)
    try:
        return await service.update_playbook(playbook_id, playbook)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{playbook_id}", status_code=204)
async def delete_playbook(
    playbook_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> None:
    """Delete a playbook."""
    service = PlaybookService(db, nats)
    try:
        await service.delete_playbook(playbook_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{playbook_id}/status", response_model=PlaybookStatus)
async def get_playbook_status(
    playbook_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> PlaybookStatus:
    """Get playbook status."""
    service = PlaybookService(db, nats)
    try:
        return await service.get_playbook_status(playbook_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{playbook_id}/execute", response_model=PlaybookExecution)
async def execute_playbook(
    playbook_id: UUID,
    metadata: Optional[Dict[str, Any]] = Body(None),
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> PlaybookExecution:
    """Execute a playbook."""
    service = PlaybookService(db, nats)
    try:
        return await service.execute_playbook(playbook_id, metadata)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/executions/{execution_id}", response_model=PlaybookExecution)
async def get_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> PlaybookExecution:
    """Get playbook execution by ID."""
    service = PlaybookService(db, nats)
    try:
        return await service.get_execution(execution_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/executions/{execution_id}", response_model=PlaybookExecution)
async def update_execution_status(
    execution_id: UUID,
    status: str = Body(...),
    error: Optional[str] = Body(None),
    steps: Optional[list] = Body(None),
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> PlaybookExecution:
    """Update playbook execution status."""
    service = PlaybookService(db, nats)
    try:
        return await service.update_execution_status(execution_id, status, error, steps)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 