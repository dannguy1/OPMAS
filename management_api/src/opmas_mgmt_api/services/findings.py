"""Finding management service."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from opmas_mgmt_api.core.exceptions import ResourceNotFoundError, ValidationError
from opmas_mgmt_api.models.findings import Finding
from opmas_mgmt_api.schemas.findings import FindingCreate, FindingResponse, FindingUpdate
from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession


class FindingService:
    """Service for managing findings."""

    def __init__(self, db: AsyncSession, nats=None):
        """Initialize service."""
        self.db = db
        self.nats = nats

    async def list_findings(
        self,
        skip: int = 0,
        limit: int = 100,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        device_id: Optional[UUID] = None,
        sort_by: str = "created_at",
        sort_direction: str = "desc",
    ) -> Dict[str, Any]:
        """List findings with optional filtering and sorting."""
        try:
            # Build base query
            query = select(Finding)

            # Add filters
            if severity:
                query = query.where(Finding.severity == severity)
            if status:
                query = query.where(Finding.status == status)
            if device_id:
                query = query.where(Finding.device_id == device_id)

            # Add sorting
            sort_column = getattr(Finding, sort_by)
            if sort_direction.lower() == "asc":
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))

            # Get total count
            count_query = select(Finding).where(query.whereclause)
            total = len((await self.db.execute(count_query)).scalars().all())

            # Apply pagination
            query = query.offset(skip).limit(limit)
            findings = (await self.db.execute(query)).scalars().all()

            # Convert to response models
            items = []
            for finding in findings:
                finding_dict = {
                    "id": finding.id,
                    "title": finding.title,
                    "description": finding.description,
                    "severity": finding.severity,
                    "status": finding.status,
                    "category": finding.category,
                    "source": finding.source,
                    "device_id": finding.device_id,
                    "finding_metadata": finding.finding_metadata,
                    "created_at": finding.created_at,
                    "updated_at": finding.updated_at,
                    "resolved_at": finding.resolved_at,
                    "resolution": finding.resolution,
                    "assigned_to": finding.assigned_to,
                }
                items.append(FindingResponse(**finding_dict))

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            raise ValidationError(f"Error listing findings: {str(e)}")

    async def create_finding(self, finding: FindingCreate):
        """Create a new finding."""
        db_finding = Finding(**finding.model_dump())
        self.db.add(db_finding)
        await self.db.commit()
        await self.db.refresh(db_finding)
        return db_finding

    async def get_finding(self, finding_id: UUID):
        """Get finding by ID."""
        finding = await self.db.get(Finding, finding_id)
        if not finding:
            raise ResourceNotFoundError(f"Finding {finding_id} not found")
        return finding

    async def update_finding(self, finding_id: UUID, finding: FindingUpdate):
        """Update a finding."""
        db_finding = await self.get_finding(finding_id)
        update_data = finding.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_finding, field, value)
        await self.db.commit()
        await self.db.refresh(db_finding)
        return db_finding

    async def delete_finding(self, finding_id: UUID):
        """Delete a finding."""
        finding = await self.get_finding(finding_id)
        await self.db.delete(finding)
        await self.db.commit()
