"""User service."""

import logging
from typing import Optional

from opmas_mgmt_api.core.security import get_password_hash, verify_password
from opmas_mgmt_api.models.user import User
from opmas_mgmt_api.schemas.auth import UserInDB
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[UserInDB]:
    """Get user by username."""
    result = await db.execute(select(User).filter(User.username == username))
    user = result.scalar_one_or_none()
    if user:
        return UserInDB.model_validate(user)
    return None


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserInDB]:
    """Get user by email."""
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        return UserInDB.model_validate(user)
    return None


async def create_user(
    db: AsyncSession, username: str, email: str, password: str, full_name: str | None = None
) -> UserInDB:
    """Create new user."""
    hashed_password = get_password_hash(password)
    db_user = User(
        username=username, email=email, hashed_password=hashed_password, full_name=full_name
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return UserInDB.model_validate(db_user)


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user."""
    try:
        user = await get_user_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    except Exception as e:
        logger.error(f"Error authenticating user: {str(e)}")
        return None
