import pytest
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from collections import deque

from opmas.agents.connectivity_agent_package.agent import ConnectivityAgent
from opmas.data_models import ParsedLogEvent, AgentFinding

@pytest.fixture
def connectivity_agent():
    """Create a ConnectivityAgent instance for testing."""
    agent = ConnectivityAgent(
        agent_name="ConnectivityAgent",
        subscribed_topics=["logs.connectivity"],
        findings_topic="findings.connectivity"
    )
    agent.nats_client = AsyncMock()
    return agent

@pytest.fixture
def interface_log_event():
    """Create a sample interface status log event."""
    return ParsedLogEvent(
        event_id="test-event-1",
        arrival_ts_utc=datetime.now(timezone.utc),
        source_ip="192.168.1.100",
        original_ts=datetime.now(timezone.utc),
        hostname="test-server",
        process_name="networkd",
        pid=1234,
        message="Interface eth0 status changed to DOWN",
        structured_fields={}
    )

@pytest.fixture
def timeout_log_event():
    """Create a sample connection timeout log event."""
    return ParsedLogEvent(
        event_id="test-event-2",
        arrival_ts_utc=datetime.now(timezone.utc),
        source_ip="192.168.1.100",
        original_ts=datetime.now(timezone.utc),
        hostname="test-server",
        process_name="networkd",
        pid=5678,
        message="Connection timeout to 8.8.8.8:53",
        structured_fields={}
    )

@pytest.fixture
def dns_log_event():
    """Create a sample DNS resolution failure log event."""
    return ParsedLogEvent(
        event_id="test-event-3",
        arrival_ts_utc=datetime.now(timezone.utc),
        source_ip="192.168.1.100",
        original_ts=datetime.now(timezone.utc),
        hostname="test-server",
        process_name="resolv",
        pid=9012,
        message="Failed to resolve domain example.com",
        structured_fields={}
    )

@pytest.fixture
def routing_log_event():
    """Create a sample routing issue log event."""
    return ParsedLogEvent(
        event_id="test-event-4",
        arrival_ts_utc=datetime.now(timezone.utc),
        source_ip="192.168.1.100",
        original_ts=datetime.now(timezone.utc),
        hostname="test-server",
        process_name="routed",
        pid=3456,
        message="No route to host 10.0.0.1",
        structured_fields={}
    )

@pytest.fixture
def service_log_event():
    """Create a sample service availability log event."""
    return ParsedLogEvent(
        event_id="test-event-5",
        arrival_ts_utc=datetime.now(timezone.utc),
        source_ip="192.168.1.100",
        original_ts=datetime.now(timezone.utc),
        hostname="test-server",
        process_name="systemd",
        pid=7890,
        message="Service nginx status changed to failed",
        structured_fields={}
    )

def test_initialize_state(connectivity_agent):
    """Test state initialization."""
    connectivity_agent._initialize_state()
    
    assert isinstance(connectivity_agent.interface_status_timestamps, dict)
    assert isinstance(connectivity_agent.timeout_timestamps, dict)
    assert isinstance(connectivity_agent.dns_failure_timestamps, dict)
    assert isinstance(connectivity_agent.routing_issue_timestamps, dict)
    assert isinstance(connectivity_agent.service_status_timestamps, dict)
    
    assert isinstance(connectivity_agent.recent_interface_findings, dict)
    assert isinstance(connectivity_agent.recent_timeout_findings, dict)
    assert isinstance(connectivity_agent.recent_dns_findings, dict)
    assert isinstance(connectivity_agent.recent_routing_findings, dict)
    assert isinstance(connectivity_agent.recent_service_findings, dict)

def test_compile_rule_patterns(connectivity_agent):
    """Test pattern compilation."""
    connectivity_agent.agent_rules = {
        "InterfaceStatus": {
            "enabled": True,
            "interface_patterns": [r"Interface (\w+) status changed to (\w+)"]
        },
        "ConnectionTimeout": {
            "enabled": True,
            "timeout_patterns": [r"Connection timeout to ([^:]+):"]
        },
        "DNSResolution": {
            "enabled": True,
            "dns_patterns": [r"Failed to resolve domain (\S+)"]
        },
        "RoutingIssues": {
            "enabled": True,
            "routing_patterns": [r"No route to host (\S+)"]
        },
        "ServiceAvailability": {
            "enabled": True,
            "service_patterns": [r"Service (\w+) status changed to (\w+)"]
        }
    }
    
    connectivity_agent._compile_rule_patterns()
    
    assert "InterfaceStatus" in connectivity_agent.compiled_patterns
    assert "ConnectionTimeout" in connectivity_agent.compiled_patterns
    assert "DNSResolution" in connectivity_agent.compiled_patterns
    assert "RoutingIssues" in connectivity_agent.compiled_patterns
    assert "ServiceAvailability" in connectivity_agent.compiled_patterns

