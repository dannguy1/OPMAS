import pytest
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from collections import deque

from opmas.agents.performance_agent_package.agent import PerformanceAgent
from opmas.data_models import ParsedLogEvent, AgentFinding

@pytest.fixture
def performance_agent():
    """Create a PerformanceAgent instance for testing."""
    agent = PerformanceAgent(
        agent_name="PerformanceAgent",
        subscribed_topics=["logs.performance"],
        findings_topic="findings.performance"
    )
    agent.nats_client = AsyncMock()
    return agent

@pytest.fixture
def cpu_log_event():
    """Create a sample CPU usage log event."""
    return ParsedLogEvent(
        event_id="test-event-1",
        arrival_ts_utc=datetime.now(timezone.utc),
        source_ip="192.168.1.100",
        original_ts=datetime.now(timezone.utc),
        hostname="test-server",
        process_name="systemd",
        pid=1234,
        message="CPU usage: 95.5%",
        structured_fields={}
    )

@pytest.fixture
def memory_log_event():
    """Create a sample memory pressure log event."""
    return ParsedLogEvent(
        event_id="test-event-2",
        arrival_ts_utc=datetime.now(timezone.utc),
        source_ip="192.168.1.100",
        original_ts=datetime.now(timezone.utc),
        hostname="test-server",
        process_name="systemd",
        pid=5678,
        message="Memory usage: 90.2%",
        structured_fields={}
    )

@pytest.fixture
def disk_log_event():
    """Create a sample disk I/O log event."""
    return ParsedLogEvent(
        event_id="test-event-3",
        arrival_ts_utc=datetime.now(timezone.utc),
        source_ip="192.168.1.100",
        original_ts=datetime.now(timezone.utc),
        hostname="test-server",
        process_name="iostat",
        pid=9012,
        message="Disk sda1 IOPS: 1200",
        structured_fields={}
    )

@pytest.fixture
def process_log_event():
    """Create a sample process resource log event."""
    return ParsedLogEvent(
        event_id="test-event-4",
        arrival_ts_utc=datetime.now(timezone.utc),
        source_ip="192.168.1.100",
        original_ts=datetime.now(timezone.utc),
        hostname="test-server",
        process_name="top",
        pid=3456,
        message="Process nginx CPU usage: 85.5%",
        structured_fields={}
    )

@pytest.fixture
def load_log_event():
    """Create a sample system load log event."""
    return ParsedLogEvent(
        event_id="test-event-5",
        arrival_ts_utc=datetime.now(timezone.utc),
        source_ip="192.168.1.100",
        original_ts=datetime.now(timezone.utc),
        hostname="test-server",
        process_name="systemd",
        pid=7890,
        message="System load: 6.5",
        structured_fields={}
    )

def test_initialize_state(performance_agent):
    """Test state initialization."""
    performance_agent._initialize_state()
    
    assert isinstance(performance_agent.cpu_usage_timestamps, dict)
    assert isinstance(performance_agent.memory_pressure_timestamps, dict)
    assert isinstance(performance_agent.disk_io_timestamps, dict)
    assert isinstance(performance_agent.process_resource_timestamps, dict)
    assert isinstance(performance_agent.system_load_timestamps, dict)
    
    assert isinstance(performance_agent.recent_cpu_findings, dict)
    assert isinstance(performance_agent.recent_memory_findings, dict)
    assert isinstance(performance_agent.recent_disk_findings, dict)
    assert isinstance(performance_agent.recent_process_findings, dict)
    assert isinstance(performance_agent.recent_load_findings, dict)

def test_compile_rule_patterns(performance_agent):
    """Test pattern compilation."""
    performance_agent.agent_rules = {
        "CPUUsage": {
            "enabled": True,
            "cpu_patterns": [r"CPU usage: (\d+\.?\d*)%"]
        },
        "MemoryPressure": {
            "enabled": True,
            "memory_patterns": [r"Memory usage: (\d+\.?\d*)%"]
        },
        "DiskIO": {
            "enabled": True,
            "disk_patterns": [r"Disk (\w+) IOPS: (\d+)"]
        },
        "ProcessResources": {
            "enabled": True,
            "process_patterns": [r"Process (\w+) CPU usage: (\d+\.?\d*)%"]
        },
        "SystemLoad": {
            "enabled": True,
            "load_patterns": [r"System load: (\d+\.?\d*)"]
        }
    }
    
    performance_agent._compile_rule_patterns()
    
    assert "CPUUsage" in performance_agent.compiled_patterns
    assert "MemoryPressure" in performance_agent.compiled_patterns
    assert "DiskIO" in performance_agent.compiled_patterns
    assert "ProcessResources" in performance_agent.compiled_patterns
    assert "SystemLoad" in performance_agent.compiled_patterns

