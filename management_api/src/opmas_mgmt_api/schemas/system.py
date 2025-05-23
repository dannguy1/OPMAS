"""System management schemas."""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class SystemHealth(BaseModel):
    """System health status."""
    status: str = Field(..., description="Overall system health status")
    components: Dict[str, Dict[str, str]] = Field(..., description="Health status of system components")
    timestamp: datetime = Field(..., description="Timestamp of health check")

class SystemMetrics(BaseModel):
    """System metrics."""
    components: Dict[str, Dict[str, Any]] = Field(..., description="Metrics from system components")
    system: Dict[str, Any] = Field(..., description="System-wide metrics")
    timestamp: datetime = Field(..., description="Timestamp of metrics collection")

class SystemStatus(BaseModel):
    """System status."""
    status: str = Field(..., description="Overall system status")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Status of system components")
    metrics: SystemMetrics = Field(..., description="System metrics")
    health: SystemHealth = Field(..., description="System health status")
    timestamp: datetime = Field(..., description="Timestamp of status check")

class SystemConfig(BaseModel):
    """System configuration."""
    version: str = Field(..., description="System version")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Component configurations")
    security: Dict[str, Any] = Field(..., description="Security settings")
    logging: Dict[str, Any] = Field(..., description="Logging configuration")
    timestamp: datetime = Field(..., description="Timestamp of configuration")

class SystemConfigUpdate(BaseModel):
    """System configuration update."""
    version: Optional[str] = Field(None, description="System version")
    components: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Component configurations")
    security: Optional[Dict[str, Any]] = Field(None, description="Security settings")
    logging: Optional[Dict[str, Any]] = Field(None, description="Logging configuration")

class SystemControl(BaseModel):
    """System control."""
    action: str = Field(..., description="Control action performed")
    status: str = Field(..., description="Status of control action")
    timestamp: datetime = Field(..., description="Timestamp of control action") 