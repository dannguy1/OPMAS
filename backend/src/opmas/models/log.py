from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Integer
from datetime import datetime
from .base import Base

class Log(Base):
    """Log model for storing system logs."""
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    level = Column(String, nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    source = Column(String, nullable=False)  # System component that generated the log
    message = Column(String, nullable=False)
    log_metadata = Column(JSON, nullable=True)  # Additional log metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<Log(device_id='{self.device_id}', level='{self.level}', timestamp='{self.timestamp}')>" 