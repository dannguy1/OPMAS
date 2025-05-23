#!/usr/bin/env python3

"""Script to run the Database Agent service."""

import asyncio
import logging
import signal
import sys
from opmas.agents.database_agent_package.agent import DatabaseAgent
from opmas.utils.logging import LogManager

# Initialize logger
logger = LogManager.get_logger(__name__)

async def main():
    """Main function to run the Database Agent service."""
    logger.info("Starting Database Agent service...")
    
    try:
        # Create and start the Database Agent
        agent = DatabaseAgent(
            agent_name="DatabaseAgent",
            subscribed_topics=["logs.database"],
            findings_topic="findings.database"
        )
        
        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(shutdown(s, agent))
            )
        
        # Start the agent
        await agent.start()
        
        # Keep the service running
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in Database Agent service: {str(e)}")
        sys.exit(1)
    finally:
        await agent.stop()
        logger.info("Database Agent service stopped.")

async def shutdown(signal, agent):
    """Handle graceful shutdown of the Database Agent."""
    logger.info(f"Received exit signal {signal.name}...")
    
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    [task.cancel() for task in tasks]
    
    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    
    await agent.stop()
    logger.info("Shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        sys.exit(1) 