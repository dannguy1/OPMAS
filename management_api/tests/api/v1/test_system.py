"""Test system management API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from opmas_mgmt_api.main import app
from opmas_mgmt_api.schemas.system import (
    SystemConfig,
    SystemControl,
    SystemHealth,
    SystemMetrics,
    SystemStatus,
)


@pytest.fixture
def test_client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_system_service():
    """Create mock system service."""
    with patch("opmas_mgmt_api.api.v1.endpoints.system.SystemService") as mock:
        service = mock.return_value
        service.get_system_status = AsyncMock()
        service.get_system_health = AsyncMock()
        service.get_system_metrics = AsyncMock()
        service.get_system_config = AsyncMock()
        service.update_system_config = AsyncMock()
        service.control_system = AsyncMock()
        service.get_system_logs = AsyncMock()
        yield service


@pytest.fixture
def test_system_status():
    """Create test system status."""
    return {
        "status": "operational",
        "components": {"database": {"status": "connected"}, "nats": {"status": "connected"}},
        "metrics": {"components": {}, "system": {}, "timestamp": datetime.utcnow().isoformat()},
        "health": {
            "status": "healthy",
            "components": {"database": {"status": "healthy"}, "nats": {"status": "healthy"}},
            "timestamp": datetime.utcnow().isoformat(),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def test_system_health():
    """Create test system health."""
    return {
        "status": "healthy",
        "components": {
            "database": {"status": "healthy", "message": "Database connection is healthy"},
            "nats": {"status": "healthy", "message": "NATS connection is healthy"},
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def test_system_metrics():
    """Create test system metrics."""
    return {
        "components": {"database": {"connections": 10}, "nats": {"messages": 100}},
        "system": {"cpu": 0.5, "memory": 0.7},
        "timestamp": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def test_system_config():
    """Create test system config."""
    return {
        "version": "1.0.0",
        "components": {"database": {"pool_size": 10}, "nats": {"max_reconnects": 5}},
        "security": {"jwt_secret": "test-secret", "token_expiry": 3600},
        "logging": {"level": "INFO", "format": "json"},
        "timestamp": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def test_system_config_update():
    """Create test system config update."""
    return {"version": "1.0.1", "components": {"database": {"pool_size": 20}}}


@pytest.fixture
def test_system_control():
    """Create test system control."""
    return {"action": "restart", "status": "accepted", "timestamp": datetime.utcnow().isoformat()}


def test_get_system_status(test_client, mock_system_service, test_system_status):
    """Test getting system status."""
    mock_system_service.get_system_status.return_value = SystemStatus(**test_system_status)

    response = test_client.get("/api/v1/system/status")
    assert response.status_code == 200
    assert response.json() == test_system_status


def test_get_system_health(test_client, mock_system_service, test_system_health):
    """Test getting system health."""
    mock_system_service.get_system_health.return_value = SystemHealth(**test_system_health)

    response = test_client.get("/api/v1/system/health")
    assert response.status_code == 200
    assert response.json() == test_system_health


def test_get_system_metrics(test_client, mock_system_service, test_system_metrics):
    """Test getting system metrics."""
    mock_system_service.get_system_metrics.return_value = SystemMetrics(**test_system_metrics)

    response = test_client.get("/api/v1/system/metrics")
    assert response.status_code == 200
    assert response.json() == test_system_metrics


def test_get_system_config(test_client, mock_system_service, test_system_config):
    """Test getting system config."""
    mock_system_service.get_system_config.return_value = SystemConfig(**test_system_config)

    response = test_client.get("/api/v1/system/config")
    assert response.status_code == 200
    assert response.json() == test_system_config


def test_update_system_config(
    test_client, mock_system_service, test_system_config, test_system_config_update
):
    """Test updating system config."""
    mock_system_service.update_system_config.return_value = SystemConfig(**test_system_config)

    response = test_client.put("/api/v1/system/config", json=test_system_config_update)
    assert response.status_code == 200
    assert response.json() == test_system_config


def test_control_system(test_client, mock_system_service, test_system_control):
    """Test controlling system."""
    mock_system_service.control_system.return_value = SystemControl(**test_system_control)

    response = test_client.post("/api/v1/system/control", json={"action": "restart"})
    assert response.status_code == 200
    assert response.json() == test_system_control


def test_get_system_logs(test_client, mock_system_service):
    """Test getting system logs."""
    test_logs = [
        {"level": "INFO", "message": "Test log message", "timestamp": datetime.utcnow().isoformat()}
    ]
    mock_system_service.get_system_logs.return_value = test_logs

    response = test_client.get("/api/v1/system/logs")
    assert response.status_code == 200
    assert response.json() == test_logs


def test_control_system_invalid_action(test_client, mock_system_service):
    """Test controlling system with invalid action."""
    response = test_client.post("/api/v1/system/control", json={"action": "invalid"})
    assert response.status_code == 400
    assert "Invalid action" in response.json()["detail"]
