import pytest
from datetime import datetime
from core.models.device import Device
from core.schemas.device import DeviceCreate

@pytest.fixture
def sample_device_data():
    return {
        "hostname": "test-router",
        "ip_address": "192.168.1.1",
        "device_type": "router",
        "configuration": {
            "model": "Test Model",
            "os_version": "1.0"
        }
    }

def test_create_device(sample_device_data):
    device = Device(**sample_device_data)
    assert device.hostname == sample_device_data["hostname"]
    assert device.ip_address == sample_device_data["ip_address"]
    assert device.device_type == sample_device_data["device_type"]
    assert device.status == "active"  # Default status
    assert device.configuration == sample_device_data["configuration"]

def test_device_validation():
    with pytest.raises(ValueError):
        Device(
            hostname="test-router",
            ip_address="invalid-ip",  # Invalid IP address
            device_type="router"
        )

def test_device_update():
    device = Device(
        hostname="test-router",
        ip_address="192.168.1.1",
        device_type="router"
    )
    
    # Update device status
    device.status = "maintenance"
    assert device.status == "maintenance"
    
    # Update configuration
    new_config = {"model": "Updated Model", "os_version": "2.0"}
    device.configuration = new_config
    assert device.configuration == new_config 