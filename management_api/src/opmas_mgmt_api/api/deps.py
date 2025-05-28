"""API dependencies."""

from typing import AsyncGenerator, Generator, Optional

import nats.aio.client as nats
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from opmas_mgmt_api.core.config import settings
from opmas_mgmt_api.db.session import async_session
from opmas_mgmt_api.schemas.auth import User
from opmas_mgmt_api.services.user import get_user_by_username
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from opmas_mgmt_api.core.nats import NATSManager

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

logger = logging.getLogger(__name__)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_username(db, username)
    if user is None:
        logger.error(f"User not found for username: {username}")
        raise credentials_exception
    return user


async def get_nats() -> NATSManager:
    """Get NATS manager instance.

    Returns:
        NATSManager: NATS manager instance
    """
    try:
        nats_manager = NATSManager()
        await nats_manager.connect()
        return nats_manager
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to NATS: {str(e)}",
        )
