"""NATS message bus manager."""

import json
import logging
from typing import Any, Dict, Optional
import nats.aio.client as nats

logger = logging.getLogger(__name__)

class NATSManager:
    """NATS message bus manager."""
    
    def __init__(self, url: str = "nats://localhost:4222"):
        """Initialize NATS manager.
        
        Args:
            url: NATS server URL
        """
        self.url = url
        self.nc = None
        
    async def connect(self) -> None:
        """Connect to NATS server."""
        try:
            self.nc = nats.Client()
            await self.nc.connect(self.url)
            logger.info(f"Connected to NATS server at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS server: {e}")
            raise
            
    async def close(self) -> None:
        """Close NATS connection."""
        if self.nc:
            await self.nc.close()
            logger.info("NATS connection closed")
            
    async def publish(self, subject: str, data: Dict[str, Any]) -> None:
        """Publish message to NATS subject.
        
        Args:
            subject: NATS subject to publish to
            data: Message data to publish
        """
        if not self.nc:
            raise RuntimeError("NATS client not connected")
            
        try:
            message = json.dumps(data).encode()
            await self.nc.publish(subject, message)
            logger.debug(f"Published message to {subject}")
        except Exception as e:
            logger.error(f"Failed to publish message to {subject}: {e}")
            raise
            
    async def subscribe(self, subject: str, callback: callable) -> None:
        """Subscribe to NATS subject.
        
        Args:
            subject: NATS subject to subscribe to
            callback: Callback function to handle messages
        """
        if not self.nc:
            raise RuntimeError("NATS client not connected")
            
        try:
            await self.nc.subscribe(subject, cb=callback)
            logger.debug(f"Subscribed to {subject}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {subject}: {e}")
            raise
            
    async def request(self, subject: str, data: Dict[str, Any], timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """Make request to NATS subject.
        
        Args:
            subject: NATS subject to request from
            data: Request data
            timeout: Request timeout in seconds
            
        Returns:
            Response data or None if timeout
        """
        if not self.nc:
            raise RuntimeError("NATS client not connected")
            
        try:
            message = json.dumps(data).encode()
            response = await self.nc.request(subject, message, timeout=timeout)
            if response:
                return json.loads(response.data.decode())
            return None
        except Exception as e:
            logger.error(f"Failed to make request to {subject}: {e}")
            raise 