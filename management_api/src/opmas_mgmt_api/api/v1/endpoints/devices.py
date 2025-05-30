"""Device management endpoints."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from opmas_mgmt_api.api.deps import get_db, get_nats
from opmas_mgmt_api.api.v1.endpoints.route_utils import create_route_builder
from opmas_mgmt_api.core.exceptions import ResourceNotFoundError, ValidationError
from opmas_mgmt_api.schemas.devices import (
    DeviceBase,
    DeviceConfiguration,
    DeviceCreate,
    DeviceDiscovery,
    DeviceList,
    DeviceMetrics,
    DeviceResponse,
    DeviceStatus,
    DeviceUpdate,
)
from opmas_mgmt_api.services.devices import DeviceService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
route = create_route_builder(router)


@route.get("", response_model=DeviceList)
async def list_devices(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    search: Optional[str] = Query(None, description="Search term"),
    sort_by: str = Query("name", description="Field to sort by"),
    sort_direction: str = Query("asc", description="Sort direction (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> DeviceList:
    """List devices with optional filtering."""
    service = DeviceService(db, nats)
    return await service.list_devices(
        skip=skip,
        limit=limit,
        device_type=device_type,
        status=status,
        enabled=enabled,
        search=search,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )


@route.post("", response_model=DeviceResponse)
async def create_device(
    device: DeviceCreate, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> DeviceResponse:
    """Create a new device."""
    service = DeviceService(db, nats)
    try:
        return await service.create_device(device)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)) -> DeviceResponse:
    """Get device by ID."""
    service = DeviceService(db, nats)
    try:
        return await service.get_device(device_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@route.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: UUID,
    device: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> DeviceResponse:
    """Update a device."""
    service = DeviceService(db, nats)
    try:
        return await service.update_device(device_id, device)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.delete("/{device_id}")
async def delete_device(device_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)) -> None:
    """Delete a device."""
    service = DeviceService(db, nats)
    try:
        await service.delete_device(device_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@route.get("/{device_id}/status", response_model=DeviceStatus)
async def get_device_status(
    device_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> DeviceStatus:
    """Get device status."""
    service = DeviceService(db, nats)
    try:
        return await service.get_device_status(device_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@route.post("/{device_id}/status", response_model=DeviceStatus)
async def update_device_status(
    device_id: UUID,
    status: str = Body(...),
    details: Optional[Dict[str, Any]] = Body(None),
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> DeviceStatus:
    """Update device status."""
    service = DeviceService(db, nats)
    try:
        return await service.update_device_status(device_id, status, details)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.get("/{device_id}/metrics", response_model=DeviceMetrics)
async def get_device_metrics(
    device_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> DeviceMetrics:
    """Get device metrics."""
    service = DeviceService(db, nats)
    try:
        return await service.get_device_metrics(device_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@route.get("/{device_id}/configuration", response_model=DeviceConfiguration)
async def get_device_configuration(
    device_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> DeviceConfiguration:
    """Get device configuration."""
    service = DeviceService(db, nats)
    try:
        return await service.get_device_configuration(device_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@route.put("/{device_id}/configuration", response_model=DeviceConfiguration)
async def update_device_configuration(
    device_id: UUID,
    configuration: Dict[str, Any] = Body(...),
    version: Optional[str] = Body(None),
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> DeviceConfiguration:
    """Update device configuration."""
    service = DeviceService(db, nats)
    try:
        return await service.update_device_configuration(device_id, configuration, version)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.post("/discover", response_model=List[DeviceDiscovery])
async def discover_devices(
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> List[DeviceDiscovery]:
    """Discover available devices."""
    service = DeviceService(db, nats)
    try:
        return await service.discover_devices(device_type)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
