"""Example agent implementation for monitoring system metrics."""
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
import asyncio
import json
import os
import psutil

from opmas.agents.packages.base.agent import BaseAgent
from opmas.agents.packages.base.models import AgentConfig, Finding, Severity

logger = structlog.get_logger(__name__)


class ExampleAgent(BaseAgent):
    """Example agent that monitors system metrics."""

    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        capabilities: List[str],
        management_api_url: str,
        nats_url: str,
        agent_id: str,
    ) -> None:
        """Initialize the example agent."""
        config = AgentConfig(
            agent_id=agent_id,
            agent_type="example",
            nats_url=nats_url,
            heartbeat_interval=30,
            log_level="INFO",
            metrics_enabled=True,
        )
        super().__init__(config)
        self.name = name
        self.version = version
        self.description = description
        self.capabilities = capabilities
        self.management_api_url = management_api_url
        self.processed_events = 0
        self.last_event_time: Optional[datetime] = None

    async def process_event(self, event: Dict[str, Any]) -> None:
        """Process a system metrics event and generate findings."""
        self.processed_events += 1
        self.last_event_time = datetime.utcnow()

        # Get system metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Check for high CPU usage
        if cpu_percent > 80:
            await self.publish_finding(
                title="High CPU Usage",
                description=f"CPU usage is at {cpu_percent}%",
                severity="warning",
                source="system_metrics",
                details={
                    "metric": "cpu_percent",
                    "value": cpu_percent,
                    "threshold": 80
                }
            )

        # Check for high memory usage
        if memory_percent > 80:
            await self.publish_finding(
                title="High Memory Usage",
                description=f"Memory usage is at {memory_percent}%",
                severity="warning",
                source="system_metrics",
                details={
                    "metric": "memory_percent",
                    "value": memory_percent,
                    "threshold": 80
                }
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

    async def start(self) -> None:
        """Start the agent."""
        await super().start()
        logger.info("example_agent_started", agent_id=self.config.agent_id)

    async def stop(self) -> None:
        """Stop the agent."""
        await super().stop()
        logger.info("example_agent_stopped", agent_id=self.config.agent_id)