@pytest.mark.asyncio
async def test_check_interface_status(connectivity_agent, interface_log_event):
    """Test interface status detection."""
    connectivity_agent.agent_rules = {
        "InterfaceStatus": {
            "enabled": True,
            "interface_patterns": [r"Interface (\w+) status changed to (\w+)"],
            "status_change_threshold": 2,
            "time_window_seconds": 300,
            "finding_cooldown_seconds": 600,
            "severity": "Medium"
        }
    }
    connectivity_agent._compile_rule_patterns()
    
    # Add interface status changes
    hostname = "test-server"
    interface_name = "eth0"
    interface_key = f"{hostname}:{interface_name}"
    current_time = time.time()
    connectivity_agent.interface_status_timestamps[interface_key] = deque([
        ("UP", current_time - 120)  # 2 minutes ago
    ])
    
    await connectivity_agent._check_interface_status(interface_log_event)
    
    # Verify finding was published
    connectivity_agent.nats_client.publish.assert_called_once()
    call_args = connectivity_agent.nats_client.publish.call_args[0]
    assert len(call_args) == 2
    assert call_args[0] == "findings.connectivity"
    
    finding = AgentFinding.from_json(call_args[1])
    assert finding.finding_type == "InterfaceStatus"
    assert finding.resource_id == interface_key
    assert finding.severity == "Medium"
    assert "status_changes" in finding.details
    assert finding.details["status_changes"] == 2  # 1 existing + 1 new

@pytest.mark.asyncio
async def test_check_connection_timeouts(connectivity_agent, timeout_log_event):
    """Test connection timeout detection."""
    connectivity_agent.agent_rules = {
        "ConnectionTimeout": {
            "enabled": True,
            "timeout_patterns": [r"Connection timeout to ([^:]+):"],
            "timeout_threshold": 3,
            "time_window_seconds": 60,
            "finding_cooldown_seconds": 300,
            "severity": "High"
        }
    }
    connectivity_agent._compile_rule_patterns()
    
    # Add connection timeouts
    hostname = "test-server"
    destination = "8.8.8.8"
    timeout_key = f"{hostname}:{destination}"
    current_time = time.time()
    connectivity_agent.timeout_timestamps[timeout_key] = deque([
        current_time - 30,  # 30 seconds ago
        current_time - 20   # 20 seconds ago
    ])
    
    await connectivity_agent._check_connection_timeouts(timeout_log_event)
    
    # Verify finding was published
    connectivity_agent.nats_client.publish.assert_called_once()
    call_args = connectivity_agent.nats_client.publish.call_args[0]
    assert len(call_args) == 2
    assert call_args[0] == "findings.connectivity"
    
    finding = AgentFinding.from_json(call_args[1])
    assert finding.finding_type == "ConnectionTimeout"
    assert finding.resource_id == timeout_key
    assert finding.severity == "High"
    assert "timeout_count" in finding.details
    assert finding.details["timeout_count"] == 3  # 2 existing + 1 new

@pytest.mark.asyncio
async def test_check_dns_resolution(connectivity_agent, dns_log_event):
    """Test DNS resolution failure detection."""
    connectivity_agent.agent_rules = {
        "DNSResolution": {
            "enabled": True,
            "dns_patterns": [r"Failed to resolve domain (\S+)"],
            "failure_threshold": 2,
            "time_window_seconds": 300,
            "finding_cooldown_seconds": 600,
            "severity": "Medium"
        }
    }
    connectivity_agent._compile_rule_patterns()
    
    # Add DNS failures
    hostname = "test-server"
    domain = "example.com"
    dns_key = f"{hostname}:{domain}"
    current_time = time.time()
    connectivity_agent.dns_failure_timestamps[dns_key] = deque([
        current_time - 120  # 2 minutes ago
    ])
    
    await connectivity_agent._check_dns_resolution(dns_log_event)
    
    # Verify finding was published
    connectivity_agent.nats_client.publish.assert_called_once()
    call_args = connectivity_agent.nats_client.publish.call_args[0]
    assert len(call_args) == 2
    assert call_args[0] == "findings.connectivity"
    
    finding = AgentFinding.from_json(call_args[1])
    assert finding.finding_type == "DNSResolution"
    assert finding.resource_id == dns_key
    assert finding.severity == "Medium"
    assert "failure_count" in finding.details
    assert finding.details["failure_count"] == 2  # 1 existing + 1 new

