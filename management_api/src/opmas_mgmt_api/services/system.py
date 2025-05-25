"""System management service."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from opmas_mgmt_api.core.config import settings
from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.models.system import SystemConfig as SystemConfigModel
from opmas_mgmt_api.schemas.system import (
    SystemConfig,
    SystemConfigUpdate,
    SystemControl,
    SystemHealth,
    SystemMetrics,
    SystemStatus,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SystemService:
    """System management service."""

    def __init__(self, db: AsyncSession, nats: NATSManager):
        """Initialize system service."""
        self.db = db
        self.nats = nats

    async def get_system_status(self) -> SystemStatus:
        """Get overall system status."""
        # Get component statuses
        components = await self._get_component_statuses()

        # Get system metrics
        metrics = await self.get_system_metrics()

        # Get system health
        health = await self.get_system_health()

        return SystemStatus(
            status="operational" if health.status == "healthy" else "degraded",
            components=components,
            metrics=metrics,
            health=health,
            timestamp=datetime.utcnow(),
        )

    async def get_system_health(self) -> SystemHealth:
        """Get system health status."""
        # Check database connection
        db_status = await self._check_database_health()

        # Check NATS connection
        nats_status = await self._check_nats_health()

        # Check component health
        component_health = await self._get_component_health()

        # Determine overall health
        if db_status["status"] == "healthy" and nats_status["status"] == "healthy":
            overall_status = "healthy"
        elif db_status["status"] == "unhealthy" or nats_status["status"] == "unhealthy":
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"

        return SystemHealth(
            status=overall_status,
            components={"database": db_status, "nats": nats_status, **component_health},
            timestamp=datetime.utcnow(),
        )

    async def get_system_metrics(self) -> SystemMetrics:
        """Get system metrics."""
        # Get component metrics
        component_metrics = await self._get_component_metrics()

        # Get system-wide metrics
        system_metrics = await self._get_system_wide_metrics()

        return SystemMetrics(
            components=component_metrics, system=system_metrics, timestamp=datetime.utcnow()
        )

    async def get_system_config(self) -> SystemConfig:
        """Get system configuration."""
        query = select(SystemConfigModel).order_by(SystemConfigModel.created_at.desc()).limit(1)
        result = await self.db.execute(query)
        config = result.scalar_one_or_none()

        if not config:
            # Return default config if none exists
            return SystemConfig(
                version=settings.VERSION,
                components=settings.COMPONENTS,
                security=settings.SECURITY,
                logging=settings.LOGGING,
                timestamp=datetime.utcnow(),
            )

        return SystemConfig(
            version=config.version,
            components=config.components,
            security=config.security,
            logging=config.logging,
            timestamp=config.updated_at,
        )

    async def update_system_config(self, config: SystemConfigUpdate) -> SystemConfig:
        """Update system configuration."""
        # Create new config entry
        new_config = SystemConfigModel(
            version=config.version,
            components=config.components,
            security=config.security,
            logging=config.logging,
        )

        self.db.add(new_config)
        await self.db.commit()
        await self.db.refresh(new_config)

        # Publish config update event
        await self.nats.publish(
            "system.config.updated",
            {"version": config.version, "timestamp": datetime.utcnow().isoformat()},
        )

        return SystemConfig(
            version=new_config.version,
            components=new_config.components,
            security=new_config.security,
            logging=new_config.logging,
            timestamp=new_config.updated_at,
        )

    async def control_system(self, action: str) -> SystemControl:
        """Control system operations."""
        valid_actions = ["start", "stop", "restart", "reload"]
        if action not in valid_actions:
            raise ValueError(f"Invalid action. Must be one of: {', '.join(valid_actions)}")

        # Publish control event
        await self.nats.publish(
            "system.control", {"action": action, "timestamp": datetime.utcnow().isoformat()}
        )

        return SystemControl(action=action, status="accepted", timestamp=datetime.utcnow())

    async def get_system_logs(
        self, level: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get system logs."""
        # TODO: Implement log retrieval from configured logging backend
        return []

    async def _get_component_statuses(self) -> Dict[str, Any]:
        """Get status of all system components."""
        # TODO: Implement component status checks
        return {}

    async def _get_component_health(self) -> Dict[str, Any]:
        """Get health status of all system components."""
        # TODO: Implement component health checks
        return {}

    async def _get_component_metrics(self) -> Dict[str, Any]:
        """Get metrics from all system components."""
        # TODO: Implement component metrics collection
        return {}

    async def _get_system_wide_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics."""
        # TODO: Implement system-wide metrics collection
        return {}

    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            # Execute simple query to check connection
            await self.db.execute("SELECT 1")
            return {"status": "healthy", "message": "Database connection is healthy"}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "message": str(e)}

    async def _check_nats_health(self) -> Dict[str, Any]:
        """Check NATS health."""
        try:
            if self.nats.is_connected():
                return {"status": "healthy", "message": "NATS connection is healthy"}
            return {"status": "unhealthy", "message": "NATS is not connected"}
        except Exception as e:
            logger.error(f"NATS health check failed: {e}")
            return {"status": "unhealthy", "message": str(e)}
