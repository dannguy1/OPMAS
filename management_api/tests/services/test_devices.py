"""Test device management service."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from opmas_mgmt_api.core.exceptions import NotFoundError, ValidationError
from opmas_mgmt_api.models.devices import Device, DeviceStatusHistory
from opmas_mgmt_api.schemas.devices import DeviceCreate, DeviceStatus, DeviceUpdate
from opmas_mgmt_api.services.devices import DeviceService
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
def device_service(mock_db_session, mock_nats):
    """Create a device service instance."""
    return DeviceService(mock_db_session, mock_nats)


async def test_list_devices(device_service, test_device):
    """Test listing devices."""
    result = await device_service.list_devices()
    assert "items" in result
    assert "total" in result
    assert "skip" in result
    assert "limit" in result


async def test_list_devices_with_filters(device_service, test_device):
    """Test listing devices with filters."""
    result = await device_service.list_devices(device_type="router", status="online", enabled=True)
    assert "items" in result
    assert "total" in result


async def test_get_device(device_service, test_device):
    """Test getting a device."""
    device = await device_service.get_device(test_device.id)
    assert device.id == test_device.id
    assert device.hostname == test_device.hostname


async def test_get_nonexistent_device(device_service):
    """Test getting a nonexistent device."""
    with pytest.raises(NotFoundError):
        await device_service.get_device(uuid4())


async def test_create_device(device_service, test_device_create):
    """Test creating a device."""
    device = await device_service.create_device(test_device_create)
    assert device.hostname == test_device_create.hostname
    assert device.ip_address == test_device_create.ip_address
    assert device.device_type == test_device_create.device_type


async def test_create_device_duplicate_hostname(device_service, test_device, test_device_create):
    """Test creating a device with duplicate hostname."""
    device_service.db.execute.return_value.scalar_one_or_none.return_value = test_device
    with pytest.raises(ValidationError):
        await device_service.create_device(test_device_create)


async def test_create_device_duplicate_ip(device_service, test_device, test_device_create):
    """Test creating a device with duplicate IP address."""
    device_service.db.execute.return_value.scalar_one_or_none.return_value = test_device
    with pytest.raises(ValidationError):
        await device_service.create_device(test_device_create)


async def test_update_device(device_service, test_device, test_device_update):
    """Test updating a device."""
    device = await device_service.update_device(test_device.id, test_device_update)
    assert device.hostname == test_device_update.hostname
    assert device.status == test_device_update.status


async def test_update_nonexistent_device(device_service, test_device_update):
    """Test updating a nonexistent device."""
    with pytest.raises(NotFoundError):
        await device_service.update_device(uuid4(), test_device_update)


async def test_delete_device(device_service, test_device):
    """Test deleting a device."""
    await device_service.delete_device(test_device.id)
    device_service.db.delete.assert_called_once()


async def test_delete_nonexistent_device(device_service):
    """Test deleting a nonexistent device."""
    with pytest.raises(NotFoundError):
        await device_service.delete_device(uuid4())


async def test_get_device_status(device_service, test_device):
    """Test getting device status."""
    status = await device_service.get_device_status(test_device.id)
    assert isinstance(status, DeviceStatus)
    assert status.status == test_device.status
    assert status.last_seen == test_device.last_seen


async def test_get_nonexistent_device_status(device_service):
    """Test getting status for nonexistent device."""
    with pytest.raises(NotFoundError):
        await device_service.get_device_status(uuid4())


async def test_update_device_status(device_service, test_device):
    """Test updating device status."""
    new_status = "offline"
    details = {"reason": "maintenance"}
    device = await device_service.update_device_status(test_device.id, new_status, details)
    assert device.status == new_status


async def test_update_nonexistent_device_status(device_service):
    """Test updating status for nonexistent device."""
    with pytest.raises(NotFoundError):
        await device_service.update_device_status(uuid4(), "offline")


async def test_discover_devices(device_service):
    """Test device discovery."""
    devices = await device_service.discover_devices()
    assert isinstance(devices, list)
