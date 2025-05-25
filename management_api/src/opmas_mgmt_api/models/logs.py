"""Log database models."""

from datetime import datetime

from opmas_mgmt_api.db.base_class import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship


class LogSource(Base):
    """Log source model."""

    __tablename__ = "log_sources"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(255), unique=True, index=True, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)

    # Relationships
    logs = relationship("LogEntry", back_populates="source")


class LogEntry(Base):
    """Log entry model."""

    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("log_sources.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    level = Column(Integer, nullable=False)  # syslog level (0-7)
    facility = Column(Integer, nullable=False)  # syslog facility (0-23)
    message = Column(Text, nullable=False)
    raw_log = Column(Text, nullable=False)  # Original log entry

    # Relationships
    source = relationship("LogSource", back_populates="logs")
