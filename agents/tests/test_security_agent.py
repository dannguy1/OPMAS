"""Tests for the security agent."""

import pytest
from datetime import datetime
from opmas.agents.security.security_agent import SecurityAgent

@pytest.fixture
def agent_config():
    """Sample agent configuration."""
    return {
        "rules": [
            {
                "id": "test-rule-1",
                "type": "file_permission",
                "severity": "high",
                "description": "Test rule",
                "parameters": {
                    "paths": ["/tmp"],
                    "max_permissions": 0o644
                }
            }
        ]
    }

@pytest.fixture
def security_agent(agent_config):
    """Create a security agent instance."""
    return SecurityAgent("test-agent-1", agent_config)

@pytest.mark.asyncio
async def test_agent_initialization(security_agent):
    """Test agent initialization."""
    assert security_agent.agent_id == "test-agent-1"
    assert security_agent.status == "initialized"
    assert len(security_agent.rules) == 1
    assert len(security_agent.findings) == 0

@pytest.mark.asyncio
async def test_agent_start_stop(security_agent):
    """Test agent start and stop."""
    # Start agent
    await security_agent.start()
    assert security_agent.status == "running"
    
    # Stop agent
    await security_agent.stop()
    assert security_agent.status == "stopped"

@pytest.mark.asyncio
async def test_agent_metrics(security_agent):
    """Test agent metrics collection."""
    metrics = await security_agent.collect_metrics()
    assert "status" in metrics
    assert "last_heartbeat" in metrics
    assert "uptime" in metrics
    assert "findings_count" in metrics
    assert "rules_count" in metrics

@pytest.mark.asyncio
async def test_agent_commands(security_agent):
    """Test agent command handling."""
    # Test status command
    response = await security_agent.handle_command("status")
    assert response["status"] == "success"
    assert "data" in response
    
    # Test check_rules command
    response = await security_agent.handle_command("check_rules")
    assert response["status"] == "success"
    assert "findings" in response["data"]
    assert "rules" in response["data"]
    
    # Test unknown command
    response = await security_agent.handle_command("unknown")
    assert response["status"] == "error" 