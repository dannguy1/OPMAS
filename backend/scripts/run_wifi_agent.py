#!/usr/bin/env python3

import asyncio
import logging
import signal
import sys

from opmas.agents.wifi_agent_package.agent import WiFiAgent
from opmas.utils.logging import LogManager

# Initialize logger
logger = LogManager.get_logger(__name__)


async def main():
    """Main entry point for the WiFi agent service."""
    logger.info("Starting WiFi agent service...")

    # Create and start the WiFi agent
    agent = WiFiAgent()
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
        logger.error(f"Failed to start WiFi agent: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await agent.stop()
        logger.info("WiFi agent service stopped")


async def shutdown(agent: WiFiAgent):
    """Handle graceful shutdown of the WiFi agent."""
    logger.info("Shutting down WiFi agent service...")
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
