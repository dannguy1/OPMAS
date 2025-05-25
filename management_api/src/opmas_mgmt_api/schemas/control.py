"""Control action schemas."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ControlActionStatus(str, Enum):
    """Control action status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ControlActionBase(BaseModel):
    """Base control action schema."""

    action: str = Field(..., description="Control action to perform")
    component: Optional[str] = Field(None, description="Component to control")


class ControlActionCreate(ControlActionBase):
    """Control action creation schema."""

    pass


class ControlActionUpdate(BaseModel):
    """Control action update schema."""

    status: ControlActionStatus = Field(..., description="New status of the action")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional details about the action"
    )


class ControlActionResponse(ControlActionBase):
    """Control action response schema."""

    id: str = Field(..., description="Unique identifier for the action")
    status: ControlActionStatus = Field(..., description="Current status of the action")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional details about the action"
    )
    created_at: datetime = Field(..., description="When the action was created")
    updated_at: datetime = Field(..., description="When the action was last updated")

    class Config:
        """Pydantic config."""

        from_attributes = True
