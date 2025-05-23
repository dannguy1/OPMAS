# Configuration management for OPMAS components.
# Loads settings from YAML files and allows overrides via environment variables.

import os
import yaml
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from functools import lru_cache

logger = logging.getLogger(__name__)

# --- Robust Configuration Paths Calculation (Corrected) ---
# Find the directory where this config.py file resides
CONFIG_PY_DIR = Path(__file__).resolve().parent # .../core/src/opmas
# Navigate up to the parent ('src')
SRC_DIR = CONFIG_PY_DIR.parent # .../core/src
# Navigate up to the parent ('core')
CORE_DIR = SRC_DIR.parent # .../core
# Navigate up to the parent (project root)
PROJECT_ROOT = CORE_DIR.parent # .../OPMAS

DEFAULT_CONFIG_DIR = PROJECT_ROOT / "core" / "config"
CORE_CONFIG_FILE_PATH = DEFAULT_CONFIG_DIR / "opmas_config.yaml"
# Removed path constants for specific config files like KB, rules, playbooks, etc.
# These paths should be defined within opmas_config.yaml or fetched from DB.

# --- Environment Variable Prefixes ---
# e.g., OPMAS_NATS_URL=nats://custom:4222 will override nats.url
ENV_VAR_PREFIX = "OPMAS_"

# --- Global variable to hold the loaded configuration ---
_config = None

class SyslogConfig(BaseModel):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=514)
    max_connections: int = Field(default=100)
    buffer_size: int = Field(default=1024)

class NATSConfig(BaseModel):
    url: str = Field(default="nats://nats:4222")
    max_reconnects: int = Field(default=5)
    reconnect_time_wait: int = Field(default=2)

class DatabaseConfig(BaseModel):
    host: str = Field(default="postgres")
    port: int = Field(default=5432)
    database: str = Field(default="opmas")
    user: str = Field(default="opmas")
    password: str = Field(default="opmas")
    pool_size: int = Field(default=5)

class RedisConfig(BaseModel):
    host: str = Field(default="redis")
    port: int = Field(default=6379)
    db: int = Field(default=0)

class LoggingConfig(BaseModel):
    level: str = Field(default="INFO")
    format: str = Field(default="json")
    rotation: str = Field(default="1 day")
    retention: str = Field(default="7 days")

