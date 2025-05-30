"""Finding management models."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from opmas_mgmt_api.db.base_class import Base
from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Finding(Base):
    """Finding model for security findings."""

    __tablename__ = "findings"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="open")
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    finding_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Foreign keys
    device_id: Mapped[UUID] = mapped_column(ForeignKey("devices.id"), nullable=False)
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id"), nullable=False)
    rule_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("rules.id"), nullable=True)
    reporter_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    device = relationship("Device", back_populates="findings")
    agent = relationship("Agent", back_populates="findings")
    rule = relationship("Rule", back_populates="findings")
    reporter = relationship("User", back_populates="findings")
    actions = relationship("Action", back_populates="finding", cascade="all, delete-orphan")
