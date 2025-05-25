"""API router configuration."""

from fastapi import APIRouter
from opmas_mgmt_api.api.v1.endpoints import agents, devices, playbooks, rules

api_router = APIRouter()

api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(rules.router, prefix="/rules", tags=["rules"])
api_router.include_router(playbooks.router, prefix="/playbooks", tags=["playbooks"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
