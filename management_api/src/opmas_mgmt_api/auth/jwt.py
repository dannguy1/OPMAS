"""JWT token handling for authentication."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, cast

from jose import JWTError, jwt
from opmas_mgmt_api.core.config import settings
from opmas_mgmt_api.models.user import User

logger = logging.getLogger(__name__)


class JWTService:
    """Service for handling JWT tokens."""

    def __init__(self) -> None:
        """Initialize JWT service."""
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = (
            settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        self.refresh_token_expire_days = (
            settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a new access token.

        Args:
            data: Token payload data
            expires_delta: Optional expiration time delta

        Returns:
            str: Encoded JWT token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )
        to_encode.update(
            {
                "exp": expire,
                "type": "access",
            }
        )
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm,
        )
        return cast(str, encoded_jwt)

    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a new refresh token.

        Args:
            data: Token payload data
            expires_delta: Optional expiration time delta

        Returns:
            str: Encoded JWT token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=self.refresh_token_expire_days
            )
        to_encode.update(
            {
                "exp": expire,
                "type": "refresh",
            }
        )
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm,
        )
        return cast(str, encoded_jwt)

    def decode_token(
        self,
        token: str,
    ) -> Optional[Dict[str, Any]]:
        """Decode a JWT token.

        Args:
            token: JWT token to decode

        Returns:
            Optional[Dict[str, Any]]: Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            return cast(Dict[str, Any], payload)
        except JWTError as e:
            logger.error(
                f"Error decoding token: {e}"
            )
            return None

    def verify_token(
        self,
        token: str,
    ) -> Optional[User]:
        """Verify a JWT token and return the associated user.

        Args:
            token: JWT token to verify

        Returns:
            Optional[User]: User object if token is valid, None otherwise
        """
        payload = self.decode_token(token)
        if payload is None:
            return None

        user_id = payload.get("sub")
        if not isinstance(user_id, str):
            return None

        # TODO: Get user from database
        return None

    def get_token_type(
        self,
        token: str,
    ) -> Optional[str]:
        """Get the type of a JWT token.

        Args:
            token: JWT token to check

        Returns:
            Optional[str]: Token type ('access' or 'refresh') or None if invalid
        """
        payload = self.decode_token(token)
        if payload is None:
            return None

        token_type = payload.get("type")
        if not isinstance(token_type, str):
            return None

        return token_type

    def verify_password(
        self,
        plain_password: str,
        hashed_password: str,
    ) -> bool:
        """Verify a password against its hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password to compare against

        Returns:
            bool: True if password matches hash, False otherwise
        """
        return cast(
            bool,
            settings.pwd_context.verify(
                plain_password,
                hashed_password,
            ),
        )

    def get_password_hash(
        self,
        password: str,
    ) -> str:
        """Generate a password hash.

        Args:
            password: Plain text password to hash

        Returns:
            str: Hashed password
        """
        return cast(
            str,
            settings.pwd_context.hash(password),
        )
