import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Query, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from opmas_mgmt_api.api.deps import get_db, get_nats
from opmas_mgmt_api.services.control import ControlService
from opmas_mgmt_api.schemas.control import (
    ControlActionResponse,
    ControlActionStatus
)
from opmas_mgmt_api.core.nats import NATSManager

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Define path relative to this file for control script ---
# Assumes structure: <project_root>/management_api/src/opmas_mgmt_api/routers/control.py
_CURRENT_FILE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_FILE_DIR.parents[3]
START_SCRIPT_PATH = _PROJECT_ROOT / "start_opmas.sh"
# -----------------------------------------------------------

async def _execute_control_script(
    action: str,
    component: Optional[str],
    control_service: ControlService,
    action_id: str
) -> None:
    """Execute control script and update action status."""
    try:
        # Update status to in progress
        await control_service.update_control_action(
            action_id,
            ControlActionStatus.IN_PROGRESS
        )

        # Prepare command
        cmd = [str(START_SCRIPT_PATH), action]
        if component:
            cmd.append(component)
        logger.info(f"Executing: {' '.join(cmd)}")

        # Execute command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=_PROJECT_ROOT
        )

        # Update status based on result
        if result.returncode == 0:
            await control_service.update_control_action(
                action_id,
                ControlActionStatus.COMPLETED,
                {
                    "stdout": result.stdout,
                    "return_code": result.returncode
                }
            )
            logger.info(f"{action.title()} command executed successfully")
        else:
            await control_service.update_control_action(
                action_id,
                ControlActionStatus.FAILED,
                {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode
                }
            )
            logger.error(f"{action.title()} command failed: {result.stderr}")

    except Exception as e:
        logger.error(f"Exception running {action} script: {e}", exc_info=True)
        await control_service.update_control_action(
            action_id,
            ControlActionStatus.FAILED,
            {"error": str(e)}
        )

# --- System Control Endpoints --- 
@router.post("/start", 
             response_model=ControlActionResponse,
             status_code=status.HTTP_202_ACCEPTED, 
             summary="Start OPMAS core components")
async def start_system(
    background_tasks: BackgroundTasks,
    component: Optional[str] = Query(None, description="Specific component to start"),
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> ControlActionResponse:
    """Start OPMAS system or specific component."""
    if not START_SCRIPT_PATH.is_file() or not os.access(START_SCRIPT_PATH, os.X_OK):
        raise HTTPException(
            status_code=500,
            detail="System start script is missing or not executable."
        )

    # Create control action
    control_service = ControlService(db, nats)
    action = await control_service.create_control_action("start", component)

    # Execute in background
    background_tasks.add_task(
        _execute_control_script,
        "start",
        component,
        control_service,
        action.id
    )

    return action

@router.post("/stop", 
             response_model=ControlActionResponse,
             status_code=status.HTTP_202_ACCEPTED, 
             summary="Stop OPMAS core components")
async def stop_system(
    background_tasks: BackgroundTasks,
    component: Optional[str] = Query(None, description="Specific component to stop"),
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> ControlActionResponse:
    """Stop OPMAS system or specific component."""
    if not START_SCRIPT_PATH.is_file() or not os.access(START_SCRIPT_PATH, os.X_OK):
        raise HTTPException(
            status_code=500,
            detail="System control script is missing or not executable."
        )

    # Create control action
    control_service = ControlService(db, nats)
    action = await control_service.create_control_action("stop", component)

    # Execute in background
    background_tasks.add_task(
        _execute_control_script,
        "stop",
        component,
        control_service,
        action.id
    )

    return action

@router.post("/restart", 
             response_model=ControlActionResponse,
             status_code=status.HTTP_202_ACCEPTED, 
             summary="Restart OPMAS core components")
async def restart_system(
    background_tasks: BackgroundTasks,
    component: Optional[str] = Query(None, description="Specific component to restart"),
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> ControlActionResponse:
    """Restart OPMAS system or specific component."""
    if not START_SCRIPT_PATH.is_file() or not os.access(START_SCRIPT_PATH, os.X_OK):
        raise HTTPException(
            status_code=500,
            detail="System control script is missing or not executable."
        )

    # Create control action
    control_service = ControlService(db, nats)
    action = await control_service.create_control_action("restart", component)

    # Execute in background
    background_tasks.add_task(
        _execute_control_script,
        "restart",
        component,
        control_service,
        action.id
    )

    return action

@router.post("/reload", 
             response_model=ControlActionResponse,
             status_code=status.HTTP_202_ACCEPTED, 
             summary="Reload OPMAS configuration")
async def reload_configuration(
    background_tasks: BackgroundTasks,
    component: Optional[str] = Query(None, description="Specific component to reload"),
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> ControlActionResponse:
    """Reload OPMAS configuration for system or specific component."""
    if not START_SCRIPT_PATH.is_file() or not os.access(START_SCRIPT_PATH, os.X_OK):
        raise HTTPException(
            status_code=500,
            detail="System control script is missing or not executable."
        )

    # Create control action
    control_service = ControlService(db, nats)
    action = await control_service.create_control_action("reload", component)

    # Execute in background
    background_tasks.add_task(
        _execute_control_script,
        "reload",
        component,
        control_service,
        action.id
    )

    return action

@router.get("/status/{action_id}", 
            response_model=ControlActionResponse,
            summary="Get status of a control action")
async def get_control_status(
    action_id: str,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> ControlActionResponse:
    """Get the status of a control action."""
    control_service = ControlService(db, nats)
    return await control_service.get_control_action(action_id)

@router.get("/actions",
            response_model=List[ControlActionResponse],
            summary="List control actions")
async def list_control_actions(
    component: Optional[str] = Query(None, description="Filter by component"),
    status: Optional[ControlActionStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of actions to return"),
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> List[ControlActionResponse]:
    """List control actions with optional filtering."""
    control_service = ControlService(db, nats)
    return await control_service.list_control_actions(component, status, limit)

@router.get("/component/{component}/status",
            response_model=Dict[str, Any],
            summary="Get component status")
async def get_component_status(
    component: str,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> Dict[str, Any]:
    """Get the current status of a specific component."""
    control_service = ControlService(db, nats)
    return await control_service.get_component_status(component)
# ------------------------------- 