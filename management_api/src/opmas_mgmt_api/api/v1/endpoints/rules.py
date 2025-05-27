"""Rule management endpoints."""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from opmas_mgmt_api.api.deps import get_db, get_nats
from opmas_mgmt_api.api.v1.endpoints.route_utils import create_route_builder
from opmas_mgmt_api.core.exceptions import ResourceNotFoundError, ValidationError
from opmas_mgmt_api.schemas.rules import (
    RuleBase,
    RuleCreate,
    RuleList,
    RuleResponse,
    RuleStatus,
    RuleUpdate,
)
from opmas_mgmt_api.services.rules import RuleService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
route = create_route_builder(router)
logger = logging.getLogger(__name__)


@route.get("", response_model=RuleList)
async def list_rules(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for rule name or description"),
    sort_by: Optional[str] = Query("name", description="Field to sort by"),
    sort_direction: Optional[str] = Query("asc", description="Sort direction (asc or desc)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> RuleList:
    """List rules with optional filtering."""
    service = RuleService(db, nats)
    try:
        result = await service.list_rules(
            skip=skip,
            limit=limit,
            search=search,
            sort_by=sort_by,
            sort_direction=sort_direction,
            agent_type=category,  # Map category to agent_type
            enabled=enabled,
        )
        return result
    except Exception as e:
        logger.error(f"Error listing rules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@route.post("", response_model=RuleResponse)
async def create_rule(
    rule: RuleCreate, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> RuleResponse:
    """Create a new rule."""
    service = RuleService(db, nats)
    try:
        return await service.create_rule(rule)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> RuleResponse:
    """Get rule by ID."""
    service = RuleService(db, nats)
    try:
        return await service.get_rule(rule_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@route.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: UUID,
    rule: RuleUpdate,
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> RuleResponse:
    """Update a rule."""
    service = RuleService(db, nats)
    try:
        return await service.update_rule(rule_id, rule)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.delete("/{rule_id}")
async def delete_rule(
    rule_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> None:
    """Delete a rule."""
    service = RuleService(db, nats)
    try:
        await service.delete_rule(rule_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@route.get("/{rule_id}/status", response_model=RuleStatus)
async def get_rule_status(
    rule_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> RuleStatus:
    """Get rule status."""
    service = RuleService(db, nats)
    try:
        return await service.get_rule_status(rule_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@route.post("/{rule_id}/status", response_model=RuleStatus)
async def update_rule_status(
    rule_id: UUID,
    status: str = Body(...),
    error: Optional[str] = Body(None),
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> RuleStatus:
    """Update rule status."""
    service = RuleService(db, nats)
    try:
        return await service.update_rule_status(rule_id, status, error)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
