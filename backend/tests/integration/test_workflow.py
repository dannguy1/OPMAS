from datetime import datetime

import pytest
from core.models.device import Device
from core.models.log import Log
from core.workflows.device_management import DeviceManagementWorkflow
from core.workflows.log_processing import LogProcessingWorkflow


@pytest.mark.asyncio
async def test_device_discovery_workflow(test_db, mock_nats):
    """Test the device discovery workflow."""
    workflow = DeviceManagementWorkflow(test_db, mock_nats)

    # Test device discovery
    devices = await workflow.discover_devices()
    assert len(devices) > 0
    assert all(isinstance(device, Device) for device in devices)
    assert all(device.status == "active" for device in devices)

    # Verify NATS messages
    assert len(mock_nats.messages) > 0
    discovery_messages = [
        msg for subject, msg in mock_nats.messages if subject == "devices.discovery"
    ]
    assert len(discovery_messages) > 0


@pytest.mark.asyncio
async def test_log_processing_workflow(test_db, sample_logs, mock_nats):
    """Test the log processing workflow."""
    workflow = LogProcessingWorkflow(test_db, mock_nats)

    # Process logs
    processed_logs = await workflow.process_logs(sample_logs)
    assert len(processed_logs) == len(sample_logs)
    assert all(isinstance(log, Log) for log in processed_logs)

    # Verify log storage
    stored_logs = await workflow.get_stored_logs()
    assert len(stored_logs) == len(sample_logs)

    # Verify NATS notifications
    notification_messages = [
        msg for subject, msg in mock_nats.messages if subject == "logs.processed"
    ]
    assert len(notification_messages) > 0


@pytest.mark.asyncio
async def test_device_monitoring_workflow(test_db, sample_device, mock_nats):
    """Test the device monitoring workflow."""
    workflow = DeviceManagementWorkflow(test_db, mock_nats)

    # Start monitoring
    await workflow.start_monitoring(sample_device)

    # Simulate device status change
    await workflow.update_device_status(sample_device.id, "warning")

    # Verify status update
    updated_device = await workflow.get_device(sample_device.id)
    assert updated_device.status == "warning"

    # Verify NATS notifications
    status_messages = [msg for subject, msg in mock_nats.messages if subject == "devices.status"]
    assert len(status_messages) > 0


@pytest.mark.asyncio
async def test_rule_evaluation_workflow(test_db, sample_device, sample_logs, sample_rules):
    """Test the rule evaluation workflow."""
    workflow = LogProcessingWorkflow(test_db, mock_nats)

    # Process logs with rules
    results = await workflow.evaluate_rules(sample_logs, sample_rules)
    assert len(results) > 0

    # Verify rule matches
    assert any(result.matched for result in results)

    # Verify actions triggered
    action_messages = [msg for subject, msg in mock_nats.messages if subject == "rules.actions"]
    assert len(action_messages) > 0


@pytest.mark.asyncio
async def test_end_to_end_workflow(test_db, sample_device, sample_logs, mock_nats):
    """Test a complete end-to-end workflow."""
    device_workflow = DeviceManagementWorkflow(test_db, mock_nats)
    log_workflow = LogProcessingWorkflow(test_db, mock_nats)

    # 1. Discover and monitor device
    await device_workflow.start_monitoring(sample_device)

    # 2. Process logs
    processed_logs = await log_workflow.process_logs(sample_logs)

    # 3. Update device status based on logs
    await device_workflow.update_device_status(sample_device.id, "active")

    # 4. Verify final state
    final_device = await device_workflow.get_device(sample_device.id)
    final_logs = await log_workflow.get_stored_logs()

    assert final_device.status == "active"
    assert len(final_logs) == len(sample_logs)

    # Verify all expected NATS messages
    expected_subjects = ["devices.monitoring", "logs.processed", "devices.status"]
    for subject in expected_subjects:
        messages = [msg for s, msg in mock_nats.messages if s == subject]
        assert len(messages) > 0
