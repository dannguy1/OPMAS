#!/usr/bin/env python3

"""Tests for the SecurityAgent class."""

import pytest
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from collections import deque

from opmas.agents.security_agent_package.agent import SecurityAgent
from opmas.data_models import ParsedLogEvent, AgentFinding

@pytest.fixture
def security_agent():
    """Create a SecurityAgent instance with a mock NATS client."""
    with patch('opmas.agents.security_agent_package.agent.BaseAgent.__init__') as mock_init:
        mock_init.return_value = None
        agent = SecurityAgent(
            agent_name="SecurityAgent",
            subscribed_topics=["logs.security"],
            findings_topic="findings.security"
        )
        agent.nats_client = AsyncMock()
        agent.publish_finding = AsyncMock()
        agent.agent_rules = {
            "AuthenticationFailures": {
                "enabled": True,
                "auth_patterns": [r"Authentication failed: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 3,
                "severity": "High"
            },
            "SuspiciousAccess": {
                "enabled": True,
                "access_patterns": [r"Suspicious access: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 3,
                "severity": "High"
            },
            "SecurityBreach": {
                "enabled": True,
                "breach_patterns": [r"Security breach: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 1,
                "severity": "Critical"
            },
            "PolicyViolation": {
                "enabled": True,
                "policy_patterns": [r"Policy violation: (\w+)"],
                "time_window_seconds": 300,
                "finding_cooldown_seconds": 600,
                "occurrence_threshold": 1,
                "severity": "High"
            }
        }
        agent._initialize_state()
        return agent

@pytest.fixture
def auth_log_event():
    """Create a sample authentication failure log event."""
    return ParsedLogEvent(
        event_id="test-auth-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Authentication failed: invalid_credentials"
    )

@pytest.fixture
def access_log_event():
    """Create a sample suspicious access log event."""
    return ParsedLogEvent(
        event_id="test-access-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Suspicious access: unauthorized_port"
    )

@pytest.fixture
def breach_log_event():
    """Create a sample security breach log event."""
    return ParsedLogEvent(
        event_id="test-breach-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Security breach: data_exfiltration"
    )

@pytest.fixture
def policy_log_event():
    """Create a sample policy violation log event."""
    return ParsedLogEvent(
        event_id="test-policy-1",
        timestamp=datetime.now(),
        hostname="test-host",
        source_ip="192.168.1.1",
        message="Policy violation: weak_password"
    )

def test_initialize_state(security_agent):
    """Test initialization of state variables."""
    assert isinstance(security_agent.auth_timestamps, dict)
    assert isinstance(security_agent.access_timestamps, dict)
    assert isinstance(security_agent.breach_timestamps, dict)
    assert isinstance(security_agent.policy_timestamps, dict)
    
    assert isinstance(security_agent.recent_auth_findings, dict)
    assert isinstance(security_agent.recent_access_findings, dict)
    assert isinstance(security_agent.recent_breach_findings, dict)
    assert isinstance(security_agent.recent_policy_findings, dict)

def test_compile_rule_patterns(security_agent):
    """Test compilation of rule patterns."""
    security_agent._compile_rule_patterns()
    
    assert "AuthenticationFailures" in security_agent.compiled_patterns
    assert "SuspiciousAccess" in security_agent.compiled_patterns
    assert "SecurityBreach" in security_agent.compiled_patterns
    assert "PolicyViolation" in security_agent.compiled_patterns
    
    for rule_name, patterns in security_agent.compiled_patterns.items():
        assert len(patterns) > 0
        for pattern in patterns:
            assert hasattr(pattern, 'search')

@pytest.mark.asyncio
async def test_check_authentication_failures(security_agent, auth_log_event):
    """Test detection of authentication failures."""
    # Add multiple auth failures to trigger threshold
    for _ in range(3):
        await security_agent._check_authentication_failures(auth_log_event)
    
    # Verify finding was published
    security_agent.publish_finding.assert_called_once()
    finding = security_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "AuthenticationFailures"
    assert finding.severity == "High"
    assert "invalid_credentials" in finding.message
    assert finding.details["auth_issues"] == ["invalid_credentials"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_check_suspicious_access(security_agent, access_log_event):
    """Test detection of suspicious access."""
    # Add multiple access attempts to trigger threshold
    for _ in range(3):
        await security_agent._check_suspicious_access(access_log_event)
    
    # Verify finding was published
    security_agent.publish_finding.assert_called_once()
    finding = security_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "SuspiciousAccess"
    assert finding.severity == "High"
    assert "unauthorized_port" in finding.message
    assert finding.details["access_issues"] == ["unauthorized_port"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_check_security_breach(security_agent, breach_log_event):
    """Test detection of security breaches."""
    await security_agent._check_security_breach(breach_log_event)
    
    # Verify finding was published
    security_agent.publish_finding.assert_called_once()
    finding = security_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "SecurityBreach"
    assert finding.severity == "Critical"
    assert "data_exfiltration" in finding.message
    assert finding.details["breach_issues"] == ["data_exfiltration"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_check_policy_violation(security_agent, policy_log_event):
    """Test detection of policy violations."""
    await security_agent._check_policy_violation(policy_log_event)
    
    # Verify finding was published
    security_agent.publish_finding.assert_called_once()
    finding = security_agent.publish_finding.call_args[0][0]
    assert isinstance(finding, AgentFinding)
    assert finding.finding_type == "PolicyViolation"
    assert finding.severity == "High"
    assert "weak_password" in finding.message
    assert finding.details["policy_issues"] == ["weak_password"]
    assert finding.details["hostname"] == "test-host"

@pytest.mark.asyncio
async def test_process_log_event(security_agent, auth_log_event):
    """Test processing of log events."""
    # Add multiple auth failures to trigger threshold
    for _ in range(3):
        await security_agent.process_log_event(auth_log_event)
    
    # Verify finding was published
    security_agent.publish_finding.assert_called_once()
    finding = security_agent.publish_finding.call_args[0][0]
    assert finding.finding_type == "AuthenticationFailures" 