"""Configuration management service."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from opmas_mgmt_api.models.configurations import Configuration, ConfigurationHistory
from opmas_mgmt_api.schemas.configurations import ConfigurationCreate, ConfigurationUpdate
from opmas_mgmt_api.core.exceptions import OPMASException
from opmas_mgmt_api.core.nats import NATSManager

class ConfigurationService:
    """Configuration management service."""
    
    def __init__(self, db: Session, nats: NATSManager):
        """Initialize service with database session and NATS manager."""
        self.db = db
        self.nats = nats

    async def list_configurations(
        self,
        skip: int = 0,
        limit: int = 100,
        component: Optional[str] = None,
        component_id: Optional[UUID] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """List configurations with optional filtering."""
        query = select(Configuration)

        if component:
            query = query.where(Configuration.component == component)
        if component_id:
            query = query.where(Configuration.component_id == component_id)
        if is_active is not None:
            query = query.where(Configuration.is_active == is_active)

        # Get total count
        count_query = select(Configuration.id).select_from(query.subquery())
        result = await self.db.execute(count_query)
        total = len(result.scalars().all())

        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        configurations = result.scalars().all()

        return {
            "items": configurations,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    async def create_configuration(
        self,
        configuration: ConfigurationCreate,
        created_by: Optional[str] = None
    ) -> Configuration:
        """Create a new configuration."""
        try:
            # Create configuration
            db_config = Configuration(**configuration.model_dump())
            self.db.add(db_config)
            await self.db.commit()
            await self.db.refresh(db_config)

            # Create history entry
            history = ConfigurationHistory(
                configuration_id=db_config.id,
                version=db_config.version,
                configuration=db_config.configuration,
                config_metadata=db_config.config_metadata,
                created_by=created_by
            )
            self.db.add(history)
            await self.db.commit()

            # Publish configuration created event
            await self.nats.publish(
                "configurations.created",
                {
                    "configuration_id": str(db_config.id),
                    "component": db_config.component,
                    "component_id": str(db_config.component_id) if db_config.component_id else None,
                    "version": db_config.version,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            return db_config
        except IntegrityError as e:
            await self.db.rollback()
            raise OPMASException(
                status_code=400,
                detail=f"Configuration creation failed: {str(e)}"
            )

    async def get_configuration(self, configuration_id: UUID) -> Configuration:
        """Get configuration by ID."""
        result = await self.db.execute(
            select(Configuration).where(Configuration.id == configuration_id)
        )
        configuration = result.scalar_one_or_none()
        if not configuration:
            raise OPMASException(
                status_code=404,
                detail="Configuration not found"
            )
        return configuration

    async def update_configuration(
        self,
        configuration_id: UUID,
        configuration: ConfigurationUpdate,
        updated_by: Optional[str] = None
    ) -> Configuration:
        """Update configuration."""
        db_config = await self.get_configuration(configuration_id)

        # Update configuration
        update_data = configuration.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_config, key, value)

        # Create history entry if configuration changed
        if "configuration" in update_data:
            history = ConfigurationHistory(
                configuration_id=db_config.id,
                version=db_config.version,
                configuration=db_config.configuration,
                config_metadata=db_config.config_metadata,
                created_by=updated_by
            )
            self.db.add(history)

        await self.db.commit()
        await self.db.refresh(db_config)

        # Publish configuration updated event
        await self.nats.publish(
            "configurations.updated",
            {
                "configuration_id": str(db_config.id),
                "component": db_config.component,
                "component_id": str(db_config.component_id) if db_config.component_id else None,
                "version": db_config.version,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        return db_config

    async def delete_configuration(self, configuration_id: UUID) -> None:
        """Delete configuration."""
        db_config = await self.get_configuration(configuration_id)
        await self.db.delete(db_config)
        await self.db.commit()

        # Publish configuration deleted event
        await self.nats.publish(
            "configurations.deleted",
            {
                "configuration_id": str(configuration_id),
                "component": db_config.component,
                "component_id": str(db_config.component_id) if db_config.component_id else None,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    async def get_configuration_history(
        self,
        configuration_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get configuration history."""
        # Verify configuration exists
        await self.get_configuration(configuration_id)

        # Get history entries
        query = select(ConfigurationHistory).where(
            ConfigurationHistory.configuration_id == configuration_id
        ).order_by(ConfigurationHistory.created_at.desc())

        # Get total count
        total = len(await self.db.execute(query))

        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        history = result.scalars().all()

        return {
            "items": history,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    async def get_active_configuration(
        self,
        component: str,
        component_id: Optional[UUID] = None
    ) -> Configuration:
        """Get active configuration for a component."""
        query = select(Configuration).where(
            Configuration.component == component,
            Configuration.is_active == True
        )

        if component_id:
            query = query.where(Configuration.component_id == component_id)

        result = await self.db.execute(query)
        configuration = result.scalar_one_or_none()

        if not configuration:
            raise OPMASException(
                status_code=404,
                detail=f"No active configuration found for component {component}"
            )

        return configuration 