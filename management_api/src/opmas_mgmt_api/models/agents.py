"""Agent management models."""

from datetime import datetime
from typing import Dict, Any
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from opmas_mgmt_api.db.base_class import Base

class Agent(Base):
    """Agent model."""
    __tablename__ = "agents"

    id = Column(PGUUID, primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    agent_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="unknown")
    enabled = Column(Boolean, default=True)
    agent_metadata = Column(JSON, nullable=True)
    last_heartbeat = Column(DateTime, nullable=True)
    version = Column(String, nullable=True)
    capabilities = Column(JSON, nullable=True)

    # Relationships
    devices = relationship("Device", back_populates="agent", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_agents_name", "name"),
        Index("ix_agents_agent_type", "agent_type"),
        Index("ix_agents_status", "status"),
        Index("ix_agents_enabled", "enabled"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "agent_type": self.agent_type,
            "status": self.status,
            "enabled": self.enabled,
            "metadata": self.agent_metadata,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "version": self.version,
            "capabilities": self.capabilities,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"<Agent {self.name} ({self.agent_type})>" 