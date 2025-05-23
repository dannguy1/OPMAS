"""API dependencies."""

from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import nats.aio.client as nats
from opmas_mgmt_api.db.session import async_session
from opmas_mgmt_api.core.config import settings

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_nats() -> Optional[nats.Client]:
    """Get NATS client.
    
    Returns:
        Optional[nats.Client]: NATS client instance
    """
    try:
        nc = nats.Client()
        await nc.connect(settings.NATS_URL)
        return nc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to NATS: {str(e)}"
        )
