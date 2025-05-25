import asyncio
from datetime import datetime

import pytest
from core.models.device import Device
from core.models.log import Log
from core.models.rule import Rule
from core.system import OPMASSystem


@pytest.fixture
async def system():
    system = OPMASSystem()
    await system.initialize()
    return system


@pytest.fixture
async def test_environment(system):
    # Set up test environment with sample devices and rules
    devices = [
        Device(
            hostname="router-01", ip_address="192.168.1.1", device_type="router", status="active"
        ),
        Device(
            hostname="switch-01", ip_address="192.168.1.2", device_type="switch", status="active"
        ),
    ]

    rules = [
        Rule(
            name="interface_down_alert",
            description="Alert when interface goes down",
            condition={"field": "message", "operator": "contains", "value": "is down"},
            action={"type": "alert", "severity": "high", "message": "Interface down detected"},
        )
    ]

    # Add devices and rules to system
    for device in devices:
        await system.add_device(device)

    for rule in rules:
        await system.add_rule(rule)

    return {"devices": devices, "rules": rules}


async def test_complete_workflow(system, test_environment):
    # Test complete system workflow

    # 1. Discover and monitor devices
    devices = await system.discover_devices()
    assert len(devices) > 0

    # 2. Generate test logs
    test_logs = [
        Log(
            device_id=devices[0].id,
            timestamp=datetime.utcnow(),
            severity="ERROR",
            message="Interface GigabitEthernet0/0/0 is down",
            source="system",
        )
    ]

    # 3. Process logs and generate alerts
    alerts = await system.process_logs(test_logs)
    assert len(alerts) > 0
    assert all(alert.severity == "high" for alert in alerts)

    # 4. Apply automation rules
    results = await system.apply_automation(alerts)
    assert all(result.success for result in results)

    # 5. Verify system state
    system_state = await system.get_system_state()
    assert system_state["active_alerts"] > 0
    assert system_state["devices_status"]["active"] == len(devices)


async def test_error_handling(system, test_environment):
    # Test system's error handling capabilities

    # 1. Test invalid device configuration
    invalid_device = Device(
        hostname="invalid-device", ip_address="invalid-ip", device_type="router"
    )

    with pytest.raises(ValueError):
        await system.add_device(invalid_device)

    # 2. Test invalid rule configuration
    invalid_rule = Rule(
        name="invalid_rule",
        description="Invalid rule",
        condition={"field": "invalid_field", "operator": "invalid_operator", "value": "test"},
        action={"type": "invalid_action"},
    )

    with pytest.raises(ValueError):
        await system.add_rule(invalid_rule)

    # 3. Test system recovery
    system_state = await system.get_system_state()
    assert system_state["status"] == "healthy"
    assert system_state["error_count"] == 0


async def test_performance(system, test_environment):
    # Test system performance under load

    # 1. Generate large number of test logs
    test_logs = []
    for i in range(100):
        test_logs.append(
            Log(
                device_id=test_environment["devices"][0].id,
                timestamp=datetime.utcnow(),
                severity="INFO",
                message=f"Test log message {i}",
                source="system",
            )
        )

    # 2. Measure processing time
    start_time = datetime.utcnow()
    alerts = await system.process_logs(test_logs)
    end_time = datetime.utcnow()

    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 5.0  # Should process 100 logs in under 5 seconds

    # 3. Verify system stability
    system_state = await system.get_system_state()
    assert system_state["status"] == "healthy"
    assert system_state["performance"]["cpu_usage"] < 80
    assert system_state["performance"]["memory_usage"] < 80
