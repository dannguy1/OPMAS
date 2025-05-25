"""NATS service for message handling."""

import logging
from typing import Any, Dict, Optional, cast

import nats
from nats.aio.client import Client as NATSClient

logger = logging.getLogger(__name__)


class NATSService:
    """NATS service for message handling."""

    def __init__(self) -> None:
        """Initialize NATS service."""
        self._client: Optional[NATSClient] = None
        self._connected = False

    async def connect(self) -> None:
        """Connect to NATS server."""
        try:
            self._client = await nats.connect()
            self._connected = True
            logger.info("Connected to NATS server")
        except Exception as e:
            logger.error(
                f"Failed to connect to NATS server: {e}"
            )
            raise

    async def disconnect(self) -> None:
        """Disconnect from NATS server."""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Disconnected from NATS server")

    async def publish(
        self,
        subject: str,
        payload: Dict[str, Any],
    ) -> None:
        """Publish message to NATS subject.

        Args:
            subject: NATS subject to publish to
            payload: Message payload
        """
        if not self._client:
            raise RuntimeError("NATS client not connected")
        try:
            await self._client.publish(subject, payload)
            logger.debug(f"Published message to {subject}")
        except Exception as e:
            logger.error(
                f"Failed to publish message: {e}"
            )
            raise

    async def subscribe(
        self,
        subject: str,
        callback: Any,
    ) -> None:
        """Subscribe to NATS subject.

        Args:
            subject: NATS subject to subscribe to
            callback: Callback function to handle messages
        """
        if not self._client:
            raise RuntimeError("NATS client not connected")
        try:
            await self._client.subscribe(subject, cb=callback)
            logger.debug(f"Subscribed to {subject}")
        except Exception as e:
            logger.error(
                f"Failed to subscribe: {e}"
            )
            raise

    async def request(
        self,
        subject: str,
        payload: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Send request to NATS subject and wait for response.

        Args:
            subject: NATS subject to send request to
            payload: Request payload

        Returns:
            Response payload or None if no response
        """
        if not self._client:
            raise RuntimeError("NATS client not connected")
        try:
            response = await self._client.request(subject, payload)
            return cast(Dict[str, Any], response)
        except Exception as e:
            logger.error(
                f"Failed to send request: {e}"
            )
            return None

    @property
    def is_connected(self) -> bool:
        """Check if NATS client is connected.

        Returns:
            True if connected, False otherwise
        """
        return self._connected


# Create singleton instance
nats_manager = NATSService()
