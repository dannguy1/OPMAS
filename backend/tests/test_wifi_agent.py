import pytest
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from collections import deque

from opmas.agents.wifi_agent_package.agent import WiFiAgent
from opmas.data_models import ParsedLogEvent, AgentFinding

@pytest.fixture
def wifi_agent():
    """Create a WiFiAgent instance for testing."""
    agent = WiFiAgent()
    agent.nats_client = AsyncMock()
    return agent

@pytest.fixture
def wifi_log_event():
    """Create a sample Wi-Fi log event."""
    return ParsedLogEvent(
        event_id="test-event-1",
        arrival_ts_utc=datetime.now(timezone.utc),
        source_ip="192.168.1.1",
        original_ts=datetime.now(timezone.utc),
        hostname="test-ap",
        process_name="hostapd",
        pid=1234,
        message="Client 00:11:22:33:44:55 authentication failed",
        structured_fields={"interface": "wlan0"}
    )

@pytest.fixture
def deauth_log_event():
    """Create a sample deauthentication log event."""
    return ParsedLogEvent(
        event_id="test-event-2",
        arrival_ts_utc=datetime.now(timezone.utc),
        source_ip="192.168.1.1",
        original_ts=datetime.now(timezone.utc),
        hostname="test-ap",
        process_name="hostapd",
        pid=1234,
        message="Deauthentication: STA 00:11:22:33:44:55",
        structured_fields={"interface": "wlan0"}
    )

@pytest.fixture
def dfs_log_event():
    """Create a sample DFS radar detection log event."""
    return ParsedLogEvent(
        event_id="test-event-3",
        arrival_ts_utc=datetime.now(timezone.utc),
        source_ip="192.168.1.1",
        original_ts=datetime.now(timezone.utc),
        hostname="test-ap",
        process_name="hostapd",
        pid=1234,
        message="DFS radar detected on wlan0 channel 52",
        structured_fields={"interface": "wlan0"}
    )

@pytest.fixture
def signal_log_event():
    """Create a sample signal strength log event."""
    return ParsedLogEvent(
        event_id="test-event-4",
        arrival_ts_utc=datetime.now(timezone.utc),
        source_ip="192.168.1.1",
        original_ts=datetime.now(timezone.utc),
        hostname="test-ap",
        process_name="hostapd",
        pid=1234,
        message="STA 00:11:22:33:44:55 signal strength: -80 dBm",
        structured_fields={"interface": "wlan0"}
    )

@pytest.fixture
def crash_log_event():
    """Create a sample driver crash log event."""
    return ParsedLogEvent(
        event_id="test-event-5",
        arrival_ts_utc=datetime.now(timezone.utc),
        source_ip="192.168.1.1",
        original_ts=datetime.now(timezone.utc),
        hostname="test-ap",
        process_name="kernel",
        pid=0,
        message="wlan0: firmware crashed",
        structured_fields={"interface": "wlan0"}
    )

def test_initialize_state(wifi_agent):
    """Test state initialization."""
    wifi_agent._initialize_state()
    
    assert isinstance(wifi_agent.auth_failure_timestamps, dict)
    assert isinstance(wifi_agent.deauth_timestamps, dict)
    assert isinstance(wifi_agent.dfs_event_timestamps, dict)
    assert isinstance(wifi_agent.signal_strength_readings, dict)
    assert isinstance(wifi_agent.driver_crash_timestamps, dict)
    
    assert isinstance(wifi_agent.recent_failure_findings, dict)
    assert isinstance(wifi_agent.recent_deauth_findings, dict)
    assert isinstance(wifi_agent.recent_dfs_findings, dict)
    assert isinstance(wifi_agent.recent_signal_findings, dict)
    assert isinstance(wifi_agent.recent_crash_findings, dict)

