"""NATS client management."""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

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
        if self.connected and self.client and self.client.is_connected:
            return

        try:
            if self.client:
                await self.client.close()
                self.client = None
                self.connected = False

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
            self.connected = False
            raise

    async def disconnect(self) -> None:
        """Disconnect from NATS server."""
        if self.client and self.connected:
            await self.client.close()
            self.connected = False
            logger.info("Disconnected from NATS server")

    async def publish(self, subject: str, payload: Dict[str, Any]) -> None:
        """Publish message to NATS subject.

        Args:
            subject: NATS subject
            payload: Message payload as dictionary
        """
        if not self.connected or not self.client or not self.client.is_connected:
            await self.connect()

        try:
            # Convert dictionary to JSON string
            message = json.dumps(payload)
            # Publish the message
            await self.client.publish(subject, message.encode())
            logger.debug("Published message to %s: %s", subject, payload)
        except Exception as e:
            logger.error("Failed to publish message to %s: %s", subject, e)
            self.connected = False
            raise

    async def subscribe(self, subject: str, callback) -> None:
        """Subscribe to NATS subject.

        Args:
            subject: NATS subject
            callback: Callback function to handle messages
        """
        if not self.connected or not self.client or not self.client.is_connected:
            await self.connect()

        try:
            await self.client.subscribe(subject, cb=callback)
            logger.debug("Subscribed to %s", subject)
        except Exception as e:
            logger.error("Failed to subscribe to %s: %s", subject, e)
            self.connected = False
            raise

    async def request(self, subject: str, payload: Dict[str, Any], timeout: float = 1.0) -> Dict[str, Any]:
        """Send request to NATS subject and wait for response.

        Args:
            subject: NATS subject
            payload: Request payload as dictionary
            timeout: Response timeout in seconds

        Returns:
            Dict[str, Any]: Response message
        """
        if not self.connected or not self.client or not self.client.is_connected:
            await self.connect()

        try:
            # Convert dictionary to JSON string
            message = json.dumps(payload)
            # Send request and get response
            response = await self.client.request(subject, message.encode(), timeout=timeout)
            # Decode and parse response
            return json.loads(response.data.decode())
        except Exception as e:
            logger.error("Failed to send request to %s: %s", subject, e)
            self.connected = False
            raise

    def is_connected(self) -> bool:
        """Check if connected to NATS server.

        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected and self.client is not None and self.client.is_connected


# Create global NATS manager instance
nats_manager = NATSManager()
