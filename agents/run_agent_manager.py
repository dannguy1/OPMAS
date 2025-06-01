#!/usr/bin/env python3
"""Script to run the OPMAS agent manager."""

import asyncio
import logging
import os
from pathlib import Path

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from opmas.agents.management.manager import AgentManager
from opmas.agents.management.registry import AgentRegistry

# Configure structlog with console output
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),  # Set to DEBUG level
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

# Configure standard logging to also show logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = structlog.get_logger(__name__)

async def main():
    """Run the agent manager."""
    try:
        # Get configuration from environment
        nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://opmas:opmas@localhost:5432/opmas")
        
        # Create database engine and session
        engine = create_async_engine(db_url)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Create database session
        async with async_session() as session:
            # Create registry with database session
            registry = AgentRegistry(session)
            
            # Create and start agent manager
            manager = AgentManager(
                db_url=db_url,
                nats_url=nats_url,
                session=session,
                registry=registry
            )
            
            await manager.start()
            
            # Keep running until interrupted
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                await manager.stop()
                
    except Exception as e:
        logger.error(f"Error running agent manager: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main()) 