"""Agent management schemas."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, IPvAnyAddress, validator

class AgentBase(BaseModel):
    """Base agent schema."""
    name: str = Field(..., description="Agent name")
    agent_type: str = Field(..., description="Type of agent (e.g., 'wifi', 'security', 'health')")
    hostname: str = Field(..., description="Agent hostname")
    ip_address: IPvAnyAddress = Field(..., description="Agent IP address")
    port: int = Field(..., ge=1, le=65535, description="Agent port")
    status: str = Field(default="unknown", description="Agent status")
    enabled: bool = Field(default=True, description="Whether the agent is enabled")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional agent metadata")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Agent configuration")

    @validator('agent_type')
    def validate_agent_type(cls, v):
        """Validate agent type."""
        valid_types = ['wifi', 'security', 'health', 'wan']
        if v not in valid_types:
            raise ValueError(f"Invalid agent type. Must be one of: {', '.join(valid_types)}")
        return v

    @validator('status')
    def validate_status(cls, v):
        """Validate agent status."""
        valid_statuses = ['unknown', 'online', 'offline', 'error', 'maintenance']
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return v

class AgentCreate(AgentBase):
    """Schema for creating an agent."""
    pass

class AgentUpdate(BaseModel):
    """Schema for updating an agent."""
    name: Optional[str] = Field(None, description="Agent name")
    agent_type: Optional[str] = Field(None, description="Type of agent")
    hostname: Optional[str] = Field(None, description="Agent hostname")
    ip_address: Optional[IPvAnyAddress] = Field(None, description="Agent IP address")
    port: Optional[int] = Field(None, ge=1, le=65535, description="Agent port")
    status: Optional[str] = Field(None, description="Agent status")
    enabled: Optional[bool] = Field(None, description="Whether the agent is enabled")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional agent metadata")
    config: Optional[Dict[str, Any]] = Field(None, description="Agent configuration")

    @validator('agent_type')
    def validate_agent_type(cls, v):
        """Validate agent type."""
        if v is not None:
            valid_types = ['wifi', 'security', 'health', 'wan']
            if v not in valid_types:
                raise ValueError(f"Invalid agent type. Must be one of: {', '.join(valid_types)}")
        return v

    @validator('status')
    def validate_status(cls, v):
        """Validate agent status."""
        if v is not None:
            valid_statuses = ['unknown', 'online', 'offline', 'error', 'maintenance']
            if v not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return v

class AgentResponse(AgentBase):
    """Schema for agent response."""
    id: UUID = Field(..., description="Agent ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_seen: Optional[datetime] = Field(None, description="Last time the agent was seen")
    device_id: Optional[UUID] = Field(None, description="Associated device ID")

    class Config:
        """Pydantic config."""
        from_attributes = True

class AgentList(BaseModel):
    """Schema for list of agents."""
    items: List[AgentResponse] = Field(..., description="List of agents")
    total: int = Field(..., description="Total number of agents")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")

class AgentStatus(BaseModel):
    """Schema for agent status."""
    status: str = Field(..., description="Agent status")
    last_seen: Optional[datetime] = Field(None, description="Last time the agent was seen")
    device_status: Optional[str] = Field(None, description="Associated device status")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional status details")

class AgentDiscovery(BaseModel):
    """Schema for agent discovery."""
    name: str = Field(..., description="Agent name")
    agent_type: str = Field(..., description="Type of agent")
    hostname: str = Field(..., description="Agent hostname")
    ip_address: IPvAnyAddress = Field(..., description="Agent IP address")
    port: int = Field(..., ge=1, le=65535, description="Agent port")
    confidence: float = Field(..., description="Confidence score of discovery")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional discovery metadata")

class AgentConfig(BaseModel):
    """Schema for agent configuration."""
    config: Dict[str, Any] = Field(..., description="Agent configuration")
    version: str = Field(..., description="Configuration version")
    last_updated: datetime = Field(..., description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional configuration metadata") 