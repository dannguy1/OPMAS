"""Initialize the database with initial data."""

import logging

from opmas_mgmt_api.db.base import Base
from opmas_mgmt_api.db.session import engine
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Initialize the database."""
    try:
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
