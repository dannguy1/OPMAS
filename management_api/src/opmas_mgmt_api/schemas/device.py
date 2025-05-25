import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, IPvAnyAddress, validator


class DeviceBase(BaseModel):
    hostname: str
    ip_address: IPvAnyAddress
    device_type: str
    configuration: Optional[Dict[str, Any]] = None

    @validator("hostname")
    def validate_hostname(cls, v):
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]$", v):
            raise ValueError("Invalid hostname format")
        return v


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    hostname: Optional[str] = None
    ip_address: Optional[IPvAnyAddress] = None
    device_type: Optional[str] = None
    status: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

    @validator("hostname")
    def validate_hostname(cls, v):
        if v is not None and not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]$", v):
            raise ValueError("Invalid hostname format")
        return v


class DeviceInDB(DeviceBase):
    id: int
    status: str
    last_seen: datetime
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class DeviceStatus(BaseModel):
    status: str
    last_seen: datetime
    is_active: bool


class DeviceConfiguration(BaseModel):
    configuration: Dict[str, Any]
    updated_at: datetime
