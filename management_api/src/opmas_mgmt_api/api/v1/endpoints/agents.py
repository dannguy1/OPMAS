"""Agent management endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from opmas_mgmt_api.api.deps import get_db, get_nats
from opmas_mgmt_api.services.agents import AgentService
from opmas_mgmt_api.schemas.agents import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentList,
    AgentStatus,
    AgentConfig,
    AgentDiscovery
)
from opmas_mgmt_api.core.exceptions import ResourceNotFoundError, ValidationError

router = APIRouter()

@router.get("/agents", response_model=AgentList)
async def list_agents(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    device_id: Optional[UUID] = Query(None, description="Filter by device ID"),
    db: AsyncSession = Depends(get_db),
    nats = Depends(get_nats)
):
    """List agents with optional filtering."""
    service = AgentService(db, nats)
    return await service.list_agents(
        skip=skip,
        limit=limit,
        agent_type=agent_type,
        status=status,
        enabled=enabled,
        device_id=device_id
    )

@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_agent(
    agent: AgentCreate,
    db: AsyncSession = Depends(get_db),
    nats = Depends(get_nats)
):
    """Create a new agent."""
    service = AgentService(db, nats)
    try:
        return await service.create_agent(agent)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats = Depends(get_nats)
):
    """Get agent by ID."""
    service = AgentService(db, nats)
    try:
        return await service.get_agent(agent_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    agent: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    nats = Depends(get_nats)
):
    """Update an agent."""
    service = AgentService(db, nats)
    try:
        return await service.update_agent(agent_id, agent)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/agents/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats = Depends(get_nats)
):
    """Delete an agent."""
    service = AgentService(db, nats)
    try:
        await service.delete_agent(agent_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/agents/{agent_id}/status", response_model=AgentStatus)
async def get_agent_status(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats = Depends(get_nats)
):
    """Get agent status."""
    service = AgentService(db, nats)
    try:
        return await service.get_agent_status(agent_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/agents/{agent_id}/status", response_model=AgentResponse)
async def update_agent_status(
    agent_id: UUID,
    status: str,
    details: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
    nats = Depends(get_nats)
):
    """Update agent status."""
    service = AgentService(db, nats)
    try:
        return await service.update_agent_status(agent_id, status, details)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/agents/{agent_id}/config", response_model=AgentConfig)
async def get_agent_config(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats = Depends(get_nats)
):
    """Get agent configuration."""
    service = AgentService(db, nats)
    try:
        return await service.get_agent_config(agent_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/agents/{agent_id}/config", response_model=AgentResponse)
async def update_agent_config(
    agent_id: UUID,
    config: dict,
    version: str,
    metadata: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
    nats = Depends(get_nats)
):
    """Update agent configuration."""
    service = AgentService(db, nats)
    try:
        return await service.update_agent_config(agent_id, config, version, metadata)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/agents/discover", response_model=List[AgentDiscovery])
async def discover_agents(
    db: AsyncSession = Depends(get_db),
    nats = Depends(get_nats)
):
    """Discover available agents."""
    service = AgentService(db, nats)
    return await service.discover_agents() 