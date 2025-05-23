#!/usr/bin/env python3

"""Tests for the SystemAgent class."""

import pytest
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from collections import deque

from opmas.agents.system_agent_package.agent import SystemAgent
from opmas.data_models import ParsedLogEvent, AgentFinding

@pytest.fixture
def system_agent():
    """Create a SystemAgent instance with a mock NATS client."""
    with patch('opmas.agents.system_agent_package.agent.BaseAgent.__init__') as mock_init:
        mock_init.return_value = None
        agent = SystemAgent(
            agent_name="SystemAgent",
            subscribed_topics=["logs.system"],
            findings_topic="findings.system"
        )
        agent.nats_client = AsyncMock()
        agent.publish_finding = AsyncMock()
        agent.agent_rules = {
            "CPUIssues": {
                "enabled": True,
                "cpu_patterns": [r"CPU usage high: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 3,
                "severity": "High"
            },
            "MemoryIssues": {
                "enabled": True,
                "memory_patterns": [r"Memory usage high: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 3,
                "severity": "High"
            },
            "ProcessIssues": {
                "enabled": True,
                "process_patterns": [r"Process error: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 1,
                "severity": "High"
            },
            "ConfigurationIssues": {
                "enabled": True,
                "config_patterns": [r"System config error: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 1,
                "severity": "Medium"
            }
        }
        agent._initialize_state()
        return agent

@pytest.fixture
def cpu_log_event():
    """Create a sample CPU issue log event."""
    return ParsedLogEvent(
        event_id="test-cpu-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="CPU usage high: 95%"
    )

@pytest.fixture
def memory_log_event():
    """Create a sample memory issue log event."""
    return ParsedLogEvent(
        event_id="test-memory-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Memory usage high: 90%"
    )

@pytest.fixture
def process_log_event():
    """Create a sample process issue log event."""
    return ParsedLogEvent(
        event_id="test-process-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Process error: zombie"
    )

@pytest.fixture
def config_log_event():
    """Create a sample configuration issue log event."""
    return ParsedLogEvent(
        event_id="test-config-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="System config error: invalid_parameter"
    )

def test_initialize_state(system_agent):
    """Test initialization of state variables."""
    assert isinstance(system_agent.cpu_timestamps, dict)
    assert isinstance(system_agent.memory_timestamps, dict)
    assert isinstance(system_agent.process_timestamps, dict)
    assert isinstance(system_agent.config_timestamps, dict)
    
    assert isinstance(system_agent.recent_cpu_findings, dict)
    assert isinstance(system_agent.recent_memory_findings, dict)
    assert isinstance(system_agent.recent_process_findings, dict)
    assert isinstance(system_agent.recent_config_findings, dict)

def test_compile_rule_patterns(system_agent):
    """Test compilation of rule patterns."""
    system_agent._compile_rule_patterns()
    
    assert "CPUIssues" in system_agent.compiled_patterns
    assert "MemoryIssues" in system_agent.compiled_patterns
    assert "ProcessIssues" in system_agent.compiled_patterns
    assert "ConfigurationIssues" in system_agent.compiled_patterns
    
    for rule_name, patterns in system_agent.compiled_patterns.items():
        assert len(patterns) > 0
        for pattern in patterns:
            assert hasattr(pattern, 'search')

@pytest.mark.asyncio
async def test_check_cpu_issues(system_agent, cpu_log_event):
    """Test detection of CPU issues."""
    # Add multiple CPU issues to trigger threshold
    for _ in range(3):
        await system_agent._check_cpu_issues(cpu_log_event)
    
    # Verify finding was published
    system_agent.publish_finding.assert_called_once()
    finding = system_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "CPUIssues"
    assert finding.severity == "High"
    assert "95%" in finding.message
    assert finding.details["cpu_issues"] == ["95%"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_check_memory_issues(system_agent, memory_log_event):
    """Test detection of memory issues."""
    # Add multiple memory issues to trigger threshold
    for _ in range(3):
        await system_agent._check_memory_issues(memory_log_event)
    
    # Verify finding was published
    system_agent.publish_finding.assert_called_once()
    finding = system_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "MemoryIssues"
    assert finding.severity == "High"
    assert "90%" in finding.message
    assert finding.details["memory_issues"] == ["90%"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_check_process_issues(system_agent, process_log_event):
    """Test detection of process issues."""
    await system_agent._check_process_issues(process_log_event)
    
    # Verify finding was published
    system_agent.publish_finding.assert_called_once()
    finding = system_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "ProcessIssues"
    assert finding.severity == "High"
    assert "zombie" in finding.message
    assert finding.details["process_issues"] == ["zombie"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_check_configuration_issues(system_agent, config_log_event):
    """Test detection of configuration issues."""
    await system_agent._check_configuration_issues(config_log_event)
    
    # Verify finding was published
    system_agent.publish_finding.assert_called_once()
    finding = system_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "ConfigurationIssues"
    assert finding.severity == "Medium"
    assert "invalid_parameter" in finding.message
    assert finding.details["config_issues"] == ["invalid_parameter"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_process_log_event(system_agent, cpu_log_event):
    """Test processing of log events."""
    # Add multiple CPU issues to trigger threshold
    for _ in range(3):
        await system_agent.process_log_event(cpu_log_event)
    
    # Verify finding was published
    system_agent.publish_finding.assert_called_once()
    finding = system_agent.publish_finding.call_args[0][0]
    assert finding.finding_type == "CPUIssues" 