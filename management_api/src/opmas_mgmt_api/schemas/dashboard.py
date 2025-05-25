"""Dashboard schemas."""

from datetime import datetime

from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Dashboard statistics."""

    total_agents: int
    active_agents: int
    total_findings: int
    critical_findings: int


class RecentActivity(BaseModel):
    """Recent system activity."""

    id: int
    timestamp: datetime
    type: str
    description: str
    severity: str
