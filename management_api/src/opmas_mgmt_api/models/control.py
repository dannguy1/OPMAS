"""Control action models."""

from datetime import datetime

from opmas_mgmt_api.db.base_class import Base
from opmas_mgmt_api.schemas.control import ControlActionStatus
from sqlalchemy import JSON, Column, DateTime, Enum, String
from sqlalchemy.sql import func


class ControlAction(Base):
    """Control action model."""

    __tablename__ = "control_actions"

    id = Column(String, primary_key=True, index=True)
    action = Column(String, nullable=False)
    component = Column(String, nullable=True)
    status = Column(Enum(ControlActionStatus), nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
