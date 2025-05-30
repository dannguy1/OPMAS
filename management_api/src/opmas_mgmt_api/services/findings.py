"""Finding management service."""

from typing import Any, Dict, List, Optional
from uuid import UUID
import logging

from opmas_mgmt_api.core.exceptions import ResourceNotFoundError, ValidationError
from opmas_mgmt_api.models.findings import Finding
from opmas_mgmt_api.schemas.findings import FindingCreate, FindingResponse, FindingUpdate
from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

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
        search: Optional[str] = None,
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
            if search:
                query = query.where((Finding.title.ilike(f"%{search}%")) | (Finding.description.ilike(f"%{search}%")))

            # Map frontend field names to model field names
            field_mapping = {
                "createdAt": "created_at",
                "updatedAt": "updated_at",
                "deviceId": "device_id",
                "resolvedAt": "resolved_at",
            }
            sort_field = field_mapping.get(sort_by, sort_by)

            # Add sorting
            sort_column = getattr(Finding, sort_field, Finding.created_at)
            if sort_direction.lower() == "asc":
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))

            # Get total count
            count_query = select(Finding.id)
            if query.whereclause is not None:
                count_query = count_query.where(query.whereclause)
            total = len((await self.db.execute(count_query)).scalars().all())

            # Apply pagination
            query = query.offset(skip).limit(limit)
            findings = (await self.db.execute(query)).scalars().all()

            # Convert to response models
            items = []
            for finding in findings:
                try:
                    finding_dict = {
                        "id": finding.id,
                        "title": finding.title,
                        "description": finding.description,
                        "severity": finding.severity,
                        "status": finding.status,
                        "source": finding.source,
                        "device_id": finding.device_id,
                        "agent_id": finding.agent_id,
                        "rule_id": finding.rule_id,
                        "reporter_id": finding.reporter_id,
                        "finding_metadata": finding.finding_metadata or {},
                        "created_at": finding.created_at,
                        "updated_at": finding.updated_at,
                        "resolved_at": finding.resolved_at,
                    }
                    items.append(FindingResponse(**finding_dict))
                except Exception as e:
                    logger.error(f"Error converting finding to response model: {str(e)}")
                    logger.error(f"Finding data: {finding.__dict__}")
                    continue

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error listing findings: {str(e)}")
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
