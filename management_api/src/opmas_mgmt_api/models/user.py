"""User model."""

from datetime import datetime
from uuid import uuid4

from opmas_mgmt_api.db.base_class import Base
from passlib.context import CryptContext
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """User model."""

    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships - commented out until other models are properly defined
    # devices = relationship("Device", back_populates="owner", foreign_keys="Device.owner_id")
    # agents = relationship("Agent", back_populates="owner", foreign_keys="Agent.owner_id")
    # rules = relationship("Rule", back_populates="owner", foreign_keys="Rule.owner_id")
    # findings = relationship("Finding", back_populates="reporter", foreign_keys="Finding.reporter_id")
    # actions = relationship("Action", back_populates="assignee", foreign_keys="Action.assignee_id")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            True if password matches hash
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Get password hash.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    @classmethod
    def get_by_username(cls, username: str):
        """Get user by username.

        Args:
            username: Username to search for

        Returns:
            User object if found, None otherwise
        """
        from opmas_mgmt_api.db.session import SessionLocal

        db = SessionLocal()
        try:
            return db.query(cls).filter(cls.username == username).first()
        finally:
            db.close()
