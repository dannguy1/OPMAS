"""Log Pydantic schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class LogSourceBase(BaseModel):
    """Base log source schema."""

    identifier: Optional[str] = Field(None, description="Source identifier")
    ip_address: Optional[str] = Field(None, description="Source IP address")


class LogSourceCreate(LogSourceBase):
    """Log source creation schema."""

    first_seen: datetime = Field(..., description="First seen timestamp")
    last_seen: datetime = Field(..., description="Last seen timestamp")


class LogSourceUpdate(LogSourceBase):
    """Log source update schema."""

    last_seen: datetime = Field(..., description="Last seen timestamp")


class LogSource(LogSourceBase):
    """Log source schema."""

    id: int = Field(..., description="Source ID")
    first_seen: datetime = Field(..., description="First seen timestamp")
    last_seen: datetime = Field(..., description="Last seen timestamp")

    class Config:
        """Pydantic config."""

        from_attributes = True


class LogEntryBase(BaseModel):
    """Base log entry schema."""

    timestamp: datetime = Field(..., description="Log timestamp")
    level: int = Field(..., description="Log level (0-7)")
    facility: int = Field(..., description="Log facility (0-23)")
    message: str = Field(..., description="Log message")
    raw_log: str = Field(..., description="Original log entry")


class LogEntryCreate(LogEntryBase):
    """Log entry creation schema."""

    source_id: int = Field(..., description="Source ID")


class LogEntry(LogEntryBase):
    """Log entry schema."""

    id: int = Field(..., description="Entry ID")
    source_id: int = Field(..., description="Source ID")
    source: LogSource = Field(..., description="Log source")

    class Config:
        """Pydantic config."""

        from_attributes = True


class LogIngestionStats(BaseModel):
    """Log ingestion statistics schema."""

    total_logs: int = Field(..., description="Total number of logs")
    source_stats: dict = Field(..., description="Statistics by source")
    time_range: dict = Field(..., description="Time range for statistics")
