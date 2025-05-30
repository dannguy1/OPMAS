"""User management models."""

from typing import Any, Dict
from uuid import UUID, uuid4

from opmas_mgmt_api.db.base_class import Base
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    devices = relationship("Device", back_populates="owner")
    agents = relationship("Agent", back_populates="owner")
    rules = relationship("Rule", back_populates="owner")
    findings = relationship("Finding", back_populates="reporter")
    actions = relationship("Action", back_populates="assignee")

    def __repr__(self) -> str:
        """Return string representation of user."""
        return f"<User {self.username}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
        }
