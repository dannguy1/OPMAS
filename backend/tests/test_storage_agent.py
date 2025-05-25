#!/usr/bin/env python3

"""Tests for the StorageAgent class."""

import time
from collections import deque
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opmas.agents.storage_agent_package.agent import StorageAgent
from opmas.data_models import AgentFinding, ParsedLogEvent


@pytest.fixture
def storage_agent():
    """Create a StorageAgent instance with a mock NATS client."""
    with patch("opmas.agents.storage_agent_package.agent.BaseAgent.__init__") as mock_init:
        mock_init.return_value = None
        agent = StorageAgent(
            agent_name="StorageAgent",
            subscribed_topics=["logs.storage"],
            findings_topic="findings.storage",
        )
        agent.nats_client = AsyncMock()
        agent.publish_finding = AsyncMock()
        agent.agent_rules = {
            "DiskSpaceIssues": {
                "enabled": True,
                "disk_patterns": [r"Disk space low: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 3,
                "severity": "High",
            },
            "IOIssues": {
                "enabled": True,
                "io_patterns": [r"I/O error: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 3,
                "severity": "Medium",
            },
            "FileSystemIssues": {
                "enabled": True,
                "fs_patterns": [r"File system error: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 1,
                "severity": "High",
            },
            "ConfigurationIssues": {
                "enabled": True,
                "config_patterns": [r"Storage config error: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 1,
                "severity": "Medium",
            },
        }
        agent._initialize_state()
        return agent


@pytest.fixture
def disk_log_event():
    """Create a sample disk space issue log event."""
    return ParsedLogEvent(
        event_id="test-disk-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Disk space low: /var",
    )


@pytest.fixture
def io_log_event():
    """Create a sample I/O issue log event."""
    return ParsedLogEvent(
        event_id="test-io-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="I/O error: timeout",
    )


@pytest.fixture
def fs_log_event():
    """Create a sample file system issue log event."""
    return ParsedLogEvent(
        event_id="test-fs-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="File system error: corruption",
    )


@pytest.fixture
def config_log_event():
    """Create a sample configuration issue log event."""
    return ParsedLogEvent(
        event_id="test-config-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Storage config error: invalid_mount",
    )


def test_initialize_state(storage_agent):
    """Test initialization of state variables."""
    assert isinstance(storage_agent.disk_timestamps, dict)
    assert isinstance(storage_agent.io_timestamps, dict)
    assert isinstance(storage_agent.fs_timestamps, dict)
    assert isinstance(storage_agent.config_timestamps, dict)

    assert isinstance(storage_agent.recent_disk_findings, dict)
    assert isinstance(storage_agent.recent_io_findings, dict)
    assert isinstance(storage_agent.recent_fs_findings, dict)
    assert isinstance(storage_agent.recent_config_findings, dict)


def test_compile_rule_patterns(storage_agent):
    """Test compilation of rule patterns."""
    storage_agent._compile_rule_patterns()

    assert "DiskSpaceIssues" in storage_agent.compiled_patterns
    assert "IOIssues" in storage_agent.compiled_patterns
    assert "FileSystemIssues" in storage_agent.compiled_patterns
    assert "ConfigurationIssues" in storage_agent.compiled_patterns

    for rule_name, patterns in storage_agent.compiled_patterns.items():
        assert len(patterns) > 0
        for pattern in patterns:
            assert hasattr(pattern, "search")


@pytest.mark.asyncio
async def test_check_disk_space_issues(storage_agent, disk_log_event):
    """Test detection of disk space issues."""
    # Add multiple disk issues to trigger threshold
    for _ in range(3):
        await storage_agent._check_disk_space_issues(disk_log_event)

    # Verify finding was published
    storage_agent.publish_finding.assert_called_once()
    finding = storage_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "DiskSpaceIssues"
    assert finding.severity == "High"
    assert "/var" in finding.message
    assert finding.details["disk_issues"] == ["/var"]
    assert finding.details["hostname"] == "test-host"


@pytest.mark.asyncio
async def test_check_io_issues(storage_agent, io_log_event):
    """Test detection of I/O issues."""
    # Add multiple I/O issues to trigger threshold
    for _ in range(3):
        await storage_agent._check_io_issues(io_log_event)

    # Verify finding was published
    storage_agent.publish_finding.assert_called_once()
    finding = storage_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "IOIssues"
    assert finding.severity == "Medium"
    assert "timeout" in finding.message
    assert finding.details["io_issues"] == ["timeout"]
    assert finding.details["hostname"] == "test-host"


@pytest.mark.asyncio
async def test_check_file_system_issues(storage_agent, fs_log_event):
    """Test detection of file system issues."""
    await storage_agent._check_file_system_issues(fs_log_event)

    # Verify finding was published
    storage_agent.publish_finding.assert_called_once()
    finding = storage_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "FileSystemIssues"
    assert finding.severity == "High"
    assert "corruption" in finding.message
    assert finding.details["fs_issues"] == ["corruption"]
    assert finding.details["hostname"] == "test-host"


@pytest.mark.asyncio
async def test_check_configuration_issues(storage_agent, config_log_event):
    """Test detection of configuration issues."""
    await storage_agent._check_configuration_issues(config_log_event)

    # Verify finding was published
    storage_agent.publish_finding.assert_called_once()
    finding = storage_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "ConfigurationIssues"
    assert finding.severity == "Medium"
    assert "invalid_mount" in finding.message
    assert finding.details["config_issues"] == ["invalid_mount"]
    assert finding.details["hostname"] == "test-host"


@pytest.mark.asyncio
async def test_process_log_event(storage_agent, disk_log_event):
    """Test processing of log events."""
    # Add multiple disk issues to trigger threshold
    for _ in range(3):
        await storage_agent.process_log_event(disk_log_event)

    # Verify finding was published
    storage_agent.publish_finding.assert_called_once()
    finding = storage_agent.publish_finding.call_args[0][0]
    assert finding.finding_type == "DiskSpaceIssues"
