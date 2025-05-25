"""NATS client management."""

import asyncio
import logging
from typing import Optional

import nats.aio.client as nats
from opmas_mgmt_api.core.config import settings

logger = logging.getLogger(__name__)


class NATSManager:
    """NATS client manager."""

    def __init__(self):
        """Initialize NATS manager."""
        self.client: Optional[nats.Client] = None
        self.connected = False

    async def connect(self) -> None:
        """Connect to NATS server."""
        if self.connected:
            return

        try:
            self.client = nats.Client()
            await self.client.connect(
                servers=[settings.NATS_URL],
                name="opmas-mgmt-api",
                connect_timeout=5,
                ping_interval=20,
                max_outstanding_pings=3,
            )
            self.connected = True
            logger.info("Connected to NATS server at %s", settings.NATS_URL)
        except Exception as e:
            logger.error("Failed to connect to NATS server: %s", e)
            raise

    async def disconnect(self) -> None:
        """Disconnect from NATS server."""
        if self.client and self.connected:
            await self.client.close()
            self.connected = False
            logger.info("Disconnected from NATS server")

    async def publish(self, subject: str, payload: bytes) -> None:
        """Publish message to NATS subject.

        Args:
            subject: NATS subject
            payload: Message payload
        """
        if not self.connected:
            await self.connect()

        try:
            await self.client.publish(subject, payload)
        except Exception as e:
            logger.error("Failed to publish message to %s: %s", subject, e)
            raise

    async def subscribe(self, subject: str, callback) -> None:
        """Subscribe to NATS subject.

        Args:
            subject: NATS subject
            callback: Callback function to handle messages
        """
        if not self.connected:
            await self.connect()

        try:
            await self.client.subscribe(subject, cb=callback)
        except Exception as e:
            logger.error("Failed to subscribe to %s: %s", subject, e)
            raise


# Create global NATS manager instance
nats_manager = NATSManager()
