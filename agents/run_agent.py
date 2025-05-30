#!/usr/bin/env python3
"""Script to run an OPMAS agent."""

import asyncio
import logging
import yaml
import sys
from pathlib import Path

from opmas.agents.security.security_agent import SecurityAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Run the agent."""
    try:
        # Load configuration
        config_path = Path(__file__).parent / "config" / "agent_config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Get security agent config
        agent_config = config["security"]
        
        # Create and start agent
        agent = SecurityAgent(agent_config["agent_id"], agent_config)
        logger.info(f"Starting agent {agent.agent_id}")
        
        # Start agent
        await agent.start()
        
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping agent...")
            await agent.stop()
            
    except Exception as e:
        logger.error(f"Error running agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 