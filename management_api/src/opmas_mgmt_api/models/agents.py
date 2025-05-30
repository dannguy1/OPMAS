"""Agent management models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from opmas_mgmt_api.db.base_class import Base
from opmas_mgmt_api.models.findings import Finding
from sqlalchemy import JSON, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Agent(Base):
    """Agent model for managing security agents."""

    __tablename__ = "agents"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="stopped")
    enabled: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    agent_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    capabilities: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Foreign keys
    device_id: Mapped[UUID] = mapped_column(ForeignKey("devices.id"), nullable=False)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    device = relationship("Device", back_populates="agents")
    owner = relationship("User", back_populates="agents")
    rules = relationship("Rule", back_populates="agent", cascade="all, delete-orphan")
    agent_rules = relationship("AgentRule", back_populates="agent", cascade="all, delete-orphan")
    findings: Mapped[List[Finding]] = relationship("Finding", back_populates="agent", foreign_keys=[Finding.agent_id])
    metrics: Mapped[List["Metric"]] = relationship("Metric", back_populates="agent", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "type": self.agent_type,
            "status": self.status,
            "version": self.version,
            "enabled": self.enabled,
            "metadata": self.agent_metadata,
            "capabilities": self.capabilities,
            "last_heartbeat": (self.last_heartbeat.isoformat() if self.last_heartbeat else None),
            "device_id": str(self.device_id),
            "owner_id": str(self.owner_id),
        }


class Metric(Base):
    """Metric model for storing agent metrics."""

    __tablename__ = "metrics"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
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


class AgentRule(Base):
    """Agent rule model."""

    __tablename__ = "agent_rules"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    condition: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    action: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    priority: Mapped[int] = mapped_column(default=1)
    enabled: Mapped[bool] = mapped_column(default=True)

    # Relationships
    agent = relationship("Agent", back_populates="agent_rules")
