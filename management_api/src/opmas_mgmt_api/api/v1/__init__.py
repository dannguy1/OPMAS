"""API v1 package."""

from fastapi import APIRouter

router = APIRouter()

# Import routers from endpoints
from .endpoints import (
    devices,
    agents,
    rules,
    playbooks,
    system,
    logs,
    configurations
)

# Include all routers
router.include_router(devices.router, prefix="/devices", tags=["Devices"])
router.include_router(agents.router, prefix="/agents", tags=["Agents"])
router.include_router(rules.router, prefix="/rules", tags=["Rules"])
router.include_router(playbooks.router, prefix="/playbooks", tags=["Playbooks"])
router.include_router(system.router, prefix="/system", tags=["System"])
router.include_router(logs.router, prefix="/logs", tags=["Logs"])
router.include_router(configurations.router, prefix="/config", tags=["Configuration"])
