"""Script to initialize database tables."""

import logging
from opmas_mgmt_api.db.base import Base
from opmas_mgmt_api.db.session import engine
from sqlalchemy import text

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Initialize database tables."""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        # Enable UUID extension if not already enabled
        with engine.connect() as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            # Set default UUID generation for users table
            conn.execute(
                text(
                    """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'users'
                        AND column_name = 'id'
                        AND column_default LIKE '%uuid_generate_v4%'
                    ) THEN
                        ALTER TABLE users ALTER COLUMN id SET DEFAULT uuid_generate_v4();
                    END IF;
                END $$;
                """
                )
            )
        logger.info("Database UUID configuration completed successfully")

    except Exception as e:
        logger.error("Failed to initialize database: %s", e)
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
