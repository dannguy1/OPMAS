"""Findings management endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from opmas_mgmt_api.api.deps import get_db, get_nats
from opmas_mgmt_api.api.v1.endpoints.route_utils import create_route_builder
from opmas_mgmt_api.core.exceptions import ResourceNotFoundError, ValidationError
from opmas_mgmt_api.schemas.findings import (
    FindingBase,
    FindingCreate,
    FindingList,
    FindingResponse,
    FindingUpdate,
)
from opmas_mgmt_api.services.findings import FindingService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
route = create_route_builder(router)


@route.get("", response_model=FindingList)
async def get_findings(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    device_id: Optional[UUID] = Query(None, description="Filter by device ID"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_direction: str = Query("desc", description="Sort direction (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> FindingList:
    """List findings with optional filtering and sorting."""
    try:
        service = FindingService(db, nats)
        result = await service.list_findings(
            skip=skip,
            limit=limit,
            severity=severity,
            status=status,
            device_id=device_id,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
        # Convert items to FindingResponse models
        items = [FindingResponse.model_validate(item) for item in result["items"]]
        return FindingList(
            items=items, total=result["total"], skip=result["skip"], limit=result["limit"]
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@route.post("", response_model=FindingResponse)
async def create_finding(
    finding: FindingCreate, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> FindingResponse:
    """Create a new finding."""
    service = FindingService(db, nats)
    try:
        return await service.create_finding(finding)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> FindingResponse:
    """Get finding by ID."""
    service = FindingService(db, nats)
    try:
        return await service.get_finding(finding_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@route.put("/{finding_id}", response_model=FindingResponse)
async def update_finding(
    finding_id: UUID,
    finding: FindingUpdate,
    db: AsyncSession = Depends(get_db),
    nats=Depends(get_nats),
) -> FindingResponse:
    """Update a finding."""
    service = FindingService(db, nats)
    try:
        return await service.update_finding(finding_id, finding)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@route.delete("/{finding_id}")
async def delete_finding(
    finding_id: UUID, db: AsyncSession = Depends(get_db), nats=Depends(get_nats)
) -> None:
    """Delete a finding."""
    service = FindingService(db, nats)
    try:
        await service.delete_finding(finding_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
