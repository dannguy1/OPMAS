"""Agent management endpoints."""

from typing import Any, Dict, List, Optional
from uuid import UUID
import logging
import asyncio

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from opmas_mgmt_api.api.deps import get_db, get_nats
from opmas_mgmt_api.api.v1.endpoints.route_utils import create_route_builder
from opmas_mgmt_api.core.exceptions import ResourceNotFoundError, ValidationError
from opmas_mgmt_api.schemas.agents import (
    AgentBase,
    AgentConfig,
    AgentCreate,
    AgentDiscovery,
    AgentList,
    AgentResponse,
    AgentStatus,
    AgentUpdate,
)
from opmas_mgmt_api.agents.agent import AgentService
from sqlalchemy.ext.asyncio import AsyncSession
from opmas_mgmt_api.core.nats import nats_manager

router = APIRouter()
route = create_route_builder(router)
logger = logging.getLogger(__name__)


@route.get("", response_model=AgentList)
async def list_agents(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    device_id: Optional[UUID] = Query(None, description="Filter by device ID"),
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> AgentList:
    """List agents with optional filtering."""
    service = AgentService(db, nats)
    return await service.list_agents(
        skip=skip,
        limit=limit,
        agent_type=agent_type,
        status=status,
        enabled=enabled,
        device_id=device_id,
    )


@route.post("", response_model=AgentResponse)
async def create_agent(
    agent: AgentCreate, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> AgentResponse:
    """Create a new agent."""
    service = AgentService(db, nats)
    try:
        return await service.create_agent(agent)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> AgentResponse:
    """Get agent by ID."""
    service = AgentService(db, nats)
    agent = await service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return agent


@route.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    agent: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> AgentResponse:
    """Update an agent."""
    service = AgentService(db, nats)
    updated_agent = await service.update_agent(agent_id, agent)
    if not updated_agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return updated_agent


@route.delete("/{agent_id}")
async def delete_agent(
    agent_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> None:
    """Delete an agent."""
    service = AgentService(db, nats)
    if not await service.delete_agent(agent_id):
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")


@route.get("/{agent_id}/status", response_model=AgentStatus)
async def get_agent_status(
    agent_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> AgentStatus:
    """Get agent status."""
    service = AgentService(db, nats)
    status = await service.get_agent_status(agent_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return status


@route.post("/{agent_id}/status", response_model=AgentStatus)
async def update_agent_status(
    agent_id: UUID,
    status: AgentStatus,
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> AgentStatus:
    """Update agent status."""
    service = AgentService(db, nats)
    updated_status = await service.update_agent_status(agent_id, status)
    if not updated_status:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return updated_status


@route.post("/discover", response_model=List[AgentDiscovery])
async def discover_agents(
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> List[AgentDiscovery]:
    """Discover available agents.

    Args:
        db: Database session
        nats: NATS client instance

    Returns:
        List[AgentDiscovery]: List of discovered agents
    """
    try:
        service = AgentService(db, nats)
        agents = await service.discover_agents()
        logger.info("Retrieved %d registered agents", len(agents))
        return agents

    except Exception as e:
        logger.error("Failed to discover agents: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to discover agents. Please try again."
        )
