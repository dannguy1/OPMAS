"""Action management models."""

from datetime import datetime
from typing import Any, Dict
from uuid import UUID, uuid4

from opmas_mgmt_api.db.base_class import Base
from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column


class Action(Base):
    """Action model."""

    __tablename__ = "actions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    action_type: Mapped[str] = mapped_column(String(50))
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    priority: Mapped[int] = mapped_column(default=1)
    finding_id: Mapped[UUID | None] = mapped_column(nullable=True)
    action_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    result: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
