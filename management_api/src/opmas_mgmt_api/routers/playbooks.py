import datetime
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from opmas.db.models import Playbook as PlaybookModel
from opmas.db.models import PlaybookStep as PlaybookStepModel

# Adjust import path if necessary
from opmas.db.utils import get_db

from ..auth.dependencies import get_current_active_user
from ..models import playbook as playbook_models
from ..models import playbook_execution as execution_models
from ..schemas import playbook as playbook_schemas

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Playbook Models for API ---
class PlaybookStepResponse(BaseModel):
    step_id: int
    step_order: int
    action_type: str
    command_template: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class PlaybookResponse(BaseModel):
    playbook_id: int
    finding_type: str
    name: str
    description: Optional[str] = None
    steps: List[PlaybookStepResponse] = []  # Include steps

    class Config:
        from_attributes = True


class PlaybooksApiResponse(BaseModel):
    playbooks: List[PlaybookResponse]
    total: int
    limit: int
    offset: int


class PlaybookCreate(BaseModel):
    name: str
    finding_type: str = Field(
        ..., description="The finding type that triggers this playbook (must be unique)"
    )
    description: Optional[str] = None


class PlaybookStepCreate(BaseModel):
    action_type: str
    description: Optional[str] = None
    command_template: Optional[str] = None


# -------------------------------


