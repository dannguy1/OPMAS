import pytest
import asyncio
from datetime import datetime
from core.workflows.device_management import DeviceManagementWorkflow
from core.models.device import Device
from core.models.log import Log

@pytest.fixture
async def device_workflow():
    workflow = DeviceManagementWorkflow()
    await workflow.initialize()
    return workflow

@pytest.fixture
async def sample_devices():
    devices = [
        Device(
            hostname="router-01",
            ip_address="192.168.1.1",
            device_type="router",
            status="active"
        ),
        Device(
            hostname="switch-01",
            ip_address="192.168.1.2",
            device_type="switch",
            status="active"
        )
    ]
    return devices

async def test_device_discovery_workflow(device_workflow):
    # Test device discovery process
    devices = await device_workflow.discover_devices()
    assert len(devices) > 0
    assert all(device.status == "active" for device in devices)
    assert all(isinstance(device, Device) for device in devices)

async def test_device_monitoring_workflow(device_workflow, sample_devices):
    # Test device monitoring process
    logs = await device_workflow.monitor_devices(sample_devices)
    assert len(logs) > 0
    assert all(isinstance(log, Log) for log in logs)
    assert all(log.device_id in [device.id for device in sample_devices] for log in logs)

async def test_alert_processing_workflow(device_workflow, sample_devices):
    # Test alert processing
    # First, create some test logs
    test_logs = [
        Log(
            device_id=sample_devices[0].id,
            timestamp=datetime.utcnow(),
            severity="ERROR",
            message="Interface down",
            source="system"
        )
    ]
    
    # Process alerts
    alerts = await device_workflow.process_alerts(test_logs)
    assert len(alerts) > 0
    assert all(alert.severity == "ERROR" for alert in alerts)

async def test_automation_workflow(device_workflow, sample_devices):
    # Test automation execution
    # Create a test rule
    test_rule = {
        "name": "interface_down_alert",
        "condition": {
            "field": "message",
            "operator": "contains",
            "value": "down"
        },
        "action": {
            "type": "alert",
            "severity": "high"
        }
    }
    
    # Execute automation
    result = await device_workflow.execute_automation(test_rule, sample_devices[0])
    assert result.success
    assert result.action_taken == "alert_created" 