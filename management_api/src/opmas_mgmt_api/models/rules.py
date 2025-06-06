"""Rule management models."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from opmas_mgmt_api.db.base_class import Base
from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Rule(Base):
    """Rule model for security rules."""

    __tablename__ = "rules"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    condition: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    action: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    priority: Mapped[int] = mapped_column(default=1)
    enabled: Mapped[bool] = mapped_column(default=True)
    rule_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    last_triggered: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    trigger_count: Mapped[int] = mapped_column(default=0)

    # Foreign keys
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id"), nullable=False)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    agent = relationship("Agent", back_populates="rules")
    owner = relationship("User", back_populates="rules")
    findings = relationship("Finding", back_populates="rule")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type,
            "condition": self.condition,
            "action": self.action,
            "priority": self.priority,
            "enabled": self.enabled,
            "rule_metadata": self.rule_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "trigger_count": self.trigger_count,
        }
