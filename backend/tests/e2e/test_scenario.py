import pytest
from datetime import datetime
from core.system import OPMASSystem
from core.models.device import Device
from core.models.log import Log
from core.models.rule import Rule

@pytest.mark.asyncio
async def test_system_initialization(test_config, mock_nats, mock_redis):
    """Test system initialization and configuration."""
    system = OPMASSystem(test_config)
    await system.initialize()
    
    assert system.is_initialized
    assert system.nats_client is not None
    assert system.redis_client is not None
    assert system.database is not None

@pytest.mark.asyncio
async def test_complete_device_management_scenario(
    test_db, sample_device, sample_logs, mock_nats, mock_redis
):
    """Test complete device management scenario."""
    system = OPMASSystem()
    await system.initialize()
    
    # 1. Add device to system
    device = await system.add_device(sample_device)
    assert device.id is not None
    assert device.status == "active"
    
    # 2. Start monitoring
    await system.start_device_monitoring(device.id)
    monitoring_messages = [msg for subject, msg in mock_nats.messages 
                         if subject == "devices.monitoring"]
    assert len(monitoring_messages) > 0
    
    # 3. Process device logs
    processed_logs = await system.process_device_logs(device.id, sample_logs)
    assert len(processed_logs) == len(sample_logs)
    
    # 4. Update device status
    await system.update_device_status(device.id, "warning")
    updated_device = await system.get_device(device.id)
    assert updated_device.status == "warning"
    
    # 5. Verify system state
    system_logs = await system.get_device_logs(device.id)
    assert len(system_logs) == len(sample_logs)
    
    # 6. Clean up
    await system.remove_device(device.id)
    with pytest.raises(Exception):
        await system.get_device(device.id)

@pytest.mark.asyncio
async def test_automation_scenario(
    test_db, sample_device, sample_logs, sample_rules, mock_nats, mock_redis
):
    """Test automation scenario with rules and actions."""
    system = OPMASSystem()
    await system.initialize()
    
    # 1. Set up device and rules
    device = await system.add_device(sample_device)
    for rule in sample_rules:
        await system.add_rule(rule)
    
    # 2. Process logs that should trigger rules
    await system.process_device_logs(device.id, sample_logs)
    
    # 3. Verify rule evaluation
    rule_results = await system.get_rule_evaluation_results(device.id)
    assert len(rule_results) > 0
    assert any(result.matched for result in rule_results)
    
    # 4. Verify automated actions
    action_messages = [msg for subject, msg in mock_nats.messages 
                      if subject == "rules.actions"]
    assert len(action_messages) > 0
    
    # 5. Verify system state after automation
    final_device = await system.get_device(device.id)
    assert final_device.status in ["active", "warning", "error"]
    
    # 6. Clean up
    await system.remove_device(device.id)
    await system.remove_all_rules()

@pytest.mark.asyncio
async def test_error_handling_scenario(
    test_db, sample_device, mock_nats, mock_redis
):
    """Test system error handling and recovery."""
    system = OPMASSystem()
    await system.initialize()
    
    # 1. Add device
    device = await system.add_device(sample_device)
    
    # 2. Simulate NATS connection failure
    mock_nats.connected = False
    with pytest.raises(Exception):
        await system.start_device_monitoring(device.id)
    
    # 3. Verify error handling
    error_logs = await system.get_error_logs()
    assert len(error_logs) > 0
    
    # 4. Simulate recovery
    mock_nats.connected = True
    await system.start_device_monitoring(device.id)
    assert device.status == "active"
    
    # 5. Clean up
    await system.remove_device(device.id)

@pytest.mark.asyncio
async def test_performance_scenario(
    test_db, sample_devices, sample_logs, mock_nats, mock_redis
):
    """Test system performance with multiple devices and logs."""
    system = OPMASSystem()
    await system.initialize()
    
    # 1. Add multiple devices
    devices = []
    for device_data in sample_devices:
        device = await system.add_device(device_data)
        devices.append(device)
    
    # 2. Process logs for all devices
    for device in devices:
        await system.process_device_logs(device.id, sample_logs)
    
    # 3. Verify system performance
    all_logs = await system.get_all_logs()
    assert len(all_logs) == len(devices) * len(sample_logs)
    
    # 4. Verify message processing
    assert len(mock_nats.messages) > 0
    
    # 5. Clean up
    for device in devices:
        await system.remove_device(device.id) 