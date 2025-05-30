"""Agent rules endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from opmas_mgmt_api.api.deps import get_db, get_nats
from opmas_mgmt_api.api.v1.endpoints.route_utils import create_route_builder
from opmas_mgmt_api.schemas.agents import (
    AgentRuleCreate,
    AgentRuleResponse,
    AgentRuleUpdate,
)
from opmas_mgmt_api.agents.agent import AgentService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
route = create_route_builder(router)


@route.get("/{agent_id}/rules", response_model=List[AgentRuleResponse])
async def list_agent_rules(
    agent_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> List[AgentRuleResponse]:
    """List agent rules."""
    service = AgentService(db, nats)
    return await service.get_agent_rules(agent_id, skip=skip, limit=limit)


@route.get("/{agent_id}/rules/{rule_id}", response_model=AgentRuleResponse)
async def get_agent_rule(
    agent_id: UUID,
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> AgentRuleResponse:
    """Get agent rule by ID."""
    service = AgentService(db, nats)
    rule = await service.get_agent_rule(agent_id, rule_id)
    if not rule:
        raise HTTPException(
            status_code=404,
            detail=f"Rule {rule_id} not found for agent {agent_id}",
        )
    return rule


@route.post("/{agent_id}/rules", response_model=AgentRuleResponse)
async def create_agent_rule(
    agent_id: UUID,
    rule: AgentRuleCreate,
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> AgentRuleResponse:
    """Create new agent rule."""
    service = AgentService(db, nats)
    created_rule = await service.create_agent_rule(agent_id, rule)
    if not created_rule:
        raise HTTPException(
            status_code=404,
            detail=f"Agent {agent_id} not found",
        )
    return created_rule


@route.put("/{agent_id}/rules/{rule_id}", response_model=AgentRuleResponse)
async def update_agent_rule(
    agent_id: UUID,
    rule_id: UUID,
    rule: AgentRuleUpdate,
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> AgentRuleResponse:
    """Update agent rule."""
    service = AgentService(db, nats)
    updated_rule = await service.update_agent_rule(agent_id, rule_id, rule)
    if not updated_rule:
        raise HTTPException(
            status_code=404,
            detail=f"Rule {rule_id} not found for agent {agent_id}",
        )
    return updated_rule


@route.delete("/{agent_id}/rules/{rule_id}")
async def delete_agent_rule(
    agent_id: UUID,
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> None:
    """Delete agent rule."""
    service = AgentService(db, nats)
    if not await service.delete_agent_rule(agent_id, rule_id):
        raise HTTPException(
            status_code=404,
            detail=f"Rule {rule_id} not found for agent {agent_id}",
        ) 