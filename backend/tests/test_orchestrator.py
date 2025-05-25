#!/usr/bin/env python3

"""Tests for the Orchestrator class."""

import time
from collections import deque
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opmas.data_models import AgentFinding, ParsedLogEvent
from opmas.db_models import Agent as AgentModel
from opmas.db_models import Finding
from opmas.orchestrator import Orchestrator


@pytest.fixture
def orchestrator():
    """Create an Orchestrator instance with mocked dependencies."""
    with patch("opmas.orchestrator.get_db_session") as mock_session:
        orchestrator = Orchestrator()
        orchestrator.nats_client = AsyncMock()
        return orchestrator


@pytest.fixture
def mock_agent():
    """Create a mock agent."""
    agent = AsyncMock()
    agent.agent_name = "TestAgent"
    agent.subscribed_topics = ["logs.test"]
    agent.findings_topic = "findings.test"
    return agent


@pytest.fixture
def sample_finding():
    """Create a sample finding."""
    return AgentFinding(
        finding_type="TestFinding",
        agent_name="TestAgent",
        resource_id="test-resource",
        severity="High",
        message="Test finding message",
        details={"test": "detail"},
        timestamp=time.time(),
    )


def test_initialize_state(orchestrator):
    """Test initialization of state variables."""
    assert isinstance(orchestrator.agents, dict)
    assert isinstance(orchestrator.active_findings, dict)
    assert isinstance(orchestrator.finding_cooldowns, dict)
    assert not orchestrator.running


def test_load_configuration(orchestrator):
    """Test loading configuration from environment."""
    orchestrator._load_configuration()

    assert orchestrator.notification_cooldown == 3600  # 1 hour
    assert orchestrator.finding_retention == 86400  # 24 hours
    assert orchestrator.cleanup_interval == 3600  # 1 hour


@pytest.mark.asyncio
async def test_start_stop(orchestrator):
    """Test starting and stopping the Orchestrator."""
    # Mock _load_agents and _subscribe_to_findings
    orchestrator._load_agents = AsyncMock()
    orchestrator._subscribe_to_findings = AsyncMock()

    # Start Orchestrator
    await orchestrator.start()
    assert orchestrator.running
    orchestrator._load_agents.assert_called_once()
    orchestrator._subscribe_to_findings.assert_called_once()

    # Stop Orchestrator
    await orchestrator.stop()
    assert not orchestrator.running
    assert not orchestrator.agents
    assert not orchestrator.active_findings
    assert not orchestrator.finding_cooldowns


@pytest.mark.asyncio
async def test_load_agents(orchestrator, mock_agent):
    """Test loading agents from database."""
    # Mock database session
    mock_session = MagicMock()
    mock_session.query.return_value.filter_by.return_value.all.return_value = [
        AgentModel(
            name="TestAgent",
            package_name="test_agent_package",
            subscribed_topics=["logs.test"],
            enabled=True,
        )
    ]

    # Mock agent class
    mock_agent_class = MagicMock(return_value=mock_agent)

    with patch("opmas.orchestrator.get_db_session", return_value=mock_session), patch(
        "opmas.orchestrator.__import__", return_value=MagicMock(TestAgentAgent=mock_agent_class)
    ):
        await orchestrator._load_agents()

        assert "TestAgent" in orchestrator.agents
        assert orchestrator.agents["TestAgent"] == mock_agent
        mock_agent.start.assert_called_once()


@pytest.mark.asyncio
async def test_subscribe_to_findings(orchestrator):
    """Test subscribing to findings topics."""
    await orchestrator._subscribe_to_findings()

    orchestrator.nats_client.subscribe.assert_called_once_with(
        "findings.>", cb=orchestrator._handle_finding
    )


@pytest.mark.asyncio
async def test_handle_finding(orchestrator, sample_finding):
    """Test handling a finding."""
    # Mock store and notify methods
    orchestrator._store_finding = AsyncMock()
    orchestrator._notify_finding = AsyncMock()

    # Create mock message
    mock_msg = MagicMock()
    mock_msg.data = sample_finding.to_json().encode()

    # Handle finding
    await orchestrator._handle_finding(mock_msg)

    # Verify finding was added to active findings
    assert sample_finding.resource_id in orchestrator.active_findings
    assert sample_finding in orchestrator.active_findings[sample_finding.resource_id]

    # Verify finding was stored and notified
    orchestrator._store_finding.assert_called_once_with(sample_finding)
    orchestrator._notify_finding.assert_called_once_with(sample_finding)


@pytest.mark.asyncio
async def test_store_finding(orchestrator, sample_finding):
    """Test storing a finding in the database."""
    # Mock database session
    mock_session = MagicMock()

    with patch("opmas.orchestrator.get_db_session", return_value=mock_session):
        await orchestrator._store_finding(sample_finding)

        # Verify finding was added to session
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

        # Verify finding details
        db_finding = mock_session.add.call_args[0][0]
        assert isinstance(db_finding, Finding)
        assert db_finding.finding_type == sample_finding.finding_type
        assert db_finding.agent_name == sample_finding.agent_name
        assert db_finding.resource_id == sample_finding.resource_id
        assert db_finding.severity == sample_finding.severity
        assert db_finding.message == sample_finding.message
        assert db_finding.details == sample_finding.details


@pytest.mark.asyncio
async def test_cleanup_task(orchestrator, sample_finding):
    """Test cleanup task."""
    # Add some findings
    resource_id = sample_finding.resource_id
    orchestrator.active_findings[resource_id] = [sample_finding]

    # Add some cooldowns
    finding_id = f"{sample_finding.finding_type}:{resource_id}"
    orchestrator.finding_cooldowns[finding_id] = time.time()

    # Run cleanup task once
    await orchestrator._cleanup_task()

    # Verify findings and cooldowns are still present (not old enough to clean up)
    assert resource_id in orchestrator.active_findings
    assert finding_id in orchestrator.finding_cooldowns

    # Make findings and cooldowns old enough to clean up
    sample_finding.timestamp = time.time() - orchestrator.finding_retention - 1
    orchestrator.finding_cooldowns[finding_id] = (
        time.time() - orchestrator.notification_cooldown - 1
    )

    # Run cleanup task again
    await orchestrator._cleanup_task()

    # Verify findings and cooldowns were cleaned up
    assert resource_id not in orchestrator.active_findings
    assert finding_id not in orchestrator.finding_cooldowns
