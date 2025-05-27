"""Finding management models."""

from datetime import datetime
from typing import Any, Dict
from uuid import UUID, uuid4

from opmas_mgmt_api.db.base_class import Base
from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column


class Finding(Base):
    """Finding model."""

    __tablename__ = "findings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(1000))
    severity: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="open")
    source: Mapped[str] = mapped_column(String(100))
    device_id: Mapped[UUID | None] = mapped_column(nullable=True)
    finding_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    resolution: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(100), nullable=True)
