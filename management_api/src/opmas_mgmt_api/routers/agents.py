import logging
import datetime
import os
from pathlib import Path
import sys
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field
from dotenv import dotenv_values

# Adjust import path if necessary
from opmas.db.utils import get_db
from opmas.db.models import Agent as AgentModel
from opmas.db.models import AgentRule as AgentRuleModel
from ..models import agent as agent_models
from ..models import device as device_models
from ..schemas import agent as agent_schemas
from ..auth.dependencies import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Define path relative to this file for agent discovery ---
# This assumes the structure: <project_root>/management_api/src/opmas_mgmt_api/routers/agents.py
# And core is: <project_root>/core/src/
# Need to go up 4 levels from routers/ to project_root
_CURRENT_FILE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_FILE_DIR.parents[3]
_CORE_SRC_DIR = _PROJECT_ROOT / 'core' / 'src'
# -------------------------------------------------------------

# --- Agent Rule Models --- 
class AgentRuleResponse(BaseModel):
    rule_id: int
    agent_id: int
    rule_name: str
    rule_config: Dict[str, Any]

    class Config:
        from_attributes = True

class AgentRulesApiResponse(BaseModel):
    rules: List[AgentRuleResponse]
    total: int
    limit: int
    offset: int
# -------------------------

# --- Agent Models --- 
class AgentResponse(BaseModel):
    agent_id: int
    name: str
    package_path: str
    description: Optional[str] = None
    is_enabled: bool

    class Config:
        from_attributes = True

class AgentsApiResponse(BaseModel):
    agents: List[AgentResponse]
    total: int
    limit: int
    offset: int

class DiscoveredAgent(BaseModel):
    name: str
    package_path: str
    description: Optional[str] = None
    
class AgentCreate(BaseModel):
    name: str 
    package_path: str 
    description: Optional[str] = None
    is_enabled: bool = True
    
class AgentUpdate(BaseModel):
    description: Optional[str] = None
    is_enabled: bool
# ---------------------

# --- Agent Rule Models ---
class AgentRuleCreate(BaseModel):
    rule_name: str
    rule_config: Dict[str, Any]

class AgentRuleUpdate(BaseModel):
    rule_name: str
    rule_config: Dict[str, Any]

# --- Agent Endpoints ---
@router.post("/", 
             response_model=AgentResponse, 
             status_code=status.HTTP_201_CREATED, 
             summary="Configure a discovered agent package")
async def create_agent(
    agent_data: AgentCreate, 
    db: Session = Depends(get_db)
) -> AgentResponse:
    """Adds a discovered agent package configuration to the database."""
    logger.info(f"Received request to CREATE agent config: {agent_data.dict()}")
    existing = db.query(AgentModel).filter(AgentModel.name == agent_data.name).first()
    if existing:
        logger.warning(f"Attempted to create agent with duplicate name: {agent_data.name}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"An agent with name '{agent_data.name}' already exists (ID: {existing.agent_id})."
        )
    # Use the calculated path
    agent_package_full_path = _CORE_SRC_DIR / 'opmas' / 'agents' / agent_data.package_path 
    if not agent_package_full_path.is_dir():
         logger.error(f"Agent package path specified does not exist: {agent_package_full_path}")
         raise HTTPException(status_code=400, detail=f"Agent package path '{agent_data.package_path}' not found.")
    try:
        new_agent_orm = AgentModel(
            name=agent_data.name,
            module_path=agent_data.package_path, # Store package dir name here
            description=agent_data.description,
            is_enabled=agent_data.is_enabled
        )
        db.add(new_agent_orm)
        db.commit()
        db.refresh(new_agent_orm) 
        logger.info(f"Successfully created agent config '{new_agent_orm.name}' with ID: {new_agent_orm.agent_id}")
        response_data = AgentResponse(
            agent_id=new_agent_orm.agent_id,
            name=new_agent_orm.name,
            package_path=new_agent_orm.module_path, # Map DB field to response field
            description=new_agent_orm.description,
            is_enabled=new_agent_orm.is_enabled
        )
        return response_data 
    except SQLAlchemyError as db_e:
        db.rollback()
        logger.error(f"Database error creating agent config: {db_e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error creating agent config: {db_e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating agent config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error creating agent config")

