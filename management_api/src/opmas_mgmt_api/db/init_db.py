"""Database initialization script."""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from opmas_mgmt_api.core.config import settings
from opmas_mgmt_api.db.base import Base

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Initialize the database."""
    try:
        # Create engine
        engine = create_engine(
            settings.SQLALCHEMY_DATABASE_URI,
            echo=settings.DB_ECHO,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT
        )
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise


def init_test_data() -> None:
    """Initialize test data."""
    # TODO: Add test data initialization
    pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()


