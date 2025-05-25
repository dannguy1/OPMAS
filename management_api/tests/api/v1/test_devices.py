"""Test device management endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from opmas_mgmt_api.main import app
from opmas_mgmt_api.models.devices import Device, DeviceStatusHistory
from opmas_mgmt_api.schemas.devices import DeviceCreate, DeviceStatus, DeviceUpdate
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def test_device():
    """Create a test device."""
    return Device(
        id=uuid4(),
        hostname="test-device",
        ip_address="192.168.1.1",
        device_type="router",
        model="test-model",
        firmware_version="1.0.0",
        status="online",
        enabled=True,
        metadata={"location": "test-location"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_seen=datetime.utcnow(),
    )


@pytest.fixture
def test_device_create():
    """Create a test device creation payload."""
    return DeviceCreate(
        hostname="test-device",
        ip_address="192.168.1.1",
        device_type="router",
        model="test-model",
        firmware_version="1.0.0",
        status="online",
        enabled=True,
        metadata={"location": "test-location"},
    )


@pytest.fixture
def test_device_update():
    """Create a test device update payload."""
    return DeviceUpdate(
        hostname="updated-device", status="offline", metadata={"location": "new-location"}
    )


@pytest.fixture
def mock_db_session(test_device):
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = test_device
    session.execute.return_value.scalar_one_or_none.return_value = test_device
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


def test_list_devices(client, test_device):
    """Test listing devices."""
    response = client.get("/api/v1/devices")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data


def test_create_device(client, test_device_create):
    """Test creating a device."""
    response = client.post("/api/v1/devices", json=test_device_create.dict())
    assert response.status_code == 201
    data = response.json()
    assert data["hostname"] == test_device_create.hostname
    assert data["ip_address"] == str(test_device_create.ip_address)
    assert data["device_type"] == test_device_create.device_type


def test_get_device(client, test_device):
    """Test getting a device."""
    response = client.get(f"/api/v1/devices/{test_device.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_device.id)
    assert data["hostname"] == test_device.hostname


def test_update_device(client, test_device, test_device_update):
    """Test updating a device."""
    response = client.patch(
        f"/api/v1/devices/{test_device.id}", json=test_device_update.dict(exclude_unset=True)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["hostname"] == test_device_update.hostname
    assert data["status"] == test_device_update.status


def test_delete_device(client, test_device):
    """Test deleting a device."""
    response = client.delete(f"/api/v1/devices/{test_device.id}")
    assert response.status_code == 204


def test_get_device_status(client, test_device):
    """Test getting device status."""
    response = client.get(f"/api/v1/devices/{test_device.id}/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "last_seen" in data
    assert "agent_status" in data
    assert "details" in data


def test_update_device_status(client, test_device):
    """Test updating device status."""
    status_data = {"status": "offline", "details": {"reason": "maintenance"}}
    response = client.patch(f"/api/v1/devices/{test_device.id}/status", json=status_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == status_data["status"]


def test_discover_devices(client):
    """Test device discovery."""
    response = client.post("/api/v1/devices/discover")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_devices_with_filters(client, test_device):
    """Test listing devices with filters."""
    response = client.get(
        "/api/v1/devices", params={"device_type": "router", "status": "online", "enabled": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_create_device_validation(client):
    """Test device creation validation."""
    invalid_device = {
        "hostname": "",  # Invalid empty hostname
        "ip_address": "invalid-ip",  # Invalid IP address
        "device_type": "router",
    }
    response = client.post("/api/v1/devices", json=invalid_device)
    assert response.status_code == 422


def test_update_device_validation(client, test_device):
    """Test device update validation."""
    invalid_update = {"ip_address": "invalid-ip"}  # Invalid IP address
    response = client.patch(f"/api/v1/devices/{test_device.id}", json=invalid_update)
    assert response.status_code == 422


def test_get_nonexistent_device(client):
    """Test getting a nonexistent device."""
    response = client.get(f"/api/v1/devices/{uuid4()}")
    assert response.status_code == 404


def test_update_nonexistent_device(client, test_device_update):
    """Test updating a nonexistent device."""
    response = client.patch(
        f"/api/v1/devices/{uuid4()}", json=test_device_update.dict(exclude_unset=True)
    )
    assert response.status_code == 404


def test_delete_nonexistent_device(client):
    """Test deleting a nonexistent device."""
    response = client.delete(f"/api/v1/devices/{uuid4()}")
    assert response.status_code == 404
