"""Dashboard schemas."""

from datetime import datetime

from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Dashboard statistics."""

    totalFindings: int
    criticalFindings: int
    totalActions: int
    pendingActions: int


class RecentActivity(BaseModel):
    """Recent system activity."""

    id: int
    timestamp: datetime
    type: str
    description: str
    severity: str