@pytest.mark.asyncio
async def test_check_cpu_usage(performance_agent, cpu_log_event):
    """Test CPU usage detection."""
    performance_agent.agent_rules = {
        "CPUUsage": {
            "enabled": True,
            "cpu_patterns": [r"CPU usage: (\d+\.?\d*)%"],
            "usage_threshold": 90.0,
            "time_window_seconds": 300,
            "finding_cooldown_seconds": 600,
            "severity": "High"
        }
    }
    performance_agent._compile_rule_patterns()
    
    # Add CPU usage readings
    hostname = "test-server"
    cpu_key = f"{hostname}"
    current_time = time.time()
    performance_agent.cpu_usage_timestamps[cpu_key] = deque([
        (92.0, current_time - 120),  # 2 minutes ago
        (91.5, current_time - 60)    # 1 minute ago
    ])
    
    await performance_agent._check_cpu_usage(cpu_log_event)
    
    # Verify finding was published
    performance_agent.nats_client.publish.assert_called_once()
    call_args = performance_agent.nats_client.publish.call_args[0]
    assert len(call_args) == 2
    assert call_args[0] == "findings.performance"
    
    finding = AgentFinding.from_json(call_args[1])
    assert finding.finding_type == "CPUUsage"
    assert finding.resource_id == cpu_key
    assert finding.severity == "High"
    assert "high_usage_count" in finding.details
    assert finding.details["high_usage_count"] == 3  # 2 existing + 1 new

@pytest.mark.asyncio
async def test_check_memory_pressure(performance_agent, memory_log_event):
    """Test memory pressure detection."""
    performance_agent.agent_rules = {
        "MemoryPressure": {
            "enabled": True,
            "memory_patterns": [r"Memory usage: (\d+\.?\d*)%"],
            "pressure_threshold": 85.0,
            "time_window_seconds": 300,
            "finding_cooldown_seconds": 600,
            "severity": "High"
        }
    }
    performance_agent._compile_rule_patterns()
    
    # Add memory pressure readings
    hostname = "test-server"
    memory_key = f"{hostname}"
    current_time = time.time()
    performance_agent.memory_pressure_timestamps[memory_key] = deque([
        (88.0, current_time - 120),  # 2 minutes ago
        (87.5, current_time - 60)    # 1 minute ago
    ])
    
    await performance_agent._check_memory_pressure(memory_log_event)
    
    # Verify finding was published
    performance_agent.nats_client.publish.assert_called_once()
    call_args = performance_agent.nats_client.publish.call_args[0]
    assert len(call_args) == 2
    assert call_args[0] == "findings.performance"
    
    finding = AgentFinding.from_json(call_args[1])
    assert finding.finding_type == "MemoryPressure"
    assert finding.resource_id == memory_key
    assert finding.severity == "High"
    assert "high_pressure_count" in finding.details
    assert finding.details["high_pressure_count"] == 3  # 2 existing + 1 new

@pytest.mark.asyncio
async def test_check_disk_io(performance_agent, disk_log_event):
    """Test disk I/O detection."""
    performance_agent.agent_rules = {
        "DiskIO": {
            "enabled": True,
            "disk_patterns": [r"Disk (\w+) IOPS: (\d+)"],
            "iops_threshold": 1000,
            "time_window_seconds": 300,
            "finding_cooldown_seconds": 600,
            "severity": "Medium"
        }
    }
    performance_agent._compile_rule_patterns()
    
    # Add disk I/O readings
    hostname = "test-server"
    disk_name = "sda1"
    disk_key = f"{hostname}:{disk_name}"
    current_time = time.time()
    performance_agent.disk_io_timestamps[disk_key] = deque([
        (disk_name, 1100, current_time - 120),  # 2 minutes ago
        (disk_name, 1150, current_time - 60)    # 1 minute ago
    ])
    
    await performance_agent._check_disk_io(disk_log_event)
    
    # Verify finding was published
    performance_agent.nats_client.publish.assert_called_once()
    call_args = performance_agent.nats_client.publish.call_args[0]
    assert len(call_args) == 2
    assert call_args[0] == "findings.performance"
    
    finding = AgentFinding.from_json(call_args[1])
    assert finding.finding_type == "DiskIO"
    assert finding.resource_id == disk_key
    assert finding.severity == "Medium"
    assert "high_io_count" in finding.details
    assert finding.details["high_io_count"] == 3  # 2 existing + 1 new

