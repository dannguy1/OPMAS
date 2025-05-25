"""Playbook management models."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from opmas_mgmt_api.db.base_class import Base
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship


class Playbook(Base):
    """Playbook model."""

    __tablename__ = "playbooks"

    id = Column(PGUUID, primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    agent_type = Column(String, nullable=False)
    steps = Column(JSON, nullable=False)  # List of PlaybookStep objects
    enabled = Column(Boolean, default=True)
    playbook_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_executed = Column(DateTime, nullable=True)
    execution_count = Column(Integer, default=0)

    # Relationships
    executions = relationship(
        "PlaybookExecution", back_populates="playbook", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_playbooks_name", "name"),
        Index("ix_playbooks_agent_type", "agent_type"),
        Index("ix_playbooks_enabled", "enabled"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type,
            "steps": self.steps,
            "enabled": self.enabled,
            "metadata": self.playbook_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_executed": self.last_executed.isoformat() if self.last_executed else None,
            "execution_count": self.execution_count,
        }


class PlaybookExecution(Base):
    """Playbook execution model."""

    __tablename__ = "playbook_executions"

    id = Column(PGUUID, primary_key=True, default=uuid4)
    playbook_id = Column(PGUUID, ForeignKey("playbooks.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)  # running, completed, failed
    error = Column(String, nullable=True)
    steps = Column(JSON, nullable=False)  # List of step execution results
    execution_metadata = Column(JSON, nullable=True)

    # Relationships
    playbook = relationship("Playbook", back_populates="executions")

    # Indexes
    __table_args__ = (
        Index("ix_playbook_executions_playbook_id", "playbook_id"),
        Index("ix_playbook_executions_status", "status"),
        Index("ix_playbook_executions_started_at", "started_at"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "playbook_id": str(self.playbook_id),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "error": self.error,
            "steps": self.steps,
            "metadata": self.execution_metadata,
        }
