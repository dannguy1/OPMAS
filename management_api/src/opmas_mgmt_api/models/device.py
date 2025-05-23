"""Device model for managing network devices."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base

class DeviceStatus(enum.Enum):
    """Device status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class Device(Base):
    """Device model for managing network devices."""
    
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, unique=True, index=True)
    ip_address = Column(String, index=True)
    device_type = Column(String)
    status = Column(Enum(DeviceStatus), default=DeviceStatus.INACTIVE)
    last_seen = Column(DateTime(timezone=True))
    configuration = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    mac_address = Column(String)
    model = Column(String)
    serial_number = Column(String)
    firmware_version = Column(String)
    
    # Foreign keys
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    
    # Relationships
    agents = relationship("Agent", back_populates="device", cascade="all, delete-orphan")
    rules = relationship("Rule", back_populates="device", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="devices") 