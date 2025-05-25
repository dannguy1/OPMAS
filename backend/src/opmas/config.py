"""
OPMAS Core Configuration Module
"""

import logging
import os
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "logging": {"level": "INFO", "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
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


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from file or environment variables.

    Args:
        config_path: Optional path to configuration file

    Returns:
        Dict containing configuration
    """
    config = DEFAULT_CONFIG.copy()

    # Load from file if provided
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                file_config = yaml.safe_load(f)
                config.update(file_config)
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {str(e)}")

    # Override with environment variables
    for key, value in os.environ.items():
        if key.startswith("OPMAS_"):
            # Convert OPMAS_DATABASE_HOST to database.host
            parts = key[6:].lower().split("_")
            if len(parts) > 1:
                section = parts[0]
                option = "_".join(parts[1:])
                if section in config:
                    config[section][option] = value

    return config


def get_config() -> Dict[str, Any]:
    """
    Get the current configuration.

    Returns:
        Dict containing configuration
    """
    return load_config()
