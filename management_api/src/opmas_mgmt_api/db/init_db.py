"""Initialize the database with initial data."""

import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opmas_mgmt_api.core.security import get_password_hash
from opmas_mgmt_api.db.base import Base
from opmas_mgmt_api.db.session import async_engine, async_session
from opmas_mgmt_api.models.user import User

logger = logging.getLogger(__name__)


async def create_initial_admin(session: AsyncSession) -> None:
    """Create initial admin user if it doesn't exist."""
    # Check if admin user exists
    result = await session.execute(select(User).where(User.username == "admin"))
    admin = result.scalar_one_or_none()

    if not admin:
        # Create admin user
        now = datetime.utcnow()
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="Administrator",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True,
            created_at=now,
            updated_at=now,
        )
        session.add(admin)
        await session.commit()
        logger.info("Initial admin user created successfully")
    else:
        logger.info("Admin user already exists")


async def init_db() -> None:
    """Initialize the database."""
    try:
        # Create tables
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

        # Create initial admin user
        async with async_session() as session:
            await create_initial_admin(session)

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
