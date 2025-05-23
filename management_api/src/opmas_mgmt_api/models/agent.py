"""Agent model for managing security agents."""

from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Enum, DateTime
from sqlalchemy.orm import relationship
import enum

from .base import Base

class AgentStatus(enum.Enum):
    """Agent status enumeration."""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UPDATING = "updating"

class Agent(Base):
    """Agent model for managing security agents."""
    
    name = Column(String, nullable=False)
    agent_type = Column(String, nullable=False)
    version = Column(String, nullable=False)
    status = Column(Enum(AgentStatus), default=AgentStatus.STOPPED)
    last_heartbeat = Column(DateTime)
    configuration = Column(JSON)
    capabilities = Column(JSON)
    
    # Foreign keys
    device_id = Column(Integer, ForeignKey("device.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    
    # Relationships
    device = relationship("Device", back_populates="agents")
    owner = relationship("User", back_populates="agents")
    rules = relationship("Rule", back_populates="agent")
    playbooks = relationship("Playbook", back_populates="agent")
