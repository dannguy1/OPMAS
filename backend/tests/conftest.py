import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator
from datetime import datetime
import asyncio

from opmas.core.config import DatabaseConfig, LoggingConfig, get_config
from opmas.core.database import DatabaseManager
from opmas.models import Base as ModelsBase
from opmas.models.base import Base as ModelsBase
from tests.utils.test_data_loader import TestDataLoader
from tests.utils.test_config import TestConfig
from tests.utils.test_db import TestDatabase
from opmas.models.device import Device
from opmas.models.log import Log
from opmas.models.rule import Rule

# Test database URL - using SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def test_db_config() -> DatabaseConfig:
    """Test database configuration."""
    return DatabaseConfig(
        host="localhost",
        port=0,  # Not used for SQLite
        database="test.db",
        user="",  # Not used for SQLite
        password="",  # Not used for SQLite
        pool_size=5
    )

@pytest.fixture(scope="session")
def test_logging_config() -> LoggingConfig:
    """Test logging configuration."""
    return LoggingConfig(
        level="DEBUG",
        format="json",
        rotation="1 day",
        retention="7 days"
    )

@pytest.fixture(scope="session")
def test_engine(test_db_config: DatabaseConfig):
    """Create test database engine."""
    engine = create_engine(TEST_DATABASE_URL)
    return engine

@pytest.fixture(scope="session")
def test_db():
    """Create a test database and return the engine."""
    engine = create_engine(TEST_DATABASE_URL)
    ModelsBase.metadata.create_all(engine)
    yield engine
    ModelsBase.metadata.drop_all(engine)
    # Clean up the SQLite database file
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture(scope="function")
def db_session(test_db):
    """Create a new database session for a test."""
    Session = sessionmaker(bind=test_db)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def db_manager(test_db_config: DatabaseConfig) -> DatabaseManager:
    """Create a database manager instance."""
    return DatabaseManager(config=test_db_config)

@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    config = get_config()
    if not config:
        raise ValueError("Configuration not loaded")
    return create_engine(config.get('database', {}).get('url', TEST_DATABASE_URL))

@pytest.fixture(scope="session")
def tables(engine):
    """Create all tables in the test database."""
    ModelsBase.metadata.create_all(engine)
    yield
    ModelsBase.metadata.drop_all(engine)

@pytest.fixture
def test_agent(db_session):
    """Create a test agent."""
    from opmas.models.agent import Agent, AgentType, AgentStatus
    
    agent = Agent(
        name="test_agent",
        type=AgentType.WIFI,
        status=AgentStatus.ACTIVE,
        configuration={"test": "config"}
    )
    db_session.add(agent)
    db_session.commit()
    return agent

@pytest.fixture
def test_log_entry(db_session):
    """Create a test log entry."""
    from opmas.models.log import LogEntry
    
    log_entry = LogEntry(
        source="test_source",
        level="INFO",
        message="Test log message",
        metadata={"test": "metadata"}
    )
    db_session.add(log_entry)
    db_session.commit()
    return log_entry

class MockNATSServer:
    """Mock NATS server for testing."""
    def __init__(self):
        self.messages = []
        self.subscribers = {}
    
    def publish(self, subject, message):
        self.messages.append((subject, message))
        if subject in self.subscribers:
            for callback in self.subscribers[subject]:
                callback(message)
    
    def subscribe(self, subject, callback):
        if subject not in self.subscribers:
            self.subscribers[subject] = []
        self.subscribers[subject].append(callback)

@pytest.fixture
def mock_nats():
    """Create a mock NATS server."""
    return MockNATSServer()

def generate_test_logs(count=100):
    """Generate test log entries."""
    logs = []
    for i in range(count):
        log = {
            "timestamp": datetime.now().isoformat(),
            "device": f"device-{i}",
            "message": f"Test log {i}",
            "level": "INFO",
            "source": "test"
        }
        logs.append(log)
    return logs

@pytest.fixture
def test_logs():
    """Provide test log entries."""
    return generate_test_logs(10)

@pytest.fixture
def test_agent_data():
    """Provide test agent data."""
    return {
        "name": "test-agent",
        "type": "wifi",
        "status": "active",
        "configuration": {
            "enabled": True,
            "rules": []
        }
    }

@pytest.fixture
def test_device_data():
    """Provide test device data."""
    return {
        "hostname": "test-device",
        "ip_address": "192.168.1.1",
        "device_type": "router",
        "status": "active"
    }

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return TestConfig()

@pytest.fixture(scope="session")
def test_data():
    """Provide test data loader."""
    return TestDataLoader()

@pytest.fixture(scope="function")
def test_db(test_config):
    """Provide test database with automatic cleanup."""
    with TestDatabase(test_config) as db:
        yield db

@pytest.fixture
def sample_device(test_data):
    """Provide a sample device for testing."""
    device_data = test_data.get_test_device(1)
    return Device(**device_data)

@pytest.fixture
def sample_devices(test_data):
    """Provide multiple sample devices for testing."""
    devices_data = test_data.load_devices()
    return [Device(**data) for data in devices_data]

@pytest.fixture
def sample_logs(test_data):
    """Provide sample logs for testing."""
    logs_data = test_data.load_logs()
    return [Log(**data) for data in logs_data]

@pytest.fixture
def sample_rules(test_data):
    """Provide sample rules for testing."""
    rules_data = test_data.load_rules()
    return [Rule(**data) for data in rules_data]

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def async_client():
    """Provide an async test client."""
    from core.app import create_app
    app = create_app()
    async with app.test_client() as client:
        yield client

@pytest.fixture
def mock_nats():
    """Provide a mock NATS client."""
    class MockNatsClient:
        async def publish(self, subject, payload):
            return True
        
        async def subscribe(self, subject, callback):
            return True
        
        async def close(self):
            return True
    
    return MockNatsClient()

@pytest.fixture
def mock_redis():
    """Provide a mock Redis client."""
    class MockRedisClient:
        def __init__(self):
            self.data = {}
        
        async def set(self, key, value):
            self.data[key] = value
            return True
        
        async def get(self, key):
            return self.data.get(key)
        
        async def delete(self, key):
            if key in self.data:
                del self.data[key]
            return True
    
    return MockRedisClient() 