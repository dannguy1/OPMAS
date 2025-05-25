"""Drop all tables script."""

import asyncio
import logging

from opmas_mgmt_api.core.config import settings
from opmas_mgmt_api.db.base import Base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def drop_all_tables():
    """Drop all tables from the database."""
    try:
        # Create async engine
        async_engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DB_ECHO,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
        )

        async with async_engine.begin() as conn:
            # Drop all tables
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("Successfully dropped all tables")

        await async_engine.dispose()
    except Exception as e:
        logger.error(f"Error dropping tables: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(drop_all_tables())
