"""Device management models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from opmas_mgmt_api.db.base_class import Base
from sqlalchemy import JSON, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Device(Base):
    """Device model for managing network devices."""

    __tablename__ = "devices"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    firmware_version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="offline")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    agents = relationship("Agent", back_populates="device")
    status_history = relationship(
        "DeviceStatusHistory", back_populates="device", cascade="all, delete-orphan"
    )


class DeviceStatusHistory(Base):
    """Device status history model."""

    __tablename__ = "device_status_history"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    device_id: Mapped[UUID] = mapped_column(ForeignKey("devices.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    device = relationship("Device", back_populates="status_history")