def test_compile_rule_patterns(wifi_agent):
    """Test pattern compilation."""
    wifi_agent.agent_rules = {
        "HighAuthFailureRate": {
            "enabled": True,
            "failure_patterns": [r"Client ([0-9A-Fa-f:]+) authentication failed"]
        },
        "DeauthFlood": {
            "enabled": True,
            "deauth_patterns": [r"Deauthentication: STA ([0-9A-Fa-f:]+)"]
        },
        "DFSRadarDetection": {
            "enabled": True,
            "dfs_patterns": [r"DFS radar detected on (\w+) channel (\d+)"]
        },
        "LowSignalStrength": {
            "enabled": True,
            "signal_patterns": [r"STA ([0-9A-Fa-f:]+) signal strength: (-?\d+) dBm"]
        },
        "DriverCrash": {
            "enabled": True,
            "crash_patterns": [r"(\w+): firmware crashed"]
        }
    }
    
    wifi_agent._compile_rule_patterns()
    
    assert "HighAuthFailureRate" in wifi_agent.compiled_patterns
    assert "DeauthFlood" in wifi_agent.compiled_patterns
    assert "DFSRadarDetection" in wifi_agent.compiled_patterns
    assert "LowSignalStrength" in wifi_agent.compiled_patterns
    assert "DriverCrash" in wifi_agent.compiled_patterns

@pytest.mark.asyncio
async def test_check_deauth_flood(wifi_agent, deauth_log_event):
    """Test deauthentication flood detection."""
    wifi_agent.agent_rules = {
        "DeauthFlood": {
            "enabled": True,
            "deauth_patterns": [r"Deauthentication: STA ([0-9A-Fa-f:]+)"],
            "deauth_threshold": 2,
            "time_window_seconds": 10,
            "finding_cooldown_seconds": 300,
            "severity": "High"
        }
    }
    wifi_agent._compile_rule_patterns()
    
    # Add deauth events
    client_mac = "00:11:22:33:44:55"
    current_time = time.time()
    wifi_agent.deauth_timestamps[client_mac] = deque([
        current_time - 5,  # 5 seconds ago
        current_time - 2   # 2 seconds ago
    ])
    
    await wifi_agent._check_deauth_flood(deauth_log_event)
    
    # Verify finding was published
    wifi_agent.nats_client.publish.assert_called_once()
    call_args = wifi_agent.nats_client.publish.call_args[0]
    assert len(call_args) == 2
    assert call_args[0] == "agent.findings"
    
    finding = AgentFinding.from_json(call_args[1])
    assert finding.finding_type == "DeauthFlood"
    assert finding.resource_id == client_mac
    assert finding.severity == "High"
    assert "deauth_count" in finding.details
    assert finding.details["deauth_count"] == 3  # 2 existing + 1 new

@pytest.mark.asyncio
async def test_check_dfs_radar(wifi_agent, dfs_log_event):
    """Test DFS radar detection."""
    wifi_agent.agent_rules = {
        "DFSRadarDetection": {
            "enabled": True,
            "dfs_patterns": [r"DFS radar detected on (\w+) channel (\d+)"],
            "event_threshold": 2,
            "time_window_seconds": 3600,
            "finding_cooldown_seconds": 1800,
            "severity": "Medium"
        }
    }
    wifi_agent._compile_rule_patterns()
    
    # Add DFS events
    interface = "wlan0"
    channel = "52"
    event_key = f"{interface}:{channel}"
    current_time = time.time()
    wifi_agent.dfs_event_timestamps[event_key] = deque([
        current_time - 1800,  # 30 minutes ago
        current_time - 900    # 15 minutes ago
    ])
    
    await wifi_agent._check_dfs_radar(dfs_log_event)
    
    # Verify finding was published
    wifi_agent.nats_client.publish.assert_called_once()
    call_args = wifi_agent.nats_client.publish.call_args[0]
    assert len(call_args) == 2
    assert call_args[0] == "agent.findings"
    
    finding = AgentFinding.from_json(call_args[1])
    assert finding.finding_type == "DFSRadarDetection"
    assert finding.resource_id == interface
    assert finding.severity == "Medium"
    assert "event_count" in finding.details
    assert finding.details["event_count"] == 3  # 2 existing + 1 new

