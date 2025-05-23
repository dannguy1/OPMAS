"""Test device management models."""

import pytest
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from opmas_mgmt_api.models.devices import Device, DeviceStatusHistory
from opmas_mgmt_api.db.base_class import Base

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
        last_seen=datetime.utcnow()
    )

@pytest.fixture
def test_status_history(test_device):
    """Create a test status history entry."""
    return DeviceStatusHistory(
        id=uuid4(),
        device_id=test_device.id,
        status="online",
        timestamp=datetime.utcnow(),
        details={"action": "status_updated"}
    )

def test_device_creation(test_device):
    """Test device creation."""
    assert test_device.id is not None
    assert test_device.hostname == "test-device"
    assert str(test_device.ip_address) == "192.168.1.1"
    assert test_device.device_type == "router"
    assert test_device.model == "test-model"
    assert test_device.firmware_version == "1.0.0"
    assert test_device.status == "online"
    assert test_device.enabled is True
    assert test_device.metadata == {"location": "test-location"}
    assert test_device.created_at is not None
    assert test_device.updated_at is not None
    assert test_device.last_seen is not None

def test_device_to_dict(test_device):
    """Test device to_dict method."""
    device_dict = test_device.to_dict()
    assert device_dict["id"] == str(test_device.id)
    assert device_dict["hostname"] == test_device.hostname
    assert device_dict["ip_address"] == str(test_device.ip_address)
    assert device_dict["device_type"] == test_device.device_type
    assert device_dict["model"] == test_device.model
    assert device_dict["firmware_version"] == test_device.firmware_version
    assert device_dict["status"] == test_device.status
    assert device_dict["enabled"] == test_device.enabled
    assert device_dict["metadata"] == test_device.metadata
    assert device_dict["created_at"] == test_device.created_at.isoformat()
    assert device_dict["updated_at"] == test_device.updated_at.isoformat()
    assert device_dict["last_seen"] == test_device.last_seen.isoformat()

def test_status_history_creation(test_status_history):
    """Test status history creation."""
    assert test_status_history.id is not None
    assert test_status_history.device_id is not None
    assert test_status_history.status == "online"
    assert test_status_history.timestamp is not None
    assert test_status_history.details == {"action": "status_updated"}

def test_status_history_to_dict(test_status_history):
    """Test status history to_dict method."""
    history_dict = test_status_history.to_dict()
    assert history_dict["id"] == str(test_status_history.id)
    assert history_dict["device_id"] == str(test_status_history.device_id)
    assert history_dict["status"] == test_status_history.status
    assert history_dict["timestamp"] == test_status_history.timestamp.isoformat()
    assert history_dict["details"] == test_status_history.details

def test_device_relationships(test_device, test_status_history):
    """Test device relationships."""
    test_device.status_history.append(test_status_history)
    assert len(test_device.status_history) == 1
    assert test_device.status_history[0].id == test_status_history.id
    assert test_status_history.device.id == test_device.id

def test_device_indexes():
    """Test device indexes."""
    indexes = Device.__table_args__
    assert any(index.name == "ix_devices_hostname" for index in indexes)
    assert any(index.name == "ix_devices_ip_address" for index in indexes)
    assert any(index.name == "ix_devices_device_type" for index in indexes)
    assert any(index.name == "ix_devices_status" for index in indexes)
    assert any(index.name == "ix_devices_enabled" for index in indexes)
    assert any(index.name == "ix_devices_agent_id" for index in indexes)

def test_status_history_indexes():
    """Test status history indexes."""
    indexes = DeviceStatusHistory.__table_args__
    assert any(index.name == "ix_device_status_history_device_id" for index in indexes)
    assert any(index.name == "ix_device_status_history_timestamp" for index in indexes)

def test_device_metadata_handling():
    """Test device metadata handling."""
    metadata = {
        "location": "test-location",
        "owner": "test-owner",
        "tags": ["test", "device"]
    }
    device = Device(
        hostname="test-device",
        ip_address="192.168.1.1",
        device_type="router",
        metadata=metadata
    )
    assert device.metadata == metadata
    assert device.metadata["location"] == "test-location"
    assert device.metadata["owner"] == "test-owner"
    assert device.metadata["tags"] == ["test", "device"]

def test_device_status_history_details_handling():
    """Test status history details handling."""
    details = {
        "action": "status_updated",
        "previous_status": "offline",
        "reason": "maintenance"
    }
    history = DeviceStatusHistory(
        device_id=uuid4(),
        status="online",
        details=details
    )
    assert history.details == details
    assert history.details["action"] == "status_updated"
    assert history.details["previous_status"] == "offline"
    assert history.details["reason"] == "maintenance" 