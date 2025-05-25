"""JWT authentication handler."""

from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from opmas_mgmt_api.config import settings
from passlib.context import CryptContext
from .schemas import TokenData

class AuthHandler:
    """JWT authentication handler."""

    def __init__(self, settings_dict: Optional[Dict[str, Any]] = None):
        """Initialize the auth handler.
        
        Args:
            settings_dict: Optional dictionary of settings. If not provided,
                          uses the global settings instance.
        """
        if settings_dict is None:
            settings_dict = settings.dict()
            
        self.secret_key = settings_dict["SECRET_KEY"]
        self.algorithm = settings_dict["ALGORITHM"]
        self.access_token_expire_minutes = settings_dict["ACCESS_TOKEN_EXPIRE_MINUTES"]
        self.refresh_token_expire_days = settings_dict["REFRESH_TOKEN_EXPIRE_DAYS"]
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def encode_token(self, user_id: int) -> str:
        """Encode a JWT token."""
        payload = {
            "exp": datetime.utcnow() + timedelta(days=0, minutes=self.access_token_expire_minutes),
            "iat": datetime.utcnow(),
            "sub": str(user_id)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None

    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_token(self, token: str) -> Optional[TokenData]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                return None
            return TokenData(username=username)
        except JWTError:
            return None 