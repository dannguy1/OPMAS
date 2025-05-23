#!/usr/bin/env python3

"""Tests for the NetworkAgent class."""

import pytest
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from collections import deque

from opmas.agents.network_agent_package.agent import NetworkAgent
from opmas.data_models import ParsedLogEvent, AgentFinding

@pytest.fixture
def network_agent():
    """Create a NetworkAgent instance with a mock NATS client."""
    with patch('opmas.agents.network_agent_package.agent.BaseAgent.__init__') as mock_init:
        mock_init.return_value = None
        agent = NetworkAgent(
            agent_name="NetworkAgent",
            subscribed_topics=["logs.network"],
            findings_topic="findings.network"
        )
        agent.nats_client = AsyncMock()
        agent.publish_finding = AsyncMock()
        agent.agent_rules = {
            "ConnectivityIssues": {
                "enabled": True,
                "connectivity_patterns": [r"Connection failed: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 3,
                "severity": "High"
            },
            "BandwidthIssues": {
                "enabled": True,
                "bandwidth_patterns": [r"Bandwidth exceeded: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 3,
                "severity": "Medium"
            },
            "LatencyIssues": {
                "enabled": True,
                "latency_patterns": [r"High latency: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 3,
                "severity": "Medium"
            },
            "NetworkSecurityIssues": {
                "enabled": True,
                "security_patterns": [r"Security alert: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 1,
                "severity": "High"
            }
        }
        agent._initialize_state()
        return agent

@pytest.fixture
def connectivity_log_event():
    """Create a sample connectivity issue log event."""
    return ParsedLogEvent(
        event_id="test-conn-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Connection failed: timeout"
    )

@pytest.fixture
def bandwidth_log_event():
    """Create a sample bandwidth issue log event."""
    return ParsedLogEvent(
        event_id="test-bw-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Bandwidth exceeded: threshold_reached"
    )

@pytest.fixture
def latency_log_event():
    """Create a sample latency issue log event."""
    return ParsedLogEvent(
        event_id="test-lat-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="High latency: packet_loss"
    )

@pytest.fixture
def security_log_event():
    """Create a sample network security issue log event."""
    return ParsedLogEvent(
        event_id="test-sec-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Security alert: port_scan"
    )

def test_initialize_state(network_agent):
    """Test initialization of state variables."""
    assert isinstance(network_agent.connectivity_timestamps, dict)
    assert isinstance(network_agent.bandwidth_timestamps, dict)
    assert isinstance(network_agent.latency_timestamps, dict)
    assert isinstance(network_agent.security_timestamps, dict)
    
    assert isinstance(network_agent.recent_connectivity_findings, dict)
    assert isinstance(network_agent.recent_bandwidth_findings, dict)
    assert isinstance(network_agent.recent_latency_findings, dict)
    assert isinstance(network_agent.recent_security_findings, dict)

def test_compile_rule_patterns(network_agent):
    """Test compilation of rule patterns."""
    network_agent._compile_rule_patterns()
    
    assert "ConnectivityIssues" in network_agent.compiled_patterns
    assert "BandwidthIssues" in network_agent.compiled_patterns
    assert "LatencyIssues" in network_agent.compiled_patterns
    assert "NetworkSecurityIssues" in network_agent.compiled_patterns
    
    for rule_name, patterns in network_agent.compiled_patterns.items():
        assert len(patterns) > 0
        for pattern in patterns:
            assert hasattr(pattern, 'search')

@pytest.mark.asyncio
async def test_check_connectivity_issues(network_agent, connectivity_log_event):
    """Test detection of connectivity issues."""
    # Add multiple connectivity issues to trigger threshold
    for _ in range(3):
        await network_agent._check_connectivity_issues(connectivity_log_event)
    
    # Verify finding was published
    network_agent.publish_finding.assert_called_once()
    finding = network_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "ConnectivityIssues"
    assert finding.severity == "High"
    assert "timeout" in finding.message
    assert finding.details["connectivity_issues"] == ["timeout"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_check_bandwidth_issues(network_agent, bandwidth_log_event):
    """Test detection of bandwidth issues."""
    # Add multiple bandwidth issues to trigger threshold
    for _ in range(3):
        await network_agent._check_bandwidth_issues(bandwidth_log_event)
    
    # Verify finding was published
    network_agent.publish_finding.assert_called_once()
    finding = network_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "BandwidthIssues"
    assert finding.severity == "Medium"
    assert "threshold_reached" in finding.message
    assert finding.details["bandwidth_issues"] == ["threshold_reached"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_check_latency_issues(network_agent, latency_log_event):
    """Test detection of latency issues."""
    # Add multiple latency issues to trigger threshold
    for _ in range(3):
        await network_agent._check_latency_issues(latency_log_event)
    
    # Verify finding was published
    network_agent.publish_finding.assert_called_once()
    finding = network_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "LatencyIssues"
    assert finding.severity == "Medium"
    assert "packet_loss" in finding.message
    assert finding.details["latency_issues"] == ["packet_loss"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_check_network_security_issues(network_agent, security_log_event):
    """Test detection of network security issues."""
    await network_agent._check_network_security_issues(security_log_event)
    
    # Verify finding was published
    network_agent.publish_finding.assert_called_once()
    finding = network_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "NetworkSecurityIssues"
    assert finding.severity == "High"
    assert "port_scan" in finding.message
    assert finding.details["security_issues"] == ["port_scan"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_process_log_event(network_agent, connectivity_log_event):
    """Test processing of log events."""
    # Add multiple connectivity issues to trigger threshold
    for _ in range(3):
        await network_agent.process_log_event(connectivity_log_event)
    
    # Verify finding was published
    network_agent.publish_finding.assert_called_once()
    finding = network_agent.publish_finding.call_args[0][0]
    assert finding.finding_type == "ConnectivityIssues" 