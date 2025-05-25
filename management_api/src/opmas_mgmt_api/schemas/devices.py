"""Device management schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, IPvAnyAddress


class DeviceBase(BaseModel):
    """Base device schema."""

    hostname: str = Field(..., description="Device hostname")
    ip_address: IPvAnyAddress = Field(..., description="Device IP address")
    device_type: str = Field(..., description="Type of device (e.g., 'router', 'switch')")
    model: Optional[str] = Field(None, description="Device model")
    firmware_version: Optional[str] = Field(None, description="Device firmware version")
    status: str = Field(default="unknown", description="Device status")
    enabled: bool = Field(default=True, description="Whether the device is enabled")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional device metadata"
    )


class DeviceCreate(DeviceBase):
    """Schema for creating a device."""

    pass


class DeviceUpdate(BaseModel):
    """Schema for updating a device."""

    hostname: Optional[str] = Field(None, description="Device hostname")
    ip_address: Optional[IPvAnyAddress] = Field(None, description="Device IP address")
    device_type: Optional[str] = Field(None, description="Type of device")
    model: Optional[str] = Field(None, description="Device model")
    firmware_version: Optional[str] = Field(None, description="Device firmware version")
    status: Optional[str] = Field(None, description="Device status")
    enabled: Optional[bool] = Field(None, description="Whether the device is enabled")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional device metadata")


class DeviceResponse(DeviceBase):
    """Schema for device response."""

    id: UUID = Field(..., description="Device ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_seen: Optional[datetime] = Field(None, description="Last seen timestamp")

    class Config:
        """Pydantic config."""

        from_attributes = True


class DeviceList(BaseModel):
    """Schema for device list response."""

    items: List[DeviceResponse] = Field(..., description="List of devices")
    total: int = Field(..., description="Total number of devices")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items returned")


class DeviceStatus(BaseModel):
    """Schema for device status."""

    status: str = Field(..., description="Device status")
    timestamp: datetime = Field(..., description="Status timestamp")
    details: Dict[str, Any] = Field(default_factory=dict, description="Status details")


class DeviceDiscovery(BaseModel):
    """Schema for discovered device."""

    ip_address: str = Field(..., description="Device IP address")
    hostname: str = Field(..., description="Device hostname")
    device_type: str = Field(..., description="Type of device")
    model: Optional[str] = Field(None, description="Device model")
    firmware_version: Optional[str] = Field(None, description="Device firmware version")
    status: str = Field(..., description="Device status")


class DeviceMetrics(BaseModel):
    """Schema for device metrics."""

    device_id: UUID = Field(..., description="Device ID")
    timestamp: datetime = Field(..., description="Metrics timestamp")
    metrics: Dict[str, Any] = Field(..., description="Device metrics")


class DeviceConfiguration(BaseModel):
    """Schema for device configuration."""

    device_id: UUID = Field(..., description="Device ID")
    configuration: Dict[str, Any] = Field(..., description="Device configuration")
    timestamp: datetime = Field(..., description="Configuration timestamp")
    version: Optional[str] = Field(None, description="Configuration version")
