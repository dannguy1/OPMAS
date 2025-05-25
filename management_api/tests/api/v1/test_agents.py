"""Test agent management endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from opmas_mgmt_api.main import app
from opmas_mgmt_api.models.agents import Agent, AgentConfigHistory, AgentStatusHistory
from opmas_mgmt_api.schemas.agents import AgentConfig, AgentCreate, AgentStatus, AgentUpdate
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def test_agent():
    """Create a test agent."""
    return Agent(
        id=uuid4(),
        name="test-agent",
        agent_type="wifi",
        hostname="test-agent.local",
        ip_address="192.168.1.100",
        port=8080,
        status="online",
        enabled=True,
        metadata={"version": "1.0.0"},
        config={"scan_interval": 300},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_seen=datetime.utcnow(),
    )


@pytest.fixture
def test_agent_create():
    """Create a test agent creation payload."""
    return AgentCreate(
        name="test-agent",
        agent_type="wifi",
        hostname="test-agent.local",
        ip_address="192.168.1.100",
        port=8080,
        status="online",
        enabled=True,
        metadata={"version": "1.0.0"},
        config={"scan_interval": 300},
    )


@pytest.fixture
def test_agent_update():
    """Create a test agent update payload."""
    return AgentUpdate(name="updated-agent", status="offline", metadata={"version": "1.1.0"})


@pytest.fixture
def mock_db_session(test_agent):
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = test_agent
    session.execute.return_value.scalar_one_or_none.return_value = test_agent
    return session


@pytest.fixture
def mock_nats():
    """Create a mock NATS manager."""
    nats = AsyncMock()
    return nats


@pytest.fixture
def client(mock_db_session, mock_nats):
    """Create a test client with mocked dependencies."""
    app.dependency_overrides = {"get_db": lambda: mock_db_session, "get_nats": lambda: mock_nats}
    return TestClient(app)


def test_list_agents(client, test_agent):
    """Test listing agents."""
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data


def test_create_agent(client, test_agent_create):
    """Test creating an agent."""
    response = client.post("/api/v1/agents", json=test_agent_create.dict())
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == test_agent_create.name
    assert data["agent_type"] == test_agent_create.agent_type
    assert data["hostname"] == test_agent_create.hostname
    assert data["ip_address"] == str(test_agent_create.ip_address)


def test_get_agent(client, test_agent):
    """Test getting an agent."""
    response = client.get(f"/api/v1/agents/{test_agent.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_agent.id)
    assert data["name"] == test_agent.name


def test_update_agent(client, test_agent, test_agent_update):
    """Test updating an agent."""
    response = client.patch(
        f"/api/v1/agents/{test_agent.id}", json=test_agent_update.dict(exclude_unset=True)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_agent_update.name
    assert data["status"] == test_agent_update.status


def test_delete_agent(client, test_agent):
    """Test deleting an agent."""
    response = client.delete(f"/api/v1/agents/{test_agent.id}")
    assert response.status_code == 204


def test_get_agent_status(client, test_agent):
    """Test getting agent status."""
    response = client.get(f"/api/v1/agents/{test_agent.id}/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "last_seen" in data
    assert "device_status" in data
    assert "details" in data


def test_update_agent_status(client, test_agent):
    """Test updating agent status."""
    status_data = {"status": "offline", "details": {"reason": "maintenance"}}
    response = client.patch(f"/api/v1/agents/{test_agent.id}/status", json=status_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == status_data["status"]


def test_get_agent_config(client, test_agent):
    """Test getting agent configuration."""
    response = client.get(f"/api/v1/agents/{test_agent.id}/config")
    assert response.status_code == 200
    data = response.json()
    assert "config" in data
    assert "version" in data
    assert "last_updated" in data


def test_update_agent_config(client, test_agent):
    """Test updating agent configuration."""
    config_data = {
        "config": {"scan_interval": 600},
        "version": "1.1.0",
        "metadata": {"updated_by": "test"},
    }
    response = client.patch(f"/api/v1/agents/{test_agent.id}/config", json=config_data)
    assert response.status_code == 200
    data = response.json()
    assert data["config"] == config_data["config"]


def test_discover_agents(client):
    """Test agent discovery."""
    response = client.post("/api/v1/agents/discover")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_agents_with_filters(client, test_agent):
    """Test listing agents with filters."""
    response = client.get(
        "/api/v1/agents", params={"agent_type": "wifi", "status": "online", "enabled": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_create_agent_validation(client):
    """Test agent creation validation."""
    invalid_agent = {
        "name": "",  # Invalid empty name
        "agent_type": "invalid",  # Invalid agent type
        "hostname": "test-agent.local",
        "ip_address": "invalid-ip",  # Invalid IP address
        "port": 70000,  # Invalid port
    }
    response = client.post("/api/v1/agents", json=invalid_agent)
    assert response.status_code == 422


def test_update_agent_validation(client, test_agent):
    """Test agent update validation."""
    invalid_update = {"agent_type": "invalid", "port": 70000}  # Invalid agent type  # Invalid port
    response = client.patch(f"/api/v1/agents/{test_agent.id}", json=invalid_update)
    assert response.status_code == 422


def test_get_nonexistent_agent(client):
    """Test getting a nonexistent agent."""
    response = client.get(f"/api/v1/agents/{uuid4()}")
    assert response.status_code == 404


def test_update_nonexistent_agent(client, test_agent_update):
    """Test updating a nonexistent agent."""
    response = client.patch(
        f"/api/v1/agents/{uuid4()}", json=test_agent_update.dict(exclude_unset=True)
    )
    assert response.status_code == 404


def test_delete_nonexistent_agent(client):
    """Test deleting a nonexistent agent."""
    response = client.delete(f"/api/v1/agents/{uuid4()}")
    assert response.status_code == 404
