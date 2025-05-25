import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from opmas.management_api.auth import create_access_token
from opmas.management_api.database import get_db
from opmas.management_api.main import app
from opmas.management_api.models import User, UserRole

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    # Create tables
    from opmas.management_api.database import Base

    Base.metadata.create_all(bind=engine)
    yield
    # Clean up
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest.fixture
def client(db_session):
    """Create a test client with the test database session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def admin_token():
    """Create an access token for an admin user."""
    return create_access_token({"sub": "admin@example.com", "role": UserRole.ADMIN})


@pytest.fixture
def user_token():
    """Create an access token for a regular user."""
    return create_access_token({"sub": "user@example.com", "role": UserRole.USER})


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


def test_device_management():
    # Create device
    device_data = {
        "hostname": "test-device",
        "ip_address": "192.168.1.1",
        "device_type": "router",
        "configuration": {"vendor": "cisco"},
    }
    response = client.post("/api/v1/devices", json=device_data)
    assert response.status_code == 200
    device_id = response.json()["id"]

    # Get device
    response = client.get(f"/api/v1/devices/{device_id}")
    assert response.status_code == 200
    assert response.json()["hostname"] == "test-device"

    # Update device
    update_data = {"status": "active"}
    response = client.put(f"/api/v1/devices/{device_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["status"] == "active"

    # Delete device
    response = client.delete(f"/api/v1/devices/{device_id}")
    assert response.status_code == 200


def test_create_agent(client, admin_token):
    """Test creating a new agent."""
    response = client.post(
        "/api/v1/agents",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test-agent",
            "type": "system",
            "config": {"host": "localhost", "port": 8080},
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-agent"
    assert data["type"] == "system"
    assert data["config"]["host"] == "localhost"
    assert data["config"]["port"] == 8080


def test_get_agent(client, admin_token):
    """Test retrieving an agent."""
    # First create an agent
    create_response = client.post(
        "/api/v1/agents",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test-agent",
            "type": "system",
            "config": {"host": "localhost", "port": 8080},
        },
    )
    agent_id = create_response.json()["id"]

    # Then retrieve it
    response = client.get(
        f"/api/v1/agents/{agent_id}", headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == agent_id
    assert data["name"] == "test-agent"


def test_update_agent(client, admin_token):
    """Test updating an agent."""
    # First create an agent
    create_response = client.post(
        "/api/v1/agents",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test-agent",
            "type": "system",
            "config": {"host": "localhost", "port": 8080},
        },
    )
    agent_id = create_response.json()["id"]

    # Then update it
    response = client.put(
        f"/api/v1/agents/{agent_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "updated-agent", "config": {"host": "new-host", "port": 9090}},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == agent_id
    assert data["name"] == "updated-agent"
    assert data["config"]["host"] == "new-host"
    assert data["config"]["port"] == 9090


def test_delete_agent(client, admin_token):
    """Test deleting an agent."""
    # First create an agent
    create_response = client.post(
        "/api/v1/agents",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test-agent",
            "type": "system",
            "config": {"host": "localhost", "port": 8080},
        },
    )
    agent_id = create_response.json()["id"]

    # Then delete it
    response = client.delete(
        f"/api/v1/agents/{agent_id}", headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 204

    # Verify it's gone
    get_response = client.get(
        f"/api/v1/agents/{agent_id}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_response.status_code == 404


def test_list_agents(client, admin_token):
    """Test listing all agents."""
    # Create multiple agents
    for i in range(3):
        client.post(
            "/api/v1/agents",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": f"test-agent-{i}",
                "type": "system",
                "config": {"host": "localhost", "port": 8080 + i},
            },
        )

    # List all agents
    response = client.get("/api/v1/agents", headers={"Authorization": f"Bearer {admin_token}"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(agent["name"].startswith("test-agent-") for agent in data)


def test_unauthorized_access(client):
    """Test unauthorized access to protected endpoints."""
    # Try to create an agent without token
    response = client.post(
        "/api/v1/agents",
        json={
            "name": "test-agent",
            "type": "system",
            "config": {"host": "localhost", "port": 8080},
        },
    )
    assert response.status_code == 401


def test_user_permissions(client, user_token):
    """Test user permissions for agent management."""
    # Try to create an agent with user token
    response = client.post(
        "/api/v1/agents",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "name": "test-agent",
            "type": "system",
            "config": {"host": "localhost", "port": 8080},
        },
    )
    assert response.status_code == 403


def test_agent_rule_management(client, admin_token):
    """Test managing agent rules."""
    # First create an agent
    create_response = client.post(
        "/api/v1/agents",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test-agent",
            "type": "system",
            "config": {"host": "localhost", "port": 8080},
        },
    )
    agent_id = create_response.json()["id"]

    # Add a rule
    rule = {
        "name": "high-cpu",
        "condition": "cpu_usage > 80",
        "action": "restart_service",
        "severity": "warning",
    }

    response = client.post(
        f"/api/v1/agents/{agent_id}/rules",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=rule,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == rule["name"]
    assert data["condition"] == rule["condition"]

    # Get agent rules
    response = client.get(
        f"/api/v1/agents/{agent_id}/rules", headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == rule["name"]


def test_playbook_management():
    # Create playbook
    playbook_data = {
        "name": "test-playbook",
        "description": "Test playbook",
        "steps": [{"name": "step1", "action": "test_action"}],
    }
    response = client.post("/api/v1/playbooks", json=playbook_data)
    assert response.status_code == 200
    playbook_id = response.json()["id"]

    # Get playbook
    response = client.get(f"/api/v1/playbooks/{playbook_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "test-playbook"

    # Update playbook
    update_data = {"is_active": False}
    response = client.put(f"/api/v1/playbooks/{playbook_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Delete playbook
    response = client.delete(f"/api/v1/playbooks/{playbook_id}")
    assert response.status_code == 200


def test_rule_management():
    # Create rule
    rule_data = {
        "name": "test-rule",
        "description": "Test rule",
        "condition": {"type": "equals", "value": "test"},
        "action": {"type": "alert", "message": "Test alert"},
    }
    response = client.post("/api/v1/rules", json=rule_data)
    assert response.status_code == 200
    rule_id = response.json()["id"]

    # Get rule
    response = client.get(f"/api/v1/rules/{rule_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "test-rule"

    # Update rule
    update_data = {"is_active": False}
    response = client.put(f"/api/v1/rules/{rule_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Delete rule
    response = client.delete(f"/api/v1/rules/{rule_id}")
    assert response.status_code == 200


def test_error_handling():
    # Test invalid device creation
    invalid_device = {
        "hostname": "test-device",
        "ip_address": "invalid-ip",  # Invalid IP
        "device_type": "router",
    }
    response = client.post("/api/v1/devices", json=invalid_device)
    assert response.status_code == 400

    # Test non-existent resource
    response = client.get("/api/v1/devices/999")
    assert response.status_code == 404

    # Test invalid update
    response = client.put("/api/v1/devices/999", json={"status": "active"})
    assert response.status_code == 404


def test_list_endpoints():
    # Test device listing
    response = client.get("/api/v1/devices")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Test agent listing
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Test playbook listing
    response = client.get("/api/v1/playbooks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Test rule listing
    response = client.get("/api/v1/rules")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
