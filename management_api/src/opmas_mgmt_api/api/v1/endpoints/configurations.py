"""Configuration management endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from opmas_mgmt_api.api.deps import get_db, get_nats
from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.schemas.configurations import (
    ConfigurationCreate,
    ConfigurationHistoryList,
    ConfigurationList,
    ConfigurationResponse,
    ConfigurationUpdate,
)
from opmas_mgmt_api.services.configurations import ConfigurationService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", response_model=ConfigurationList)
async def list_configurations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    component: Optional[str] = None,
    component_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats),
) -> ConfigurationList:
    """List configurations with optional filtering."""
    service = ConfigurationService(db, nats)
    result = await service.list_configurations(skip, limit, component, component_id, is_active)
    return result


@router.post("", response_model=ConfigurationResponse, status_code=201)
async def create_configuration(
    configuration: ConfigurationCreate,
    created_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats),
) -> ConfigurationResponse:
    """Create a new configuration."""
    service = ConfigurationService(db, nats)
    try:
        return await service.create_configuration(configuration, created_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{configuration_id}", response_model=ConfigurationResponse)
async def get_configuration(
    configuration_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats),
) -> ConfigurationResponse:
    """Get configuration by ID."""
    service = ConfigurationService(db, nats)
    try:
        return await service.get_configuration(configuration_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{configuration_id}", response_model=ConfigurationResponse)
async def update_configuration(
    configuration_id: UUID,
    configuration: ConfigurationUpdate,
    updated_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats),
) -> ConfigurationResponse:
    """Update configuration."""
    service = ConfigurationService(db, nats)
    try:
        return await service.update_configuration(configuration_id, configuration, updated_by)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{configuration_id}", status_code=204)
async def delete_configuration(
    configuration_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats),
) -> None:
    """Delete configuration."""
    service = ConfigurationService(db, nats)
    try:
        await service.delete_configuration(configuration_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{configuration_id}/history", response_model=ConfigurationHistoryList)
async def get_configuration_history(
    configuration_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats),
) -> ConfigurationHistoryList:
    """Get configuration history."""
    service = ConfigurationService(db, nats)
    try:
        return await service.get_configuration_history(configuration_id, skip, limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/component/{component}/active", response_model=ConfigurationResponse)
async def get_active_configuration(
    component: str,
    component_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats),
) -> ConfigurationResponse:
    """Get active configuration for a component."""
    service = ConfigurationService(db, nats)
    try:
        return await service.get_active_configuration(component, component_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
