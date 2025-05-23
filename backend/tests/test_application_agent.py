#!/usr/bin/env python3

"""Tests for the ApplicationAgent class."""

import pytest
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from collections import deque

from opmas.agents.application_agent_package.agent import ApplicationAgent
from opmas.data_models import ParsedLogEvent, AgentFinding

@pytest.fixture
def application_agent():
    """Create an ApplicationAgent instance with a mock NATS client."""
    with patch('opmas.agents.application_agent_package.agent.BaseAgent.__init__') as mock_init:
        mock_init.return_value = None
        agent = ApplicationAgent(
            agent_name="ApplicationAgent",
            subscribed_topics=["logs.application"],
            findings_topic="findings.application"
        )
        agent.nats_client = AsyncMock()
        agent.publish_finding = AsyncMock()
        agent.agent_rules = {
            "ApplicationErrors": {
                "enabled": True,
                "error_patterns": [r"Application error: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 3,
                "severity": "High"
            },
            "PerformanceDegradation": {
                "enabled": True,
                "performance_patterns": [r"Performance issue: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 3,
                "severity": "Medium"
            },
            "DatabaseIssues": {
                "enabled": True,
                "database_patterns": [r"Database error: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 3,
                "severity": "High"
            },
            "APIFailures": {
                "enabled": True,
                "api_patterns": [r"API failure: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 3,
                "severity": "High"
            },
            "ConfigurationIssues": {
                "enabled": True,
                "config_patterns": [r"Configuration error: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 1,
                "severity": "Medium"
            }
        }
        agent._initialize_state()
        return agent

@pytest.fixture
def error_log_event():
    """Create a sample application error log event."""
    return ParsedLogEvent(
        event_id="test-error-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Application error: null_pointer"
    )

@pytest.fixture
def performance_log_event():
    """Create a sample performance degradation log event."""
    return ParsedLogEvent(
        event_id="test-performance-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Performance issue: high_latency"
    )

@pytest.fixture
def database_log_event():
    """Create a sample database issue log event."""
    return ParsedLogEvent(
        event_id="test-database-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Database error: connection_timeout"
    )

@pytest.fixture
def api_log_event():
    """Create a sample API failure log event."""
    return ParsedLogEvent(
        event_id="test-api-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="API failure: rate_limit"
    )

@pytest.fixture
def config_log_event():
    """Create a sample configuration issue log event."""
    return ParsedLogEvent(
        event_id="test-config-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Configuration error: invalid_setting"
    )

def test_initialize_state(application_agent):
    """Test initialization of state variables."""
    assert isinstance(application_agent.error_timestamps, dict)
    assert isinstance(application_agent.performance_timestamps, dict)
    assert isinstance(application_agent.database_timestamps, dict)
    assert isinstance(application_agent.api_timestamps, dict)
    assert isinstance(application_agent.config_timestamps, dict)
    
    assert isinstance(application_agent.recent_error_findings, dict)
    assert isinstance(application_agent.recent_performance_findings, dict)
    assert isinstance(application_agent.recent_database_findings, dict)
    assert isinstance(application_agent.recent_api_findings, dict)
    assert isinstance(application_agent.recent_config_findings, dict)

def test_compile_rule_patterns(application_agent):
    """Test compilation of rule patterns."""
    application_agent._compile_rule_patterns()
    
    assert "ApplicationErrors" in application_agent.compiled_patterns
    assert "PerformanceDegradation" in application_agent.compiled_patterns
    assert "DatabaseIssues" in application_agent.compiled_patterns
    assert "APIFailures" in application_agent.compiled_patterns
    assert "ConfigurationIssues" in application_agent.compiled_patterns
    
    for rule_name, patterns in application_agent.compiled_patterns.items():
        assert len(patterns) > 0
        for pattern in patterns:
            assert hasattr(pattern, 'search')

@pytest.mark.asyncio
async def test_check_application_errors(application_agent, error_log_event):
    """Test detection of application errors."""
    # Add multiple errors to trigger threshold
    for _ in range(3):
        await application_agent._check_application_errors(error_log_event)
    
    # Verify finding was published
    application_agent.publish_finding.assert_called_once()
    finding = application_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "ApplicationErrors"
    assert finding.severity == "High"
    assert "null_pointer" in finding.message
    assert finding.details["error_types"] == ["null_pointer"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_check_performance_degradation(application_agent, performance_log_event):
    """Test detection of performance degradation."""
    # Add multiple performance issues to trigger threshold
    for _ in range(3):
        await application_agent._check_performance_degradation(performance_log_event)
    
    # Verify finding was published
    application_agent.publish_finding.assert_called_once()
    finding = application_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "PerformanceDegradation"
    assert finding.severity == "Medium"
    assert "high_latency" in finding.message
    assert finding.details["performance_issues"] == ["high_latency"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_check_database_issues(application_agent, database_log_event):
    """Test detection of database issues."""
    # Add multiple database issues to trigger threshold
    for _ in range(3):
        await application_agent._check_database_issues(database_log_event)
    
    # Verify finding was published
    application_agent.publish_finding.assert_called_once()
    finding = application_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "DatabaseIssues"
    assert finding.severity == "High"
    assert "connection_timeout" in finding.message
    assert finding.details["database_issues"] == ["connection_timeout"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_check_api_failures(application_agent, api_log_event):
    """Test detection of API failures."""
    # Add multiple API failures to trigger threshold
    for _ in range(3):
        await application_agent._check_api_failures(api_log_event)
    
    # Verify finding was published
    application_agent.publish_finding.assert_called_once()
    finding = application_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "APIFailures"
    assert finding.severity == "High"
    assert "rate_limit" in finding.message
    assert finding.details["api_issues"] == ["rate_limit"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_check_configuration_issues(application_agent, config_log_event):
    """Test detection of configuration issues."""
    await application_agent._check_configuration_issues(config_log_event)
    
    # Verify finding was published
    application_agent.publish_finding.assert_called_once()
    finding = application_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "ConfigurationIssues"
    assert finding.severity == "Medium"
    assert "invalid_setting" in finding.message
    assert finding.details["config_issues"] == ["invalid_setting"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_process_log_event(application_agent, error_log_event):
    """Test processing of log events."""
    # Add multiple errors to trigger threshold
    for _ in range(3):
        await application_agent.process_log_event(error_log_event)
    
    # Verify finding was published
    application_agent.publish_finding.assert_called_once()
    finding = application_agent.publish_finding.call_args[0][0]
    assert finding.finding_type == "ApplicationErrors" 