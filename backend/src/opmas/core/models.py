import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Severity(enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AgentStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class ActionStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Device(Base):
    __tablename__ = "device_inventory"

    id = Column(Integer, primary_key=True)
    hostname = Column(String, unique=True, nullable=False)
    ip_address = Column(String, nullable=False)
    model = Column(String)
    firmware_version = Column(String)
    last_seen = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")
    credentials = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    findings = relationship("Finding", back_populates="device")
    actions = relationship("Action", back_populates="device")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(String, nullable=False)
    status = Column(Enum(AgentStatus), default=AgentStatus.ACTIVE)
    config = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rules = relationship("AgentRule", back_populates="agent")
    findings = relationship("Finding", back_populates="agent")


class AgentRule(Base):
    __tablename__ = "agent_rules"

    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    pattern = Column(String, nullable=False)
    severity = Column(Enum(Severity), default=Severity.INFO)
    threshold = Column(Integer)
    enabled = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agent = relationship("Agent", back_populates="rules")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True)
    finding_id = Column(String, unique=True, nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("device_inventory.id"), nullable=False)
    severity = Column(Enum(Severity), nullable=False)
    finding_type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agent = relationship("Agent", back_populates="findings")
    device = relationship("Device", back_populates="findings")
    actions = relationship("Action", back_populates="finding")


class Playbook(Base):
    __tablename__ = "playbooks"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    steps = Column(JSON, nullable=False)
    enabled = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Action(Base):
    __tablename__ = "intended_actions"

    id = Column(Integer, primary_key=True)
    action_id = Column(String, unique=True, nullable=False)
    finding_id = Column(Integer, ForeignKey("findings.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("device_inventory.id"), nullable=False)
    action_type = Column(String, nullable=False)
    command = Column(String)
    status = Column(Enum(ActionStatus), default=ActionStatus.PENDING)
    result = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    finding = relationship("Finding", back_populates="actions")
    device = relationship("Device", back_populates="actions")
