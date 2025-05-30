"""API router."""

from fastapi import APIRouter
from opmas_mgmt_api.api.v1.endpoints import (
    actions,
    agents,
    auth,
    dashboard,
    devices,
    findings,
    playbooks,
    rules,
    system,
)

api_router = APIRouter()

# Include auth router
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Include other routers
api_router.include_router(actions.router, prefix="/actions", tags=["actions"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(findings.router, prefix="/findings", tags=["findings"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(playbooks.router, prefix="/playbooks", tags=["playbooks"])
api_router.include_router(rules.router, prefix="/rules", tags=["rules"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