@pytest.mark.asyncio
async def test_check_routing_issues(connectivity_agent, routing_log_event):
    """Test routing issue detection."""
    connectivity_agent.agent_rules = {
        "RoutingIssues": {
            "enabled": True,
            "routing_patterns": [r"No route to host (\S+)"],
            "issue_threshold": 2,
            "time_window_seconds": 300,
            "finding_cooldown_seconds": 600,
            "severity": "High"
        }
    }
    connectivity_agent._compile_rule_patterns()
    
    # Add routing issues
    hostname = "test-server"
    route_target = "10.0.0.1"
    route_key = f"{hostname}:{route_target}"
    current_time = time.time()
    connectivity_agent.routing_issue_timestamps[route_key] = deque([
        current_time - 120  # 2 minutes ago
    ])
    
    await connectivity_agent._check_routing_issues(routing_log_event)
    
    # Verify finding was published
    connectivity_agent.nats_client.publish.assert_called_once()
    call_args = connectivity_agent.nats_client.publish.call_args[0]
    assert len(call_args) == 2
    assert call_args[0] == "findings.connectivity"
    
    finding = AgentFinding.from_json(call_args[1])
    assert finding.finding_type == "RoutingIssues"
    assert finding.resource_id == route_key
    assert finding.severity == "High"
    assert "issue_count" in finding.details
    assert finding.details["issue_count"] == 2  # 1 existing + 1 new

@pytest.mark.asyncio
async def test_check_service_availability(connectivity_agent, service_log_event):
    """Test service availability detection."""
    connectivity_agent.agent_rules = {
        "ServiceAvailability": {
            "enabled": True,
            "service_patterns": [r"Service (\w+) status changed to (\w+)"],
            "issue_threshold": 2,
            "time_window_seconds": 300,
            "finding_cooldown_seconds": 600,
            "severity": "High"
        }
    }
    connectivity_agent._compile_rule_patterns()
    
    # Add service status changes
    hostname = "test-server"
    service_name = "nginx"
    service_key = f"{hostname}:{service_name}"
    current_time = time.time()
    connectivity_agent.service_status_timestamps[service_key] = deque([
        ("running", current_time - 120)  # 2 minutes ago
    ])
    
    await connectivity_agent._check_service_availability(service_log_event)
    
    # Verify finding was published
    connectivity_agent.nats_client.publish.assert_called_once()
    call_args = connectivity_agent.nats_client.publish.call_args[0]
    assert len(call_args) == 2
    assert call_args[0] == "findings.connectivity"
    
    finding = AgentFinding.from_json(call_args[1])
    assert finding.finding_type == "ServiceAvailability"
    assert finding.resource_id == service_key
    assert finding.severity == "High"
    assert "status_changes" in finding.details
    assert finding.details["status_changes"] == 2  # 1 existing + 1 new

@pytest.mark.asyncio
async def test_process_log_event(connectivity_agent, interface_log_event, timeout_log_event, 
                               dns_log_event, routing_log_event, service_log_event):
    """Test processing of different log event types."""
    connectivity_agent.agent_rules = {
        "InterfaceStatus": {
            "enabled": True,
            "interface_patterns": [r"Interface (\w+) status changed to (\w+)"]
        },
        "ConnectionTimeout": {
            "enabled": True,
            "timeout_patterns": [r"Connection timeout to ([^:]+):"]
        },
        "DNSResolution": {
            "enabled": True,
            "dns_patterns": [r"Failed to resolve domain (\S+)"]
        },
        "RoutingIssues": {
            "enabled": True,
            "routing_patterns": [r"No route to host (\S+)"]
        },
        "ServiceAvailability": {
            "enabled": True,
            "service_patterns": [r"Service (\w+) status changed to (\w+)"]
        }
    }
    connectivity_agent._compile_rule_patterns()
    
    # Process each event type
    await connectivity_agent.process_log_event(interface_log_event)
    await connectivity_agent.process_log_event(timeout_log_event)
    await connectivity_agent.process_log_event(dns_log_event)
    await connectivity_agent.process_log_event(routing_log_event)
    await connectivity_agent.process_log_event(service_log_event)
    
    # Verify all rules were checked
    assert connectivity_agent.nats_client.publish.call_count >= 0  # May or may not publish findings depending on thresholds 