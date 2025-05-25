"""System management models."""

from datetime import datetime

from opmas_mgmt_api.db.base_class import Base
from sqlalchemy import JSON, Column, DateTime, String
from sqlalchemy.sql import func


class SystemConfig(Base):
    """System configuration model."""

    __tablename__ = "system_configs"

    id = Column(String, primary_key=True, index=True)
    version = Column(String, nullable=False)
    components = Column(JSON, nullable=False)
    security = Column(JSON, nullable=False)
    logging = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
