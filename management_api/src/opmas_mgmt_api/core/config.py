"""Configuration settings for the management API."""

import logging
import secrets
from typing import Any, Dict, List, Optional

from passlib.context import CryptContext
from pydantic import AnyHttpUrl, Field, PostgresDsn, validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings."""

    # API settings
    API_V1_STR: str = "/api/v1"  # Base path for all API endpoints
    PROJECT_NAME: str = "OPMAS Management API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Management API for OPMAS Agents"

    # Database settings
    DATABASE_URL: Optional[str] = None
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    DB_ECHO: bool = Field(
        default=True,
        description="Enable SQL query logging"
    )
    DB_POOL_SIZE: int = Field(
        default=20,
        description="Database connection pool size"
    )
    DB_MAX_OVERFLOW: int = Field(
        default=10,
        description="Maximum number of connections that can be created beyond pool_size"
    )
    DB_POOL_TIMEOUT: int = Field(
        default=30,
        description="Timeout for getting a connection from the pool"
    )

    # NATS settings
    NATS_URL: str = Field(
        default="nats://localhost:4222",
        description="NATS server URL"
    )
    NATS_CLUSTER_ID: str = Field(
        default="opmas-cluster",
        description="NATS cluster ID"
    )

    # Redis settings
    REDIS_URL: str = "redis://redis:6379/0"

    # Security settings
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT token generation"
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="Algorithm used for JWT token generation"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh token expiration time in days"
    )
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = Field(
        default=24,
        description="Password reset token expiration time in hours"
    )

    # CORS settings
    CORS_ORIGINS: str = ""  # Changed to str to handle raw input
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000"],
        description="List of allowed CORS origins"
    )

    # Logging settings
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
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

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """Assemble database connection URI."""
        if isinstance(v, str):
            return v
        if values.get("SQLALCHEMY_DATABASE_URI"):
            return values["SQLALCHEMY_DATABASE_URI"]
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

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

    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"  # Allow extra fields in the settings
    )


# Create global settings instance
settings = Settings()
