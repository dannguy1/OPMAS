"""Test agent management schemas."""

from datetime import datetime
from uuid import UUID, uuid4

import pytest
from opmas_mgmt_api.schemas.agents import (
    AgentConfig,
    AgentCreate,
    AgentDiscovery,
    AgentList,
    AgentResponse,
    AgentStatus,
    AgentUpdate,
)
from pydantic import ValidationError


@pytest.fixture
def test_agent_create():
    """Create a test agent creation payload."""
    return {
        "name": "test-agent",
        "agent_type": "wifi",
        "hostname": "test-agent.local",
        "ip_address": "192.168.1.100",
        "port": 8080,
        "status": "online",
        "enabled": True,
        "metadata": {"version": "1.0.0"},
        "config": {"scan_interval": 300},
    }


@pytest.fixture
def test_agent_update():
    """Create a test agent update payload."""
    return {"name": "updated-agent", "status": "offline", "metadata": {"version": "1.1.0"}}


@pytest.fixture
def test_agent_response():
    """Create a test agent response payload."""
    return {
        "id": str(uuid4()),
        "name": "test-agent",
        "agent_type": "wifi",
        "hostname": "test-agent.local",
        "ip_address": "192.168.1.100",
        "port": 8080,
        "status": "online",
        "enabled": True,
        "metadata": {"version": "1.0.0"},
        "config": {"scan_interval": 300},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "last_seen": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def test_agent_list():
    """Create a test agent list payload."""
    return {
        "items": [
            {
                "id": str(uuid4()),
                "name": "test-agent-1",
                "agent_type": "wifi",
                "hostname": "test-agent-1.local",
                "ip_address": "192.168.1.101",
                "port": 8080,
                "status": "online",
                "enabled": True,
                "metadata": {"version": "1.0.0"},
                "config": {"scan_interval": 300},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "last_seen": datetime.utcnow().isoformat(),
            },
            {
                "id": str(uuid4()),
                "name": "test-agent-2",
                "agent_type": "wifi",
                "hostname": "test-agent-2.local",
                "ip_address": "192.168.1.102",
                "port": 8080,
                "status": "offline",
                "enabled": True,
                "metadata": {"version": "1.0.0"},
                "config": {"scan_interval": 300},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "last_seen": datetime.utcnow().isoformat(),
            },
        ],
        "total": 2,
        "skip": 0,
        "limit": 100,
    }


@pytest.fixture
def test_agent_status():
    """Create a test agent status payload."""
    return {
        "status": "online",
        "last_seen": datetime.utcnow().isoformat(),
        "device_status": "healthy",
        "details": {"reason": "startup"},
    }


@pytest.fixture
def test_agent_config():
    """Create a test agent config payload."""
    return {
        "config": {"scan_interval": 300},
        "version": "1.0.0",
        "last_updated": datetime.utcnow().isoformat(),
        "metadata": {"updated_by": "system"},
    }


@pytest.fixture
def test_agent_discovery():
    """Create a test agent discovery payload."""
    return {
        "id": str(uuid4()),
        "name": "test-agent",
        "agent_type": "wifi",
        "hostname": "test-agent.local",
        "ip_address": "192.168.1.100",
        "port": 8080,
        "status": "online",
        "metadata": {"version": "1.0.0"},
    }


def test_agent_create_validation(test_agent_create):
    """Test agent creation validation."""
    agent = AgentCreate(**test_agent_create)
    assert agent.name == test_agent_create["name"]
    assert agent.agent_type == test_agent_create["agent_type"]
    assert agent.hostname == test_agent_create["hostname"]
    assert agent.ip_address == test_agent_create["ip_address"]
    assert agent.port == test_agent_create["port"]
    assert agent.status == test_agent_create["status"]
    assert agent.enabled == test_agent_create["enabled"]
    assert agent.metadata == test_agent_create["metadata"]
    assert agent.config == test_agent_create["config"]


def test_agent_create_validation_invalid():
    """Test agent creation validation with invalid data."""
    invalid_data = {
        "name": "",  # Invalid empty name
        "agent_type": "invalid",  # Invalid agent type
        "hostname": "test-agent.local",
        "ip_address": "invalid-ip",  # Invalid IP address
        "port": 70000,  # Invalid port
    }
    with pytest.raises(ValidationError):
        AgentCreate(**invalid_data)


def test_agent_update_validation(test_agent_update):
    """Test agent update validation."""
    agent = AgentUpdate(**test_agent_update)
    assert agent.name == test_agent_update["name"]
    assert agent.status == test_agent_update["status"]
    assert agent.metadata == test_agent_update["metadata"]


def test_agent_update_validation_invalid():
    """Test agent update validation with invalid data."""
    invalid_data = {"agent_type": "invalid", "port": 70000}  # Invalid agent type  # Invalid port
    with pytest.raises(ValidationError):
        AgentUpdate(**invalid_data)


def test_agent_response_validation(test_agent_response):
    """Test agent response validation."""
    agent = AgentResponse(**test_agent_response)
    assert agent.id == UUID(test_agent_response["id"])
    assert agent.name == test_agent_response["name"]
    assert agent.agent_type == test_agent_response["agent_type"]
    assert agent.hostname == test_agent_response["hostname"]
    assert agent.ip_address == test_agent_response["ip_address"]
    assert agent.port == test_agent_response["port"]
    assert agent.status == test_agent_response["status"]
    assert agent.enabled == test_agent_response["enabled"]
    assert agent.metadata == test_agent_response["metadata"]
    assert agent.config == test_agent_response["config"]


def test_agent_list_validation(test_agent_list):
    """Test agent list validation."""
    agent_list = AgentList(**test_agent_list)
    assert len(agent_list.items) == len(test_agent_list["items"])
    assert agent_list.total == test_agent_list["total"]
    assert agent_list.skip == test_agent_list["skip"]
    assert agent_list.limit == test_agent_list["limit"]


def test_agent_status_validation(test_agent_status):
    """Test agent status validation."""
    status = AgentStatus(**test_agent_status)
    assert status.status == test_agent_status["status"]
    assert status.device_status == test_agent_status["device_status"]
    assert status.details == test_agent_status["details"]


def test_agent_status_validation_invalid():
    """Test agent status validation with invalid data."""
    invalid_data = {"status": "invalid_status"}  # Invalid status
    with pytest.raises(ValidationError):
        AgentStatus(**invalid_data)


def test_agent_config_validation(test_agent_config):
    """Test agent config validation."""
    config = AgentConfig(**test_agent_config)
    assert config.config == test_agent_config["config"]
    assert config.version == test_agent_config["version"]
    assert config.metadata == test_agent_config["metadata"]


def test_agent_discovery_validation(test_agent_discovery):
    """Test agent discovery validation."""
    discovery = AgentDiscovery(**test_agent_discovery)
    assert discovery.id == UUID(test_agent_discovery["id"])
    assert discovery.name == test_agent_discovery["name"]
    assert discovery.agent_type == test_agent_discovery["agent_type"]
    assert discovery.hostname == test_agent_discovery["hostname"]
    assert discovery.ip_address == test_agent_discovery["ip_address"]
    assert discovery.port == test_agent_discovery["port"]
    assert discovery.status == test_agent_discovery["status"]
    assert discovery.metadata == test_agent_discovery["metadata"]


def test_agent_discovery_validation_invalid():
    """Test agent discovery validation with invalid data."""
    invalid_data = {
        "id": str(uuid4()),
        "name": "test-agent",
        "agent_type": "invalid",  # Invalid agent type
        "hostname": "test-agent.local",
        "ip_address": "invalid-ip",  # Invalid IP address
        "port": 70000,  # Invalid port
    }
    with pytest.raises(ValidationError):
        AgentDiscovery(**invalid_data)
