"""Finding service for managing security findings."""

import logging
from typing import List, Optional

from opmas_mgmt_api.models.finding import Finding
from opmas_mgmt_api.schemas.finding import FindingCreate, FindingUpdate
from sqlalchemy import asc, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# Define valid sort fields (in snake_case)
VALID_SORT_FIELDS = {
    "created_at",
    "updated_at",
    "resolved_at",
    "title",
    "severity",
    "status",
    "source",
    "device_id",
    "agent_id",
    "rule_id",
}

# Map camelCase to snake_case for sort fields
CAMEL_TO_SNAKE = {
    "createdAt": "created_at",
    "updatedAt": "updated_at",
    "resolvedAt": "resolved_at",
    "deviceId": "device_id",
    "agentId": "agent_id",
    "ruleId": "rule_id",
}

class FindingService:
    """Service for managing security findings."""

    def __init__(self, db: AsyncSession):
        """Initialize finding service."""
        self.db = db

    async def get_findings(
        self,
        search: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "created_at",
        sort_direction: str = "desc",
    ) -> List[Finding]:
        """Get findings with optional filtering and sorting.

        Args:
            search: Optional search term to filter by title or description
            severity: Optional severity filter
            status: Optional status filter
            sort_by: Field to sort by
            sort_direction: Sort direction (asc/desc)

        Returns:
            List of findings matching the criteria

        Raises:
            HTTPException: If sort parameters are invalid
        """
        query = select(Finding)

        # Apply filters
        if search:
            query = query.where(
                or_(
                    Finding.title.ilike(f"%{search}%"),
                    Finding.description.ilike(f"%{search}%"),
                )
            )
        if severity:
            query = query.where(Finding.severity == severity)
        if status:
            query = query.where(Finding.status == status)

        # Convert sort field to snake_case if needed
        sort_by = CAMEL_TO_SNAKE.get(sort_by, sort_by)

        # Validate sort parameters
        if sort_by not in VALID_SORT_FIELDS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid sort field. Must be one of: {', '.join(sorted(VALID_SORT_FIELDS))}",
            )
        if sort_direction.lower() not in ["asc", "desc"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid sort direction. Must be either 'asc' or 'desc'",
            )

        # Apply sorting
        sort_column = getattr(Finding, sort_by)
        if sort_direction.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_finding(self, finding_id: str) -> Optional[Finding]:
        """Get a finding by ID.

        Args:
            finding_id: ID of the finding to retrieve

        Returns:
            Finding if found, None otherwise
        """
        query = select(Finding).where(Finding.id == finding_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_finding(self, finding_data: FindingCreate) -> Finding:
        """Create a new finding.

        Args:
            finding_data: Finding data

        Returns:
            Created finding
        """
        finding = Finding(**finding_data.model_dump())
        self.db.add(finding)
        await self.db.commit()
        await self.db.refresh(finding)
        return finding

    async def update_finding(
        self, finding_id: str, finding_data: FindingUpdate
    ) -> Optional[Finding]:
        """Update a finding.

        Args:
            finding_id: ID of the finding to update
            finding_data: Updated finding data

        Returns:
            Updated finding if found, None otherwise
        """
        finding = await self.get_finding(finding_id)
        if not finding:
            return None

        update_data = finding_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(finding, field, value)

        await self.db.commit()
        await self.db.refresh(finding)
        return finding

    async def delete_finding(self, finding_id: str) -> bool:
        """Delete a finding.

        Args:
            finding_id: ID of the finding to delete

        Returns:
            True if deleted, False if not found
        """
        finding = await self.get_finding(finding_id)
        if not finding:
            return False

        await self.db.delete(finding)
        await self.db.commit()
        return True
