"""
OPMAS Core Main Module
"""

import asyncio
import logging
from typing import NoReturn

from .config import Config, load_config

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main entry point for OPMAS."""
    config = load_config()
    logger.info("Starting OPMAS", config=config.model_dump())


def run() -> NoReturn:
    """Run OPMAS."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down OPMAS")
    except Exception as e:
        logger.error("OPMAS failed", exc_info=e)
        raise


if __name__ == "__main__":
    run()
