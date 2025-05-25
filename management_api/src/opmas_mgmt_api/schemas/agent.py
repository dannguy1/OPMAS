"""Agent management schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class AgentBase(BaseModel):
    """Base agent schema."""

    name: str = Field(..., description="Agent name")
    type: str = Field(..., description="Agent type (wifi, security, health, wan)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Agent configuration")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Agent metadata")

    @validator("type")
    def validate_type(cls, v):
        """Validate agent type."""
        valid_types = ["wifi", "security", "health", "wan"]
        if v not in valid_types:
            raise ValueError(f'Agent type must be one of: {", ".join(valid_types)}')
        return v


class AgentCreate(AgentBase):
    """Agent creation schema."""

    pass


class AgentUpdate(BaseModel):
    """Agent update schema."""

    name: Optional[str] = Field(None, description="Agent name")
    type: Optional[str] = Field(None, description="Agent type")
    config: Optional[Dict[str, Any]] = Field(None, description="Agent configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Agent metadata")

    @validator("type")
    def validate_type(cls, v):
        """Validate agent type."""
        if v is not None:
            valid_types = ["wifi", "security", "health", "wan"]
            if v not in valid_types:
                raise ValueError(f'Agent type must be one of: {", ".join(valid_types)}')
        return v


class AgentInDB(AgentBase):
    """Agent database schema."""

    id: str = Field(..., description="Agent ID")
    status: str = Field(..., description="Agent status")
    last_seen: Optional[datetime] = Field(None, description="Last seen timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic config."""

        orm_mode = True


class Agent(AgentInDB):
    """Agent response schema."""

    pass


class AgentRuleBase(BaseModel):
    """Base agent rule schema."""

    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    condition: Dict[str, Any] = Field(..., description="Rule condition")
    action: Dict[str, Any] = Field(..., description="Rule action")
    priority: int = Field(0, description="Rule priority")
    enabled: bool = Field(True, description="Whether rule is enabled")


class AgentRuleCreate(AgentRuleBase):
    """Agent rule creation schema."""

    pass


class AgentRuleUpdate(BaseModel):
    """Agent rule update schema."""

    name: Optional[str] = Field(None, description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    condition: Optional[Dict[str, Any]] = Field(None, description="Rule condition")
    action: Optional[Dict[str, Any]] = Field(None, description="Rule action")
    priority: Optional[int] = Field(None, description="Rule priority")
    enabled: Optional[bool] = Field(None, description="Whether rule is enabled")


class AgentRuleInDB(AgentRuleBase):
    """Agent rule database schema."""

    id: str = Field(..., description="Rule ID")
    agent_id: str = Field(..., description="Agent ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic config."""

        orm_mode = True


class AgentRule(AgentRuleInDB):
    """Agent rule response schema."""

    pass


class AgentDiscovery(BaseModel):
    """Agent discovery schema."""

    agent_id: str = Field(..., description="Discovered agent ID")
    name: str = Field(..., description="Discovered agent name")
    type: str = Field(..., description="Discovered agent type")
    metadata: Dict[str, Any] = Field(..., description="Discovered agent metadata")
    discovered_at: datetime = Field(..., description="Discovery timestamp")
