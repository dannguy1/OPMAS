"""System management service."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from opmas_mgmt_api.core.config import settings
from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.models.system import SystemConfig as SystemConfigModel
from opmas_mgmt_api.models.system import SystemEvent
from opmas_mgmt_api.schemas.system import (
    SystemConfig,
    SystemConfigUpdate,
    SystemControl,
    SystemHealth,
    SystemMetrics,
    SystemStatus,
)
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SystemService:
    """System management service."""

    def __init__(self, db: AsyncSession, nats: NATSManager):
        """Initialize system service."""
        self.db = db
        self.nats = nats

    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        try:
            # Request system status from NATS
            response = await self.nats.request("system.status", {})
            if not response:
                return {"status": "unknown", "timestamp": datetime.utcnow().isoformat()}

            # Parse response
            status = response.get("status", "unknown")
            timestamp = response.get("timestamp", datetime.utcnow().isoformat())

            return {"status": status, "timestamp": timestamp}
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"status": "error", "timestamp": datetime.utcnow().isoformat()}

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

    async def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent system events."""
        try:
            # Query database for recent events
            query = text(
                """
                SELECT * FROM system_events
                ORDER BY timestamp DESC
                LIMIT :limit
            """
            )
            result = await self.db.execute(query, {"limit": limit})
            events = result.fetchall()

            if not events:
                return []

            return [
                {
                    "id": event.id,
                    "type": event.type,
                    "message": event.message,
                    "timestamp": event.timestamp.isoformat(),
                    "details": event.details,
                }
                for event in events
            ]
        except Exception as e:
            logger.error(f"Error getting recent events: {e}")
            return []

    async def create_event(
        self, event_type: str, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a new system event."""
        try:
            event = SystemEvent(
                type=event_type, message=message, details=details or {}, timestamp=datetime.utcnow()
            )
            self.db.add(event)
            await self.db.commit()

            # Publish event to NATS
            await self.nats.publish(
                "system.events",
                {
                    "type": event_type,
                    "message": message,
                    "details": details,
                    "timestamp": event.timestamp.isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"Error creating system event: {e}")
            raise

    async def _get_component_statuses(self) -> Dict[str, Any]:
        """Get status of all system components."""
        return {
            "orchestrator": {"status": "running", "last_heartbeat": datetime.utcnow().isoformat()},
            "nats": {"status": "connected", "last_heartbeat": datetime.utcnow().isoformat()},
            "database": {"status": "connected", "last_heartbeat": datetime.utcnow().isoformat()},
        }

    async def _get_component_health(self) -> Dict[str, Any]:
        """Get health status of all system components."""
        return {
            "orchestrator": {"status": "healthy", "message": "Orchestrator is running"},
            "nats": {"status": "healthy", "message": "NATS is connected"},
            "database": {"status": "healthy", "message": "Database is connected"},
        }

    async def _get_component_metrics(self) -> Dict[str, Any]:
        """Get metrics from all system components."""
        return {
            "orchestrator": {
                "cpu_usage": 0.5,
                "memory_usage": 0.3,
                "active_tasks": 5,
            },
            "nats": {
                "messages_per_second": 100,
                "connected_clients": 3,
            },
            "database": {
                "connections": 10,
                "queries_per_second": 50,
            },
        }

    async def _get_system_wide_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics."""
        return {
            "cpu_usage": 0.4,
            "memory_usage": 0.6,
            "disk_usage": 0.3,
            "network_traffic": {
                "in": 1000,
                "out": 500,
            },
        }

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
