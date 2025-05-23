from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import rule as rule_models
from ..models import agent as agent_models
from ..schemas import rule as rule_schemas
from ..database import get_db
from ..auth.dependencies import get_current_active_user
from datetime import datetime

router = APIRouter()

@router.get("/rules", response_model=List[rule_schemas.RuleInDB])
async def list_rules(
    skip: int = 0,
    limit: int = 100,
    agent_id: Optional[int] = None,
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = db.query(rule_models.Rule)
    
    if agent_id:
        query = query.filter(rule_models.Rule.agent_id == agent_id)
    if enabled is not None:
        query = query.filter(rule_models.Rule.enabled == enabled)
    
    rules = query.order_by(rule_models.Rule.priority.desc()).offset(skip).limit(limit).all()
    return rules

@router.post("/rules", response_model=rule_schemas.RuleInDB)
async def create_rule(
    rule: rule_schemas.RuleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Check if rule with same name exists
    db_rule = db.query(rule_models.Rule).filter(
        rule_models.Rule.name == rule.name
    ).first()
    if db_rule:
        raise HTTPException(
            status_code=400,
            detail="Rule with this name already exists"
        )
    
    # Check if agent exists
    agent = db.query(agent_models.Agent).filter(
        agent_models.Agent.id == rule.agent_id
    ).first()
    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found"
        )
    
    # Create new rule
    db_rule = rule_models.Rule(**rule.dict())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

@router.get("/rules/{rule_id}", response_model=rule_schemas.RuleInDB)
async def get_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    rule = db.query(rule_models.Rule).filter(
        rule_models.Rule.id == rule_id
    ).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule

@router.put("/rules/{rule_id}", response_model=rule_schemas.RuleInDB)
async def update_rule(
    rule_id: int,
    rule: rule_schemas.RuleUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    db_rule = db.query(rule_models.Rule).filter(
        rule_models.Rule.id == rule_id
    ).first()
    if db_rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # Check name uniqueness if being updated
    if rule.name and rule.name != db_rule.name:
        existing = db.query(rule_models.Rule).filter(
            rule_models.Rule.name == rule.name
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Rule with this name already exists"
            )
    
    # Check agent existence if being updated
    if rule.agent_id and rule.agent_id != db_rule.agent_id:
        agent = db.query(agent_models.Agent).filter(
            agent_models.Agent.id == rule.agent_id
        ).first()
        if not agent:
            raise HTTPException(
                status_code=404,
                detail="Agent not found"
            )
    
    # Update rule fields
    for key, value in rule.dict(exclude_unset=True).items():
        setattr(db_rule, key, value)
    
    db.commit()
    db.refresh(db_rule)
    return db_rule

@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    rule = db.query(rule_models.Rule).filter(
        rule_models.Rule.id == rule_id
    ).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    db.delete(rule)
    db.commit()
    return {"message": "Rule deleted successfully"}

@router.get("/rules/{rule_id}/status", response_model=rule_schemas.RuleStatus)
async def get_rule_status(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    rule = db.query(rule_models.Rule).filter(
        rule_models.Rule.id == rule_id
    ).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return {
        "enabled": rule.enabled,
        "updated_at": rule.updated_at or rule.created_at
    }

@router.put("/rules/{rule_id}/status", response_model=rule_schemas.RuleStatus)
async def update_rule_status(
    rule_id: int,
    enabled: bool = Query(..., description="New rule status"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    rule = db.query(rule_models.Rule).filter(
        rule_models.Rule.id == rule_id
    ).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rule.enabled = enabled
    db.commit()
    db.refresh(rule)
    
    return {
        "enabled": rule.enabled,
        "updated_at": rule.updated_at or rule.created_at
    } 