@router.get("/", 
            response_model=AgentsApiResponse, 
            summary="Get a list of configured agents")
async def list_agents(
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[int] = None,
    status: Optional[str] = None,
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> AgentsApiResponse:
    """Retrieves a paginated list of agents defined in the database."""
    logger.info(f"Received request for GET /agents (skip={skip}, limit={limit}, device_id={device_id}, status={status}, enabled={enabled})")
    query = db.query(agent_models.Agent)
    
    if device_id:
        query = query.filter(agent_models.Agent.device_id == device_id)
    if status:
        query = query.filter(agent_models.Agent.status == status)
    if enabled is not None:
        query = query.filter(agent_models.Agent.enabled == enabled)
    
    total = query.count()
    agents_orm = query.offset(skip).limit(limit).all()
    mapped_agents = []
    for agent in agents_orm:
        mapped_agents.append(AgentResponse(
            agent_id=agent.id,
            name=agent.name,
            package_path=agent.module_path, # Explicit mapping needed
            description=agent.description,
            is_enabled=agent.enabled
        ))
    return AgentsApiResponse(
        agents=mapped_agents, 
        total=total,
        limit=limit,
        offset=skip
    )

@router.get("/discover",
            response_model=List[DiscoveredAgent],
            summary="Discover potential agent packages not yet configured")
async def discover_agents(db: Session = Depends(get_db)) -> List[DiscoveredAgent]:
    """Scans the filesystem for agent packages and returns those not already in the DB by name."""
    logger.info("Received request to discover agent packages")
    discovered = []
    # Use the calculated path
    agents_base_dir = _CORE_SRC_DIR / 'opmas' / 'agents'
    logger.debug(f"Scanning for agent packages in: {agents_base_dir}")
    if not agents_base_dir.is_dir():
        logger.error(f"Agents base directory not found: {agents_base_dir}")
        return []
    try:
        existing_agents_query = db.query(AgentModel.name).all()
        existing_agent_names = {name for (name,) in existing_agents_query}
        logger.debug(f"Existing agent names in DB: {existing_agent_names}")
        for item in agents_base_dir.iterdir():
            if item.is_dir() and item.name != "__pycache__" and not item.name.endswith("_template"):
                package_dir = item
                package_name = item.name
                env_file = package_dir / ".env"
                agent_py_file = package_dir / "agent.py"
                if env_file.is_file() and agent_py_file.is_file():
                    logger.debug(f"Found potential agent package: {package_name}")
                    try:
                        env_vars = dotenv_values(env_file)
                        agent_name = env_vars.get("AGENT_NAME")
                        agent_desc = env_vars.get("AGENT_DESCRIPTION")
                        if not agent_name:
                            logger.warning(f"Skipping package '{package_name}': AGENT_NAME missing in .env file.")
                            continue
                        if agent_name in existing_agent_names:
                            logger.debug(f"Skipping already configured agent (by name): '{agent_name}' from package '{package_name}'")
                            continue
                        logger.info(f"Discovered potential new agent: name='{agent_name}', description='{agent_desc}', package='{package_name}'")
                        discovered.append(DiscoveredAgent(
                            name=agent_name,
                            package_path=package_name,
                            description=agent_desc
                        ))
                    except Exception as env_err:
                        logger.error(f"Error processing .env file for package '{package_name}': {env_err}", exc_info=True)
                        continue
    except Exception as e:
        logger.error(f"Error during agent package discovery: {e}", exc_info=True)
        pass 
    return discovered

@router.put("/{agent_id}",
            response_model=AgentResponse, 
            summary="Update an agent's configuration (description, enabled status)")
async def update_agent(
    agent_id: int,
    agent_update_data: AgentUpdate,
    db: Session = Depends(get_db)
) -> AgentResponse:
    logger.info(f"Received request to UPDATE agent ID {agent_id} with data: {agent_update_data.dict()}")
    agent_orm = db.query(AgentModel).filter(AgentModel.agent_id == agent_id).first()
    if agent_orm is None:
        logger.warning(f"Agent with ID {agent_id} not found for update.")
        raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
    try:
        agent_orm.description = agent_update_data.description
        agent_orm.is_enabled = agent_update_data.is_enabled
        db.commit()
        db.refresh(agent_orm)
        logger.info(f"Successfully updated agent '{agent_orm.name}' (ID: {agent_id})")
        response_data = AgentResponse(
            agent_id=agent_orm.agent_id,
            name=agent_orm.name,
            package_path=agent_orm.module_path,
            description=agent_orm.description,
            is_enabled=agent_orm.is_enabled
        )
        return response_data
    except SQLAlchemyError as db_e:
        db.rollback()
        logger.error(f"Database error updating agent {agent_id}: {db_e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error updating agent: {db_e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error updating agent")

@router.delete("/{agent_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Delete an agent and all its associated rules")
async def delete_agent(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Deletes an agent and all its associated rules from the database."""
    logger.info(f"Received request to DELETE agent ID {agent_id}")
    agent_orm = db.query(AgentModel).filter(AgentModel.agent_id == agent_id).first()
    if agent_orm is None:
        logger.warning(f"Agent with ID {agent_id} not found for deletion.")
        raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
    try:
        # The cascade="all, delete-orphan" on the relationship will handle deleting associated rules
        db.delete(agent_orm)
        db.commit()
        logger.info(f"Successfully deleted agent '{agent_orm.name}' (ID: {agent_id}) and its rules")
        return None
    except SQLAlchemyError as db_e:
        db.rollback()
        logger.error(f"Database error deleting agent {agent_id}: {db_e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error deleting agent: {db_e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error deleting agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error deleting agent")

# --- Agent Rule Endpoints ---
@router.get("/{agent_id}/rules", 
            response_model=AgentRulesApiResponse, 
            summary="Get the rules configured for a specific agent")
async def list_agent_rules(
    agent_id: int,
    limit: int = 50, 
    offset: int = 0,
    db: Session = Depends(get_db)
) -> AgentRulesApiResponse:
    """Retrieves a paginated list of rules for a specific agent ID."""
    logger.info(f"Received request for rules for agent {agent_id} (limit={limit}, offset={offset})")
    agent = db.query(AgentModel.agent_id).filter(AgentModel.agent_id == agent_id).first()
    if not agent:
        logger.warning(f"Agent {agent_id} not found when trying to list rules.")
        raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
    try:
        total = db.query(AgentRuleModel).filter(AgentRuleModel.agent_id == agent_id).count()
        rules_orm = (
            db.query(AgentRuleModel)
            .filter(AgentRuleModel.agent_id == agent_id)
            .order_by(AgentRuleModel.rule_name)
            .offset(offset)
            .limit(limit)
            .all()
        )
        return AgentRulesApiResponse(
             rules=rules_orm,
             total=total,
             limit=limit,
             offset=offset
        )
    except Exception as e:
        logger.error(f"Error fetching rules for agent {agent_id} from database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch rules for agent {agent_id} from database")

@router.post("/{agent_id}/rules",
            response_model=AgentRuleResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Create a new rule for a specific agent")
async def create_agent_rule(
    agent_id: int,
    rule_data: AgentRuleCreate,
    db: Session = Depends(get_db)
) -> AgentRuleResponse:
    """Creates a new rule for the specified agent."""
    logger.info(f"Received request to CREATE rule for agent {agent_id} with data: {rule_data.dict()}")
    agent = db.query(AgentModel).filter(AgentModel.agent_id == agent_id).first()
    if not agent:
        logger.warning(f"Agent {agent_id} not found when trying to create rule.")
        raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
    
    # Check for duplicate rule name for this agent
    existing_rule = db.query(AgentRuleModel).filter(
        AgentRuleModel.agent_id == agent_id,
        AgentRuleModel.rule_name == rule_data.rule_name
    ).first()
    if existing_rule:
        logger.warning(f"Rule with name '{rule_data.rule_name}' already exists for agent {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A rule named '{rule_data.rule_name}' already exists for this agent"
        )
    
    try:
        new_rule = AgentRuleModel(
            agent_id=agent_id,
            rule_name=rule_data.rule_name,
            rule_config=rule_data.rule_config
        )
        db.add(new_rule)
        db.commit()
        db.refresh(new_rule)
        logger.info(f"Successfully created rule '{new_rule.rule_name}' for agent {agent_id}")
        return new_rule
    except SQLAlchemyError as db_e:
        db.rollback()
        logger.error(f"Database error creating rule for agent {agent_id}: {db_e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error creating rule: {db_e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating rule for agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error creating rule")

@router.put("/{agent_id}/rules/{rule_id}",
            response_model=AgentRuleResponse,
            summary="Update a specific rule for an agent")
async def update_agent_rule(
    agent_id: int,
    rule_id: int,
    rule_update_data: AgentRuleUpdate,
    db: Session = Depends(get_db)
) -> AgentRuleResponse:
    """Updates an existing rule for the specified agent."""
    logger.info(f"Received request to UPDATE rule {rule_id} for agent {agent_id}")
    rule_orm = db.query(AgentRuleModel).filter(
        AgentRuleModel.agent_id == agent_id,
        AgentRuleModel.rule_id == rule_id
    ).first()
    
    if rule_orm is None:
        logger.warning(f"Rule {rule_id} not found for agent {agent_id}")
        # Check if agent exists to give more specific error
        agent_exists = db.query(AgentModel.agent_id).filter(AgentModel.agent_id == agent_id).first()
        if not agent_exists:
            raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
        raise HTTPException(status_code=404, detail=f"Rule with ID {rule_id} not found for agent {agent_id}")
    
    # Check for name conflict if name is being changed
    if rule_update_data.rule_name != rule_orm.rule_name:
        name_conflict = db.query(AgentRuleModel).filter(
            AgentRuleModel.agent_id == agent_id,
            AgentRuleModel.rule_name == rule_update_data.rule_name,
            AgentRuleModel.rule_id != rule_id
        ).first()
        if name_conflict:
            logger.warning(f"Rule name '{rule_update_data.rule_name}' already exists for agent {agent_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A rule named '{rule_update_data.rule_name}' already exists for this agent"
            )
    
    try:
        rule_orm.rule_name = rule_update_data.rule_name
        rule_orm.rule_config = rule_update_data.rule_config
        db.commit()
        db.refresh(rule_orm)
        logger.info(f"Successfully updated rule {rule_id} for agent {agent_id}")
        return rule_orm
    except SQLAlchemyError as db_e:
        db.rollback()
        logger.error(f"Database error updating rule {rule_id} for agent {agent_id}: {db_e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error updating rule: {db_e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating rule {rule_id} for agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error updating rule")

@router.delete("/{agent_id}/rules/{rule_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Delete a specific rule from an agent")
async def delete_agent_rule(
    agent_id: int,
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Deletes a specific rule from an agent."""
    logger.info(f"Received request to DELETE rule {rule_id} from agent {agent_id}")
    rule_orm = db.query(AgentRuleModel).filter(
        AgentRuleModel.agent_id == agent_id,
        AgentRuleModel.rule_id == rule_id
    ).first()
    
    if rule_orm is None:
        logger.warning(f"Rule {rule_id} not found for agent {agent_id}")
        # Check if agent exists to give more specific error
        agent_exists = db.query(AgentModel.agent_id).filter(AgentModel.agent_id == agent_id).first()
        if not agent_exists:
            raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
        raise HTTPException(status_code=404, detail=f"Rule with ID {rule_id} not found for agent {agent_id}")
    
    try:
        db.delete(rule_orm)
        db.commit()
        logger.info(f"Successfully deleted rule {rule_id} from agent {agent_id}")
        return None
    except SQLAlchemyError as db_e:
        db.rollback()
        logger.error(f"Database error deleting rule {rule_id} from agent {agent_id}: {db_e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error deleting rule: {db_e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error deleting rule {rule_id} from agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error deleting rule")

@router.get("/agents/{agent_id}", response_model=agent_schemas.AgentInDB)
async def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    agent = db.query(agent_models.Agent).filter(
        agent_models.Agent.id == agent_id
    ).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/agents/{agent_id}", response_model=agent_schemas.AgentInDB)
async def update_agent(
    agent_id: int,
    agent: agent_schemas.AgentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    db_agent = db.query(agent_models.Agent).filter(
        agent_models.Agent.id == agent_id
    ).first()
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check name uniqueness if being updated
    if agent.name and agent.name != db_agent.name:
        existing = db.query(agent_models.Agent).filter(
            agent_models.Agent.name == agent.name
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Agent with this name already exists"
            )
    
    # Check device existence if being updated
    if agent.device_id and agent.device_id != db_agent.device_id:
        device = db.query(device_models.Device).filter(
            device_models.Device.id == agent.device_id
        ).first()
        if not device:
            raise HTTPException(
                status_code=404,
                detail="Device not found"
            )
    
    # Update agent fields
    for key, value in agent.dict(exclude_unset=True).items():
        setattr(db_agent, key, value)
    
    db.commit()
    db.refresh(db_agent)
    return db_agent

@router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    agent = db.query(agent_models.Agent).filter(
        agent_models.Agent.id == agent_id
    ).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db.delete(agent)
    db.commit()
    return {"message": "Agent deleted successfully"}

@router.get("/agents/{agent_id}/status", response_model=agent_schemas.AgentStatus)
async def get_agent_status(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    agent = db.query(agent_models.Agent).filter(
        agent_models.Agent.id == agent_id
    ).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "status": agent.status,
        "last_heartbeat": agent.last_heartbeat,
        "enabled": agent.enabled
    }

@router.put("/agents/{agent_id}/status", response_model=agent_schemas.AgentStatus)
async def update_agent_status(
    agent_id: int,
    status: str = Query(..., description="New agent status"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    agent = db.query(agent_models.Agent).filter(
        agent_models.Agent.id == agent_id
    ).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.status = status
    agent.last_heartbeat = datetime.utcnow()
    db.commit()
    db.refresh(agent)
    
    return {
        "status": agent.status,
        "last_heartbeat": agent.last_heartbeat,
        "enabled": agent.enabled
    }

@router.get("/agents/{agent_id}/configuration", response_model=agent_schemas.AgentConfiguration)
async def get_agent_configuration(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    agent = db.query(agent_models.Agent).filter(
        agent_models.Agent.id == agent_id
    ).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "configuration": agent.configuration,
        "updated_at": agent.updated_at or agent.created_at
    }

@router.put("/agents/{agent_id}/configuration", response_model=agent_schemas.AgentConfiguration)
async def update_agent_configuration(
    agent_id: int,
    configuration: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    agent = db.query(agent_models.Agent).filter(
        agent_models.Agent.id == agent_id
    ).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.configuration = configuration
    db.commit()
    db.refresh(agent)
    
    return {
        "configuration": agent.configuration,
        "updated_at": agent.updated_at or agent.created_at
    }

@router.get("/agents/{agent_id}/topics", response_model=agent_schemas.AgentTopics)
async def get_agent_topics(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    agent = db.query(agent_models.Agent).filter(
        agent_models.Agent.id == agent_id
    ).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "subscribed_topics": agent.subscribed_topics,
        "updated_at": agent.updated_at or agent.created_at
    }

@router.put("/agents/{agent_id}/topics", response_model=agent_schemas.AgentTopics)
async def update_agent_topics(
    agent_id: int,
    topics: List[str],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    agent = db.query(agent_models.Agent).filter(
        agent_models.Agent.id == agent_id
    ).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.subscribed_topics = topics
    db.commit()
    db.refresh(agent)
    
    return {
        "subscribed_topics": agent.subscribed_topics,
        "updated_at": agent.updated_at or agent.created_at
    }
# -------------------------- 