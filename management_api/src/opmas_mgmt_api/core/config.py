"""Application configuration."""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator, Field

class Settings(BaseSettings):
    """Application settings."""
    
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "OPMAS Management API"
    
    # Database settings
    DATABASE_URL: str
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = Field(default=20)
    DB_MAX_OVERFLOW: int = Field(default=10)
    DB_POOL_TIMEOUT: int = Field(default=30)
    
    # NATS settings
    NATS_URL: str
    NATS_CLUSTER_ID: str = "opmas-cluster"
    
    # Redis settings
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Security settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24
    
    # CORS settings
    CORS_ORIGINS: List[AnyHttpUrl] = []
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
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
    
    @validator("CORS_ORIGINS", "BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Assemble CORS origins."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        """Pydantic config."""
        case_sensitive = True
        env_file = ".env"

# Create global settings instance
settings = Settings() 