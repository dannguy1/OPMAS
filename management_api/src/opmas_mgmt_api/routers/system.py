import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
import nats
from ..database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Pydantic Model for Status ---
class SystemStatus(BaseModel):
    status: str = "ok"
    message: str = "Management API is operational"
    nats_status: str = "disconnected"
    nats_error: str = ""
    db_status: str = "disconnected"
    db_error: str = ""
    # Add timestamp or other info if needed later
# ---------------------------------

# --- System Status Endpoint ---
@router.get("/status", 
            response_model=SystemStatus,
            tags=["System"], 
            summary="Check the operational status of the Management API")
async def get_system_status(db: Session = Depends(get_db)) -> SystemStatus:
    """Returns the current status of the Management API."""
    logger.debug("Received request for /api/v1/status")
    
    status_response = SystemStatus()
    
    # Check NATS connection
    try:
        # Try to connect to NATS
        nc = await nats.connect("nats://localhost:4222", name="mgmt_api_status_check")
        if nc and nc.is_connected:
            status_response.nats_status = "connected"
            await nc.close()  # Close the connection after checking
        else:
            status_response.nats_error = "NATS client exists but not connected"
    except Exception as e:
        logger.error(f"Error checking NATS connection: {e}")
        status_response.nats_status = "error"
        status_response.nats_error = str(e)
        
    # Check database connection
    try:
        # Simple query to verify connection using text()
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            status_response.db_status = "connected"
        else:
            status_response.db_error = f"Unexpected result from test query: {result}"
    except Exception as e:
        logger.error(f"Error checking database connection: {e}")
        status_response.db_status = "error"
        status_response.db_error = str(e)
        
    # Set overall status based on component statuses
    if status_response.nats_status == "error" or status_response.db_status == "error":
        status_response.status = "error"
        error_msgs = []
        if status_response.nats_error:
            error_msgs.append(f"NATS error: {status_response.nats_error}")
        if status_response.db_error:
            error_msgs.append(f"Database error: {status_response.db_error}")
        status_response.message = " | ".join(error_msgs)
    elif status_response.nats_status == "disconnected" or status_response.db_status == "disconnected":
        status_response.status = "degraded"
        status_response.message = "One or more system components are disconnected"
        
    return status_response
# ----------------------------------- 