import pytest
import asyncio
import time
from datetime import datetime
from core.system import OPMASSystem
from core.models.device import Device
from core.models.log import Log

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_device_creation_performance(test_db, benchmark):
    """Benchmark device creation performance."""
    system = OPMASSystem()
    await system.initialize()
    
    async def create_devices(count: int):
        devices = []
        for i in range(count):
            device = await system.add_device({
                "hostname": f"test-device-{i}",
                "ip_address": f"192.168.1.{i}",
                "device_type": "router",
                "status": "active"
            })
            devices.append(device)
        return devices
    
    # Benchmark device creation
    result = await benchmark(create_devices, 100)
    assert len(result) == 100

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_log_processing_performance(test_db, sample_logs, benchmark):
    """Benchmark log processing performance."""
    system = OPMASSystem()
    await system.initialize()
    
    # Create test device
    device = await system.add_device({
        "hostname": "test-device",
        "ip_address": "192.168.1.1",
        "device_type": "router",
        "status": "active"
    })
    
    async def process_logs(logs):
        return await system.process_device_logs(device.id, logs)
    
    # Benchmark log processing
    result = await benchmark(process_logs, sample_logs)
    assert len(result) == len(sample_logs)

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_concurrent_operations(test_db, sample_devices, sample_logs):
    """Test system performance under concurrent operations."""
    system = OPMASSystem()
    await system.initialize()
    
    async def device_operation(device_data):
        # Add device
        device = await system.add_device(device_data)
        # Process logs
        await system.process_device_logs(device.id, sample_logs)
        # Update status
        await system.update_device_status(device.id, "active")
        return device
    
    # Run concurrent operations
    start_time = time.time()
    tasks = [device_operation(device) for device in sample_devices]
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    # Verify results
    assert len(results) == len(sample_devices)
    assert all(isinstance(device, Device) for device in results)
    
    # Calculate and log performance metrics
    total_time = end_time - start_time
    operations_per_second = len(sample_devices) / total_time
    print(f"\nPerformance Metrics:")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Operations per second: {operations_per_second:.2f}")

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_database_query_performance(test_db, sample_devices, sample_logs):
    """Benchmark database query performance."""
    system = OPMASSystem()
    await system.initialize()
    
    # Set up test data
    for device_data in sample_devices:
        device = await system.add_device(device_data)
        await system.process_device_logs(device.id, sample_logs)
    
    async def run_queries():
        # Test different query patterns
        devices = await system.get_all_devices()
        logs = await system.get_all_logs()
        active_devices = await system.get_devices_by_status("active")
        recent_logs = await system.get_recent_logs(limit=100)
        
        return {
            "devices": len(devices),
            "logs": len(logs),
            "active_devices": len(active_devices),
            "recent_logs": len(recent_logs)
        }
    
    # Run benchmark
    result = await benchmark(run_queries)
    assert result["devices"] == len(sample_devices)
    assert result["logs"] == len(sample_devices) * len(sample_logs)

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_message_processing_performance(test_db, mock_nats, sample_logs):
    """Benchmark message processing performance."""
    system = OPMASSystem()
    await system.initialize()
    
    async def process_messages():
        # Process multiple messages concurrently
        tasks = []
        for log in sample_logs:
            task = asyncio.create_task(
                system.process_message("logs.new", log)
            )
            tasks.append(task)
        return await asyncio.gather(*tasks)
    
    # Run benchmark
    results = await benchmark(process_messages)
    assert len(results) == len(sample_logs)
    
    # Verify NATS messages
    assert len(mock_nats.messages) == len(sample_logs)

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_memory_usage(test_db, sample_devices, sample_logs):
    """Test memory usage under load."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    system = OPMASSystem()
    await system.initialize()
    
    # Perform operations
    for device_data in sample_devices:
        device = await system.add_device(device_data)
        await system.process_device_logs(device.id, sample_logs)
    
    # Measure memory usage
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    print(f"\nMemory Usage:")
    print(f"Initial memory: {initial_memory / 1024 / 1024:.2f} MB")
    print(f"Final memory: {final_memory / 1024 / 1024:.2f} MB")
    print(f"Memory increase: {memory_increase / 1024 / 1024:.2f} MB")
    
    # Verify memory usage is within acceptable limits
    assert memory_increase < 500 * 1024 * 1024  # Less than 500MB increase 