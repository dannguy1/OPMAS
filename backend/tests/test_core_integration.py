import pytest
import pytest_asyncio
import asyncio
import nats
import redis
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from opmas.models.device import Device
from opmas.models.log import Log
from opmas.models.rule import Rule
from opmas.models.base import Base
from opmas.core.config import get_settings

# Test configuration
settings = get_settings()

@pytest.fixture(scope="session")
def db_engine():
    """Create database engine for testing."""
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(db_engine):
    """Create database session for testing."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest_asyncio.fixture(scope="session")
async def nats_client():
    """Create NATS client for testing."""
    nc = await nats.connect(settings.nats_url)
    try:
        yield nc
    finally:
        await nc.close()

@pytest.fixture(scope="session")
def redis_client():
    """Create Redis client for testing."""
    client = redis.Redis.from_url(settings.redis_url)
    yield client
    client.close()

@pytest.mark.asyncio
async def test_database_connection(db_session):
    """Test database connection and basic operations."""
    # Create test device
    device = Device(
        hostname="test-router",
        ip_address="192.168.1.1",
        device_type="router",
        status="active"
    )
    db_session.add(device)
    db_session.commit()
    
    # Verify device was created
    saved_device = db_session.query(Device).filter_by(hostname="test-router").first()
    assert saved_device is not None
    assert saved_device.ip_address == "192.168.1.1"
    
    # Create test log
    log = Log(
        device_id=saved_device.id,
        timestamp=datetime.utcnow(),
        level="INFO",
        source="test",
        message="Test log message"
    )
    db_session.add(log)
    db_session.commit()
    
    # Verify log was created
    saved_log = db_session.query(Log).filter_by(device_id=saved_device.id).first()
    assert saved_log is not None
    assert saved_log.level == "INFO"

@pytest.mark.asyncio
async def test_nats_connection(nats_client):
    """Test NATS connection and message publishing/subscribing."""
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
    """Test Redis connection and basic operations."""
    # Test key
    test_key = "test:key"
    test_value = "test_value"
    
    # Set and get value
    redis_client.set(test_key, test_value)
    retrieved_value = redis_client.get(test_key)
    assert retrieved_value.decode() == test_value
    
    # Test key expiration
    redis_client.setex(test_key, 1, test_value)
    assert redis_client.ttl(test_key) > 0
    
    # Clean up
    redis_client.delete(test_key)

@pytest.mark.asyncio
async def test_integrated_workflow(db_session, nats_client, redis_client):
    """Test integrated workflow using all three services."""
    # 1. Create a device in PostgreSQL
    device = Device(
        hostname="test-device",
        ip_address="192.168.1.2",
        device_type="sensor",
        status="active"
    )
    db_session.add(device)
    db_session.commit()
    
    # 2. Store device status in Redis
    device_key = f"device:status:{device.id}"
    redis_client.hset(device_key, mapping={
        "status": "active",
        "last_seen": datetime.utcnow().isoformat()
    })
    
    # 3. Set up NATS subscription before publishing
    status_subject = f"device.status.{device.id}"
    future = asyncio.Future()
    
    async def status_handler(msg):
        try:
            if not future.done():
                future.set_result(msg.data)
        except Exception as e:
            if not future.done():
                future.set_exception(e)
    
    # Subscribe to the status subject
    subscription = await nats_client.subscribe(status_subject, cb=status_handler)
    
    try:
        # 4. Publish device status update via NATS
        status_message = {
            "device_id": device.id,
            "status": "active",
            "timestamp": datetime.utcnow().isoformat()
        }
        await nats_client.publish(status_subject, str(status_message).encode())
        
        # 5. Wait for the message with a reasonable timeout
        received_message = await asyncio.wait_for(future, timeout=5.0)
        assert received_message is not None
        
        # 6. Verify all components
        # Check PostgreSQL
        saved_device = db_session.query(Device).filter_by(id=device.id).first()
        assert saved_device is not None
        assert saved_device.status == "active"
        
        # Check Redis
        device_status = redis_client.hgetall(device_key)
        assert device_status is not None
        assert device_status[b"status"] == b"active"
        
    finally:
        # Clean up NATS subscription
        await subscription.unsubscribe()
        if not future.done():
            future.cancel() 