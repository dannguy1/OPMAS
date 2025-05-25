from uuid import uuid4

from opmas_mgmt_api.db.base_class import Base
from passlib.context import CryptContext
from sqlalchemy import Boolean, Column, DateTime, String, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

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
