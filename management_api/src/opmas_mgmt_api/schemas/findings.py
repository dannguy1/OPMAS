"""Finding management schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FindingBase(BaseModel):
    """Base schema for findings."""

    title: str = Field(..., description="Finding title")
    description: str = Field(..., description="Finding description")
    severity: str = Field(..., description="Finding severity")
    status: str = Field("open", description="Finding status")
    source: str = Field(..., description="Finding source")
    device_id: Optional[UUID] = Field(None, description="Associated device ID")
    finding_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class FindingCreate(FindingBase):
    """Schema for creating a finding."""

    pass


class FindingUpdate(BaseModel):
    """Schema for updating a finding."""

    title: Optional[str] = Field(None, description="Finding title")
    description: Optional[str] = Field(None, description="Finding description")
    severity: Optional[str] = Field(None, description="Finding severity")
    status: Optional[str] = Field(None, description="Finding status")
    source: Optional[str] = Field(None, description="Finding source")
    device_id: Optional[UUID] = Field(None, description="Associated device ID")
    finding_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FindingResponse(FindingBase):
    """Schema for finding response."""

    id: UUID = Field(..., description="Finding ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    resolution: Optional[str] = Field(None, description="Resolution details")
    assigned_to: Optional[str] = Field(None, description="Assigned user/team")

    class Config:
        """Pydantic config."""

        from_attributes = True


class FindingList(BaseModel):
    """Schema for list of findings."""

    items: List[FindingResponse] = Field(..., description="List of findings")
    total: int = Field(..., description="Total number of findings")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")
