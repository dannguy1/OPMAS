#!/usr/bin/env python3

import asyncio
import logging
import signal
import sys

from opmas.core.logging import LogManager
from opmas.parsers.log_parser import LogParser

logger = LogManager().get_logger(__name__)


async def main():
    """Main entry point for the log parser service."""
    # Create and start the log parser
    parser = LogParser()

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(parser.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start the parser
        await parser.start()

        # Keep the service running
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Error running log parser service: {e}")
        sys.exit(1)
    finally:
        await parser.stop()


if __name__ == "__main__":
    asyncio.run(main())
