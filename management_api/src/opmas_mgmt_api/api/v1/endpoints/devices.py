"""Device management endpoints."""

from typing import Optional, Dict, Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from opmas_mgmt_api.api.deps import get_db, get_nats
from opmas_mgmt_api.services.devices import DeviceService
from opmas_mgmt_api.schemas.devices import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceList,
    DeviceStatus,
    DeviceDiscovery,
    DeviceMetrics,
    DeviceConfiguration
)
from opmas_mgmt_api.core.nats import NATSManager

router = APIRouter()

@router.get("", response_model=DeviceList)
async def list_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    device_type: Optional[str] = None,
    status: Optional[str] = None,
    enabled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> DeviceList:
    """List devices with optional filtering."""
    service = DeviceService(db, nats)
    result = await service.list_devices(skip, limit, device_type, status, enabled)
    return result

@router.post("", response_model=DeviceResponse, status_code=201)
async def create_device(
    device: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> DeviceResponse:
    """Create a new device."""
    service = DeviceService(db, nats)
    try:
        return await service.create_device(device)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> DeviceResponse:
    """Get device by ID."""
    service = DeviceService(db, nats)
    try:
        return await service.get_device(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: UUID,
    device: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> DeviceResponse:
    """Update device details."""
    service = DeviceService(db, nats)
    try:
        return await service.update_device(device_id, device)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{device_id}", status_code=204)
async def delete_device(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> None:
    """Delete a device."""
    service = DeviceService(db, nats)
    try:
        await service.delete_device(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{device_id}/status", response_model=DeviceStatus)
async def get_device_status(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> DeviceStatus:
    """Get device status."""
    service = DeviceService(db, nats)
    try:
        return await service.get_device_status(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/discover", response_model=List[DeviceDiscovery])
async def discover_devices(
    network: str = Query(..., description="Network to scan (CIDR notation)"),
    device_types: Optional[List[str]] = Query(None, description="Filter by device types"),
    timeout: int = Query(5, ge=1, le=30, description="Discovery timeout in seconds"),
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> List[DeviceDiscovery]:
    """Discover devices on the network."""
    service = DeviceService(db, nats)
    try:
        return await service.discover_devices(network, device_types, timeout)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{device_id}/metrics", response_model=DeviceMetrics)
async def get_device_metrics(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> DeviceMetrics:
    """Get device metrics."""
    service = DeviceService(db, nats)
    try:
        return await service.get_device_metrics(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{device_id}/configuration", response_model=DeviceConfiguration)
async def get_device_configuration(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> DeviceConfiguration:
    """Get device configuration."""
    service = DeviceService(db, nats)
    try:
        return await service.get_device_configuration(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{device_id}/configuration", response_model=DeviceConfiguration)
async def update_device_configuration(
    device_id: UUID,
    configuration: Dict[str, Any] = Body(..., description="Device configuration"),
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> DeviceConfiguration:
    """Update device configuration."""
    service = DeviceService(db, nats)
    try:
        return await service.update_device_configuration(device_id, configuration)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) 