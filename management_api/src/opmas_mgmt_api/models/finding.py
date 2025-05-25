"""Finding model for storing security findings."""

from datetime import datetime
from typing import Optional

from opmas_mgmt_api.db.base_class import Base
from sqlalchemy import Column, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class Finding(Base):
    """Finding model for storing security findings."""

    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        Enum("critical", "high", "medium", "low", name="finding_severity"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum("open", "in_progress", "resolved", "closed", name="finding_status"),
        nullable=False,
        default="open",
    )
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    device_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    agent_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    rule_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    additional_data: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON string for additional data
