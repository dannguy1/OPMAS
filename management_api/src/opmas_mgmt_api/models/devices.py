"""Device management models."""

from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, INET
from sqlalchemy.orm import relationship

from opmas_mgmt_api.db.base_class import Base

class Device(Base):
    """Device model."""
    __tablename__ = "devices"

    id = Column(PGUUID, primary_key=True, default=uuid4)
    hostname = Column(String, nullable=False)
    ip_address = Column(INET, nullable=False)
    device_type = Column(String, nullable=False)
    model = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    status = Column(String, nullable=False, default="unknown")
    enabled = Column(Boolean, default=True)
    device_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, nullable=True)
    agent_id = Column(PGUUID, ForeignKey("agents.id"), nullable=True)

    # Relationships
    agent = relationship("Agent", back_populates="devices")
    status_history = relationship("DeviceStatusHistory", back_populates="device", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_devices_hostname", "hostname"),
        Index("ix_devices_ip_address", "ip_address"),
        Index("ix_devices_device_type", "device_type"),
        Index("ix_devices_status", "status"),
        Index("ix_devices_enabled", "enabled"),
        Index("ix_devices_agent_id", "agent_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "hostname": self.hostname,
            "ip_address": str(self.ip_address),
            "device_type": self.device_type,
            "model": self.model,
            "firmware_version": self.firmware_version,
            "status": self.status,
            "enabled": self.enabled,
            "metadata": self.device_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "agent_id": str(self.agent_id) if self.agent_id else None
        }

class DeviceStatusHistory(Base):
    """Device status history model."""
    __tablename__ = "device_status_history"

    id = Column(PGUUID, primary_key=True, default=uuid4)
    device_id = Column(PGUUID, ForeignKey("devices.id"), nullable=False)
    status = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    details = Column(JSON, nullable=True)

    # Relationships
    device = relationship("Device", back_populates="status_history")

    # Indexes
    __table_args__ = (
        Index("ix_device_status_history_device_id", "device_id"),
        Index("ix_device_status_history_timestamp", "timestamp"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "device_id": str(self.device_id),
            "status": self.status,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "details": self.details
        } 