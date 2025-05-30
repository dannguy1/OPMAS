"""Playbook management service."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from opmas_mgmt_api.core.exceptions import ResourceNotFoundError, ValidationError
from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.models.playbooks import Playbook, PlaybookExecution
from opmas_mgmt_api.schemas.playbooks import PlaybookCreate
from opmas_mgmt_api.schemas.playbooks import PlaybookExecution as PlaybookExecutionSchema
from opmas_mgmt_api.schemas.playbooks import PlaybookStatus, PlaybookUpdate
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class PlaybookService:
    """Playbook management service."""

    def __init__(self, db: AsyncSession, nats: NATSManager):
        """Initialize service."""
        self.db = db
        self.nats = nats

    async def list_playbooks(
        self,
        skip: int = 0,
        limit: int = 100,
        agent_type: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """List playbooks with optional filtering."""
        # Build base query with only existing columns
        base_query = select(
            Playbook.id,
            Playbook.name,
            Playbook.description,
            Playbook.agent_type,
            Playbook.enabled,
            Playbook.steps,
            Playbook.playbook_metadata,
            Playbook.created_at,
            Playbook.updated_at,
            Playbook.last_executed,
            Playbook.execution_count,
            Playbook.owner_id,
        )

        # Apply filters
        if agent_type:
            base_query = base_query.where(Playbook.agent_type == agent_type)
        if enabled is not None:
            base_query = base_query.where(Playbook.enabled == enabled)

        # Get total count
        count_query = select(Playbook.id)
        if base_query.whereclause is not None:
            count_query = count_query.where(base_query.whereclause)
        result = await self.db.execute(count_query)
        total = len(result.scalars().all())

        # Get paginated results
        query = base_query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        playbooks = result.scalars().all()

        return {
            "items": playbooks,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def get_playbook(self, playbook_id: UUID) -> Playbook:
        """Get playbook by ID."""
        query = select(Playbook).where(Playbook.id == playbook_id)
        result = await self.db.execute(query)
        playbook = result.scalar_one_or_none()

        if not playbook:
            raise ResourceNotFoundError(f"Playbook not found: {playbook_id}")

        return playbook

    async def create_playbook(self, playbook_data: PlaybookCreate) -> Playbook:
        """Create a new playbook."""
        # Check for duplicate name
        query = select(Playbook).where(Playbook.name == playbook_data.name)
        result = await self.db.execute(query)
        if result.scalar_one_or_none():
            raise ValidationError(f"Playbook creation failed: duplicate name: {playbook_data.name}")

        playbook = Playbook(**playbook_data.dict())
        self.db.add(playbook)
        await self.db.commit()
        await self.db.refresh(playbook)

        # Publish playbook creation event
        await self.nats.publish(
            "playbooks.created",
            {
                "playbook_id": str(playbook.id),
                "agent_type": playbook.agent_type,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return playbook

    async def update_playbook(self, playbook_id: UUID, playbook_data: PlaybookUpdate) -> Playbook:
        """Update a playbook."""
        playbook = await self.get_playbook(playbook_id)

        # Check for duplicate name if name is being updated
        if playbook_data.name and playbook_data.name != playbook.name:
            query = select(Playbook).where(Playbook.name == playbook_data.name)
            result = await self.db.execute(query)
            if result.scalar_one_or_none():
                raise ValidationError(f"Playbook update failed: duplicate name: {playbook_data.name}")

        update_data = playbook_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(playbook, field, value)

        playbook.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(playbook)

        # Publish playbook update event
        await self.nats.publish(
            "playbooks.updated",
            {
                "playbook_id": str(playbook.id),
                "agent_type": playbook.agent_type,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return playbook

    async def delete_playbook(self, playbook_id: UUID) -> None:
        """Delete a playbook."""
        playbook = await self.get_playbook(playbook_id)

        await self.db.delete(playbook)
        await self.db.commit()

        # Publish playbook deletion event
        await self.nats.publish(
            "playbooks.deleted",
            {
                "playbook_id": str(playbook_id),
                "agent_type": playbook.agent_type,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def get_playbook_status(self, playbook_id: UUID) -> PlaybookStatus:
        """Get playbook status."""
        playbook = await self.get_playbook(playbook_id)

        return PlaybookStatus(
            status="active" if playbook.enabled else "disabled",
            last_executed=playbook.last_executed,
            execution_count=playbook.execution_count,
            details={"agent_type": playbook.agent_type, "step_count": len(playbook.steps)},
        )

    async def execute_playbook(
        self, playbook_id: UUID, metadata: Optional[Dict[str, Any]] = None
    ) -> PlaybookExecutionSchema:
        """Execute a playbook."""
        playbook = await self.get_playbook(playbook_id)

        if not playbook.enabled:
            raise ValidationError(f"Cannot execute disabled playbook: {playbook_id}")

        # Create execution record
        execution = PlaybookExecution(
            playbook_id=playbook_id,
            status="running",
            steps=[],  # Will be populated as steps are executed
            execution_metadata=metadata,
        )
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)

        # Publish playbook execution event
        await self.nats.publish(
            "playbooks.execution.started",
            {
                "playbook_id": str(playbook_id),
                "execution_id": str(execution.id),
                "agent_type": playbook.agent_type,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return PlaybookExecutionSchema(
            playbook_id=playbook_id,
            started_at=execution.started_at,
            status=execution.status,
            steps=execution.steps,
            metadata=execution.execution_metadata,
        )

    async def get_execution(self, execution_id: UUID) -> PlaybookExecutionSchema:
        """Get playbook execution by ID."""
        query = select(PlaybookExecution).where(PlaybookExecution.id == execution_id)
        result = await self.db.execute(query)
        execution = result.scalar_one_or_none()

        if not execution:
            raise ResourceNotFoundError(f"Playbook execution not found: {execution_id}")

        return PlaybookExecutionSchema(
            playbook_id=execution.playbook_id,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            status=execution.status,
            error=execution.error,
            steps=execution.steps,
            metadata=execution.execution_metadata,
        )

    async def update_execution_status(
        self,
        execution_id: UUID,
        status: str,
        error: Optional[str] = None,
        steps: Optional[List[Dict[str, Any]]] = None,
    ) -> PlaybookExecutionSchema:
        """Update playbook execution status."""
        query = select(PlaybookExecution).where(PlaybookExecution.id == execution_id)
        result = await self.db.execute(query)
        execution = result.scalar_one_or_none()

        if not execution:
            raise ResourceNotFoundError(f"Playbook execution not found: {execution_id}")

        execution.status = status
        if error:
            execution.error = error
        if steps:
            execution.steps = steps
        if status in ["completed", "failed"]:
            execution.completed_at = datetime.utcnow()

            # Update playbook execution count and last executed time
            playbook = await self.get_playbook(execution.playbook_id)
            playbook.execution_count += 1
            playbook.last_executed = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(execution)

        # Publish execution status update event
        await self.nats.publish(
            "playbooks.execution.updated",
            {
                "playbook_id": str(execution.playbook_id),
                "execution_id": str(execution.id),
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return await self.get_execution(execution_id)
