"""Rule model for security rules."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base

class RuleSeverity(enum.Enum):
    """Rule severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Rule(Base):
    """Rule model for security rules."""
    
    __tablename__ = "rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    condition = Column(JSON, nullable=False)  # Rule condition in JSON format
    action = Column(JSON, nullable=False)  # Action to take in JSON format
    severity = Column(Enum(RuleSeverity), default=RuleSeverity.MEDIUM)
    is_enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    
    # Foreign keys
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    
    # Relationships
    agent = relationship("Agent", back_populates="rules")
    owner = relationship("User", back_populates="rules")
    findings = relationship("Finding", back_populates="rule")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 