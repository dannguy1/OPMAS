"""Create admin user script."""

import asyncio
import logging

from opmas_mgmt_api.core.security import get_password_hash
from opmas_mgmt_api.db.base import Base
from opmas_mgmt_api.db.session import async_engine, async_session
from opmas_mgmt_api.models.user import User
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_admin_user():
    """Create admin user if it doesn't exist."""
    try:
        # Create all tables
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Created database tables")

        # Check if admin user exists
        async with async_session() as session:
            result = await session.execute(text("SELECT id FROM users WHERE username = 'admin'"))
            admin = result.scalar_one_or_none()

            if admin:
                logger.info("Admin user already exists")
                return

            # Create admin user
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_superuser=True,
                full_name="System Administrator",
            )
            session.add(admin_user)
            await session.commit()
            logger.info("Created admin user successfully")

    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(create_admin_user())
