from sqlalchemy import Column, String, JSON, Integer, Enum
from .base import Base, TimestampMixin
import enum

class AgentType(enum.Enum):
    """Enum for different types of agents."""
    WIFI = "wifi"
    SECURITY = "security"
    HEALTH = "health"
    WAN = "wan"

class AgentStatus(enum.Enum):
    """Enum for agent status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class Agent(Base, TimestampMixin):
    """Model for managing different types of agents."""
    __tablename__ = 'agents'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    type = Column(Enum(AgentType), nullable=False, index=True)
    status = Column(Enum(AgentStatus), nullable=False, index=True)
    configuration = Column(JSON)
    last_heartbeat = Column(String)  # ISO format timestamp of last heartbeat
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}', type='{self.type.value}')>" 