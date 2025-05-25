from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, String

from .base import Base


class Rule(Base):
    """Rule model for storing analysis rules."""

    __tablename__ = "rules"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    pattern = Column(String, nullable=False)  # Regex pattern or rule definition
    severity = Column(String, nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    enabled = Column(Boolean, nullable=False, default=True)
    parameters = Column(JSON, nullable=True)  # Additional rule parameters
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Rule(name='{self.name}', severity='{self.severity}')>"
