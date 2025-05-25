"""JWT authentication handler."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from opmas_mgmt_api.auth.models import User
from opmas_mgmt_api.core.config import settings
from passlib.context import CryptContext
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Configure password hashing with explicit bcrypt settings
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Use a reasonable number of rounds
    bcrypt__ident="2b",  # Use the latest bcrypt version
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


class Token(BaseModel):
    """Token model."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model."""

    username: Optional[str] = None


class AuthHandler:
    """JWT authentication handler."""

    def __init__(self, settings: Dict[str, Any]):
        """Initialize auth handler.

        Args:
            settings: Application settings
        """
        self.secret_key = settings["SECRET_KEY"]
        self.algorithm = settings["ALGORITHM"]
        self.access_token_expire_minutes = settings["ACCESS_TOKEN_EXPIRE_MINUTES"]
        self.refresh_token_expire_days = settings["REFRESH_TOKEN_EXPIRE_DAYS"]

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            True if password matches hash
        """
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Get password hash.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create access token.

        Args:
            data: Token data
            expires_delta: Token expiration time

        Returns:
            JWT token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """Create refresh token.

        Args:
            data: Token data

        Returns:
            JWT token
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify token.

        Args:
            token: JWT token

        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None

    def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        """Get current user.

        Args:
            token: JWT token

        Returns:
            User: Current user

        Raises:
            HTTPException: If token is invalid
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except JWTError:
            raise credentials_exception
        user = User.get_by_username(token_data.username)
        if user is None:
            raise credentials_exception
        return user

    def get_current_active_user(self, current_user: User = Depends(get_current_user)) -> User:
        """Get current active user.

        Args:
            current_user: Current user

        Returns:
            User: Current active user

        Raises:
            HTTPException: If user is inactive
        """
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user

    def get_current_superuser(self, current_user: User = Depends(get_current_user)) -> User:
        """Get current superuser.

        Args:
            current_user: Current user

        Returns:
            User: Current superuser

        Raises:
            HTTPException: If user is not superuser
        """
        if not current_user.is_superuser:
            raise HTTPException(status_code=400, detail="The user doesn't have enough privileges")
        return current_user
