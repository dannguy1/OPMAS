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
from opmas_mgmt_api.services.agents import AgentService
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
    try:
        return await service.get_agent(agent_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@route.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    agent: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> AgentResponse:
    """Update an agent."""
    service = AgentService(db, nats)
    try:
        return await service.update_agent(agent_id, agent)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.delete("/{agent_id}")
async def delete_agent(
    agent_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> None:
    """Delete an agent."""
    service = AgentService(db, nats)
    try:
        await service.delete_agent(agent_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@route.get("/{agent_id}/status", response_model=AgentStatus)
async def get_agent_status(
    agent_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> AgentStatus:
    """Get agent status."""
    service = AgentService(db, nats)
    try:
        return await service.get_agent_status(agent_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@route.post("/{agent_id}/status", response_model=AgentStatus)
async def update_agent_status(
    agent_id: UUID,
    status: str = Body(...),
    details: Optional[Dict[str, Any]] = Body(None),
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> AgentStatus:
    """Update agent status."""
    service = AgentService(db, nats)
    try:
        return await service.update_agent_status(agent_id, status, details)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.get("/{agent_id}/config", response_model=AgentConfig)
async def get_agent_config(
    agent_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> AgentConfig:
    """Get agent configuration."""
    service = AgentService(db, nats)
    try:
        return await service.get_agent_config(agent_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@route.put("/{agent_id}/config", response_model=AgentConfig)
async def update_agent_config(
    agent_id: UUID,
    config: Dict[str, Any] = Body(...),
    version: str = Body(...),
    metadata: Optional[Dict[str, Any]] = Body(None),
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> AgentConfig:
    """Update agent configuration."""
    service = AgentService(db, nats)
    try:
        return await service.update_agent_config(agent_id, config, version, metadata)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
