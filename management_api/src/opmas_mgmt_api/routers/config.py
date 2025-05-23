import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException

# Adjust import path if necessary
from opmas.config import get_config

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Core Configuration Endpoint --- 
@router.get("/core", 
            response_model=Dict[str, Any], 
            summary="Get the current core system configuration")
async def get_core_configuration() -> Dict[str, Any]:
    """Retrieves the currently loaded core configuration settings."""
    logger.info("Received request for GET /config/core")
    core_config = get_config()
    if core_config is None:
        logger.error("Core config requested via API, but it is not loaded.")
        raise HTTPException(status_code=500, detail="Core configuration is not currently loaded.")
    return core_config
# --------------------------------- 