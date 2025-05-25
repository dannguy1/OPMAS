"""Configuration management schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ConfigurationBase(BaseModel):
    """Base configuration schema."""

    name: str = Field(..., description="Configuration name")
    description: Optional[str] = Field(None, description="Configuration description")
    component: str = Field(..., description="Component type (e.g., 'system', 'agent', 'device')")
    component_id: Optional[UUID] = Field(
        None, description="ID of the component this config belongs to"
    )
    version: str = Field(..., description="Configuration version")
    is_active: bool = Field(default=True, description="Whether this configuration is active")
    configuration: Dict[str, Any] = Field(..., description="Configuration data")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ConfigurationCreate(ConfigurationBase):
    """Schema for creating a configuration."""

    pass


class ConfigurationUpdate(BaseModel):
    """Schema for updating a configuration."""

    name: Optional[str] = Field(None, description="Configuration name")
    description: Optional[str] = Field(None, description="Configuration description")
    version: Optional[str] = Field(None, description="Configuration version")
    is_active: Optional[bool] = Field(None, description="Whether this configuration is active")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Configuration data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ConfigurationResponse(ConfigurationBase):
    """Schema for configuration response."""

    id: UUID = Field(..., description="Configuration ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic config."""

        from_attributes = True


class ConfigurationList(BaseModel):
    """Schema for configuration list response."""

    items: List[ConfigurationResponse] = Field(..., description="List of configurations")
    total: int = Field(..., description="Total number of configurations")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items returned")


class ConfigurationHistoryBase(BaseModel):
    """Base configuration history schema."""

    version: str = Field(..., description="Configuration version")
    configuration: Dict[str, Any] = Field(..., description="Configuration data")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    created_by: Optional[str] = Field(None, description="User or system that made the change")


class ConfigurationHistoryResponse(ConfigurationHistoryBase):
    """Schema for configuration history response."""

    id: UUID = Field(..., description="History entry ID")
    configuration_id: UUID = Field(..., description="Configuration ID")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        """Pydantic config."""

        from_attributes = True


class ConfigurationHistoryList(BaseModel):
    """Schema for configuration history list response."""

    items: List[ConfigurationHistoryResponse] = Field(..., description="List of history entries")
    total: int = Field(..., description="Total number of history entries")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items returned")
