#!/usr/bin/env python3

"""Main FastAPI application for the Management API."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from ..core.database import DatabaseManager
from ..data_models import AgentStatus, FindingSeverity
from ..db_models import Agent, AgentRule, Finding
from ..db_utils import get_db_session
from .schemas import (
    AgentCreate,
    AgentResponse,
    AgentRuleCreate,
    AgentRuleResponse,
    AgentRuleUpdate,
    AgentUpdate,
    FindingFilter,
    FindingResponse,
)

# Get logger
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="OPMAS Management API",
    description="API for managing OPMAS agents and findings",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure this based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    logger.info("Initializing database tables...")
    try:
        db_manager = DatabaseManager()
        db_manager.init_db()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        raise


# --- Agent Endpoints ---


@app.post("/agents", response_model=AgentResponse)
async def create_agent(agent: AgentCreate, db: Session = Depends(get_db_session)):
    """Create a new agent."""
    try:
        db_agent = Agent(
            name=agent.name,
            package_name=agent.package_name,
            subscribed_topics=agent.subscribed_topics,
            enabled=agent.enabled,
        )
        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)
        return db_agent
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents", response_model=List[AgentResponse])
async def list_agents(enabled: Optional[bool] = None, db: Session = Depends(get_db_session)):
    """List all agents, optionally filtered by enabled status."""
    query = db.query(Agent)
    if enabled is not None:
        query = query.filter(Agent.enabled == enabled)
    return query.all()


@app.get("/agents/{agent_name}", response_model=AgentResponse)
async def get_agent(agent_name: str, db: Session = Depends(get_db_session)):
    """Get a specific agent by name."""
    agent = db.query(Agent).filter(Agent.name == agent_name).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@app.put("/agents/{agent_name}", response_model=AgentResponse)
async def update_agent(
    agent_name: str, agent_update: AgentUpdate, db: Session = Depends(get_db_session)
):
    """Update an existing agent."""
    db_agent = db.query(Agent).filter(Agent.name == agent_name).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        for field, value in agent_update.dict(exclude_unset=True).items():
            setattr(db_agent, field, value)

        db.commit()
        db.refresh(db_agent)
        return db_agent
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/agents/{agent_name}")
async def delete_agent(agent_name: str, db: Session = Depends(get_db_session)):
    """Delete an agent."""
    db_agent = db.query(Agent).filter(Agent.name == agent_name).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        db.delete(db_agent)
        db.commit()
        return {"message": "Agent deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Agent Rule Endpoints ---


@app.post("/agents/{agent_name}/rules", response_model=AgentRuleResponse)
async def create_agent_rule(
    agent_name: str, rule: AgentRuleCreate, db: Session = Depends(get_db_session)
):
    """Create a new rule for an agent."""
    db_agent = db.query(Agent).filter(Agent.name == agent_name).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        db_rule = AgentRule(
            agent_id=db_agent.id,
            name=rule.name,
            description=rule.description,
            pattern=rule.pattern,
            severity=rule.severity,
            enabled=rule.enabled,
            cooldown_seconds=rule.cooldown_seconds,
            threshold=rule.threshold,
        )
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)
        return db_rule
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating agent rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_name}/rules", response_model=List[AgentRuleResponse])
async def list_agent_rules(
    agent_name: str, enabled: Optional[bool] = None, db: Session = Depends(get_db_session)
):
    """List all rules for an agent."""
    db_agent = db.query(Agent).filter(Agent.name == agent_name).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    query = db.query(AgentRule).filter(AgentRule.agent_id == db_agent.id)
    if enabled is not None:
        query = query.filter(AgentRule.enabled == enabled)
    return query.all()


@app.put("/agents/{agent_name}/rules/{rule_name}", response_model=AgentRuleResponse)
async def update_agent_rule(
    agent_name: str,
    rule_name: str,
    rule_update: AgentRuleUpdate,
    db: Session = Depends(get_db_session),
):
    """Update an existing agent rule."""
    db_agent = db.query(Agent).filter(Agent.name == agent_name).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    db_rule = (
        db.query(AgentRule)
        .filter(AgentRule.agent_id == db_agent.id, AgentRule.name == rule_name)
        .first()
    )
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    try:
        for field, value in rule_update.dict(exclude_unset=True).items():
            setattr(db_rule, field, value)

        db.commit()
        db.refresh(db_rule)
        return db_rule
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating agent rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/agents/{agent_name}/rules/{rule_name}")
async def delete_agent_rule(agent_name: str, rule_name: str, db: Session = Depends(get_db_session)):
    """Delete an agent rule."""
    db_agent = db.query(Agent).filter(Agent.name == agent_name).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    db_rule = (
        db.query(AgentRule)
        .filter(AgentRule.agent_id == db_agent.id, AgentRule.name == rule_name)
        .first()
    )
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    try:
        db.delete(db_rule)
        db.commit()
        return {"message": "Rule deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting agent rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Finding Endpoints ---


@app.get("/findings", response_model=List[FindingResponse])
async def list_findings(filter: FindingFilter = Depends(), db: Session = Depends(get_db_session)):
    """List findings with optional filtering."""
    query = db.query(Finding)

    # Apply filters
    if filter.agent_name:
        query = query.filter(Finding.agent_name == filter.agent_name)
    if filter.finding_type:
        query = query.filter(Finding.finding_type == filter.finding_type)
    if filter.severity:
        query = query.filter(Finding.severity == filter.severity)
    if filter.resource_id:
        query = query.filter(Finding.resource_id == filter.resource_id)
    if filter.start_time:
        query = query.filter(Finding.timestamp >= filter.start_time)
    if filter.end_time:
        query = query.filter(Finding.timestamp <= filter.end_time)

    # Apply sorting
    if filter.sort_by:
        sort_column = getattr(Finding, filter.sort_by, Finding.timestamp)
        if filter.sort_desc:
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(Finding.timestamp.desc())

    # Apply pagination
    if filter.limit:
        query = query.limit(filter.limit)
    if filter.offset:
        query = query.offset(filter.offset)

    return query.all()


@app.get("/findings/{finding_id}", response_model=FindingResponse)
async def get_finding(finding_id: int, db: Session = Depends(get_db_session)):
    """Get a specific finding by ID."""
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@app.delete("/findings/{finding_id}")
async def delete_finding(finding_id: int, db: Session = Depends(get_db_session)):
    """Delete a finding."""
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    try:
        db.delete(finding)
        db.commit()
        return {"message": "Finding deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting finding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Health Check Endpoint ---


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
