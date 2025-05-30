"""Agent discovery implementation."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class AgentDiscovery:
    """Discovers and loads agent configurations."""

    def __init__(self):
        """Initialize the agent discovery."""
        self._running = False
        # Point to the packages directory
        self._agents_dir = Path(__file__).parent.parent / "packages"
        self._skip_patterns = {
            "__pycache__",
            "_template",
            "test"
        }

    async def start(self) -> None:
        """Start the agent discovery."""
        if self._running:
            return

        logger.info("Starting agent discovery")
        self._running = True

    async def stop(self) -> None:
        """Stop the agent discovery."""
        if not self._running:
            return

        logger.info("Stopping agent discovery")
        self._running = False

    async def discover_agents(self) -> List[Dict]:
        """Discover agent configurations."""
        if not self._running:
            return []

        agents = []
        for agent_dir in self._agents_dir.iterdir():
            if not agent_dir.is_dir():
                continue

            # Skip patterns
            if agent_dir.name in self._skip_patterns:
                continue

            # Check for .env file
            env_file = agent_dir / ".env"
            if not env_file.exists():
                continue

            try:
                # Load configuration
                config = await self._load_agent_config(agent_dir)
                if config:
                    agents.append(config)
            except Exception as e:
                logger.error(f"Failed to load agent config from {agent_dir}: {e}")

        return agents

    async def _load_agent_config(self, agent_dir: Path) -> Optional[Dict]:
        """Load agent configuration from directory."""
        try:
            # Load .env file
            env_file = agent_dir / ".env"
            load_dotenv(env_file)

            # Get basic config
            config = {
                "agent_id": os.getenv("AGENT_ID"),
                "name": os.getenv("AGENT_NAME"),
                "description": os.getenv("AGENT_DESCRIPTION"),
                "type": agent_dir.name,
                "path": str(agent_dir)
            }

            # Load additional config from config.yaml if exists
            config_file = agent_dir / "config.yaml"
            if config_file.exists():
                with open(config_file) as f:
                    config.update(yaml.safe_load(f))

            return config
        except Exception as e:
            logger.error(f"Failed to load agent config: {e}")
            return None 