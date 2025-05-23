"""Log ingestion endpoints."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, validator
import re

from opmas_mgmt_api.api.deps import get_db, get_nats
from opmas_mgmt_api.services.logs import LogService
from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.core.exceptions import OPMASException

logger = logging.getLogger(__name__)

router = APIRouter()

class LogIngestionRequest(BaseModel):
    """Log ingestion request model."""
    logs: List[str] = Field(..., description="List of log entries to ingest")
    source_identifier: Optional[str] = Field(None, description="Identifier for the log source")
    explicit_source_ip: Optional[str] = Field(None, description="Original source IP address")

    @validator('logs')
    def validate_logs(cls, v):
        """Validate log entries."""
        if not v:
            raise ValueError("At least one log entry is required")
        if len(v) > 1000:  # Limit batch size
            raise ValueError("Maximum 1000 log entries per request")
        return v

    @validator('explicit_source_ip')
    def validate_source_ip(cls, v):
        """Validate source IP address format."""
        if v:
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if not re.match(ip_pattern, v):
                raise ValueError("Invalid IP address format")
        return v

class LogIngestionResponse(BaseModel):
    """Log ingestion response model."""
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(..., description="Timestamp of ingestion")
    log_count: int = Field(..., description="Number of logs ingested")

@router.post("/ingest", response_model=LogIngestionResponse)
async def ingest_logs(
    request: Request,
    data: LogIngestionRequest,
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> LogIngestionResponse:
    """Ingest logs from various sources.
    
    This endpoint accepts logs in syslog format or raw text format.
    The logs are validated, parsed, and forwarded to the appropriate agents via NATS.
    
    Args:
        request: FastAPI request object
        data: Log ingestion request data
        db: Database session
        nats: NATS manager
        
    Returns:
        LogIngestionResponse: Response containing ingestion status
        
    Raises:
        HTTPException: If validation fails or processing error occurs
    """
    try:
        service = LogService(db, nats)
        
        # Get client IP if not explicitly provided
        source_ip = data.explicit_source_ip or request.client.host
        
        # Process logs
        processed_count = await service.process_logs(
            logs=data.logs,
            source_identifier=data.source_identifier,
            source_ip=source_ip
        )
        
        return LogIngestionResponse(
            message=f"Successfully ingested {processed_count} logs",
            timestamp=datetime.utcnow(),
            log_count=processed_count
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Log ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/status", response_model=Dict[str, Any])
async def get_log_ingestion_status(
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> Dict[str, Any]:
    """Get log ingestion service status.
    
    Returns:
        Dict[str, Any]: Status information including:
            - service_status: Overall service status
            - nats_connection: NATS connection status
            - processing_stats: Log processing statistics
            - error_count: Number of processing errors
    """
    service = LogService(db, nats)
    return await service.get_status()

@router.get("/stats", response_model=Dict[str, Any])
async def get_log_ingestion_stats(
    start_time: Optional[datetime] = Query(None, description="Start time for statistics"),
    end_time: Optional[datetime] = Query(None, description="End time for statistics"),
    db: AsyncSession = Depends(get_db),
    nats: NATSManager = Depends(get_nats)
) -> Dict[str, Any]:
    """Get log ingestion statistics.
    
    Args:
        start_time: Optional start time for statistics
        end_time: Optional end time for statistics
        db: Database session
        nats: NATS manager
        
    Returns:
        Dict[str, Any]: Statistics including:
            - total_logs: Total number of logs processed
            - success_count: Number of successfully processed logs
            - error_count: Number of processing errors
            - avg_processing_time: Average processing time per log
            - source_stats: Statistics by source
    """
    service = LogService(db, nats)
    return await service.get_statistics(start_time, end_time) 