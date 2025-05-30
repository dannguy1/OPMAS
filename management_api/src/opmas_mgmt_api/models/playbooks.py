"""Playbook management models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from opmas_mgmt_api.db.base_class import Base
from sqlalchemy import JSON
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class ExecutionStatus(str, Enum):
    """Playbook execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Playbook(Base):
    """Playbook model for automation workflows."""

    __tablename__ = "playbooks"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    steps: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    enabled: Mapped[bool] = mapped_column(default=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    last_executed: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    execution_count: Mapped[int] = mapped_column(default=0)
    owner_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    agent_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("agents.id"), nullable=True)

    # Relationships
    owner = relationship("User", back_populates="playbooks")
    agent = relationship("Agent", back_populates="playbooks")
    executions = relationship("PlaybookExecution", back_populates="playbook", cascade="all, delete-orphan")


class PlaybookExecution(Base):
    """Playbook execution model."""

    __tablename__ = "playbook_executions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    playbook_id: Mapped[UUID] = mapped_column(ForeignKey("playbooks.id"), nullable=False)
    status: Mapped[ExecutionStatus] = mapped_column(SQLEnum(ExecutionStatus), default=ExecutionStatus.PENDING)
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    results: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    playbook = relationship("Playbook", back_populates="executions")
