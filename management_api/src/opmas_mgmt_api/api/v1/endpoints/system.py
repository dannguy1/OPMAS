"""System management endpoints."""

from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from opmas_mgmt_api.api.deps import get_db, get_nats
from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.schemas.system import (
    SystemConfig,
    SystemConfigUpdate,
    SystemControl,
    SystemHealth,
    SystemMetrics,
    SystemStatus,
)
from opmas_mgmt_api.services.system import SystemService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    db: AsyncSession = Depends(get_db), nats: NATSManager = Depends(get_nats)
) -> SystemStatus:
    """Get overall system status."""
    service = SystemService(db, nats)
    return await service.get_system_status()


@router.get("/health", response_model=SystemHealth)
async def get_system_health(
    db: AsyncSession = Depends(get_db), nats: NATSManager = Depends(get_nats)
) -> SystemHealth:
    """Get system health status."""
    service = SystemService(db, nats)
    return await service.get_system_health()


@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics(
    db: AsyncSession = Depends(get_db), nats: NATSManager = Depends(get_nats)
) -> SystemMetrics:
    """Get system metrics."""
    service = SystemService(db, nats)
    return await service.get_system_metrics()


@router.get("/config", response_model=SystemConfig)
async def get_system_config(
    db: AsyncSession = Depends(get_db), nats: NATSManager = Depends(get_nats)
) -> SystemConfig:
    """Get system configuration."""
    service = SystemService(db, nats)
    return await service.get_system_config()


@router.put("/config", response_model=SystemConfig)
async def update_system_config(
    config: SystemConfigUpdate,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats),
) -> SystemConfig:
    """Update system configuration."""
    service = SystemService(db, nats)
    return await service.update_system_config(config)


@router.post("/control", response_model=SystemControl)
async def control_system(
    action: str = Body(..., description="Control action to perform"),
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats),
) -> SystemControl:
    """Control system operations."""
    service = SystemService(db, nats)
    return await service.control_system(action)


@router.get("/logs", response_model=List[Dict[str, Any]])
async def get_system_logs(
    level: str = Query(None, description="Log level filter"),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats),
) -> List[Dict[str, Any]]:
    """Get system logs."""
    service = SystemService(db, nats)
    return await service.get_system_logs(level, limit)
