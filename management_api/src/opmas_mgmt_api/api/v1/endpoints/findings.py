"""Findings endpoints."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from opmas_mgmt_api.api.deps import get_current_user, get_db
from opmas_mgmt_api.schemas.auth import User
from opmas_mgmt_api.schemas.finding import Finding, FindingCreate, FindingUpdate
from opmas_mgmt_api.services.finding import FindingService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=List[Finding])
async def get_findings(
    search: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_direction: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Finding]:
    """Get findings with optional filtering and sorting.

    Args:
        search: Optional search term
        severity: Optional severity filter
        status: Optional status filter
        sort_by: Field to sort by
        sort_direction: Sort direction (asc/desc)

    Returns:
        List of findings matching the criteria
    """
    try:
        finding_service = FindingService(db)
        findings = await finding_service.get_findings(
            search=search,
            severity=severity,
            status=status,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
        return findings
    except Exception as e:
        logger.error(f"Error getting findings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve findings",
        )


@router.post("", response_model=Finding, status_code=status.HTTP_201_CREATED)
async def create_finding(
    finding: FindingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Finding:
    """Create a new finding.

    Args:
        finding: Finding data

    Returns:
        Created finding
    """
    try:
        finding_service = FindingService(db)
        return await finding_service.create_finding(finding)
    except Exception as e:
        logger.error(f"Error creating finding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create finding",
        )


@router.get("/{finding_id}", response_model=Finding)
async def get_finding(
    finding_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Finding:
    """Get a finding by ID.

    Args:
        finding_id: ID of the finding to retrieve

    Returns:
        Finding if found

    Raises:
        HTTPException: If finding is not found
    """
    try:
        finding_service = FindingService(db)
        finding = await finding_service.get_finding(finding_id)
        if not finding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Finding not found",
            )
        return finding
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting finding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve finding",
        )


@router.put("/{finding_id}", response_model=Finding)
async def update_finding(
    finding_id: str,
    finding: FindingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Finding:
    """Update a finding.

    Args:
        finding_id: ID of the finding to update
        finding: Updated finding data

    Returns:
        Updated finding

    Raises:
        HTTPException: If finding is not found
    """
    try:
        finding_service = FindingService(db)
        updated_finding = await finding_service.update_finding(finding_id, finding)
        if not updated_finding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Finding not found",
            )
        return updated_finding
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating finding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update finding",
        )


@router.delete("/{finding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_finding(
    finding_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a finding.

    Args:
        finding_id: ID of the finding to delete

    Raises:
        HTTPException: If finding is not found
    """
    try:
        finding_service = FindingService(db)
        if not await finding_service.delete_finding(finding_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Finding not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting finding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete finding",
        )
