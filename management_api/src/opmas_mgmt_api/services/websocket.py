"""WebSocket service for real-time communication."""

import logging
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket
from opmas_mgmt_api.services.nats import NATSService

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket manager for handling real-time connections."""

    def __init__(
        self,
        nats: Optional[NATSService] = None,
    ) -> None:
        """Initialize WebSocket manager.

        Args:
            nats: Optional NATS service instance
        """
        self._nats = nats
        self._connections: Set[WebSocket] = set()
        self._device_subscriptions: Dict[str, Set[WebSocket]] = {}
        self._agent_subscriptions: Dict[str, Set[WebSocket]] = {}
        self._rule_subscriptions: Dict[str, Set[WebSocket]] = {}
        self._system_subscriptions: Set[WebSocket] = set()

    async def connect(
        self,
        websocket: WebSocket,
    ) -> None:
        """Connect a new WebSocket client.

        Args:
            websocket: WebSocket connection to add
        """
        await websocket.accept()
        self._connections.add(websocket)
        logger.debug("New WebSocket connection established")

    async def disconnect(
        self,
        websocket: WebSocket,
    ) -> None:
        """Disconnect a WebSocket client.

        Args:
            websocket: WebSocket connection to remove
        """
        self._connections.remove(websocket)
        for subscriptions in self._device_subscriptions.values():
            subscriptions.discard(websocket)
        for subscriptions in self._agent_subscriptions.values():
            subscriptions.discard(websocket)
        for subscriptions in self._rule_subscriptions.values():
            subscriptions.discard(websocket)
        self._system_subscriptions.discard(websocket)
        logger.debug("WebSocket connection closed")

    async def subscribe_to_device(
        self,
        device_id: str,
        websocket: WebSocket,
    ) -> None:
        """Subscribe WebSocket to device updates.

        Args:
            device_id: Device ID to subscribe to
            websocket: WebSocket connection to subscribe
        """
        if device_id not in self._device_subscriptions:
            self._device_subscriptions[device_id] = set()
        self._device_subscriptions[device_id].add(websocket)
        logger.debug(f"Subscribed to device {device_id}")

    async def subscribe_to_agent(
        self,
        agent_id: str,
        websocket: WebSocket,
    ) -> None:
        """Subscribe WebSocket to agent updates.

        Args:
            agent_id: Agent ID to subscribe to
            websocket: WebSocket connection to subscribe
        """
        if agent_id not in self._agent_subscriptions:
            self._agent_subscriptions[agent_id] = set()
        self._agent_subscriptions[agent_id].add(websocket)
        logger.debug(f"Subscribed to agent {agent_id}")

    async def subscribe_to_rule(
        self,
        rule_id: str,
        websocket: WebSocket,
    ) -> None:
        """Subscribe WebSocket to rule updates.

        Args:
            rule_id: Rule ID to subscribe to
            websocket: WebSocket connection to subscribe
        """
        if rule_id not in self._rule_subscriptions:
            self._rule_subscriptions[rule_id] = set()
        self._rule_subscriptions[rule_id].add(websocket)
        logger.debug(f"Subscribed to rule {rule_id}")

    async def subscribe_to_system(
        self,
        websocket: WebSocket,
    ) -> None:
        """Subscribe WebSocket to system-wide updates.

        Args:
            websocket: WebSocket connection to subscribe
        """
        self._system_subscriptions.add(websocket)
        logger.debug("Subscribed to system updates")

    async def broadcast_device_update(
        self,
        device_id: str,
        message: Dict[str, Any],
    ) -> None:
        """Broadcast device update to subscribers.

        Args:
            device_id: Device ID that was updated
            message: Update message to broadcast
        """
        if device_id in self._device_subscriptions:
            for websocket in self._device_subscriptions[device_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(
                        f"Error broadcasting to device {device_id}: {e}"
                    )

    async def broadcast_agent_update(
        self,
        agent_id: str,
        message: Dict[str, Any],
    ) -> None:
        """Broadcast agent update to subscribers.

        Args:
            agent_id: Agent ID that was updated
            message: Update message to broadcast
        """
        if agent_id in self._agent_subscriptions:
            for websocket in self._agent_subscriptions[agent_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(
                        f"Error broadcasting to agent {agent_id}: {e}"
                    )

    async def broadcast_rule_update(
        self,
        rule_id: str,
        message: Dict[str, Any],
    ) -> None:
        """Broadcast rule update to subscribers.

        Args:
            rule_id: Rule ID that was updated
            message: Update message to broadcast
        """
        if rule_id in self._rule_subscriptions:
            for websocket in self._rule_subscriptions[rule_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(
                        f"Error broadcasting to rule {rule_id}: {e}"
                    )

    async def broadcast_system_update(
        self,
        message: Dict[str, Any],
    ) -> None:
        """Broadcast system update to all subscribers.

        Args:
            message: Update message to broadcast
        """
        for websocket in self._system_subscriptions:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(
                    f"Error broadcasting system update: {e}"
                )
