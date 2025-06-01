"""Database models for agent management."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Column, DateTime, String, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Agent(Base):
    """Agent model."""

    __tablename__ = "agent_instances"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    agent_type = Column(String, nullable=False)
    version = Column(String, nullable=False)
    status = Column(String, nullable=False, default="inactive")
    enabled = Column(String, nullable=False, default="true")
    config = Column(JSON, nullable=True)
    agent_metadata = Column(JSON, nullable=True)
    capabilities = Column(JSON, nullable=True)
    last_heartbeat = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False) 