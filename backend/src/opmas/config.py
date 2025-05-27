"""
OPMAS Core Configuration Module
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field

# Install types-PyYAML for type checking
try:
    import types_yaml  # type: ignore
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
    "database": {
        "host": "postgres",
        "port": 5432,
        "database": "opmas",
        "user": "opmas",
        "password": "opmas",
    },
    "redis": {"host": "redis", "port": 6379, "db": 0},
    "nats": {"host": "nats", "port": 4222},
}


class Config(BaseModel):
    """OPMAS configuration."""

    nats_url: str = Field(
        default="nats://localhost:4222",
        description="NATS server URL",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    metrics_enabled: bool = Field(
        default=True,
        description="Whether to enable metrics collection",
    )


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from file or environment variables."""
    if config_path is None:
        config_path = os.getenv("OPMAS_CONFIG", "config.yaml")

    config_data: Dict[str, Any] = {}

    # Load from file if it exists
    if Path(config_path).exists():
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f) or {}

    # Override with environment variables
    env_prefix = "OPMAS_"
    for key, value in os.environ.items():
        if key.startswith(env_prefix):
            config_key = key[len(env_prefix) :].lower()
            config_data[config_key] = value

    return Config(**config_data)


def save_config(config: Config, config_path: str) -> None:
    """Save configuration to file."""
    config_data = config.model_dump()
    with open(config_path, "w") as f:
        yaml.safe_dump(config_data, f)


def get_config() -> Config:
    """
    Get the current configuration.

    Returns:
        Config containing configuration
    """
    return load_config()