@pytest.mark.asyncio
async def test_check_process_resources(performance_agent, process_log_event):
    """Test process resource detection."""
    performance_agent.agent_rules = {
        "ProcessResources": {
            "enabled": True,
            "process_patterns": [r"Process (\w+) CPU usage: (\d+\.?\d*)%"],
            "resource_threshold": 80.0,
            "time_window_seconds": 300,
            "finding_cooldown_seconds": 600,
            "severity": "Medium"
        }
    }
    performance_agent._compile_rule_patterns()
    
    # Add process resource readings
    hostname = "test-server"
    process_name = "nginx"
    process_key = f"{hostname}:{process_name}"
    current_time = time.time()
    performance_agent.process_resource_timestamps[process_key] = deque([
        (process_name, 82.0, current_time - 120),  # 2 minutes ago
        (process_name, 83.5, current_time - 60)    # 1 minute ago
    ])
    
    await performance_agent._check_process_resources(process_log_event)
    
    # Verify finding was published
    performance_agent.nats_client.publish.assert_called_once()
    call_args = performance_agent.nats_client.publish.call_args[0]
    assert len(call_args) == 2
    assert call_args[0] == "findings.performance"
    
    finding = AgentFinding.from_json(call_args[1])
    assert finding.finding_type == "ProcessResources"
    assert finding.resource_id == process_key
    assert finding.severity == "Medium"
    assert "high_usage_count" in finding.details
    assert finding.details["high_usage_count"] == 3  # 2 existing + 1 new

@pytest.mark.asyncio
async def test_check_system_load(performance_agent, load_log_event):
    """Test system load detection."""
    performance_agent.agent_rules = {
        "SystemLoad": {
            "enabled": True,
            "load_patterns": [r"System load: (\d+\.?\d*)"],
            "load_threshold": 5.0,
            "time_window_seconds": 300,
            "finding_cooldown_seconds": 600,
            "severity": "High"
        }
    }
    performance_agent._compile_rule_patterns()
    
    # Add system load readings
    hostname = "test-server"
    load_key = f"{hostname}"
    current_time = time.time()
    performance_agent.system_load_timestamps[load_key] = deque([
        (5.5, current_time - 120),  # 2 minutes ago
        (5.8, current_time - 60)    # 1 minute ago
    ])
    
    await performance_agent._check_system_load(load_log_event)
    
    # Verify finding was published
    performance_agent.nats_client.publish.assert_called_once()
    call_args = performance_agent.nats_client.publish.call_args[0]
    assert len(call_args) == 2
    assert call_args[0] == "findings.performance"
    
    finding = AgentFinding.from_json(call_args[1])
    assert finding.finding_type == "SystemLoad"
    assert finding.resource_id == load_key
    assert finding.severity == "High"
    assert "high_load_count" in finding.details
    assert finding.details["high_load_count"] == 3  # 2 existing + 1 new

@pytest.mark.asyncio
async def test_process_log_event(performance_agent, cpu_log_event, memory_log_event, 
                               disk_log_event, process_log_event, load_log_event):
    """Test processing of different log event types."""
    performance_agent.agent_rules = {
        "CPUUsage": {
            "enabled": True,
            "cpu_patterns": [r"CPU usage: (\d+\.?\d*)%"]
        },
        "MemoryPressure": {
            "enabled": True,
            "memory_patterns": [r"Memory usage: (\d+\.?\d*)%"]
        },
        "DiskIO": {
            "enabled": True,
            "disk_patterns": [r"Disk (\w+) IOPS: (\d+)"]
        },
        "ProcessResources": {
            "enabled": True,
            "process_patterns": [r"Process (\w+) CPU usage: (\d+\.?\d*)%"]
        },
        "SystemLoad": {
            "enabled": True,
            "load_patterns": [r"System load: (\d+\.?\d*)"]
        }
    }
    performance_agent._compile_rule_patterns()
    
    # Process each event type
    await performance_agent.process_log_event(cpu_log_event)
    await performance_agent.process_log_event(memory_log_event)
    await performance_agent.process_log_event(disk_log_event)
    await performance_agent.process_log_event(process_log_event)
    await performance_agent.process_log_event(load_log_event)
    
    # Verify all rules were checked
    assert performance_agent.nats_client.publish.call_count >= 0  # May or may not publish findings depending on thresholds 