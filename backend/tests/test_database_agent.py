#!/usr/bin/env python3

"""Tests for the DatabaseAgent class."""

import pytest
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from collections import deque

from opmas.agents.database_agent_package.agent import DatabaseAgent
from opmas.data_models import ParsedLogEvent, AgentFinding

@pytest.fixture
def database_agent():
    """Create a DatabaseAgent instance with a mock NATS client."""
    with patch('opmas.agents.database_agent_package.agent.BaseAgent.__init__') as mock_init:
        mock_init.return_value = None
        agent = DatabaseAgent(
            agent_name="DatabaseAgent",
            subscribed_topics=["logs.database"],
            findings_topic="findings.database"
        )
        agent.nats_client = AsyncMock()
        agent.publish_finding = AsyncMock()
        agent.agent_rules = {
            "ConnectionIssues": {
                "enabled": True,
                "connection_patterns": [r"Connection failed: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 3,
                "severity": "High"
            },
            "QueryPerformanceIssues": {
                "enabled": True,
                "query_patterns": [r"Slow query: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 3,
                "severity": "Medium"
            },
            "DataIntegrityIssues": {
                "enabled": True,
                "integrity_patterns": [r"Data corruption: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 1,
                "severity": "High"
            },
            "ConfigurationIssues": {
                "enabled": True,
                "config_patterns": [r"Invalid config: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 1,
                "severity": "Medium"
            }
        }
        agent._initialize_state()
        return agent

@pytest.fixture
def connection_log_event():
    """Create a sample connection issue log event."""
    return ParsedLogEvent(
        event_id="test-conn-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Connection failed: timeout"
    )

@pytest.fixture
def query_log_event():
    """Create a sample query performance issue log event."""
    return ParsedLogEvent(
        event_id="test-query-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Slow query: missing_index"
    )

@pytest.fixture
def integrity_log_event():
    """Create a sample data integrity issue log event."""
    return ParsedLogEvent(
        event_id="test-int-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Data corruption: checksum_mismatch"
    )

@pytest.fixture
def config_log_event():
    """Create a sample configuration issue log event."""
    return ParsedLogEvent(
        event_id="test-config-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Invalid config: max_connections"
    )

def test_initialize_state(database_agent):
    """Test initialization of state variables."""
    assert isinstance(database_agent.connection_timestamps, dict)
    assert isinstance(database_agent.query_timestamps, dict)
    assert isinstance(database_agent.integrity_timestamps, dict)
    assert isinstance(database_agent.config_timestamps, dict)
    
    assert isinstance(database_agent.recent_connection_findings, dict)
    assert isinstance(database_agent.recent_query_findings, dict)
    assert isinstance(database_agent.recent_integrity_findings, dict)
    assert isinstance(database_agent.recent_config_findings, dict)

def test_compile_rule_patterns(database_agent):
    """Test compilation of rule patterns."""
    database_agent._compile_rule_patterns()
    
    assert "ConnectionIssues" in database_agent.compiled_patterns
    assert "QueryPerformanceIssues" in database_agent.compiled_patterns
    assert "DataIntegrityIssues" in database_agent.compiled_patterns
    assert "ConfigurationIssues" in database_agent.compiled_patterns
    
    for rule_name, patterns in database_agent.compiled_patterns.items():
        assert len(patterns) > 0
        for pattern in patterns:
            assert hasattr(pattern, 'search')

@pytest.mark.asyncio
async def test_check_connection_issues(database_agent, connection_log_event):
    """Test detection of connection issues."""
    # Add multiple connection issues to trigger threshold
    for _ in range(3):
        await database_agent._check_connection_issues(connection_log_event)
    
    # Verify finding was published
    database_agent.publish_finding.assert_called_once()
    finding = database_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "ConnectionIssues"
    assert finding.severity == "High"
    assert "timeout" in finding.message
    assert finding.details["connection_issues"] == ["timeout"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_check_query_performance_issues(database_agent, query_log_event):
    """Test detection of query performance issues."""
    # Add multiple query issues to trigger threshold
    for _ in range(3):
        await database_agent._check_query_performance_issues(query_log_event)
    
    # Verify finding was published
    database_agent.publish_finding.assert_called_once()
    finding = database_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "QueryPerformanceIssues"
    assert finding.severity == "Medium"
    assert "missing_index" in finding.message
    assert finding.details["query_issues"] == ["missing_index"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_check_data_integrity_issues(database_agent, integrity_log_event):
    """Test detection of data integrity issues."""
    await database_agent._check_data_integrity_issues(integrity_log_event)
    
    # Verify finding was published
    database_agent.publish_finding.assert_called_once()
    finding = database_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "DataIntegrityIssues"
    assert finding.severity == "High"
    assert "checksum_mismatch" in finding.message
    assert finding.details["integrity_issues"] == ["checksum_mismatch"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_check_configuration_issues(database_agent, config_log_event):
    """Test detection of configuration issues."""
    await database_agent._check_configuration_issues(config_log_event)
    
    # Verify finding was published
    database_agent.publish_finding.assert_called_once()
    finding = database_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "ConfigurationIssues"
    assert finding.severity == "Medium"
    assert "max_connections" in finding.message
    assert finding.details["config_issues"] == ["max_connections"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_process_log_event(database_agent, connection_log_event):
    """Test processing of log events."""
    # Add multiple connection issues to trigger threshold
    for _ in range(3):
        await database_agent.process_log_event(connection_log_event)
    
    # Verify finding was published
    database_agent.publish_finding.assert_called_once()
    finding = database_agent.publish_finding.call_args[0][0]
    assert finding.finding_type == "ConnectionIssues" 