"""Authentication dependencies."""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from opmas_mgmt_api.auth.jwt import AuthHandler
from opmas_mgmt_api.auth.models import User
from opmas_mgmt_api.core.config import settings
from opmas_mgmt_api.db.session import get_db
from sqlalchemy.orm import Session

from .schemas import TokenData

logger = logging.getLogger(__name__)

# Create auth handler instance
auth_handler = AuthHandler(settings.dict())

# Create OAuth2 scheme with correct token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Get current user from token.

    Args:
        token: JWT token
        db: Database session

    Returns:
        User: Current user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify token
        payload = auth_handler.verify_token(token)
        if payload is None:
            logger.warning("Invalid token: payload is None")
            raise credentials_exception

        # Get username from token
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Invalid token: username is None")
            raise credentials_exception

        # Get user from database
        user = User.get_by_username(username)
        if user is None:
            logger.warning(f"User not found: {username}")
            raise credentials_exception

        return user

    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        raise credentials_exception


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user.

    Args:
        current_user: Current user

    Returns:
        User: Current active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user attempted access: {current_user.username}")
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Get current superuser.

    Args:
        current_user: Current user

    Returns:
        User: Current superuser

    Raises:
        HTTPException: If user is not superuser
    """
    if not current_user.is_superuser:
        logger.warning(f"Non-superuser attempted superuser access: {current_user.username}")
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user
