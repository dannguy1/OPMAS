"""Agent management schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, IPvAnyAddress, validator


class AgentBase(BaseModel):
    """Base agent schema."""

    name: str = Field(..., description="Agent name")
    agent_type: str = Field(..., description="Type of agent")
    hostname: str = Field(..., description="Agent hostname")
    ip_address: IPvAnyAddress = Field(..., description="Agent IP address")
    port: int = Field(..., ge=1, le=65535, description="Agent port")
    status: str = Field(default="unknown", description="Agent status")
    enabled: bool = Field(default=True, description="Whether the agent is enabled")
    agent_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional agent metadata"
    )
    config: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Agent configuration"
    )

    @validator("agent_type")
    def validate_agent_type(cls, v: str) -> str:
        """Validate agent type."""
        valid_types = ["custom", "system", "network", "security"]
        if v not in valid_types:
            msg = f"Invalid agent type. Must be one of: {', '.join(valid_types)}"
            raise ValueError(msg)
        return v

    @validator("status")
    def validate_status(cls, v: str) -> str:
        """Validate agent status."""
        valid_statuses = ["unknown", "online", "offline", "error", "maintenance", "active"]
        if v not in valid_statuses:
            msg = f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            raise ValueError(msg)
        return v


class AgentCreate(AgentBase):
    """Agent creation schema."""

    pass


class AgentUpdate(BaseModel):
    """Agent update schema."""

    name: Optional[str] = Field(None, description="Agent name")
    agent_type: Optional[str] = Field(None, description="Type of agent")
    hostname: Optional[str] = Field(None, description="Agent hostname")
    ip_address: Optional[IPvAnyAddress] = Field(None, description="Agent IP address")
    port: Optional[int] = Field(None, ge=1, le=65535, description="Agent port")
    status: Optional[str] = Field(None, description="Agent status")
    enabled: Optional[bool] = Field(None, description="Whether the agent is enabled")
    agent_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional agent metadata")
    config: Optional[Dict[str, Any]] = Field(None, description="Agent configuration")

    @validator("agent_type")
    def validate_agent_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate agent type."""
        if v is None:
            return v
        valid_types = ["custom", "system", "network", "security"]
        if v not in valid_types:
            msg = f"Invalid agent type. Must be one of: {', '.join(valid_types)}"
            raise ValueError(msg)
        return v

    @validator("status")
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate agent status."""
        if v is None:
            return v
        valid_statuses = ["unknown", "online", "offline", "error", "maintenance", "active"]
        if v not in valid_statuses:
            msg = f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            raise ValueError(msg)
        return v


class AgentResponse(AgentBase):
    """Agent response schema."""

    id: UUID = Field(..., description="Agent ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_seen: Optional[datetime] = Field(None, description="Last time the agent was seen")
    device_id: Optional[UUID] = Field(None, description="Associated device ID")
    agent_type: str = Field(default="unknown", description="Type of agent")
    status: str = Field(default="unknown", description="Agent status")
    agent_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional agent metadata"
    )
    hostname: str = Field(default="", description="Agent hostname")
    ip_address: IPvAnyAddress = Field(..., description="Agent IP address")
    port: int = Field(..., ge=1, le=65535, description="Agent port")
    confidence: Optional[float] = Field(None, description="Confidence score of discovery")

    @validator("status")
    def validate_status(cls, v: str) -> str:
        """Validate agent status."""
        valid_statuses = ["unknown", "online", "offline", "error", "maintenance", "active"]
        if v not in valid_statuses:
            msg = f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            raise ValueError(msg)
        return v

    class Config:
        """Pydantic config."""

        from_attributes = True


class AgentStatus(BaseModel):
    """Agent status schema."""

    status: str = Field(..., description="Agent status")
    timestamp: datetime = Field(..., description="Status timestamp")
    details: Dict[str, Any] = Field(default_factory=dict, description="Status details")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Agent metrics")

    @validator("status")
    def validate_status(cls, v: str) -> str:
        """Validate agent status."""
        valid_statuses = ["unknown", "online", "offline", "error", "maintenance", "active"]
        if v not in valid_statuses:
            msg = f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            raise ValueError(msg)
        return v


class AgentDiscovery(BaseModel):
    """Agent discovery schema."""

    name: str = Field(..., description="Agent name")
    agent_type: str = Field(..., description="Type of agent")
    hostname: str = Field(..., description="Agent hostname")
    ip_address: IPvAnyAddress = Field(..., description="Agent IP address")
    port: int = Field(..., ge=1, le=65535, description="Agent port")
    confidence: float = Field(..., description="Confidence score of discovery")
    agent_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional discovery metadata"
    )


class AgentConfig(BaseModel):
    """Agent configuration schema."""

    config: Dict[str, Any] = Field(..., description="Agent configuration")
    version: str = Field(..., description="Configuration version")
    last_updated: datetime = Field(..., description="Last update timestamp")
    agent_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional configuration metadata"
    )


class AgentList(BaseModel):
    """List of agents response schema."""

    agents: List[AgentResponse] = Field(..., description="List of agents")
    total: int = Field(..., description="Total number of agents")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")

    class Config:
        """Pydantic config."""

        from_attributes = True
