import os
from pathlib import Path
from typing import Any, Dict

import yaml


class TestConfig:
    def __init__(self):
        config_path = Path(__file__).parent.parent / "fixtures" / "config" / "test_config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        self.database_config = config["database"]
        self.logging_config = config["logging"]

    @property
    def nats_config(self) -> Dict[str, Any]:
        """Get NATS configuration."""
        return self.config["nats"]

    @property
    def redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration."""
        return self.config["redis"]

    @property
    def test_config(self) -> Dict[str, Any]:
        """Get test-specific configuration."""
        return self.config["test"]

    def get_database_url(self) -> str:
        """Get formatted database URL."""
        db = self.database_config
        return f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['name']}"

    def get_nats_url(self) -> str:
        """Get formatted NATS URL."""
        nats = self.nats_config
        return f"nats://{nats['host']}:{nats['port']}"

    def get_redis_url(self) -> str:
        """Get formatted Redis URL."""
        redis = self.redis_config
        return f"redis://{redis['host']}:{redis['port']}/{redis['db']}"
