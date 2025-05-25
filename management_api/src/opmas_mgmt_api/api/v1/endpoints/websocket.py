"""WebSocket endpoints for real-time updates."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from opmas_mgmt_api.core.security import verify_token
from opmas_mgmt_api.core.websocket import WebSocketManager

logger = logging.getLogger(__name__)

router = APIRouter()
websocket_manager = WebSocketManager()


@router.websocket("/ws/system")
async def system_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """WebSocket endpoint for system updates.

    Args:
        websocket: WebSocket connection
        token: Optional authentication token
    """
    try:
        await websocket_manager.connect(websocket, token)
        await websocket_manager.subscribe_to_system(websocket)

        try:
            while True:
                data = await websocket.receive_text()
                # Handle incoming messages if needed
                logger.debug(f"Received message: {data}")
        except WebSocketDisconnect:
            await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if not websocket.client_state.DISCONNECTED:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


@router.websocket("/ws/device/{device_id}")
async def device_websocket(
    websocket: WebSocket,
    device_id: str,
    token: Optional[str] = Query(None),
):
    """WebSocket endpoint for device updates.

    Args:
        websocket: WebSocket connection
        device_id: Device ID to subscribe to
        token: Optional authentication token
    """
    try:
        await websocket_manager.connect(websocket, token)
        await websocket_manager.subscribe_to_device(device_id, websocket)

        try:
            while True:
                data = await websocket.receive_text()
                # Handle incoming messages if needed
                logger.debug(f"Received message for device {device_id}: {data}")
        except WebSocketDisconnect:
            await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error for device {device_id}: {e}")
        if not websocket.client_state.DISCONNECTED:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


@router.websocket("/ws/agent/{agent_id}")
async def agent_websocket(
    websocket: WebSocket,
    agent_id: str,
    token: Optional[str] = Query(None),
):
    """WebSocket endpoint for agent updates.

    Args:
        websocket: WebSocket connection
        agent_id: Agent ID to subscribe to
        token: Optional authentication token
    """
    try:
        await websocket_manager.connect(websocket, token)
        await websocket_manager.subscribe_to_agent(agent_id, websocket)

        try:
            while True:
                data = await websocket.receive_text()
                # Handle incoming messages if needed
                logger.debug(f"Received message for agent {agent_id}: {data}")
        except WebSocketDisconnect:
            await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error for agent {agent_id}: {e}")
        if not websocket.client_state.DISCONNECTED:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


@router.websocket("/ws/rule/{rule_id}")
async def rule_websocket(
    websocket: WebSocket,
    rule_id: str,
    token: Optional[str] = Query(None),
):
    """WebSocket endpoint for rule updates.

    Args:
        websocket: WebSocket connection
        rule_id: Rule ID to subscribe to
        token: Optional authentication token
    """
    try:
        await websocket_manager.connect(websocket, token)
        await websocket_manager.subscribe_to_rule(rule_id, websocket)

        try:
            while True:
                data = await websocket.receive_text()
                # Handle incoming messages if needed
                logger.debug(f"Received message for rule {rule_id}: {data}")
        except WebSocketDisconnect:
            await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error for rule {rule_id}: {e}")
        if not websocket.client_state.DISCONNECTED:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
