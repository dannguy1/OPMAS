"""NATS message bus integration."""

import json
import logging
import asyncio
from typing import Any, Callable, Dict, Optional
import nats
from nats.aio.client import Client as NATS
from opmas_mgmt_api.core.config import settings

logger = logging.getLogger(__name__)

class NATSManager:
    """NATS message bus manager."""
    
    def __init__(self):
        """Initialize NATS manager."""
        self.settings = settings
        self.nc: Optional[NATS] = None
        self._subscribers: Dict[str, Callable] = {}
        
    async def connect(self):
        """Connect to NATS server."""
        if self.nc is None:
            try:
                self.nc = await nats.connect(self.settings.NATS_URL)
                logger.info("Successfully connected to NATS server")
            except Exception as e:
                logger.error("Failed to connect to NATS server: %s", e)
                raise
                
    async def close(self):
        """Close NATS connection."""
        if self.nc is not None:
            await self.nc.close()
            self.nc = None
            
    async def publish(self, subject: str, data: Dict[str, Any]):
        """Publish message to NATS subject."""
        if self.nc is None:
            await self.connect()
            
        try:
            message = json.dumps(data).encode()
            await self.nc.publish(subject, message)
            logger.debug("Published message to %s", subject)
        except Exception as e:
            logger.error("Failed to publish message to %s: %s", subject, e)
            raise
            
    async def subscribe(self, subject: str, callback: Callable):
        """Subscribe to NATS subject."""
        if self.nc is None:
            await self.connect()
            
        try:
            await self.nc.subscribe(subject, cb=callback)
            self._subscribers[subject] = callback
            logger.debug("Subscribed to %s", subject)
        except Exception as e:
            logger.error("Failed to subscribe to %s: %s", subject, e)
            raise
            
    async def unsubscribe(self, subject: str):
        """Unsubscribe from NATS subject."""
        if self.nc is not None and subject in self._subscribers:
            try:
                await self.nc.unsubscribe(subject)
                del self._subscribers[subject]
                logger.debug("Unsubscribed from %s", subject)
            except Exception as e:
                logger.error("Failed to unsubscribe from %s: %s", subject, e)
                raise

# Create global NATS manager instance
nats_manager = NATSManager() 