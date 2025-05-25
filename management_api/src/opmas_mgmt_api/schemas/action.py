"""Pydantic models for Action responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ActionBase(BaseModel):
    """Base Action model with common attributes."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    priority: str = Field(..., pattern="^(high|medium|low)$")
    status: str = Field(..., pattern="^(pending|in_progress|completed|failed)$")
    finding_id: Optional[str] = Field(
        None, pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    device_id: Optional[str] = Field(
        None, pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    agent_id: Optional[str] = Field(
        None, pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    assigned_to: Optional[str] = Field(None, min_length=1, max_length=255)
    due_date: Optional[datetime] = None
    additional_data: Optional[str] = None


class ActionCreate(ActionBase):
    """Model for creating a new action."""

    pass


class ActionUpdate(BaseModel):
    """Model for updating an existing action."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    priority: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|failed)$")
    finding_id: Optional[str] = Field(
        None, pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    device_id: Optional[str] = Field(
        None, pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    agent_id: Optional[str] = Field(
        None, pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    assigned_to: Optional[str] = Field(None, min_length=1, max_length=255)
    due_date: Optional[datetime] = None
    additional_data: Optional[str] = None


class Action(ActionBase):
    """Model for action responses."""

    id: str = Field(..., pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True
