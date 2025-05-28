"""Recreate admin user script."""

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


async def recreate_admin_user():
    """Delete and recreate admin user."""
    try:
        # Delete existing admin user
        async with async_session() as session:
            await session.execute(text("DELETE FROM users WHERE username = 'admin'"))
            await session.commit()
            logger.info("Deleted existing admin user")

            # Create new admin user
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
            logger.info("Created new admin user successfully")

    except Exception as e:
        logger.error(f"Error recreating admin user: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(recreate_admin_user()) 