"""Action model for storing remediation actions."""

from datetime import datetime
from typing import Optional

from opmas_mgmt_api.db.base_class import Base
from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class Action(Base):
    """Action model for storing remediation actions."""

    __tablename__ = "actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(
        Enum("high", "medium", "low", name="action_priority"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum("pending", "in_progress", "completed", "failed", name="action_status"),
        nullable=False,
        default="pending",
    )
    finding_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    agent_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    additional_data: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON string for additional data
