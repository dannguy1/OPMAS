"""Database session management."""

import logging
from contextlib import contextmanager
from typing import Generator

from opmas_mgmt_api.config import get_settings
from opmas_mgmt_api.core.config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and session manager."""

    def __init__(self):
        """Initialize the database manager."""
        self.settings = get_settings()
        self.engine = None
        self.session_factory = None

    def init_db(self):
        """Initialize database connection and session factory."""
        if self.engine is None:
            self.engine = create_engine(
                self.settings.database_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_pre_ping=True,
            )

            # Test connection
            try:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1")).scalar()
                logger.info("Successfully connected to database")
            except Exception as e:
                logger.error("Failed to connect to database: %s", e)
                raise

            self.session_factory = sessionmaker(
                bind=self.engine, autocommit=False, autoflush=False, expire_on_commit=False
            )

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session context manager."""
        if self.session_factory is None:
            self.init_db()

        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            logger.error("Database session error: %s", e)
            session.rollback()
            raise
        finally:
            session.close()

    def get_db(self) -> Generator[Session, None, None]:
        """FastAPI dependency to get a database session."""
        if self.session_factory is None:
            self.init_db()

        session = self.session_factory()
        try:
            yield session
        finally:
            session.close()


# Create global database manager instance
db_manager = DatabaseManager()

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DB_ECHO, future=True)

# Create async session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)


async def init_db() -> None:
    """Initialize async database connection."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Successfully connected to database")
    except Exception as e:
        logger.error("Failed to connect to database: %s", e)
        raise
