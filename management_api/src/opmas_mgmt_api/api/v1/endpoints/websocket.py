"""WebSocket endpoints for real-time updates."""

import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from opmas_mgmt_api.core.websocket import WebSocketManager

logger = logging.getLogger(__name__)

router = APIRouter()


def get_websocket_manager() -> WebSocketManager:
    """Get WebSocket manager instance.

    Returns:
        WebSocket manager instance
    """
    return WebSocketManager()


@router.websocket("/ws/devices/{device_id}")
async def device_websocket(
    websocket: WebSocket,
    device_id: str,
    manager: WebSocketManager = Depends(get_websocket_manager),
) -> None:
    """Handle WebSocket connection for device updates.

    Args:
        websocket: WebSocket connection
        device_id: Device ID to subscribe to
        manager: WebSocket manager instance
    """
    try:
        await manager.connect(websocket)
        await manager.subscribe_to_device(device_id)
        try:
            while True:
                await websocket.receive_text()
                # Handle incoming messages if needed
        except WebSocketDisconnect:
            await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in device websocket: {e}")
        await manager.disconnect(websocket)


@router.websocket("/ws/agents/{agent_id}")
async def agent_websocket(
    websocket: WebSocket,
    agent_id: str,
    manager: WebSocketManager = Depends(get_websocket_manager),
) -> None:
    """Handle WebSocket connection for agent updates.

    Args:
        websocket: WebSocket connection
        agent_id: Agent ID to subscribe to
        manager: WebSocket manager instance
    """
    try:
        await manager.connect(websocket)
        await manager.subscribe_to_agent(agent_id)
        try:
            while True:
                await websocket.receive_text()
                # Handle incoming messages if needed
        except WebSocketDisconnect:
            await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in agent websocket: {e}")
        await manager.disconnect(websocket)


@router.websocket("/ws/rules/{rule_id}")
async def rule_websocket(
    websocket: WebSocket,
    rule_id: str,
    manager: WebSocketManager = Depends(get_websocket_manager),
) -> None:
    """Handle WebSocket connection for rule updates.

    Args:
        websocket: WebSocket connection
        rule_id: Rule ID to subscribe to
        manager: WebSocket manager instance
    """
    try:
        await manager.connect(websocket)
        await manager.subscribe_to_rule(rule_id)
        try:
            while True:
                await websocket.receive_text()
                # Handle incoming messages if needed
        except WebSocketDisconnect:
            await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in rule websocket: {e}")
        await manager.disconnect(websocket)


@router.websocket("/ws/system")
async def system_websocket(
    websocket: WebSocket,
    manager: WebSocketManager = Depends(get_websocket_manager),
) -> None:
    """Handle WebSocket connection for system-wide updates.

    Args:
        websocket: WebSocket connection
        manager: WebSocket manager instance
    """
    try:
        await manager.connect(websocket)
        await manager.subscribe_to_system()
        try:
            while True:
                await websocket.receive_text()
                # Handle incoming messages if needed
        except WebSocketDisconnect:
            await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in system websocket: {e}")
        await manager.disconnect(websocket)
