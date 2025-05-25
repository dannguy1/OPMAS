#!/usr/bin/env python3

"""Pydantic schema models for the Management API."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Status of an agent."""

    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class FindingSeverity(str, Enum):
    """Severity levels for findings."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


# --- Agent Schemas ---


class AgentBase(BaseModel):
    """Base schema for agent data."""

    name: str = Field(..., description="Name of the agent")
    package_name: str = Field(..., description="Python package name for the agent")
    subscribed_topics: List[str] = Field(..., description="List of NATS topics to subscribe to")
    enabled: bool = Field(True, description="Whether the agent is enabled")


class AgentCreate(AgentBase):
    """Schema for creating a new agent."""

    pass


class AgentUpdate(BaseModel):
    """Schema for updating an existing agent."""

    package_name: Optional[str] = Field(None, description="Python package name for the agent")
    subscribed_topics: Optional[List[str]] = Field(
        None, description="List of NATS topics to subscribe to"
    )
    enabled: Optional[bool] = Field(None, description="Whether the agent is enabled")


class AgentResponse(AgentBase):
    """Schema for agent response data."""

    id: int = Field(..., description="Database ID of the agent")
    status: AgentStatus = Field(..., description="Current status of the agent")
    created_at: datetime = Field(..., description="When the agent was created")
    updated_at: datetime = Field(..., description="When the agent was last updated")

    class Config:
        orm_mode = True


# --- Agent Rule Schemas ---


class AgentRuleBase(BaseModel):
    """Base schema for agent rule data."""

    name: str = Field(..., description="Name of the rule")
    description: str = Field(..., description="Description of what the rule detects")
    pattern: str = Field(..., description="Regex pattern to match in log messages")
    severity: FindingSeverity = Field(..., description="Severity level for findings from this rule")
    enabled: bool = Field(True, description="Whether the rule is enabled")
    cooldown_seconds: int = Field(..., description="Cooldown period between findings in seconds")
    threshold: int = Field(..., description="Number of occurrences required to trigger a finding")


class AgentRuleCreate(AgentRuleBase):
    """Schema for creating a new agent rule."""

    pass


class AgentRuleUpdate(BaseModel):
    """Schema for updating an existing agent rule."""

    description: Optional[str] = Field(None, description="Description of what the rule detects")
    pattern: Optional[str] = Field(None, description="Regex pattern to match in log messages")
    severity: Optional[FindingSeverity] = Field(
        None, description="Severity level for findings from this rule"
    )
    enabled: Optional[bool] = Field(None, description="Whether the rule is enabled")
    cooldown_seconds: Optional[int] = Field(
        None, description="Cooldown period between findings in seconds"
    )
    threshold: Optional[int] = Field(
        None, description="Number of occurrences required to trigger a finding"
    )


class AgentRuleResponse(AgentRuleBase):
    """Schema for agent rule response data."""

    id: int = Field(..., description="Database ID of the rule")
    agent_id: int = Field(..., description="ID of the agent this rule belongs to")
    created_at: datetime = Field(..., description="When the rule was created")
    updated_at: datetime = Field(..., description="When the rule was last updated")

    class Config:
        orm_mode = True


# --- Finding Schemas ---


class FindingBase(BaseModel):
    """Base schema for finding data."""

    finding_type: str = Field(..., description="Type of finding")
    agent_name: str = Field(..., description="Name of the agent that created the finding")
    resource_id: str = Field(..., description="ID of the resource the finding is about")
    severity: FindingSeverity = Field(..., description="Severity level of the finding")
    message: str = Field(..., description="Human-readable message describing the finding")
    details: Dict[str, Any] = Field(..., description="Additional details about the finding")


class FindingResponse(FindingBase):
    """Schema for finding response data."""

    id: int = Field(..., description="Database ID of the finding")
    timestamp: datetime = Field(..., description="When the finding was created")

    class Config:
        orm_mode = True


# --- Finding Filter Schema ---


class FindingFilter(BaseModel):
    """Schema for filtering findings."""

    agent_name: Optional[str] = Field(None, description="Filter by agent name")
    finding_type: Optional[str] = Field(None, description="Filter by finding type")
    severity: Optional[FindingSeverity] = Field(None, description="Filter by severity level")
    resource_id: Optional[str] = Field(None, description="Filter by resource ID")
    start_time: Optional[datetime] = Field(None, description="Filter by start time")
    end_time: Optional[datetime] = Field(None, description="Filter by end time")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_desc: Optional[bool] = Field(False, description="Sort in descending order")
    limit: Optional[int] = Field(None, description="Maximum number of findings to return")
    offset: Optional[int] = Field(None, description="Number of findings to skip")
