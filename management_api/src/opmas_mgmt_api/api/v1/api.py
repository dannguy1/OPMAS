"""API router."""

from fastapi import APIRouter
from opmas_mgmt_api.api.v1.endpoints import agents, auth, dashboard, system, websocket

api_router = APIRouter()

# Include auth router
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Include other routers
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
