"""Integration tests for core backend connectivity."""

import asyncio

import nats
import pytest
import pytest_asyncio
import redis
from fastapi.testclient import TestClient
from opmas_mgmt_api.config import get_settings
from opmas_mgmt_api.db.session import db_manager
from opmas_mgmt_api.main import app
from opmas_mgmt_api.services.nats import nats_manager
from sqlalchemy.orm import Session

settings = get_settings()


@pytest.fixture(scope="session")
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(scope="session")
def db():
    """Create test database session."""
    with db_manager.get_session() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
async def nats_client():
    """Create test NATS client."""
    nc = await nats.connect(settings.nats_url)
    try:
        yield nc
    finally:
        await nc.close()


@pytest.fixture(scope="session")
def redis_client():
    """Create test Redis client."""
    client = redis.Redis.from_url(settings.redis_url)
    yield client
    client.close()


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data
    assert "database" in data["services"]
    assert "nats" in data["services"]


def test_database_connection(db: Session):
    """Test database connection."""
    # Try to execute a simple query
    result = db.execute("SELECT 1").scalar()
    assert result == 1


@pytest.mark.asyncio
async def test_nats_connection(nats_client):
    """Test NATS connection."""
    # Create a test subject
    test_subject = "test.subject"
    test_message = b"Test message"

    # Create a future to wait for the message
    future = asyncio.Future()

    # Subscribe to the test subject
    async def message_handler(msg):
        future.set_result(msg.data)

    await nats_client.subscribe(test_subject, cb=message_handler)

    # Publish a test message
    await nats_client.publish(test_subject, test_message)

    # Wait for the message to be received
    received_message = await asyncio.wait_for(future, timeout=5.0)
    assert received_message == test_message


def test_redis_connection(redis_client):
    """Test Redis connection."""
    # Test key
    test_key = "test:key"
    test_value = "test_value"

    # Set and get value
    redis_client.set(test_key, test_value)
    retrieved_value = redis_client.get(test_key)
    assert retrieved_value.decode() == test_value

    # Clean up
    redis_client.delete(test_key)


@pytest.mark.asyncio
async def test_integrated_workflow(client, db: Session, nats_client, redis_client):
    """Test integrated workflow using all three services."""
    # 1. Create a test device via API
    device_data = {
        "hostname": "test-device",
        "ip_address": "192.168.1.2",
        "device_type": "sensor",
        "status": "active",
    }
    response = client.post("/api/v1/devices", json=device_data)
    assert response.status_code == 200
    device = response.json()
    assert device["hostname"] == device_data["hostname"]

    # 2. Store device status in Redis
    device_key = f"device:status:{device['id']}"
    redis_client.hset(device_key, mapping={"status": "active", "last_seen": "2024-03-20T12:00:00Z"})

    # 3. Publish device status update via NATS
    status_subject = f"device.status.{device['id']}"
    status_message = {
        "device_id": device["id"],
        "status": "active",
        "timestamp": "2024-03-20T12:00:00Z",
    }
    await nats_client.publish(status_subject, str(status_message).encode())

    # 4. Verify device status via API
    response = client.get(f"/api/v1/devices/{device['id']}/status")
    assert response.status_code == 200
    status = response.json()
    assert status["status"] == "active"

    # 5. Clean up
    response = client.delete(f"/api/v1/devices/{device['id']}")
    assert response.status_code == 200
    redis_client.delete(device_key)
