"""Test device management endpoints."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from opmas_mgmt_api.core.exceptions import OPMASException
from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.main import app
from opmas_mgmt_api.models.devices import Device
from opmas_mgmt_api.schemas.devices import DeviceCreate, DeviceStatus, DeviceUpdate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def test_device():
    """Create a test device."""
    return Device(
        id=uuid4(),
        hostname="test-device",
        ip_address="192.168.1.1",
        device_type="router",
        model="Test Model",
        firmware_version="1.0.0",
        status="active",
        enabled=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def mock_nats():
    """Create a mock NATS manager."""
    nats = AsyncMock(spec=NATSManager)
    nats.publish = AsyncMock()
    return nats


@pytest.fixture
def client(mock_nats):
    """Create a test client with mocked dependencies."""
    app.dependency_overrides[get_nats] = lambda: mock_nats
    return TestClient(app)


# Basic CRUD Tests
@pytest.mark.asyncio
async def test_list_devices_empty(client, db_session):
    """Test listing devices when database is empty."""
    response = client.get("/api/v1/devices")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_devices_with_filters(client, test_device, db_session):
    """Test listing devices with various filters."""
    db_session.add(test_device)
    await db_session.commit()

    # Test device_type filter
    response = client.get("/api/v1/devices?device_type=router")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1

    # Test status filter
    response = client.get("/api/v1/devices?status=active")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1

    # Test enabled filter
    response = client.get("/api/v1/devices?enabled=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1

    # Test pagination
    response = client.get("/api/v1/devices?skip=0&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["skip"] == 0
    assert data["limit"] == 1


@pytest.mark.asyncio
async def test_create_device_validation(client, db_session):
    """Test device creation validation."""
    # Test invalid IP address
    invalid_data = {
        "hostname": "invalid-device",
        "ip_address": "invalid-ip",
        "device_type": "router",
    }
    response = client.post("/api/v1/devices", json=invalid_data)
    assert response.status_code == 422

    # Test missing required fields
    invalid_data = {"hostname": "invalid-device"}
    response = client.post("/api/v1/devices", json=invalid_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_device_duplicate(client, test_device, db_session):
    """Test creating device with duplicate IP."""
    db_session.add(test_device)
    await db_session.commit()

    duplicate_data = {
        "hostname": "duplicate-device",
        "ip_address": test_device.ip_address,
        "device_type": "router",
    }
    response = client.post("/api/v1/devices", json=duplicate_data)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_device_partial(client, test_device, db_session):
    """Test partial device update."""
    db_session.add(test_device)
    await db_session.commit()

    update_data = {"hostname": "updated-hostname"}
    response = client.put(f"/api/v1/devices/{test_device.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["hostname"] == update_data["hostname"]
    assert data["ip_address"] == test_device.ip_address  # Unchanged


@pytest.mark.asyncio
async def test_update_device_not_found(client):
    """Test updating non-existent device."""
    update_data = {"hostname": "updated-hostname"}
    response = client.put(f"/api/v1/devices/{uuid4()}", json=update_data)
    assert response.status_code == 404


# Device Status Tests
@pytest.mark.asyncio
async def test_device_status_transitions(client, test_device, db_session):
    """Test device status transitions."""
    db_session.add(test_device)
    await db_session.commit()

    # Test status update
    status_data = {"status": "maintenance", "details": {"reason": "scheduled maintenance"}}
    response = client.put(f"/api/v1/devices/{test_device.id}/status", json=status_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == status_data["status"]

    # Verify status in device details
    response = client.get(f"/api/v1/devices/{test_device.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == status_data["status"]


# Device Discovery Tests
@pytest.mark.asyncio
async def test_discover_devices_invalid_network(client):
    """Test device discovery with invalid network."""
    response = client.post("/api/v1/devices/discover?network=invalid-network")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_discover_devices_timeout(client, mock_nats):
    """Test device discovery timeout handling."""
    with patch("opmas_mgmt_api.services.devices.DeviceService.discover_devices") as mock_discover:
        mock_discover.side_effect = asyncio.TimeoutError()
        response = client.post("/api/v1/devices/discover?network=192.168.1.0/24")
        assert response.status_code == 503


# Device Metrics Tests
@pytest.mark.asyncio
async def test_get_device_metrics_unavailable(client, test_device, db_session):
    """Test getting metrics from unavailable device."""
    db_session.add(test_device)
    await db_session.commit()

    with patch("opmas_mgmt_api.services.devices.DeviceService.get_device_metrics") as mock_metrics:
        mock_metrics.side_effect = OPMASException(status_code=503, detail="Device unavailable")
        response = client.get(f"/api/v1/devices/{test_device.id}/metrics")
        assert response.status_code == 503


# Device Configuration Tests
@pytest.mark.asyncio
async def test_update_device_configuration_validation(client, test_device, db_session):
    """Test device configuration update validation."""
    db_session.add(test_device)
    await db_session.commit()

    # Test invalid configuration format
    invalid_config = "invalid-config"
    response = client.put(f"/api/v1/devices/{test_device.id}/configuration", json=invalid_config)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_device_configuration_rejected(client, test_device, db_session):
    """Test device configuration update rejection."""
    db_session.add(test_device)
    await db_session.commit()

    with patch(
        "opmas_mgmt_api.services.devices.DeviceService.update_device_configuration"
    ) as mock_update:
        mock_update.side_effect = OPMASException(
            status_code=400, detail="Configuration rejected by device"
        )
        response = client.put(
            f"/api/v1/devices/{test_device.id}/configuration", json={"setting": "value"}
        )
        assert response.status_code == 400


# Error Handling Tests
@pytest.mark.asyncio
async def test_database_error_handling(client, test_device, db_session):
    """Test database error handling."""
    with patch("opmas_mgmt_api.services.devices.DeviceService.list_devices") as mock_list:
        mock_list.side_effect = Exception("Database error")
        response = client.get("/api/v1/devices")
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_nats_error_handling(client, test_device, db_session):
    """Test NATS error handling."""
    db_session.add(test_device)
    await db_session.commit()

    with patch("opmas_mgmt_api.core.nats.NATSManager.publish") as mock_publish:
        mock_publish.side_effect = Exception("NATS error")
        response = client.put(f"/api/v1/devices/{test_device.id}/status", json={"status": "active"})
        assert response.status_code == 200  # Should still succeed, just log the error


# Integration Tests
@pytest.mark.asyncio
async def test_device_lifecycle(client, db_session):
    """Test complete device lifecycle."""
    # Create device
    device_data = {
        "hostname": "lifecycle-device",
        "ip_address": "192.168.1.100",
        "device_type": "router",
        "model": "Test Model",
        "firmware_version": "1.0.0",
    }
    response = client.post("/api/v1/devices", json=device_data)
    assert response.status_code == 201
    device_id = response.json()["id"]

    # Update device
    update_data = {"hostname": "updated-lifecycle-device", "status": "maintenance"}
    response = client.put(f"/api/v1/devices/{device_id}", json=update_data)
    assert response.status_code == 200

    # Get device metrics
    response = client.get(f"/api/v1/devices/{device_id}/metrics")
    assert response.status_code == 200

    # Update configuration
    config_data = {"interfaces": {"eth0": {"enabled": True, "ip": "192.168.1.100/24"}}}
    response = client.put(f"/api/v1/devices/{device_id}/configuration", json=config_data)
    assert response.status_code == 200

    # Delete device
    response = client.delete(f"/api/v1/devices/{device_id}")
    assert response.status_code == 204

    # Verify device is deleted
    response = client.get(f"/api/v1/devices/{device_id}")
    assert response.status_code == 404
