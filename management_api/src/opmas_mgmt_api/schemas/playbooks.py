"""Playbook management schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PlaybookStep(BaseModel):
    """Schema for playbook step."""

    name: str = Field(..., description="Step name")
    description: Optional[str] = Field(None, description="Step description")
    action_type: str = Field(..., description="Type of action to perform")
    action_config: Dict[str, Any] = Field(..., description="Action configuration in JSON format")
    order: int = Field(..., description="Step execution order")
    timeout: Optional[int] = Field(None, description="Step timeout in seconds")
    retry_count: Optional[int] = Field(None, description="Number of retry attempts")
    retry_delay: Optional[int] = Field(None, description="Delay between retries in seconds")
    enabled: bool = Field(default=True, description="Whether the step is enabled")
    extra_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional step metadata")


class PlaybookBase(BaseModel):
    """Base playbook schema."""

    name: str = Field(..., description="Playbook name")
    description: Optional[str] = Field(None, description="Playbook description")
    agent_type: str = Field(..., description="Type of agent this playbook applies to")
    steps: List[PlaybookStep] = Field(..., description="List of playbook steps")
    enabled: bool = Field(default=True, description="Whether the playbook is enabled")
    playbook_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional playbook metadata")


class PlaybookCreate(PlaybookBase):
    """Schema for creating a playbook."""

    pass


class PlaybookUpdate(BaseModel):
    """Schema for updating a playbook."""

    name: Optional[str] = Field(None, description="Playbook name")
    description: Optional[str] = Field(None, description="Playbook description")
    steps: Optional[List[PlaybookStep]] = Field(None, description="List of playbook steps")
    enabled: Optional[bool] = Field(None, description="Whether the playbook is enabled")
    playbook_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional playbook metadata")


class PlaybookResponse(PlaybookBase):
    """Schema for playbook response."""

    id: UUID = Field(..., description="Playbook ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_executed: Optional[datetime] = Field(None, description="Last time the playbook was executed")
    execution_count: int = Field(default=0, description="Number of times the playbook has been executed")

    class Config:
        """Pydantic config."""

        from_attributes = True


class PlaybookList(BaseModel):
    """Schema for list of playbooks."""

    items: List[PlaybookResponse]
    total: int
    skip: int
    limit: int


class PlaybookStatus(BaseModel):
    """Schema for playbook status."""

    status: str = Field(..., description="Playbook status")
    last_executed: Optional[datetime] = Field(None, description="Last time the playbook was executed")
    execution_count: int = Field(..., description="Number of times the playbook has been executed")
    last_error: Optional[str] = Field(None, description="Last error message if any")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional status details")


class PlaybookExecution(BaseModel):
    """Schema for playbook execution."""

    playbook_id: UUID = Field(..., description="Playbook ID")
    started_at: datetime = Field(..., description="Execution start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Execution completion timestamp")
    status: str = Field(..., description="Execution status")
    error: Optional[str] = Field(None, description="Error message if any")
    steps: List[Dict[str, Any]] = Field(..., description="Step execution results")
    extra_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional execution metadata")
