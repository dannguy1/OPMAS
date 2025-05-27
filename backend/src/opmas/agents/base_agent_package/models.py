"""Data models for the base agent package."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class Severity(str, Enum):
    """Severity levels for findings."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Finding(BaseModel):
    """A finding reported by an agent."""

    finding_id: str = Field(..., description="Unique identifier for the finding")
    agent_id: str = Field(..., description="ID of the agent that reported the finding")
    agent_type: str = Field(
        ..., description="Type of the agent that reported the finding"
    )
    severity: Severity = Field(..., description="Severity level of the finding")
    title: str = Field(..., description="Short title describing the finding")
    description: str = Field(..., description="Detailed description of the finding")
    source: str = Field(..., description="Source of the finding")
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional details about the finding",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the finding was created",
    )
    remediation: Optional[str] = Field(None, description="Suggested remediation steps")
    references: List[str] = Field(
        default_factory=list,
        description="Reference links or documentation",
    )

    @validator("finding_id")
    def validate_finding_id(cls, v: str) -> str:
        """Validate the finding ID format."""
        if not v or len(v) < 8:
            raise ValueError("Finding ID must be at least 8 characters long")
        return v

    @validator("severity")
    def validate_severity(cls, v: Severity) -> Severity:
        """Validate the severity level."""
        if v not in Severity:
            raise ValueError(f"Invalid severity level: {v}")
        return v


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    agent_id: str = Field(..., description="Unique identifier for the agent")
    agent_type: str = Field(..., description="Type of the agent")
    nats_url: str = Field(..., description="NATS server URL")
    heartbeat_interval: int = Field(
        default=30,
        description="Interval in seconds between heartbeats",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level for the agent",
    )
    metrics_enabled: bool = Field(
        default=True,
        description="Whether to enable metrics collection",
    )

    @validator("agent_id")
    def validate_agent_id(cls, v: str) -> str:
        """Validate the agent ID format."""
        if not v or len(v) < 8:
            raise ValueError("Agent ID must be at least 8 characters long")
        return v

    @validator("nats_url")
    def validate_nats_url(cls, v: str) -> str:
        """Validate the NATS URL format."""
        if not v.startswith(("nats://", "tls://")):
            raise ValueError("NATS URL must start with nats:// or tls://")
        return v

    @validator("heartbeat_interval")
    def validate_heartbeat_interval(cls, v: int) -> int:
        """Validate the heartbeat interval."""
        if v < 5:
            raise ValueError("Heartbeat interval must be at least 5 seconds")
        return v

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate the log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v.upper()
