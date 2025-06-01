"""Agent discovery implementation."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class AgentDiscovery:
    """Discovers available agents."""

    def __init__(self):
        """Initialize agent discovery."""
        # Get the base directory (agents/src/opmas)
        base_dir = Path(__file__).parent.parent.parent
        self.agent_dir = base_dir / "agents" / "packages"
        logger.info(f"Agent discovery initialized with directory: {self.agent_dir}")

    async def start(self) -> None:
        """Start agent discovery."""
        logger.info("Starting agent discovery")

    async def stop(self) -> None:
        """Stop agent discovery."""
        pass

    async def discover_agents(self) -> List[Dict]:
        """Discover available agents."""
        discovered_agents = []
        
        if not self.agent_dir.exists():
            logger.error(f"Agent packages directory does not exist: {self.agent_dir}")
            return discovered_agents

        logger.info(f"Scanning directory for agents: {self.agent_dir}")
        
        # Look for agent directories
        for agent_dir in self.agent_dir.iterdir():
            if not agent_dir.is_dir():
                continue
                
            # Look for config files
            config_file = agent_dir / "config.json"
            env_file = agent_dir / ".env"
            
            if config_file.exists():
                try:
                    with open(config_file) as f:
                        config = json.load(f)
                        config['path'] = str(agent_dir)
                        discovered_agents.append(config)
                        logger.info(f"Loaded agent config: {config}")
                except Exception as e:
                    logger.error(f"Error loading config for {agent_dir}: {e}")
            elif env_file.exists():
                try:
                    # Read existing .env file
                    env_vars = {}
                    with open(env_file) as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                key, value = line.split('=', 1)
                                env_vars[key.strip()] = value.strip()
                    
                    # Create agent config from .env
                    config = {
                        'agent_id': env_vars.get('AGENT_ID', f"{agent_dir.name}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"),
                        'name': env_vars.get('AGENT_NAME', agent_dir.name),
                        'description': env_vars.get('AGENT_DESCRIPTION', ''),
                        'type': env_vars.get('AGENT_TYPE', agent_dir.name),
                        'path': str(agent_dir),
                        'status': env_vars.get('AGENT_STATUS', 'inactive')
                    }
                    
                    # Update .env with agent ID if not present
                    if 'AGENT_ID' not in env_vars:
                        with open(env_file, 'a') as f:
                            f.write(f"\nAGENT_ID={config['agent_id']}\n")
                    
                    discovered_agents.append(config)
                    logger.info(f"Loaded agent config from .env: {config}")
                except Exception as e:
                    logger.error(f"Error loading .env for {agent_dir}: {e}")

        logger.info(f"Discovery complete. Found {len(discovered_agents)} agents: {[a['name'] for a in discovered_agents]}")
        return discovered_agents 