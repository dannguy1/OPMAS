"""Dashboard endpoints."""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from opmas_mgmt_api.api.deps import get_current_user, get_db, get_nats
from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.schemas.auth import User
from opmas_mgmt_api.schemas.dashboard import DashboardStats, RecentActivity
from opmas_mgmt_api.services.agents import AgentService
from opmas_mgmt_api.services.logs import LogService
from opmas_mgmt_api.services.system import SystemService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> DashboardStats:
    """Get dashboard statistics."""
    try:
        # Initialize services without NATS for now
        system_service = SystemService(db, None)
        agent_service = AgentService(db, None)
        log_service = LogService(db, None)

        # Get system status
        try:
            system_status = await system_service.get_system_status()
        except Exception as e:
            logger.warning(f"Error getting system status: {e}")
            system_status = {"status": "unknown", "timestamp": None}

        # Get agents
        try:
            agents = await agent_service.get_agents()
            active_agents = [a for a in agents if a.status == "running"] if agents else []
        except Exception as e:
            logger.warning(f"Error getting agents: {e}")
            agents = []
            active_agents = []

        # Get log statistics
        try:
            log_stats = await log_service.get_statistics()
        except Exception as e:
            logger.warning(f"Error getting log statistics: {e}")
            log_stats = {"total_logs": 0}

        return DashboardStats(
            total_agents=len(agents),
            active_agents=len(active_agents),
            total_findings=log_stats.get("total_logs", 0),
            critical_findings=0,  # TODO: Implement critical findings count
        )
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity/recent", response_model=list[RecentActivity])
async def get_recent_activity(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[RecentActivity]:
    """Get recent system activity."""
    try:
        log_service = LogService(db, None)
        system_service = SystemService(db, None)

        # Get recent logs
        try:
            recent_logs = await log_service.get_recent_logs(10)
        except Exception as e:
            logger.warning(f"Error getting recent logs: {e}")
            recent_logs = []

        # Get recent system events
        try:
            recent_events = await system_service.get_recent_events(10)
        except Exception as e:
            logger.warning(f"Error getting recent events: {e}")
            recent_events = []

        # Combine and sort by timestamp
        all_activity = recent_logs + recent_events
        all_activity.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Convert to RecentActivity model
        return [
            RecentActivity(
                id=i,
                timestamp=activity.get("timestamp"),
                type=activity.get("type", "unknown"),
                description=activity.get("description", ""),
                severity=activity.get("severity", "info"),
            )
            for i, activity in enumerate(all_activity[:10])
        ]
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))
