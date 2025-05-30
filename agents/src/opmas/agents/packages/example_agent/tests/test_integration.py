"""Integration tests for the example agent."""
import asyncio
import json
from datetime import datetime
from typing import Any, AsyncGenerator

import pytest
from nats.aio.client import Client as NATS

from ...base_agent_package.models import AgentConfig, Finding, Severity
from ..agent import ExampleAgent


@pytest.fixture
async def nats_client() -> AsyncGenerator[NATS, None]:
    """Create a test NATS client."""
    client = NATS()
    await client.connect("nats://localhost:4222")
    yield client
    await client.close()


@pytest.fixture
def agent_config() -> AgentConfig:
    """Create a test agent configuration."""
    return AgentConfig(
        agent_id="test-agent-123",
        agent_type="example",
        nats_url="nats://localhost:4222",
        heartbeat_interval=30,
        log_level="INFO",
        metrics_enabled=True,
    )


@pytest.fixture
async def example_agent(
    agent_config: AgentConfig,
) -> AsyncGenerator[ExampleAgent, None]:
    """Create a test example agent."""
    agent = ExampleAgent(agent_config)
    await agent.start()
    yield agent
    await agent.stop()


@pytest.mark.asyncio
async def test_agent_lifecycle(
    example_agent: ExampleAgent, agent_config: AgentConfig
) -> None:
    """Test agent startup and shutdown."""
    # Agent should be running after start
    health = await example_agent.check_health()
    assert health["status"] == "healthy"
    assert health["uptime"] is not None

    # Stop the agent
    await example_agent.stop()
    health = await example_agent.check_health()
    assert health["status"] == "error"


@pytest.mark.asyncio
async def test_publish_finding(example_agent: ExampleAgent, nats_client: NATS) -> None:
    """Test publishing a finding to NATS."""
    # Subscribe to the findings topic
    findings = []

    async def message_handler(msg: Any) -> None:
        findings.append(json.loads(msg.data.decode()))

    await nats_client.subscribe(
        f"findings.{example_agent.config.agent_type}", cb=message_handler
    )

    # Create and publish a finding
    finding = Finding(
        finding_id="test-finding-123",
        agent_id=example_agent.config.agent_id,
        agent_type=example_agent.config.agent_type,
        severity=Severity.HIGH,
        title="Test Finding",
        description="Test finding description",
        source="test",
        details={"test": "data"},
    )

    await example_agent.publish_finding(finding)

    # Wait for the message to be received
    await asyncio.sleep(0.1)

    # Verify the finding was published
    assert len(findings) == 1
    published_finding = findings[0]
    assert published_finding["finding_id"] == finding.finding_id
    assert published_finding["severity"] == finding.severity.value
    assert published_finding["title"] == finding.title


@pytest.mark.asyncio
async def test_process_event_integration(
    example_agent: ExampleAgent, nats_client: NATS
) -> None:
    """Test end-to-end event processing."""
    # Subscribe to the findings topic
    findings = []

    async def message_handler(msg: Any) -> None:
        findings.append(json.loads(msg.data.decode()))

    await nats_client.subscribe(
        f"findings.{example_agent.config.agent_type}", cb=message_handler
    )

    # Process an event that should trigger a finding
    event = {
        "type": "system_metrics",
        "cpu_usage": 95,
        "timestamp": datetime.utcnow().isoformat(),
        "host": "test-host",
    }

    await example_agent.process_event(event)

    # Wait for the message to be received
    await asyncio.sleep(0.1)

    # Verify the finding was published
    assert len(findings) == 1
    finding = findings[0]
    assert finding["severity"] == Severity.HIGH.value
    assert finding["title"] == "High CPU Usage Detected"
    assert finding["details"]["cpu_usage"] == 95


@pytest.mark.asyncio
async def test_heartbeat_update(example_agent: ExampleAgent) -> None:
    """Test agent heartbeat updates."""
    # Get initial health
    initial_health = await example_agent.check_health()
    initial_heartbeat = initial_health["last_heartbeat"]

    # Update heartbeat
    await example_agent.update_heartbeat()

    # Get updated health
    updated_health = await example_agent.check_health()
    updated_heartbeat = updated_health["last_heartbeat"]

    # Verify heartbeat was updated
    assert updated_heartbeat != initial_heartbeat
    assert updated_health["status"] == "healthy"
