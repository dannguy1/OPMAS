"""Agent management models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from opmas_mgmt_api.db.base_class import Base
from opmas_mgmt_api.models.findings import Finding
from sqlalchemy import JSON, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Agent(Base):
    """Agent model for managing security agents."""

    __tablename__ = "agents"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    agent_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=dict
    )
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    findings: Mapped[List[Finding]] = relationship(
        "Finding", back_populates="agent", foreign_keys=[Finding.agent_id]
    )
    metrics: Mapped[List["Metric"]] = relationship(
        "Metric", back_populates="agent", cascade="all, delete-orphan"
    )
    devices: Mapped[List["Device"]] = relationship("Device", back_populates="agent")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "version": self.version,
            "config": self.config,
            "metadata": self.agent_metadata,
            "last_heartbeat": (self.last_heartbeat.isoformat() if self.last_heartbeat else None),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Metric(Base):
    """Metric model for storing agent metrics."""

    __tablename__ = "metrics"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    agent_id: Mapped[UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Relationships
    agent = relationship("Agent", back_populates="metrics")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics,
        }
