"""Action management schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ActionBase(BaseModel):
    """Base schema for actions."""

    name: str = Field(..., description="Action name")
    description: Optional[str] = Field(None, description="Action description")
    action_type: str = Field(..., description="Type of action")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    status: str = Field("pending", description="Action status")
    priority: int = Field(1, ge=1, le=5, description="Action priority (1-5)")
    finding_id: Optional[UUID] = Field(None, description="Associated finding ID")
    action_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ActionCreate(ActionBase):
    """Schema for creating an action."""

    pass


class ActionUpdate(BaseModel):
    """Schema for updating an action."""

    name: Optional[str] = Field(None, description="Action name")
    description: Optional[str] = Field(None, description="Action description")
    action_type: Optional[str] = Field(None, description="Type of action")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action parameters")
    status: Optional[str] = Field(None, description="Action status")
    priority: Optional[int] = Field(None, ge=1, le=5, description="Action priority (1-5)")
    finding_id: Optional[UUID] = Field(None, description="Associated finding ID")
    action_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ActionResponse(ActionBase):
    """Schema for action response."""

    id: UUID = Field(..., description="Action ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    result: Optional[Dict[str, Any]] = Field(None, description="Action result")
    error: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        """Pydantic config."""

        from_attributes = True


class ActionList(BaseModel):
    """Schema for list of actions."""

    items: List[ActionResponse] = Field(..., description="List of actions")
    total: int = Field(..., description="Total number of actions")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")
