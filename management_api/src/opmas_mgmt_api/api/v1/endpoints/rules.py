"""Rule management endpoints."""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from opmas_mgmt_api.api.deps import get_db, get_nats
from opmas_mgmt_api.services.rules import RuleService
from opmas_mgmt_api.schemas.rules import (
    RuleCreate,
    RuleUpdate,
    RuleResponse,
    RuleList,
    RuleStatus
)
from opmas_mgmt_api.core.nats import NATSManager

router = APIRouter()

@router.get("", response_model=RuleList)
async def list_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    agent_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> RuleList:
    """List rules with optional filtering."""
    service = RuleService(db, nats)
    result = await service.list_rules(skip, limit, agent_type, enabled)
    return result

@router.post("", response_model=RuleResponse, status_code=201)
async def create_rule(
    rule: RuleCreate,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> RuleResponse:
    """Create a new rule."""
    service = RuleService(db, nats)
    try:
        return await service.create_rule(rule)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> RuleResponse:
    """Get rule by ID."""
    service = RuleService(db, nats)
    try:
        return await service.get_rule(rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: UUID,
    rule: RuleUpdate,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> RuleResponse:
    """Update a rule."""
    service = RuleService(db, nats)
    try:
        return await service.update_rule(rule_id, rule)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> None:
    """Delete a rule."""
    service = RuleService(db, nats)
    try:
        await service.delete_rule(rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{rule_id}/status", response_model=RuleStatus)
async def get_rule_status(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> RuleStatus:
    """Get rule status."""
    service = RuleService(db, nats)
    try:
        return await service.get_rule_status(rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{rule_id}/status", response_model=RuleStatus)
async def update_rule_status(
    rule_id: UUID,
    status: str,
    error: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> RuleStatus:
    """Update rule status."""
    service = RuleService(db, nats)
    try:
        return await service.update_rule_status(rule_id, status, error)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 