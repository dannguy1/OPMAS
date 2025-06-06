#!/usr/bin/env python3

import asyncio
import logging
import signal
import sys

from opmas.agents.connectivity_agent_package.agent import ConnectivityAgent
from opmas.utils.logging import LogManager

# Initialize logger
logger = LogManager.get_logger(__name__)


async def main():
    """Main entry point for the Connectivity agent service."""
    logger.info("Starting Connectivity agent service...")

    # Create and start the Connectivity agent
    agent = ConnectivityAgent(
        agent_name="ConnectivityAgent",
        subscribed_topics=["logs.connectivity"],
        findings_topic="findings.connectivity",
    )
    try:
        await agent.start()

        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(agent)))

        # Keep the service running
        while True:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before retrying

    except Exception as e:
        logger.error(f"Failed to start Connectivity agent: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await agent.stop()
        logger.info("Connectivity agent service stopped")


async def shutdown(agent: ConnectivityAgent):
    """Handle graceful shutdown of the Connectivity agent."""
    logger.info("Shutting down Connectivity agent service...")
    await agent.stop()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    asyncio.get_event_loop().stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)
