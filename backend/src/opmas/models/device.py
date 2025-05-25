from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Integer, String

from .base import Base


class DeviceStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class Device(Base):
    """Device model for storing OpenWRT device information."""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hostname = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    device_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default=DeviceStatus.ACTIVE)
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Device(hostname='{self.hostname}', ip_address='{self.ip_address}')>"
