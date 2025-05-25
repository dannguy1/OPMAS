"""Rule management schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RuleBase(BaseModel):
    """Base rule schema."""

    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    agent_type: str = Field(..., description="Type of agent this rule applies to")
    condition: Dict[str, Any] = Field(..., description="Rule condition in JSON format")
    action: Dict[str, Any] = Field(..., description="Rule action in JSON format")
    priority: int = Field(default=0, description="Rule priority (higher number = higher priority)")
    enabled: bool = Field(default=True, description="Whether the rule is enabled")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional rule metadata")


class RuleCreate(RuleBase):
    """Schema for creating a rule."""

    pass


class RuleUpdate(BaseModel):
    """Schema for updating a rule."""

    name: Optional[str] = Field(None, description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    condition: Optional[Dict[str, Any]] = Field(None, description="Rule condition in JSON format")
    action: Optional[Dict[str, Any]] = Field(None, description="Rule action in JSON format")
    priority: Optional[int] = Field(None, description="Rule priority")
    enabled: Optional[bool] = Field(None, description="Whether the rule is enabled")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional rule metadata")


class RuleResponse(RuleBase):
    """Schema for rule response."""

    id: UUID = Field(..., description="Rule ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_triggered: Optional[datetime] = Field(None, description="Last time the rule was triggered")
    trigger_count: int = Field(default=0, description="Number of times the rule has been triggered")

    class Config:
        """Pydantic config."""

        from_attributes = True


class RuleList(BaseModel):
    """Schema for list of rules."""

    items: List[RuleResponse] = Field(..., description="List of rules")
    total: int = Field(..., description="Total number of rules")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")


class RuleStatus(BaseModel):
    """Schema for rule status."""

    status: str = Field(..., description="Rule status")
    last_triggered: Optional[datetime] = Field(None, description="Last time the rule was triggered")
    trigger_count: int = Field(..., description="Number of times the rule has been triggered")
    last_error: Optional[str] = Field(None, description="Last error message if any")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional status details")
