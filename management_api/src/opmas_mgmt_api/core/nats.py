"""NATS message broker integration."""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional, TypeVar

from nats.aio.client import Client as NATS
from nats.aio.msg import Msg
from nats.js.client import JetStreamContext
from opmas_mgmt_api.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class NATSManager:
    """Manages NATS connection and message handling."""

    _instance: Optional["NATSManager"] = None
    _nc: Optional[NATS] = None
    _js: Optional[JetStreamContext] = None
    _connected: bool = False
    _lock: asyncio.Lock = asyncio.Lock()

    def __new__(cls) -> "NATSManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self) -> None:
        """Connect to NATS server."""
        if self._connected:
            return

        async with self._lock:
            if self._connected:  # Double check after acquiring lock
                return

            try:
                settings = get_settings()
                self._nc = NATS()
                await self._nc.connect(settings.NATS_URL)
                self._js = self._nc.jetstream()
                self._connected = True
                logger.info("Successfully connected to NATS server")
            except Exception as e:
                logger.error(f"Failed to connect to NATS: {e}")
                raise

    async def disconnect(self) -> None:
        """Disconnect from NATS server."""
        if not self._connected:
            return

        async with self._lock:
            if not self._connected:  # Double check after acquiring lock
                return

            try:
                if self._nc:
                    await self._nc.drain()
                    await self._nc.close()
                self._connected = False
                logger.info("Disconnected from NATS server")
            except Exception as e:
                logger.error(f"Error disconnecting from NATS: {e}")
                raise

    async def publish(
        self,
        subject: str,
        payload: Any,
        stream: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Publish message to NATS subject.

        Args:
            subject: NATS subject to publish to
            payload: Message payload
            stream: Optional stream name for JetStream
            headers: Optional message headers

        Raises:
            RuntimeError: If not connected to NATS
        """
        if not self._connected or not self._nc:
            raise RuntimeError("Not connected to NATS")

        try:
            if isinstance(payload, (dict, list)):
                payload = json.dumps(payload).encode()
            elif not isinstance(payload, bytes):
                payload = str(payload).encode()

            if stream and self._js:
                await self._js.publish(
                    subject,
                    payload,
                    stream=stream,
                    headers=headers,
                )
            else:
                await self._nc.publish(subject, payload, headers=headers)
        except Exception as e:
            logger.error(f"Error publishing to {subject}: {e}")
            raise

    async def subscribe(
        self,
        subject: str,
        callback: Callable[[Msg], None],
        queue: Optional[str] = None,
        stream: Optional[str] = None,
    ) -> None:
        """Subscribe to NATS subject.

        Args:
            subject: NATS subject to subscribe to
            callback: Callback function to handle messages
            queue: Optional queue group name
            stream: Optional stream name for JetStream

        Raises:
            RuntimeError: If not connected to NATS
        """
        if not self._connected or not self._nc:
            raise RuntimeError("Not connected to NATS")

        try:
            if stream and self._js:
                await self._js.subscribe(
                    subject,
                    queue=queue,
                    stream=stream,
                    cb=callback,
                )
            else:
                await self._nc.subscribe(
                    subject,
                    queue=queue,
                    cb=callback,
                )
        except Exception as e:
            logger.error(f"Error subscribing to {subject}: {e}")
            raise

    async def request(
        self,
        subject: str,
        payload: Any,
        timeout: float = 1.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> Msg:
        """Make request to NATS subject.

        Args:
            subject: NATS subject to request from
            payload: Request payload
            timeout: Request timeout in seconds
            headers: Optional message headers

        Returns:
            Response message

        Raises:
            RuntimeError: If not connected to NATS
        """
        if not self._connected or not self._nc:
            raise RuntimeError("Not connected to NATS")

        try:
            if isinstance(payload, (dict, list)):
                payload = json.dumps(payload).encode()
            elif not isinstance(payload, bytes):
                payload = str(payload).encode()

            return await self._nc.request(
                subject,
                payload,
                timeout=timeout,
                headers=headers,
            )
        except Exception as e:
            logger.error(f"Error making request to {subject}: {e}")
            raise

    @property
    def is_connected(self) -> bool:
        """Check if connected to NATS.

        Returns:
            True if connected, False otherwise
        """
        return self._connected

    @property
    def client(self) -> Optional[NATS]:
        """Get NATS client instance.

        Returns:
            NATS client instance or None if not connected
        """
        return self._nc

    @property
    def jetstream(self) -> Optional[JetStreamContext]:
        """Get JetStream context.

        Returns:
            JetStream context or None if not connected
        """
        return self._js
