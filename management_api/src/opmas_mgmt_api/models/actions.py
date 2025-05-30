"""Action management models."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from opmas_mgmt_api.db.base_class import Base
from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Action(Base):
    """Action model for security actions."""

    __tablename__ = "actions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    priority: Mapped[int] = mapped_column(default=1)
    action_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Foreign keys
    finding_id: Mapped[UUID] = mapped_column(ForeignKey("findings.id"), nullable=False)
    assignee_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    finding = relationship("Finding", back_populates="actions")
    assignee = relationship("User", back_populates="actions")
