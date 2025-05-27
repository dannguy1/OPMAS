"""Base agent implementation for OPMAS agents."""  # noqa: D200
from datetime import datetime
from typing import Any, Dict, Optional

import structlog
from nats.aio.client import Client as NATS

from .exceptions import AgentError, ValidationError
from .models import AgentConfig, Finding

logger = structlog.get_logger(__name__)


class BaseAgent:
    """Base class for all OPMAS agents."""

    def __init__(self, config: AgentConfig) -> None:
        """Initialize the agent with configuration."""
        self.config = config
        self.nats_client = NATS()
        self._running = False
        self._start_time: Optional[datetime] = None
        self._last_heartbeat: Optional[datetime] = None

    async def start(self) -> None:
        """Start the agent and connect to NATS."""
        try:
            await self.nats_client.connect(
                self.config.nats_url,
                name=f"{self.config.agent_id}-{self.config.agent_type}",
            )
            self._running = True
            self._start_time = datetime.utcnow()
            self._last_heartbeat = self._start_time
            logger.info(
                "agent_started",
                agent_id=self.config.agent_id,
                agent_type=self.config.agent_type,
            )
        except Exception as e:
            raise AgentError(f"Failed to start agent: {str(e)}") from e

    async def stop(self) -> None:
        """Stop the agent and disconnect from NATS."""
        if self._running:
            await self.nats_client.close()
            self._running = False
            logger.info(
                "agent_stopped",
                agent_id=self.config.agent_id,
                agent_type=self.config.agent_type,
            )

    async def publish_finding(self, finding: Finding) -> None:
        """Publish a finding to NATS."""
        if not self._running:
            raise AgentError("Agent is not running")
        try:
            await self.nats_client.publish(
                f"findings.{self.config.agent_type}",
                finding.model_dump_json().encode(),
            )
            logger.info(
                "finding_published",
                agent_id=self.config.agent_id,
                finding_id=finding.finding_id,
            )
        except Exception as e:
            raise AgentError(f"Failed to publish finding: {str(e)}") from e

    async def process_event(self, event: Dict[str, Any]) -> None:
        """Process an event and generate findings."""
        raise NotImplementedError("Subclasses must implement process_event")

    async def validate_config(self) -> None:
        """Validate the agent configuration."""
        try:
            self.config.model_validate(self.config.model_dump())
        except Exception as e:
            raise ValidationError(f"Invalid configuration: {str(e)}") from e

    async def check_health(self) -> Dict[str, Any]:
        """Check the health of the agent."""
        if not self._running:
            return {
                "status": "error",
                "message": "Agent is not running",
                "uptime": None,
                "last_heartbeat": None,
            }

        uptime = None
        if self._start_time:
            uptime = (datetime.utcnow() - self._start_time).total_seconds()

        return {
            "status": "healthy",
            "message": "Agent is running",
            "uptime": uptime,
            "last_heartbeat": self._last_heartbeat.isoformat()
            if self._last_heartbeat
            else None,
        }

    async def update_heartbeat(self) -> None:
        """Update the agent's heartbeat timestamp."""
        self._last_heartbeat = datetime.utcnow()
        logger.debug(
            "heartbeat_updated",
            agent_id=self.config.agent_id,
            timestamp=self._last_heartbeat.isoformat(),
        )
