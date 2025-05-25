"""NATS service for message broker functionality."""

import json
import logging
from typing import Any, Dict, Optional

import nats
from nats.aio.client import Client as NATSClient

logger = logging.getLogger(__name__)


class NATSService:
    """NATS service for message broker functionality."""

    def __init__(self, url: str = "nats://localhost:4222"):
        """Initialize NATS service.

        Args:
            url: NATS server URL
        """
        self.url = url
        self.client: Optional[NATSClient] = None

    async def connect(self) -> None:
        """Connect to NATS server."""
        try:
            self.client = await nats.connect(self.url)
            logger.info("Connected to NATS server")
        except Exception as e:
            logger.error(f"Failed to connect to NATS server: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from NATS server."""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Disconnected from NATS server")

    def is_connected(self) -> bool:
        """Check if connected to NATS server.

        Returns:
            bool: True if connected, False otherwise
        """
        return self.client is not None and self.client.is_connected

    async def publish(self, subject: str, message: Dict[str, Any]) -> None:
        """Publish message to NATS subject.

        Args:
            subject: NATS subject
            message: Message to publish
        """
        if not self.client:
            raise RuntimeError("NATS client not connected")

        try:
            await self.client.publish(subject, json.dumps(message).encode())
            logger.debug(f"Published message to {subject}")
        except Exception as e:
            logger.error(f"Failed to publish message to {subject}: {e}")
            raise

    async def subscribe(self, subject: str, callback: Any, queue: Optional[str] = None) -> None:
        """Subscribe to NATS subject.

        Args:
            subject: NATS subject
            callback: Callback function to handle messages
            queue: Optional queue group name
        """
        if not self.client:
            raise RuntimeError("NATS client not connected")

        try:
            await self.client.subscribe(subject, queue=queue, cb=callback)
            logger.debug(f"Subscribed to {subject}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {subject}: {e}")
            raise

    async def request(
        self, subject: str, message: Dict[str, Any], timeout: float = 1.0
    ) -> Dict[str, Any]:
        """Send request to NATS subject and wait for response.

        Args:
            subject: NATS subject
            message: Request message
            timeout: Response timeout in seconds

        Returns:
            Dict[str, Any]: Response message
        """
        if not self.client:
            raise RuntimeError("NATS client not connected")

        try:
            response = await self.client.request(
                subject, json.dumps(message).encode(), timeout=timeout
            )
            return json.loads(response.data.decode())
        except Exception as e:
            logger.error(f"Failed to send request to {subject}: {e}")
            raise
