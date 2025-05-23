import pytest
import asyncio
from opmas.config import load_config
from opmas.agents.base_agent import BaseAgent

@pytest.fixture(autouse=True)
def setup_config():
    """Load configuration before each test."""
    load_config()

class TestAgent(BaseAgent):
    """Test implementation of BaseAgent for testing."""
    async def process_log_event(self, event):
        pass

@pytest.mark.asyncio
async def test_base_agent_initialization():
    """Test basic agent initialization."""
    agent = TestAgent(
        agent_name="TestAgent",
        subscribed_topics=["test.topic"],
        findings_topic="test.findings",
        load_rules_from_config=False  # Skip rule loading for basic test
    )
    assert agent.agent_name == "TestAgent"
    assert agent.subscribed_topics == ["test.topic"]
    assert agent.findings_topic == "test.findings"
    assert agent.queue_group == "TestAgent"  # Default to agent name 

@pytest.mark.asyncio
async def test_nats_connection():
    """Test NATS connection handling."""
    agent = TestAgent(
        agent_name="TestAgent",
        subscribed_topics=["test.topic"],
        findings_topic="test.findings",
        load_rules_from_config=False
    )
    
    # Test connection error handling
    agent.config['nats']['url'] = 'nats://nonexistent:4222'
    with pytest.raises(ConnectionError):
        await agent.connect()
    
    # Test successful connection (requires running NATS server)
    agent.config['nats']['url'] = 'nats://localhost:4222'
    try:
        await agent.connect()
        assert agent.nc is not None
        assert agent.js is not None
    finally:
        await agent.disconnect() 

@pytest.mark.asyncio
async def test_rule_loading_and_processing():
    """Test rule loading and event processing."""
    # Create agent with rule loading enabled
    agent = TestAgent(
        agent_name="TestAgent",
        subscribed_topics=["test.topic"],
        findings_topic="test.findings",
        load_rules_from_config=True
    )
    
    # Verify rules are loaded
    assert len(agent.rules) > 0, "No rules were loaded"
    
    # Test event processing
    test_event = {
        "timestamp": "2024-03-20T12:00:00Z",
        "source": "test_source",
        "message": "test message"
    }
    
    # Process event and check results
    result = await agent.process_log_event(test_event)
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "source" in result
    assert "message" in result 

@pytest.mark.asyncio
async def test_rule_matching_and_findings():
    """Test rule matching logic and findings generation."""
    agent = TestAgent(
        agent_name="TestAgent",
        subscribed_topics=["test.topic"],
        findings_topic="test.findings",
        load_rules_from_config=True
    )

    # Test event that should match a rule
    matching_event = {
        "timestamp": "2024-03-20T12:00:00Z",
        "source": "test_source",
        "severity": "error",
        "message": "Connection failed"
    }

    # Test event that shouldn't match any rules
    non_matching_event = {
        "timestamp": "2024-03-20T12:00:00Z",
        "source": "test_source",
        "severity": "info",
        "message": "Normal operation"
    }

    # Process events and check findings
    finding = await agent.process_log_event(matching_event)
    assert finding is not None
    assert "rule_id" in finding
    assert "severity" in finding
    assert finding["severity"] == "error"

    non_matching_finding = await agent.process_log_event(non_matching_event)
    assert non_matching_finding is None or "rule_id" not in non_matching_finding

@pytest.mark.asyncio
async def test_wan_connectivity_agent():
    """Integration test for WAN Connectivity Agent."""
    from opmas.agents.wan_connectivity_agent_package.agent import WANConnectivityAgent
    
    agent = WANConnectivityAgent()
    assert agent.agent_name == "WANConnectivityAgent"
    assert "wan.connectivity" in agent.subscribed_topics
    
    # Test WAN-specific event processing
    wan_event = {
        "timestamp": "2024-03-20T12:00:00Z",
        "source": "wan_interface",
        "status": "down",
        "message": "WAN interface disconnected"
    }
    
    finding = await agent.process_log_event(wan_event)
    assert finding is not None
    assert "wan_status" in finding
    assert finding["severity"] in ["warning", "error"]

@pytest.mark.asyncio
async def test_device_health_agent():
    """Integration test for Device Health Agent."""
    from opmas.agents.device_health_agent_package.agent import DeviceHealthAgent
    
    agent = DeviceHealthAgent()
    assert agent.agent_name == "DeviceHealthAgent"
    assert "device.health" in agent.subscribed_topics
    
    # Test health monitoring event
    health_event = {
        "timestamp": "2024-03-20T12:00:00Z",
        "source": "system_monitor",
        "cpu_usage": 95.0,
        "memory_usage": 85.0,
        "message": "High resource usage detected"
    }
    
    finding = await agent.process_log_event(health_event)
    assert finding is not None
    assert "resource_metrics" in finding
    assert finding["severity"] in ["warning", "error"]

@pytest.mark.asyncio
async def test_network_security_agent():
    """Integration test for Network Security Agent."""
    from opmas.agents.network_security_agent_package.agent import NetworkSecurityAgent
    
    agent = NetworkSecurityAgent()
    assert agent.agent_name == "NetworkSecurityAgent"
    assert "network.security" in agent.subscribed_topics
    
    # Test security event processing
    security_event = {
        "timestamp": "2024-03-20T12:00:00Z",
        "source": "firewall",
        "event_type": "intrusion_attempt",
        "src_ip": "192.168.1.100",
        "dest_ip": "10.0.0.1",
        "message": "Potential port scan detected"
    }
    
    finding = await agent.process_log_event(security_event)
    assert finding is not None
    assert "threat_type" in finding
    assert "source_ip" in finding
    assert finding["severity"] in ["warning", "error", "critical"]

@pytest.mark.asyncio
async def test_concurrent_event_processing():
    """Test concurrent event processing capabilities."""
    agent = TestAgent(
        agent_name="TestAgent",
        subscribed_topics=["test.topic"],
        findings_topic="test.findings",
        load_rules_from_config=True
    )
    
    # Create multiple test events
    events = [
        {
            "timestamp": f"2024-03-20T12:00:{i:02d}Z",
            "source": "test_source",
            "severity": "error" if i % 2 == 0 else "info",
            "message": f"Test message {i}"
        }
        for i in range(10)
    ]
    
    # Process events concurrently
    tasks = [agent.process_log_event(event) for event in events]
    findings = await asyncio.gather(*tasks)
    
    # Verify findings
    assert len(findings) == 10
    error_findings = [f for f in findings if f and f.get("severity") == "error"]
    assert len(error_findings) == 5  # Half of the events should generate error findings

@pytest.mark.asyncio
async def test_error_handling():
    """Test agent error handling capabilities."""
    agent = TestAgent(
        agent_name="TestAgent",
        subscribed_topics=["test.topic"],
        findings_topic="test.findings",
        load_rules_from_config=True
    )
    
    # Test with malformed event
    malformed_event = {
        "timestamp": "invalid_timestamp",
        "message": "Test message"
        # Missing required fields
    }
    
    # Should handle malformed event gracefully
    try:
        finding = await agent.process_log_event(malformed_event)
        assert finding is None or "error" in finding
    except Exception as e:
        pytest.fail(f"Agent should handle malformed events gracefully: {str(e)}")
    
    # Test with None event
    try:
        finding = await agent.process_log_event(None)
        assert finding is None
    except Exception as e:
        pytest.fail(f"Agent should handle None events gracefully: {str(e)}") 