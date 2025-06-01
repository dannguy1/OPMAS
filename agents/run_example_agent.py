#!/usr/bin/env python3
"""Script to run the example agent."""

import asyncio
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from dotenv import load_dotenv
from opmas.agents.packages.example_agent.agent import ExampleAgent
from opmas.agents.packages.base.models import AgentConfig

async def main():
    """Run the example agent."""
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    agent_id = os.getenv("AGENT_ID", "example-agent-1")
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    heartbeat_interval = int(os.getenv("HEARTBEAT_INTERVAL", "30"))
    log_level = os.getenv("LOG_LEVEL", "INFO")
    metrics_enabled = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    
    # Create agent configuration
    config = AgentConfig(
        agent_id=agent_id,
        agent_type="example",
        nats_url=nats_url,
        heartbeat_interval=heartbeat_interval,
        log_level=log_level,
        metrics_enabled=metrics_enabled
    )
    
    # Create and start agent
    agent = ExampleAgent(
        name="Example System Monitor",
        version="1.0.0",
        description="Monitors system metrics and generates findings",
        capabilities=["system_metrics", "health_monitoring"],
        management_api_url="http://localhost:8000",
        nats_url=nats_url,
        agent_id=agent_id
    )
    
    try:
        await agent.start()
        print(f"Agent {agent_id} started. Press Ctrl+C to stop.")
        
        # Keep the agent running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping agent...")
    finally:
        await agent.stop()
        print("Agent stopped.")

if __name__ == "__main__":
    asyncio.run(main()) 