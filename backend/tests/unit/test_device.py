import pytest
from datetime import datetime
from core.models.device import Device
from core.schemas.device import DeviceCreate, DeviceUpdate

def test_create_device(sample_device_data):
    """Test device creation from data."""
    device = Device(**sample_device_data)
    assert device.hostname == sample_device_data["hostname"]
    assert device.ip_address == sample_device_data["ip_address"]
    assert device.device_type == sample_device_data["device_type"]
    assert device.status == sample_device_data["status"]
    assert device.is_active is True

def test_device_update(sample_device):
    """Test device update functionality."""
    update_data = {
        "status": "inactive",
        "configuration": {"new_setting": "value"}
    }
    for key, value in update_data.items():
        setattr(sample_device, key, value)
    
    assert sample_device.status == "inactive"
    assert sample_device.configuration == {"new_setting": "value"}

def test_device_validation(sample_device_data):
    """Test device data validation."""
    # Test valid data
    device = DeviceCreate(**sample_device_data)
    assert device.hostname == sample_device_data["hostname"]
    
    # Test invalid data
    invalid_data = sample_device_data.copy()
    invalid_data["ip_address"] = "invalid_ip"
    with pytest.raises(ValueError):
        DeviceCreate(**invalid_data)

def test_device_relationships(sample_device, sample_logs):
    """Test device relationships with logs."""
    device_logs = [log for log in sample_logs if log.device_id == sample_device.id]
    assert len(device_logs) > 0
    assert all(log.device_id == sample_device.id for log in device_logs)

@pytest.mark.asyncio
async def test_device_async_operations(async_client, sample_device):
    """Test async operations on devices."""
    # Test device retrieval
    response = await async_client.get(f"/api/v1/devices/{sample_device.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["hostname"] == sample_device.hostname
    
    # Test device update
    update_data = {"status": "maintenance"}
    response = await async_client.put(
        f"/api/v1/devices/{sample_device.id}",
        json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "maintenance" 