"""Unit tests for the example agent."""
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from ...base_agent_package.models import AgentConfig, Finding, Severity
from ..agent import ExampleAgent


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
def example_agent(agent_config: AgentConfig) -> ExampleAgent:
    """Create a test example agent."""
    return ExampleAgent(agent_config)


@pytest.mark.asyncio
async def test_agent_initialization(
    example_agent: ExampleAgent, agent_config: AgentConfig
) -> None:
    """Test agent initialization."""
    assert example_agent.config == agent_config
    assert example_agent.processed_events == 0
    assert example_agent.last_event_time is None


@pytest.mark.asyncio
async def test_process_event_cpu_usage(example_agent: ExampleAgent) -> None:
    """Test processing an event with high CPU usage."""
    event = {
        "type": "system_metrics",
        "cpu_usage": 95,
        "timestamp": datetime.utcnow().isoformat(),
        "host": "test-host",
    }

    with patch.object(
        example_agent, "publish_finding", new_callable=AsyncMock
    ) as mock_publish:
        await example_agent.process_event(event)
        mock_publish.assert_called_once()

        # Verify the finding
        finding = mock_publish.call_args[0][0]
        assert isinstance(finding, Finding)
        assert finding.severity == Severity.HIGH
        assert finding.title == "High CPU Usage Detected"
        assert finding.details["cpu_usage"] == 95
        assert finding.details["host"] == "test-host"


@pytest.mark.asyncio
async def test_process_event_memory_usage(example_agent: ExampleAgent) -> None:
    """Test processing an event with high memory usage."""
    event = {
        "type": "system_metrics",
        "memory_usage": 90,
        "timestamp": datetime.utcnow().isoformat(),
        "host": "test-host",
    }

    with patch.object(
        example_agent, "publish_finding", new_callable=AsyncMock
    ) as mock_publish:
        await example_agent.process_event(event)
        mock_publish.assert_called_once()

        # Verify the finding
        finding = mock_publish.call_args[0][0]
        assert isinstance(finding, Finding)
        assert finding.severity == Severity.MEDIUM
        assert finding.title == "High Memory Usage Detected"
        assert finding.details["memory_usage"] == 90
        assert finding.details["host"] == "test-host"


@pytest.mark.asyncio
async def test_process_event_no_thresholds(example_agent: ExampleAgent) -> None:
    """Test processing an event that doesn't trigger any findings."""
    event = {
        "type": "system_metrics",
        "cpu_usage": 50,
        "memory_usage": 50,
        "timestamp": datetime.utcnow().isoformat(),
        "host": "test-host",
    }

    with patch.object(
        example_agent, "publish_finding", new_callable=AsyncMock
    ) as mock_publish:
        await example_agent.process_event(event)
        mock_publish.assert_not_called()
        assert example_agent.processed_events == 1


@pytest.mark.asyncio
async def test_process_event_invalid_data(example_agent: ExampleAgent) -> None:
    """Test processing an event with invalid data."""
    event = {
        "type": "system_metrics",
        # Missing required fields
    }

    with patch.object(
        example_agent, "publish_finding", new_callable=AsyncMock
    ) as mock_publish:
        await example_agent.process_event(event)
        mock_publish.assert_not_called()
        assert example_agent.processed_events == 1


@pytest.mark.asyncio
async def test_get_metrics(example_agent: ExampleAgent) -> None:
    """Test getting agent metrics."""
    # Process some events first
    event = {
        "type": "system_metrics",
        "cpu_usage": 50,
        "memory_usage": 50,
    }
    await example_agent.process_event(event)

    metrics = await example_agent.get_metrics()
    assert metrics["processed_events"] == 1
    assert metrics["agent_id"] == example_agent.config.agent_id
    assert metrics["agent_type"] == example_agent.config.agent_type
    assert metrics["last_event_time"] is not None
