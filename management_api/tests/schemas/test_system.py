"""Test system management schemas."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from opmas_mgmt_api.schemas.system import (
    SystemStatus,
    SystemHealth,
    SystemMetrics,
    SystemConfig,
    SystemConfigUpdate,
    SystemControl
)

@pytest.fixture
def test_system_status():
    """Create test system status."""
    return {
        "status": "operational",
        "components": {
            "database": {"status": "connected"},
            "nats": {"status": "connected"}
        },
        "metrics": {
            "components": {},
            "system": {},
            "timestamp": datetime.utcnow().isoformat()
        },
        "health": {
            "status": "healthy",
            "components": {
                "database": {"status": "healthy"},
                "nats": {"status": "healthy"}
            },
            "timestamp": datetime.utcnow().isoformat()
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@pytest.fixture
def test_system_health():
    """Create test system health."""
    return {
        "status": "healthy",
        "components": {
            "database": {"status": "healthy", "message": "Database connection is healthy"},
            "nats": {"status": "healthy", "message": "NATS connection is healthy"}
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@pytest.fixture
def test_system_metrics():
    """Create test system metrics."""
    return {
        "components": {
            "database": {"connections": 10},
            "nats": {"messages": 100}
        },
        "system": {
            "cpu": 0.5,
            "memory": 0.7
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@pytest.fixture
def test_system_config():
    """Create test system config."""
    return {
        "version": "1.0.0",
        "components": {
            "database": {"pool_size": 10},
            "nats": {"max_reconnects": 5}
        },
        "security": {
            "jwt_secret": "test-secret",
            "token_expiry": 3600
        },
        "logging": {
            "level": "INFO",
            "format": "json"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@pytest.fixture
def test_system_config_update():
    """Create test system config update."""
    return {
        "version": "1.0.1",
        "components": {
            "database": {"pool_size": 20}
        }
    }

@pytest.fixture
def test_system_control():
    """Create test system control."""
    return {
        "action": "restart",
        "status": "accepted",
        "timestamp": datetime.utcnow().isoformat()
    }

def test_system_status_validation(test_system_status):
    """Test system status validation."""
    status = SystemStatus(**test_system_status)
    assert status.status == test_system_status["status"]
    assert status.components == test_system_status["components"]
    assert status.metrics.components == test_system_status["metrics"]["components"]
    assert status.metrics.system == test_system_status["metrics"]["system"]
    assert status.health.status == test_system_status["health"]["status"]
    assert status.health.components == test_system_status["health"]["components"]

def test_system_status_validation_invalid():
    """Test system status validation with invalid data."""
    invalid_data = {
        "status": "invalid_status",  # Invalid status
        "components": {},
        "metrics": {
            "components": {},
            "system": {},
            "timestamp": datetime.utcnow().isoformat()
        },
        "health": {
            "status": "healthy",
            "components": {},
            "timestamp": datetime.utcnow().isoformat()
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    with pytest.raises(ValidationError):
        SystemStatus(**invalid_data)

def test_system_health_validation(test_system_health):
    """Test system health validation."""
    health = SystemHealth(**test_system_health)
    assert health.status == test_system_health["status"]
    assert health.components == test_system_health["components"]

def test_system_health_validation_invalid():
    """Test system health validation with invalid data."""
    invalid_data = {
        "status": "invalid_status",  # Invalid status
        "components": {},
        "timestamp": datetime.utcnow().isoformat()
    }
    with pytest.raises(ValidationError):
        SystemHealth(**invalid_data)

def test_system_metrics_validation(test_system_metrics):
    """Test system metrics validation."""
    metrics = SystemMetrics(**test_system_metrics)
    assert metrics.components == test_system_metrics["components"]
    assert metrics.system == test_system_metrics["system"]

def test_system_config_validation(test_system_config):
    """Test system config validation."""
    config = SystemConfig(**test_system_config)
    assert config.version == test_system_config["version"]
    assert config.components == test_system_config["components"]
    assert config.security == test_system_config["security"]
    assert config.logging == test_system_config["logging"]

def test_system_config_validation_invalid():
    """Test system config validation with invalid data."""
    invalid_data = {
        "version": None,  # Required field
        "components": {},
        "security": {},
        "logging": {},
        "timestamp": datetime.utcnow().isoformat()
    }
    with pytest.raises(ValidationError):
        SystemConfig(**invalid_data)

def test_system_config_update_validation(test_system_config_update):
    """Test system config update validation."""
    config = SystemConfigUpdate(**test_system_config_update)
    assert config.version == test_system_config_update["version"]
    assert config.components == test_system_config_update["components"]

def test_system_control_validation(test_system_control):
    """Test system control validation."""
    control = SystemControl(**test_system_control)
    assert control.action == test_system_control["action"]
    assert control.status == test_system_control["status"]

def test_system_control_validation_invalid():
    """Test system control validation with invalid data."""
    invalid_data = {
        "action": "invalid_action",  # Invalid action
        "status": "accepted",
        "timestamp": datetime.utcnow().isoformat()
    }
    with pytest.raises(ValidationError):
        SystemControl(**invalid_data) 