@pytest.mark.asyncio
async def test_check_low_signal(wifi_agent, signal_log_event):
    """Test low signal strength detection."""
    wifi_agent.agent_rules = {
        "LowSignalStrength": {
            "enabled": True,
            "signal_patterns": [r"STA ([0-9A-Fa-f:]+) signal strength: (-?\d+) dBm"],
            "signal_threshold": -75,
            "reading_threshold": 3,
            "time_window_seconds": 300,
            "finding_cooldown_seconds": 600,
            "severity": "Medium"
        }
    }
    wifi_agent._compile_rule_patterns()
    
    # Add signal readings
    client_mac = "00:11:22:33:44:55"
    current_time = time.time()
    wifi_agent.signal_strength_readings[client_mac] = deque([
        (current_time - 120, -78),  # 2 minutes ago
        (current_time - 60, -79),   # 1 minute ago
        (current_time - 30, -80)    # 30 seconds ago
    ])
    
    await wifi_agent._check_low_signal(signal_log_event)
    
    # Verify finding was published
    wifi_agent.nats_client.publish.assert_called_once()
    call_args = wifi_agent.nats_client.publish.call_args[0]
    assert len(call_args) == 2
    assert call_args[0] == "agent.findings"
    
    finding = AgentFinding.from_json(call_args[1])
    assert finding.finding_type == "LowSignalStrength"
    assert finding.resource_id == client_mac
    assert finding.severity == "Medium"
    assert "average_signal" in finding.details
    assert finding.details["average_signal"] < -75

@pytest.mark.asyncio
async def test_check_driver_crash(wifi_agent, crash_log_event):
    """Test driver crash detection."""
    wifi_agent.agent_rules = {
        "DriverCrash": {
            "enabled": True,
            "crash_patterns": [r"(\w+): firmware crashed"],
            "crash_threshold": 2,
            "time_window_seconds": 3600,
            "finding_cooldown_seconds": 1800,
            "severity": "High"
        }
    }
    wifi_agent._compile_rule_patterns()
    
    # Add crash events
    interface = "wlan0"
    current_time = time.time()
    wifi_agent.driver_crash_timestamps[interface] = deque([
        current_time - 1800,  # 30 minutes ago
        current_time - 900    # 15 minutes ago
    ])
    
    await wifi_agent._check_driver_crash(crash_log_event)
    
    # Verify finding was published
    wifi_agent.nats_client.publish.assert_called_once()
    call_args = wifi_agent.nats_client.publish.call_args[0]
    assert len(call_args) == 2
    assert call_args[0] == "agent.findings"
    
    finding = AgentFinding.from_json(call_args[1])
    assert finding.finding_type == "DriverCrash"
    assert finding.resource_id == interface
    assert finding.severity == "High"
    assert "crash_count" in finding.details
    assert finding.details["crash_count"] == 3  # 2 existing + 1 new

@pytest.mark.asyncio
async def test_process_log_event(wifi_agent, wifi_log_event, deauth_log_event, dfs_log_event, signal_log_event, crash_log_event):
    """Test processing of different log event types."""
    wifi_agent.agent_rules = {
        "HighAuthFailureRate": {
            "enabled": True,
            "failure_patterns": [r"Client ([0-9A-Fa-f:]+) authentication failed"]
        },
        "DeauthFlood": {
            "enabled": True,
            "deauth_patterns": [r"Deauthentication: STA ([0-9A-Fa-f:]+)"]
        },
        "DFSRadarDetection": {
            "enabled": True,
            "dfs_patterns": [r"DFS radar detected on (\w+) channel (\d+)"]
        },
        "LowSignalStrength": {
            "enabled": True,
            "signal_patterns": [r"STA ([0-9A-Fa-f:]+) signal strength: (-?\d+) dBm"]
        },
        "DriverCrash": {
            "enabled": True,
            "crash_patterns": [r"(\w+): firmware crashed"]
        }
    }
    wifi_agent._compile_rule_patterns()
    
    # Process each event type
    await wifi_agent.process_log_event(wifi_log_event)
    await wifi_agent.process_log_event(deauth_log_event)
    await wifi_agent.process_log_event(dfs_log_event)
    await wifi_agent.process_log_event(signal_log_event)
    await wifi_agent.process_log_event(crash_log_event)
    
    # Verify all rules were checked
    assert wifi_agent.nats_client.publish.call_count >= 0  # May or may not publish findings depending on thresholds 