class OPMASConfig(BaseModel):
    syslog: SyslogConfig = Field(default_factory=SyslogConfig)
    nats: NATSConfig = Field(default_factory=NATSConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.getenv("OPMAS_CONFIG_PATH")
        self.config: Optional[OPMASConfig] = None
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file and environment variables."""
        config_dict: Dict[str, Any] = {}

        # Load from YAML if path is provided
        if self.config_path and Path(self.config_path).exists():
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)

        # Override with environment variables
        for field in OPMASConfig.__fields__:
            env_value = os.getenv(f"OPMAS_{field.upper()}")
            if env_value:
                config_dict[field] = yaml.safe_load(env_value)

        self.config = OPMASConfig(**config_dict)

    def get_config(self) -> OPMASConfig:
        """Get the current configuration."""
        if not self.config:
            self._load_config()
        return self.config

    def reload_config(self) -> None:
        """Reload configuration from file and environment."""
        self._load_config()

# --- Configuration Loading Function ---

def load_config(config_path: Path = CORE_CONFIG_FILE_PATH) -> None:
    """Loads the main OPMAS configuration from the specified YAML file.

    This function loads the primary YAML file which should contain bootstrap
    information like NATS URL and Database connection details.
    It stores the loaded configuration in a global variable accessible
    via get_config().
    """
    global _config
    config_path_str = str(config_path)
    logger.info(f"Loading core configuration from {config_path_str}")
    loaded_data = load_yaml_file(config_path)

    if loaded_data is None:
        logger.critical(f"Failed to load core configuration from {config_path_str}. OPMAS cannot start correctly.")
        _config = None
        raise FileNotFoundError(f"Failed to load configuration file: {config_path_str}")
    else:
        _config = loaded_data
        logger.info(f"Loaded core configuration from {config_path_str}")
        # Removed specific processing/validation of paths like knowledge_base, etc.
        # Components needing specific config will query the DB later.

def get_config() -> dict | None:
    """Returns the loaded configuration dictionary.

    Returns:
        dict or None: The loaded configuration dictionary, or None if not loaded.
    """
    if _config is None:
         logger.warning("get_config() called before configuration was successfully loaded.")
    return _config

def load_yaml_file(path: Union[str, Path]) -> Dict[str, Any]:
    """Load and parse a YAML file.
    
    Args:
        path: Path to the YAML file (string or Path object)
        
    Returns:
        Dict containing the parsed YAML data
    """
    # Convert string path to Path object if needed
    if isinstance(path, str):
        path = Path(path)
        
    try:
        if not path.is_file():
            logger.error(f"YAML file not found: {path}")
            return {}
            
        with path.open('r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Error loading YAML file {path}: {e}", exc_info=True)
        return {}

# --- Helper to create a default core config file if needed ---
def _create_default_core_config(default_config: Dict[str, Any], file_path: Path = CORE_CONFIG_FILE_PATH):
    """Creates a default core config file if it doesn't exist."""
    if not file_path.exists():
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open('w') as f:
                yaml.dump(default_config, f, indent=2, default_flow_style=False)
            logger.info(f"Created default core configuration file at {file_path}")
        except Exception as e:
            logger.error(f"Failed to create default core config file {file_path}: {e}", exc_info=True)


# Example Usage (for illustration)
if __name__ == '__main__':
    # Setup basic logging for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create a default core config if it doesn't exist
    initial_config = get_config() # Load once to populate defaults
    _create_default_core_config(initial_config)

    # Test loading
    print("--- Loading Configuration ---")
    config = get_config() # Should be cached now
    print(f"NATS URL: {config.get('nats', {}).get('url')}")
    print(f"DB Path: {config.get('knowledge_base', {}).get('database_path')}")
    print(f"Log Level: {config.get('logging', {}).get('level')}")

    # Test environment override (run like: OPMAS_NATS_URL=test_url python src/opmas/config.py)
    print("\n--- Testing Environment Override (Example: export OPMAS_NATS_URL=nats://override:4222) ---")
    # In a real run, env vars would be set before the script starts
    # os.environ["OPMAS_NATS_URL"] = "nats://env_override:4222"
    # os.environ["OPMAS_LOGGING_LEVEL"] = "DEBUG"
    # _config_cache = None # Clear cache to force reload with env vars
    # config = get_config()
    # print(f"NATS URL (after potential override): {config.get('nats', {}).get('url')}")
    # print(f"Log Level (after potential override): {config.get('logging', {}).get('level')}")

    # Test loading specific files
    print("\n--- Testing Specific File Loaders ---")
    rules_path = config.get('knowledge_base', {}).get('agent_rules_path')
    if rules_path:
        agent_rules = load_yaml_file(rules_path)
        if agent_rules:
            print(f"Loaded Agent Rules (first level keys): {list(agent_rules.keys())}")
        else:
            print("Could not load agent rules.")

    playbooks_path = config.get('knowledge_base', {}).get('playbooks_path')
    if playbooks_path:
        playbooks = load_yaml_file(playbooks_path)
        if playbooks:
             print(f"Loaded Playbooks (first level keys): {list(playbooks.keys())}")
        else:
            print("Could not load playbooks.")

    print("\nConfiguration loading demo finished.")

class Settings(BaseSettings):
    """Application settings."""
    # Database settings
    database_url: str = os.getenv("DATABASE_URL", "postgresql://opmas:opmas@localhost:5432/opmas")
    
    # Redis settings
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # NATS settings
    nats_url: str = os.getenv("NATS_URL", "nats://localhost:4222")
    
    class Config:
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings() 