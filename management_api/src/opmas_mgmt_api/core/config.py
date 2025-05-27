"""Application configuration."""

import logging
import secrets
from typing import Any, Dict, List, Optional

from passlib.context import CryptContext
from pydantic import AnyHttpUrl, Field, PostgresDsn, validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings."""

    # API settings
    API_V1_STR: str = "/api/v1"  # Base path for all API endpoints
    PROJECT_NAME: str = "OPMAS Management API"
    VERSION: str = "1.0.0"

    # Database settings
    DATABASE_URL: str = "postgresql+asyncpg://opmas:opmas@postgres:5432/opmas"
    DB_ECHO: bool = True  # Enable SQL query logging for debugging
    DB_POOL_SIZE: int = 5  # Reduce pool size for development
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_TIMEOUT: int = 30
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    # NATS settings
    NATS_URL: str = "nats://nats:4222"
    NATS_CLUSTER_ID: str = "opmas-cluster"
    NATS_USERNAME: Optional[str] = None
    NATS_PASSWORD: Optional[str] = None

    # Redis settings
    REDIS_URL: str = "redis://redis:6379/0"

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """Assemble database connection string."""
        if isinstance(v, str):
            return v
        return values.get("DATABASE_URL")

    # Security settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24
    PWD_CONTEXT: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # CORS settings
    CORS_ORIGINS: str = ""  # Changed to str to handle raw input
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "logs/opmas_mgmt_api.log"

    # Environment settings
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Metrics settings
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp/prometheus_multiproc"

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600

    # File upload settings
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = ["json", "yaml", "yml", "txt"]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str], values: dict) -> List[str]:
        """Assemble CORS origins."""
        if isinstance(v, str):
            if v.startswith("["):
                # Handle JSON array format
                import json

                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    return [i.strip() for i in v.split(",")]
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []

    @validator("BACKEND_CORS_ORIGINS", always=True)
    def set_cors_origins(cls, v: List[str], values: dict) -> List[str]:
        """Set CORS origins from CORS_ORIGINS if not set."""
        if not v and "CORS_ORIGINS" in values:
            return cls.assemble_cors_origins(values["CORS_ORIGINS"], values)
        return v

    class Config:
        """Pydantic config."""

        case_sensitive = True
        env_file = ".env"


# Create global settings instance
settings = Settings()