# --- GET Playbooks (List) ---
@router.get("/playbooks", response_model=List[playbook_schemas.PlaybookInDB])
async def list_playbooks(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    query = db.query(playbook_models.Playbook)

    if is_active is not None:
        query = query.filter(playbook_models.Playbook.is_active == is_active)

    playbooks = (
        query.order_by(playbook_models.Playbook.created_at.desc()).offset(skip).limit(limit).all()
    )
    return playbooks


@router.post("/playbooks", response_model=playbook_schemas.PlaybookInDB)
async def create_playbook(
    playbook: playbook_schemas.PlaybookCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    # Check if playbook with same name exists
    db_playbook = (
        db.query(playbook_models.Playbook)
        .filter(playbook_models.Playbook.name == playbook.name)
        .first()
    )
    if db_playbook:
        raise HTTPException(status_code=400, detail="Playbook with this name already exists")

    # Create new playbook
    db_playbook = playbook_models.Playbook(**playbook.dict())
    db.add(db_playbook)
    db.commit()
    db.refresh(db_playbook)
    return db_playbook


@router.get("/playbooks/{playbook_id}", response_model=playbook_schemas.PlaybookInDB)
async def get_playbook(
    playbook_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)
):
    playbook = (
        db.query(playbook_models.Playbook)
        .filter(playbook_models.Playbook.id == playbook_id)
        .first()
    )
    if playbook is None:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return playbook


@router.put("/playbooks/{playbook_id}", response_model=playbook_schemas.PlaybookInDB)
async def update_playbook(
    playbook_id: int,
    playbook: playbook_schemas.PlaybookUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    db_playbook = (
        db.query(playbook_models.Playbook)
        .filter(playbook_models.Playbook.id == playbook_id)
        .first()
    )
    if db_playbook is None:
        raise HTTPException(status_code=404, detail="Playbook not found")

    # Check name uniqueness if being updated
    if playbook.name and playbook.name != db_playbook.name:
        existing = (
            db.query(playbook_models.Playbook)
            .filter(playbook_models.Playbook.name == playbook.name)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Playbook with this name already exists")

    # Update playbook fields
    for key, value in playbook.dict(exclude_unset=True).items():
        setattr(db_playbook, key, value)

    db.commit()
    db.refresh(db_playbook)
    return db_playbook


@router.delete("/playbooks/{playbook_id}")
async def delete_playbook(
    playbook_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)
):
    playbook = (
        db.query(playbook_models.Playbook)
        .filter(playbook_models.Playbook.id == playbook_id)
        .first()
    )
    if playbook is None:
        raise HTTPException(status_code=404, detail="Playbook not found")

    db.delete(playbook)
    db.commit()
    return {"message": "Playbook deleted successfully"}


@router.get("/playbooks/{playbook_id}/status", response_model=playbook_schemas.PlaybookStatus)
async def get_playbook_status(
    playbook_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)
):
    playbook = (
        db.query(playbook_models.Playbook)
        .filter(playbook_models.Playbook.id == playbook_id)
        .first()
    )
    if playbook is None:
        raise HTTPException(status_code=404, detail="Playbook not found")

    return {
        "is_active": playbook.is_active,
        "updated_at": playbook.updated_at or playbook.created_at,
    }


@router.put("/playbooks/{playbook_id}/status", response_model=playbook_schemas.PlaybookStatus)
async def update_playbook_status(
    playbook_id: int,
    is_active: bool = Query(..., description="New playbook status"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    playbook = (
        db.query(playbook_models.Playbook)
        .filter(playbook_models.Playbook.id == playbook_id)
        .first()
    )
    if playbook is None:
        raise HTTPException(status_code=404, detail="Playbook not found")

    playbook.is_active = is_active
    db.commit()
    db.refresh(playbook)

    return {
        "is_active": playbook.is_active,
        "updated_at": playbook.updated_at or playbook.created_at,
    }


@router.post(
    "/playbooks/{playbook_id}/execute", response_model=playbook_schemas.PlaybookExecutionInDB
)
async def execute_playbook(
    playbook_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)
):
    # Check if playbook exists and is active
    playbook = (
        db.query(playbook_models.Playbook)
        .filter(
            playbook_models.Playbook.id == playbook_id, playbook_models.Playbook.is_active == True
        )
        .first()
    )
    if playbook is None:
        raise HTTPException(status_code=404, detail="Playbook not found or not active")

    # Create new execution
    execution = execution_models.PlaybookExecution(
        playbook_id=playbook_id, status=execution_models.ExecutionStatus.PENDING
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    # TODO: Trigger actual playbook execution
    # This would typically involve:
    # 1. Publishing a message to a message queue
    # 2. Having a worker process pick up the execution
    # 3. Updating the execution status as it progresses

    return execution


@router.get(
    "/playbooks/{playbook_id}/executions",
    response_model=List[playbook_schemas.PlaybookExecutionInDB],
)
async def list_playbook_executions(
    playbook_id: int,
    skip: int = 0,
    limit: int = 100,
    status: Optional[execution_models.ExecutionStatus] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    # Check if playbook exists
    playbook = (
        db.query(playbook_models.Playbook)
        .filter(playbook_models.Playbook.id == playbook_id)
        .first()
    )
    if playbook is None:
        raise HTTPException(status_code=404, detail="Playbook not found")

    query = db.query(execution_models.PlaybookExecution).filter(
        execution_models.PlaybookExecution.playbook_id == playbook_id
    )

    if status:
        query = query.filter(execution_models.PlaybookExecution.status == status)

    executions = (
        query.order_by(execution_models.PlaybookExecution.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return executions


@router.get(
    "/playbooks/executions/{execution_id}", response_model=playbook_schemas.PlaybookExecutionInDB
)
async def get_execution(
    execution_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)
):
    execution = (
        db.query(execution_models.PlaybookExecution)
        .filter(execution_models.PlaybookExecution.id == execution_id)
        .first()
    )
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.put(
    "/playbooks/executions/{execution_id}", response_model=playbook_schemas.PlaybookExecutionInDB
)
async def update_execution(
    execution_id: int,
    execution_update: playbook_schemas.PlaybookExecutionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    execution = (
        db.query(execution_models.PlaybookExecution)
        .filter(execution_models.PlaybookExecution.id == execution_id)
        .first()
    )
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Update execution fields
    for key, value in execution_update.dict(exclude_unset=True).items():
        setattr(execution, key, value)

    db.commit()
    db.refresh(execution)
    return execution


# --- DELETE Playbook Step ---
@router.delete(
    "/{playbook_id}/steps/{step_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Playbook Steps"],  # Keep specific tag for steps
    summary="Delete a specific step from a playbook",
)
async def delete_playbook_step(playbook_id: int, step_id: int, db: Session = Depends(get_db)):
    """Deletes a specific step from a playbook by its ID."""
    logger.info(f"Received request to DELETE step {step_id} from playbook {playbook_id}")
    try:
        step_orm = (
            db.query(PlaybookStepModel)
            .filter(
                PlaybookStepModel.playbook_id == playbook_id, PlaybookStepModel.step_id == step_id
            )
            .first()
        )
        if step_orm is None:
            logger.warning(
                f"Step with ID {step_id} not found in playbook {playbook_id} for deletion."
            )
            playbook_exists = (
                db.query(PlaybookModel.playbook_id)
                .filter(PlaybookModel.playbook_id == playbook_id)
                .first()
            )
            if not playbook_exists:
                raise HTTPException(
                    status_code=404, detail=f"Playbook with ID {playbook_id} not found"
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Step with ID {step_id} not found in playbook {playbook_id}",
                )
        db.delete(step_orm)
        db.commit()
        logger.info(f"Successfully deleted step ID {step_id} from playbook ID {playbook_id}")
        return
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error deleting step {step_id} from playbook {playbook_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to delete step {step_id} from playbook {playbook_id}"
        )


# --------------------------


# --- ADD Step to Playbook ---
@router.post(
    "/{playbook_id}/steps",
    response_model=PlaybookStepResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Playbook Steps"],
    summary="Add a new step to a specific playbook",
)
async def add_playbook_step(
    playbook_id: int, step_data: PlaybookStepCreate, db: Session = Depends(get_db)
) -> PlaybookStepModel:
    """Adds a new step to the end of the specified playbook."""
    logger.info(
        f"Received request to ADD step to playbook {playbook_id} with data: {step_data.dict()}"
    )
    playbook = db.query(PlaybookModel).filter(PlaybookModel.playbook_id == playbook_id).first()
    if not playbook:
        logger.warning(f"Playbook {playbook_id} not found when trying to add step.")
        raise HTTPException(status_code=404, detail=f"Playbook with ID {playbook_id} not found")
    try:
        max_order = (
            db.query(func.max(PlaybookStepModel.step_order))
            .filter(PlaybookStepModel.playbook_id == playbook_id)
            .scalar()
        )
        next_order = (max_order or 0) + 1
        logger.debug(f"Determined next step order for playbook {playbook_id}: {next_order}")
        new_step = PlaybookStepModel(
            playbook_id=playbook_id,
            step_order=next_order,
            action_type=step_data.action_type,
            description=step_data.description,
            command_template=step_data.command_template,
        )
        db.add(new_step)
        db.commit()
        db.refresh(new_step)
        logger.info(
            f"Successfully added step {new_step.step_id} (order {new_step.step_order}) to playbook {playbook_id}"
        )
        return new_step
    except SQLAlchemyError as db_e:
        db.rollback()
        logger.error(f"Database error adding step to playbook {playbook_id}: {db_e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error adding step: {db_e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error adding step to playbook {playbook_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error adding step")


# --------------------------


# --- UPDATE Playbook Step ---
@router.put(
    "/{playbook_id}/steps/{step_id}",
    response_model=PlaybookStepResponse,
    tags=["Playbook Steps"],
    summary="Update details for a specific playbook step",
)
async def update_playbook_step(
    playbook_id: int,
    step_id: int,
    step_update_data: PlaybookStepCreate,
    db: Session = Depends(get_db),
) -> PlaybookStepModel:
    """Updates an existing step within a playbook."""
    logger.info(
        f"Received request to UPDATE step {step_id} in playbook {playbook_id} with data: {step_update_data.dict()}"
    )
    step_orm = (
        db.query(PlaybookStepModel)
        .filter(PlaybookStepModel.playbook_id == playbook_id, PlaybookStepModel.step_id == step_id)
        .first()
    )
    if step_orm is None:
        logger.warning(f"Step with ID {step_id} not found in playbook {playbook_id} for update.")
        playbook_exists = (
            db.query(PlaybookModel.playbook_id)
            .filter(PlaybookModel.playbook_id == playbook_id)
            .first()
        )
        if not playbook_exists:
            raise HTTPException(status_code=404, detail=f"Playbook with ID {playbook_id} not found")
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Step with ID {step_id} not found in playbook {playbook_id}",
            )
    step_orm.action_type = step_update_data.action_type
    step_orm.description = step_update_data.description
    step_orm.command_template = step_update_data.command_template
    try:
        db.add(step_orm)
        db.commit()
        db.refresh(step_orm)
        logger.info(f"Successfully updated step ID {step_id} in playbook ID {playbook_id}")
        return step_orm
    except SQLAlchemyError as db_e:
        db.rollback()
        logger.error(
            f"Database error updating step {step_id} in playbook {playbook_id}: {db_e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Database error updating step: {db_e}")
    except Exception as e:
        db.rollback()
        logger.error(
            f"Unexpected error updating step {step_id} in playbook {playbook_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Unexpected error updating step")


# --------------------------
