"""Pydantic models for Finding responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FindingBase(BaseModel):
    """Base Finding model with common attributes."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    severity: str = Field(..., pattern="^(critical|high|medium|low)$")
    status: str = Field(..., pattern="^(open|in_progress|resolved|closed)$")
    source: str = Field(..., min_length=1, max_length=255)
    device_id: Optional[str] = Field(
        None, pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    agent_id: Optional[str] = Field(
        None, pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    rule_id: Optional[str] = Field(
        None, pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    additional_data: Optional[str] = None


class FindingCreate(FindingBase):
    """Model for creating a new finding."""

    pass


class FindingUpdate(BaseModel):
    """Model for updating an existing finding."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    severity: Optional[str] = Field(None, pattern="^(critical|high|medium|low)$")
    status: Optional[str] = Field(None, pattern="^(open|in_progress|resolved|closed)$")
    source: Optional[str] = Field(None, min_length=1, max_length=255)
    device_id: Optional[str] = Field(
        None, pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    agent_id: Optional[str] = Field(
        None, pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    rule_id: Optional[str] = Field(
        None, pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    additional_data: Optional[str] = None


class Finding(FindingBase):
    """Model for finding responses."""

    id: str = Field(..., pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True
