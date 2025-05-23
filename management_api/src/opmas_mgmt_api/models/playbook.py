"""Playbook model for automation workflows."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base

class PlaybookStatus(enum.Enum):
    """Playbook status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

class Playbook(Base):
    """Playbook model for automation workflows."""
    
    __tablename__ = "playbooks"
    
    playbook_id = Column(Integer, primary_key=True, index=True)
    finding_type = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    workflow = Column(JSON, nullable=False)  # Workflow definition in JSON format
    status = Column(Enum(PlaybookStatus), default=PlaybookStatus.DRAFT)
    is_enabled = Column(Boolean, default=True)
    schedule = Column(JSON)  # Schedule configuration in JSON format
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    
    # Foreign keys
    agent_id = Column(Integer, ForeignKey("agent.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    
    # Relationships
    agent = relationship("Agent", back_populates="playbooks")
    owner = relationship("User", back_populates="playbooks")
    executions = relationship("PlaybookExecution", back_populates="playbook") 