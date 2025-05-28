"""Script to run the example agent."""
import asyncio
import os
import sys
import uuid
import logging
from dotenv import load_dotenv
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent.parent.parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import structlog

from opmas.agents.example_agent.agent import ExampleAgent

# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Load environment variables
load_dotenv()

def ensure_agent_id() -> str:
    """Ensure AGENT_ID exists in .env file."""
    env_path = Path(__file__).parent / '.env'
    if not env_path.exists():
        raise FileNotFoundError(f"Agent .env file not found at {env_path}")

    # Read current .env content
    with open(env_path, 'r') as f:
        lines = f.readlines()

    # Check if AGENT_ID exists and is not commented out
    agent_id = None
    for i, line in enumerate(lines):
        if line.strip().startswith('AGENT_ID='):
            agent_id = line.split('=')[1].strip()
            break
        elif line.strip().startswith('#AGENT_ID='):
            # Found commented out AGENT_ID
            agent_id = None
            break

    # If no AGENT_ID found or it's commented out, generate one
    if not agent_id:
        agent_id = str(uuid.uuid4())
        # Add or update AGENT_ID in .env
        with open(env_path, 'w') as f:
            for line in lines:
                if line.strip().startswith('#AGENT_ID='):
                    # Replace commented out line
                    f.write(f'AGENT_ID={agent_id}\n')
                elif not line.strip().startswith('AGENT_ID='):
                    f.write(line)
            # If no AGENT_ID line found at all, add it
            if not any(line.strip().startswith('AGENT_ID=') for line in lines):
                f.write(f'\nAGENT_ID={agent_id}\n')
        logger.info("generated_new_agent_id", agent_id=agent_id)

    return agent_id

async def main() -> None:
    """Run the example agent."""
    try:
        # Ensure AGENT_ID exists
        agent_id = ensure_agent_id()

        # Create agent instance
        agent = ExampleAgent(
            name=os.getenv("AGENT_NAME", "example-agent"),
            version="0.1.0",
            description=os.getenv("AGENT_DESCRIPTION", "Example agent for monitoring system resources"),
            capabilities=["resource_monitoring", "finding_generation"],
            management_api_url=os.getenv("MANAGEMENT_API_URL", "http://localhost:8000"),
            nats_url=os.getenv("NATS_URL", "nats://localhost:4222"),
            agent_id=agent_id
        )

        # Start the agent
        logger.info("starting_example_agent")
        await agent.start()

        # Keep the agent running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("stopping_example_agent")
            await agent.stop()
            logger.info("example_agent_stopped")

    except Exception as e:
        logger.error("error_running_example_agent", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main()) 