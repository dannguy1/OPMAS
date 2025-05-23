"""Configuration management models."""

from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from opmas_mgmt_api.db.base_class import Base

class Configuration(Base):
    """Configuration model."""
    __tablename__ = "configurations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    component = Column(String, nullable=False)  # e.g., 'system', 'agent', 'device'
    component_id = Column(PGUUID(as_uuid=True))  # ID of the component this config belongs to
    version = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    configuration = Column(JSON, nullable=False)
    config_metadata = Column(JSON)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    history = relationship("ConfigurationHistory", back_populates="configuration", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "component": self.component,
            "component_id": str(self.component_id) if self.component_id else None,
            "version": self.version,
            "is_active": self.is_active,
            "configuration": self.configuration,
            "metadata": self.config_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class ConfigurationHistory(Base):
    """Configuration history model."""
    __tablename__ = "configuration_history"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    configuration_id = Column(PGUUID(as_uuid=True), ForeignKey("configurations.id"), nullable=False)
    version = Column(String, nullable=False)
    configuration = Column(JSON, nullable=False)
    config_metadata = Column(JSON)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String)  # User or system that made the change

    # Relationships
    configuration = relationship("Configuration", back_populates="history")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "configuration_id": str(self.configuration_id),
            "version": self.version,
            "configuration": self.configuration,
            "metadata": self.config_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by
        } 