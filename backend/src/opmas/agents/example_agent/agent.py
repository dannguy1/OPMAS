"""Example agent implementation for monitoring system metrics."""
from datetime import datetime
from typing import Any, Dict, Optional

import structlog

from ...base_agent_package.agent import BaseAgent
from ...base_agent_package.models import AgentConfig, Finding, Severity

logger = structlog.get_logger(__name__)


class ExampleAgent(BaseAgent):
    """Example agent that monitors system metrics."""

    def __init__(self, config: AgentConfig) -> None:
        """Initialize the example agent."""
        super().__init__(config)
        self.processed_events = 0
        self.last_event_time: Optional[datetime] = None

    async def process_event(self, event: Dict[str, Any]) -> None:
        """Process a system metrics event and generate findings."""
        self.processed_events += 1
        self.last_event_time = datetime.utcnow()

        # Check CPU usage
        if event.get("cpu_usage", 0) > 90:
            await self.publish_finding(
                Finding(
                    finding_id=f"cpu-high-{self.processed_events}",
                    agent_id=self.config.agent_id,
                    agent_type=self.config.agent_type,
                    severity=Severity.HIGH,
                    title="High CPU Usage Detected",
                    description="System CPU usage is above 90%",
                    source="system_metrics",
                    details={
                        "cpu_usage": event["cpu_usage"],
                        "host": event.get("host", "unknown"),
                    },
                )
            )

        # Check memory usage
        if event.get("memory_usage", 0) > 85:
            await self.publish_finding(
                Finding(
                    finding_id=f"memory-high-{self.processed_events}",
                    agent_id=self.config.agent_id,
                    agent_type=self.config.agent_type,
                    severity=Severity.MEDIUM,
                    title="High Memory Usage Detected",
                    description="System memory usage is above 85%",
                    source="system_metrics",
                    details={
                        "memory_usage": event["memory_usage"],
                        "host": event.get("host", "unknown"),
                    },
                )
            )

    async def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics."""
        return {
            "processed_events": self.processed_events,
            "agent_id": self.config.agent_id,
            "agent_type": self.config.agent_type,
            "last_event_time": self.last_event_time.isoformat()
            if self.last_event_time
            else None,
        }
