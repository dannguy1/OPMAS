"""System management models."""

from datetime import datetime
from typing import Any, Dict, Optional

from opmas_mgmt_api.db.base_class import Base
from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class SystemConfig(Base):
    """System configuration model."""

    __tablename__ = "system_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(String(50))
    components: Mapped[Dict[str, Any]] = mapped_column(JSON)
    security: Mapped[Dict[str, Any]] = mapped_column(JSON)
    logging: Mapped[Dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class SystemEvent(Base):
    """System event model."""

    __tablename__ = "system_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(String(500))
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
