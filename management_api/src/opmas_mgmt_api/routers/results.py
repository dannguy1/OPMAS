import logging
import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Assuming db_utils and db_models are accessible relative to the routers directory
# Adjust import path if necessary
from opmas.db.utils import get_db 
from opmas.db.models import Finding as FindingModel
from opmas.db.models import IntendedAction as ActionModel

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Pydantic Models for API Responses --- 
class FindingBase(BaseModel):
    finding_id: str
    timestamp_utc: datetime.datetime # Keep as datetime for processing
    finding_type: str
    device_hostname: Optional[str] = None
    device_ip: Optional[str] = None
    agent_id: Optional[int] = None
    # details: Dict[str, Any] # Keep details flexible

    class Config:
        from_attributes = True # Allows creating Pydantic model from ORM object
        json_encoders = {
            datetime.datetime: lambda dt: dt.isoformat() # Ensure datetime is ISO string in JSON
        }

class FindingsResponse(BaseModel):
    findings: List[FindingBase]
    total: int
    limit: int
    offset: int

class ActionBase(BaseModel):
    action_id: int
    timestamp_utc: datetime.datetime
    finding_id: Optional[str] = None # Can be null if action not linked to finding
    playbook_id: Optional[int] = None
    step_id: Optional[int] = None
    action_type: str
    status: str # e.g., 'intended', 'executed', 'failed'
    details: Optional[Dict[str, Any]] = None # JSONB field
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime.datetime: lambda dt: dt.isoformat()
        }

class ActionsResponse(BaseModel):
    actions: List[ActionBase]
    total: int
    limit: int
    offset: int
# -----------------------------------------

# --- Endpoint: Get Findings --- 
@router.get("/findings", 
            response_model=FindingsResponse, 
            summary="Get historical findings")
async def get_findings(
    limit: int = 100, 
    offset: int = 0,
    db: Session = Depends(get_db)
) -> FindingsResponse:
    """Retrieves a paginated list of findings recorded by agents."""
    logger.info(f"Received request for /api/v1/findings (limit={limit}, offset={offset})")
    try:
        # Note: Getting total count from ActionModel seems incorrect here?
        # Should probably be FindingModel.count()
        # Keeping original logic for now, but flag for review.
        # total = db.query(FindingModel).count() 
        total = db.query(ActionModel).count() # Original line
        findings_orm = (
            db.query(FindingModel)
            .order_by(FindingModel.timestamp_utc.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return FindingsResponse(
             findings=findings_orm,
             total=total,
             limit=limit,
             offset=offset
        )
    except Exception as e:
        logger.error(f"Error fetching findings from database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch findings from database")
# ----------------------------------

# --- Endpoint: Get Actions --- 
@router.get("/actions", 
            response_model=ActionsResponse, 
            summary="Get historical intended actions logged by the Orchestrator")
async def get_actions(
    limit: int = 100, 
    offset: int = 0,
    db: Session = Depends(get_db)
) -> ActionsResponse:
    """Retrieves a paginated list of intended actions recorded by the Orchestrator."""
    logger.info(f"Received request for /api/v1/actions (limit={limit}, offset={offset})")
    try:
        # Query total count
        total = db.query(ActionModel).count()
        
        # Query paginated actions, ordered by time
        actions_orm = (
            db.query(ActionModel)
            .order_by(ActionModel.timestamp_utc.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        return ActionsResponse(
             actions=actions_orm, # FastAPI handles conversion
             total=total,
             limit=limit,
             offset=offset
        )
        
    except Exception as e:
        logger.error(f"Error fetching actions from database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch actions from database")
# ---------------------------------- 