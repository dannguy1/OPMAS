"""Test system management service."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from opmas_mgmt_api.models.system import SystemConfig
from opmas_mgmt_api.schemas.system import SystemConfig as SystemConfigSchema
from opmas_mgmt_api.schemas.system import (
    SystemConfigUpdate,
    SystemControl,
    SystemHealth,
    SystemMetrics,
    SystemStatus,
)
from opmas_mgmt_api.services.system import SystemService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_db():
    """Create mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_nats():
    """Create mock NATS manager."""
    nats = MagicMock()
    nats.publish = AsyncMock()
    nats.is_connected = MagicMock(return_value=True)
    return nats


@pytest.fixture
def system_service(mock_db, mock_nats):
    """Create system service instance."""
    return SystemService(mock_db, mock_nats)


@pytest.fixture
def test_system_config():
    """Create test system config."""
    return SystemConfig(
        id="test-id",
        version="1.0.0",
        components={"database": {"pool_size": 10}, "nats": {"max_reconnects": 5}},
        security={"jwt_secret": "test-secret", "token_expiry": 3600},
        logging={"level": "INFO", "format": "json"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


async def test_get_system_status(system_service):
    """Test getting system status."""
    status = await system_service.get_system_status()
    assert isinstance(status, SystemStatus)
    assert status.status in ["operational", "degraded"]
    assert isinstance(status.components, dict)
    assert isinstance(status.metrics, SystemMetrics)
    assert isinstance(status.health, SystemHealth)
    assert isinstance(status.timestamp, datetime)


async def test_get_system_health(system_service):
    """Test getting system health."""
    health = await system_service.get_system_health()
    assert isinstance(health, SystemHealth)
    assert health.status in ["healthy", "unhealthy", "degraded"]
    assert isinstance(health.components, dict)
    assert isinstance(health.timestamp, datetime)


async def test_get_system_metrics(system_service):
    """Test getting system metrics."""
    metrics = await system_service.get_system_metrics()
    assert isinstance(metrics, SystemMetrics)
    assert isinstance(metrics.components, dict)
    assert isinstance(metrics.system, dict)
    assert isinstance(metrics.timestamp, datetime)


async def test_get_system_config(system_service, test_system_config):
    """Test getting system config."""
    system_service.db.execute.return_value.scalar_one_or_none.return_value = test_system_config

    config = await system_service.get_system_config()
    assert isinstance(config, SystemConfigSchema)
    assert config.version == test_system_config.version
    assert config.components == test_system_config.components
    assert config.security == test_system_config.security
    assert config.logging == test_system_config.logging
    assert isinstance(config.timestamp, datetime)


async def test_get_system_config_default(system_service):
    """Test getting default system config."""
    system_service.db.execute.return_value.scalar_one_or_none.return_value = None

    config = await system_service.get_system_config()
    assert isinstance(config, SystemConfigSchema)
    assert config.version is not None
    assert isinstance(config.components, dict)
    assert isinstance(config.security, dict)
    assert isinstance(config.logging, dict)
    assert isinstance(config.timestamp, datetime)


async def test_update_system_config(system_service, test_system_config):
    """Test updating system config."""
    update_data = SystemConfigUpdate(version="1.0.1", components={"database": {"pool_size": 20}})

    system_service.db.add = MagicMock()
    system_service.db.refresh = AsyncMock()

    config = await system_service.update_system_config(update_data)
    assert isinstance(config, SystemConfigSchema)
    assert config.version == update_data.version
    assert config.components["database"]["pool_size"] == 20
    assert isinstance(config.timestamp, datetime)

    system_service.nats.publish.assert_called_once()
    system_service.db.add.assert_called_once()
    system_service.db.commit.assert_called_once()
    system_service.db.refresh.assert_called_once()


async def test_control_system(system_service):
    """Test controlling system."""
    action = "restart"
    control = await system_service.control_system(action)
    assert isinstance(control, SystemControl)
    assert control.action == action
    assert control.status == "accepted"
    assert isinstance(control.timestamp, datetime)

    system_service.nats.publish.assert_called_once()


async def test_control_system_invalid_action(system_service):
    """Test controlling system with invalid action."""
    with pytest.raises(ValueError):
        await system_service.control_system("invalid")


async def test_get_system_logs(system_service):
    """Test getting system logs."""
    logs = await system_service.get_system_logs()
    assert isinstance(logs, list)


async def test_check_database_health(system_service):
    """Test checking database health."""
    health = await system_service._check_database_health()
    assert isinstance(health, dict)
    assert "status" in health
    assert "message" in health
    assert health["status"] in ["healthy", "unhealthy"]


async def test_check_nats_health(system_service):
    """Test checking NATS health."""
    health = await system_service._check_nats_health()
    assert isinstance(health, dict)
    assert "status" in health
    assert "message" in health
    assert health["status"] in ["healthy", "unhealthy"]
