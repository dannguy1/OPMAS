"""Agent management API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from opmas_mgmt_api.api import deps
from opmas_mgmt_api.schemas.agent import (
    Agent,
    AgentCreate,
    AgentDiscovery,
    AgentRule,
    AgentRuleCreate,
    AgentRuleUpdate,
    AgentUpdate,
)
from opmas_mgmt_api.services.agent import AgentService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=List[Agent])
async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    agent_type: Optional[str] = None,
    db: AsyncSession = Depends(deps.get_db),
    nats: NATSManager = Depends(deps.get_nats),
) -> List[Agent]:
    """List all agents."""
    service = AgentService(db, nats)
    return await service.get_agents(skip=skip, limit=limit, agent_type=agent_type)


@router.post("/", response_model=Agent)
async def create_agent(
    agent: AgentCreate,
    db: AsyncSession = Depends(deps.get_db),
    nats: NATSManager = Depends(deps.get_nats),
) -> Agent:
    """Create new agent."""
    service = AgentService(db, nats)
    return await service.create_agent(agent)


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(deps.get_db),
    nats: NATSManager = Depends(deps.get_nats),
) -> Agent:
    """Get agent by ID."""
    service = AgentService(db, nats)
    agent = await service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: str,
    agent: AgentUpdate,
    db: AsyncSession = Depends(deps.get_db),
    nats: NATSManager = Depends(deps.get_nats),
) -> Agent:
    """Update agent."""
    service = AgentService(db, nats)
    updated_agent = await service.update_agent(agent_id, agent)
    if not updated_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return updated_agent


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(deps.get_db),
    nats: NATSManager = Depends(deps.get_nats),
) -> dict:
    """Delete agent."""
    service = AgentService(db, nats)
    if not await service.delete_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": "success"}


@router.get("/discover", response_model=List[AgentDiscovery])
async def discover_agents(
    db: AsyncSession = Depends(deps.get_db), nats: NATSManager = Depends(deps.get_nats)
) -> List[AgentDiscovery]:
    """Discover available agents."""
    service = AgentService(db, nats)
    return await service.discover_agents()


@router.get("/{agent_id}/rules", response_model=List[AgentRule])
async def list_agent_rules(
    agent_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(deps.get_db),
    nats: NATSManager = Depends(deps.get_nats),
) -> List[AgentRule]:
    """List agent rules."""
    service = AgentService(db, nats)
    return await service.get_agent_rules(agent_id, skip=skip, limit=limit)


@router.post("/{agent_id}/rules", response_model=AgentRule)
async def create_agent_rule(
    agent_id: str,
    rule: AgentRuleCreate,
    db: AsyncSession = Depends(deps.get_db),
    nats: NATSManager = Depends(deps.get_nats),
) -> AgentRule:
    """Create agent rule."""
    service = AgentService(db, nats)
    created_rule = await service.create_agent_rule(agent_id, rule)
    if not created_rule:
        raise HTTPException(status_code=404, detail="Agent not found")
    return created_rule


@router.get("/{agent_id}/rules/{rule_id}", response_model=AgentRule)
async def get_agent_rule(
    agent_id: str,
    rule_id: str,
    db: AsyncSession = Depends(deps.get_db),
    nats: NATSManager = Depends(deps.get_nats),
) -> AgentRule:
    """Get agent rule."""
    service = AgentService(db, nats)
    rule = await service.get_agent_rule(agent_id, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.put("/{agent_id}/rules/{rule_id}", response_model=AgentRule)
async def update_agent_rule(
    agent_id: str,
    rule_id: str,
    rule: AgentRuleUpdate,
    db: AsyncSession = Depends(deps.get_db),
    nats: NATSManager = Depends(deps.get_nats),
) -> AgentRule:
    """Update agent rule."""
    service = AgentService(db, nats)
    updated_rule = await service.update_agent_rule(agent_id, rule_id, rule)
    if not updated_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return updated_rule


@router.delete("/{agent_id}/rules/{rule_id}")
async def delete_agent_rule(
    agent_id: str,
    rule_id: str,
    db: AsyncSession = Depends(deps.get_db),
    nats: NATSManager = Depends(deps.get_nats),
) -> dict:
    """Delete agent rule."""
    service = AgentService(db, nats)
    if not await service.delete_agent_rule(agent_id, rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"status": "success"}
