"""System management endpoints."""

from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from opmas_mgmt_api.api.deps import get_db, get_nats
from opmas_mgmt_api.api.v1.endpoints.route_utils import create_route_builder
from opmas_mgmt_api.core.exceptions import ValidationError, ResourceNotFoundError
from opmas_mgmt_api.schemas.system import (
    SystemHealth,
    SystemMetrics,
    SystemStatus,
    SystemConfig,
    SystemConfigUpdate,
    SystemControl,
)
from opmas_mgmt_api.services.system import SystemService
from sqlalchemy.ext.asyncio import AsyncSession
import logging

router = APIRouter()
route = create_route_builder(router)
logger = logging.getLogger(__name__)


@route.get("/health", response_model=SystemHealth)
async def get_health(
    db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> SystemHealth:
    """Get system health status."""
    service = SystemService(db, nats)
    try:
        return await service.get_health()
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.get("/metrics", response_model=SystemMetrics)
async def get_metrics(
    db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> SystemMetrics:
    """Get system metrics."""
    service = SystemService(db, nats)
    try:
        return await service.get_metrics()
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.get("/status", response_model=SystemStatus)
async def get_status(
    db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> SystemStatus:
    """Get system status."""
    service = SystemService(db, nats)
    try:
        return await service.get_status()
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.get("/config", response_model=SystemConfig)
async def get_config(
    db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> SystemConfig:
    """Get system configuration."""
    service = SystemService(db, nats)
    try:
        return await service.get_config()
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.put("/config", response_model=SystemConfig)
async def update_config(
    config: SystemConfigUpdate,
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> SystemConfig:
    """Update system configuration."""
    service = SystemService(db, nats)
    try:
        return await service.update_config(config)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.post("/control", response_model=SystemControl)
async def control_system(
    action: str = Body(..., description="Control action to perform"),
    params: Optional[Dict[str, Any]] = Body(None, description="Action parameters"),
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> SystemControl:
    """Perform system control action."""
    service = SystemService(db, nats)
    try:
        return await service.control_system(action, params)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.get("", response_model=Dict[str, Any])
async def list_systems(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for system version or components"),
    sort_by: Optional[str] = Query("version", description="Field to sort by"),
    sort_direction: Optional[str] = Query("asc", description="Sort direction (asc or desc)"),
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> Dict[str, Any]:
    """List system configurations with optional filtering."""
    service = SystemService(db, nats)
    try:
        result = await service.list_systems(
            skip=skip,
            limit=limit,
            search=search,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
        return result
    except Exception as e:
        logger.error(f"Error listing systems: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
