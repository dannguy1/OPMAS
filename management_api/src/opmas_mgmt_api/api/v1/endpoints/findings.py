"""Findings endpoints."""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from opmas_mgmt_api.api.deps import get_current_user, get_db
from opmas_mgmt_api.models.user import User
from opmas_mgmt_api.schemas.findings import FindingResponse, FindingCreate, FindingUpdate, FindingList
from opmas_mgmt_api.services.findings import FindingService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=FindingList)
async def list_findings(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    device_id: Optional[UUID] = None,
    agent_id: Optional[UUID] = None
) -> FindingList:
    """List findings with optional filtering."""
    service = FindingService(db)
    result = await service.list_findings(
        skip=skip,
        limit=limit,
        severity=severity,
        status=status,
        device_id=device_id
    )
    return result

@router.post("/", response_model=FindingResponse)
async def create_new_finding(
    finding: FindingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FindingResponse:
    """Create new finding."""
    service = FindingService(db)
    db_finding = await service.create_finding(finding)
    return FindingResponse.model_validate(db_finding)

@router.get("/{finding_id}", response_model=FindingResponse)
async def read_finding(
    finding_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FindingResponse:
    """Get finding by ID."""
    service = FindingService(db)
    finding = await service.get_finding(finding_id)
    return FindingResponse.model_validate(finding)

@router.put("/{finding_id}", response_model=FindingResponse)
async def update_existing_finding(
    finding_id: UUID,
    finding: FindingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FindingResponse:
    """Update finding."""
    service = FindingService(db)
    updated_finding = await service.update_finding(finding_id, finding)
    return FindingResponse.model_validate(updated_finding)

@router.delete("/{finding_id}")
async def delete_existing_finding(
    finding_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete finding."""
    service = FindingService(db)
    await service.delete_finding(finding_id)
    return {"status": "success"}
