"""Test configuration management endpoints."""

import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from opmas_mgmt_api.main import app
from opmas_mgmt_api.models.configurations import Configuration, ConfigurationHistory
from opmas_mgmt_api.schemas.configurations import ConfigurationCreate, ConfigurationUpdate
from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.core.exceptions import OPMASException

@pytest.fixture
def test_configuration():
    """Create a test configuration."""
    return Configuration(
        id=uuid4(),
        name="test-config",
        description="Test configuration",
        config_type="network",
        content={
            "interfaces": {
                "eth0": {"enabled": True, "ip": "192.168.1.1/24"}
            }
        },
        version="1.0.0",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def mock_nats():
    """Create a mock NATS manager."""
    nats = AsyncMock(spec=NATSManager)
    nats.publish = AsyncMock()
    return nats

@pytest.fixture
def client(mock_nats):
    """Create a test client with mocked dependencies."""
    app.dependency_overrides[get_nats] = lambda: mock_nats
    return TestClient(app)

# Basic CRUD Tests
@pytest.mark.asyncio
async def test_list_configurations_empty(client, db_session):
    """Test listing configurations when database is empty."""
    response = client.get("/api/v1/configurations")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0
    assert data["total"] == 0

@pytest.mark.asyncio
async def test_list_configurations_with_filters(client, test_configuration, db_session):
    """Test listing configurations with various filters."""
    db_session.add(test_configuration)
    await db_session.commit()

    # Test config_type filter
    response = client.get("/api/v1/configurations?config_type=network")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1

    # Test is_active filter
    response = client.get("/api/v1/configurations?is_active=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1

    # Test pagination
    response = client.get("/api/v1/configurations?skip=0&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["skip"] == 0
    assert data["limit"] == 1

@pytest.mark.asyncio
async def test_create_configuration_validation(client, db_session):
    """Test configuration creation validation."""
    # Test invalid content format
    invalid_data = {
        "name": "invalid-config",
        "config_type": "network",
        "content": "invalid-content"
    }
    response = client.post("/api/v1/configurations", json=invalid_data)
    assert response.status_code == 422

    # Test missing required fields
    invalid_data = {
        "name": "invalid-config"
    }
    response = client.post("/api/v1/configurations", json=invalid_data)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_configuration_duplicate(client, test_configuration, db_session):
    """Test creating configuration with duplicate name."""
    db_session.add(test_configuration)
    await db_session.commit()

    duplicate_data = {
        "name": test_configuration.name,
        "config_type": "network",
        "content": {"setting": "value"}
    }
    response = client.post("/api/v1/configurations", json=duplicate_data)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_update_configuration_partial(client, test_configuration, db_session):
    """Test partial configuration update."""
    db_session.add(test_configuration)
    await db_session.commit()

    update_data = {
        "name": "updated-config-name"
    }
    response = client.put(f"/api/v1/configurations/{test_configuration.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["content"] == test_configuration.content  # Unchanged

@pytest.mark.asyncio
async def test_update_configuration_not_found(client):
    """Test updating non-existent configuration."""
    update_data = {
        "name": "updated-config-name"
    }
    response = client.put(f"/api/v1/configurations/{uuid4()}", json=update_data)
    assert response.status_code == 404

# Configuration Version Tests
@pytest.mark.asyncio
async def test_configuration_version_management(client, test_configuration, db_session):
    """Test configuration version management."""
    db_session.add(test_configuration)
    await db_session.commit()

    # Create new version
    new_version_data = {
        "content": {
            "interfaces": {
                "eth0": {"enabled": True, "ip": "192.168.1.2/24"}
            }
        },
        "version": "1.0.1"
    }
    response = client.post(
        f"/api/v1/configurations/{test_configuration.id}/versions",
        json=new_version_data
    )
    assert response.status_code == 201
    data = response.json()
    assert data["version"] == new_version_data["version"]

    # List versions
    response = client.get(f"/api/v1/configurations/{test_configuration.id}/versions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

# Configuration Deployment Tests
@pytest.mark.asyncio
async def test_deploy_configuration_validation(client, test_configuration, db_session):
    """Test configuration deployment validation."""
    db_session.add(test_configuration)
    await db_session.commit()

    # Test invalid device ID
    response = client.post(
        f"/api/v1/configurations/{test_configuration.id}/deploy",
        json={"device_ids": ["invalid-id"]}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_deploy_configuration_failure(client, test_configuration, db_session):
    """Test configuration deployment failure handling."""
    db_session.add(test_configuration)
    await db_session.commit()

    with patch("opmas_mgmt_api.services.configurations.ConfigurationService.deploy_configuration") as mock_deploy:
        mock_deploy.side_effect = OPMASException(
            status_code=400,
            detail="Deployment failed"
        )
        response = client.post(
            f"/api/v1/configurations/{test_configuration.id}/deploy",
            json={"device_ids": [str(uuid4())]}
        )
        assert response.status_code == 400

# Configuration Template Tests
@pytest.mark.asyncio
async def test_create_configuration_from_template(client, db_session):
    """Test creating configuration from template."""
    template_data = {
        "name": "template-config",
        "config_type": "network",
        "template": {
            "interfaces": {
                "eth0": {"enabled": True, "ip": "{{ip_address}}/24"}
            }
        },
        "variables": ["ip_address"]
    }
    response = client.post("/api/v1/configurations/templates", json=template_data)
    assert response.status_code == 201

    # Create configuration from template
    config_data = {
        "name": "from-template",
        "template_id": response.json()["id"],
        "variables": {
            "ip_address": "192.168.1.100"
        }
    }
    response = client.post("/api/v1/configurations/from-template", json=config_data)
    assert response.status_code == 201
    data = response.json()
    assert data["content"]["interfaces"]["eth0"]["ip"] == "192.168.1.100/24"

# Error Handling Tests
@pytest.mark.asyncio
async def test_database_error_handling(client, test_configuration, db_session):
    """Test database error handling."""
    with patch("opmas_mgmt_api.services.configurations.ConfigurationService.list_configurations") as mock_list:
        mock_list.side_effect = Exception("Database error")
        response = client.get("/api/v1/configurations")
        assert response.status_code == 500

@pytest.mark.asyncio
async def test_nats_error_handling(client, test_configuration, db_session):
    """Test NATS error handling."""
    db_session.add(test_configuration)
    await db_session.commit()

    with patch("opmas_mgmt_api.core.nats.NATSManager.publish") as mock_publish:
        mock_publish.side_effect = Exception("NATS error")
        response = client.post(
            f"/api/v1/configurations/{test_configuration.id}/deploy",
            json={"device_ids": [str(uuid4())]}
        )
        assert response.status_code == 500

# Integration Tests
@pytest.mark.asyncio
async def test_configuration_lifecycle(client, db_session):
    """Test complete configuration lifecycle."""
    # Create configuration
    config_data = {
        "name": "lifecycle-config",
        "config_type": "network",
        "content": {
            "interfaces": {
                "eth0": {"enabled": True, "ip": "192.168.1.100/24"}
            }
        }
    }
    response = client.post("/api/v1/configurations", json=config_data)
    assert response.status_code == 201
    config_id = response.json()["id"]

    # Update configuration
    update_data = {
        "name": "updated-lifecycle-config",
        "content": {
            "interfaces": {
                "eth0": {"enabled": True, "ip": "192.168.1.200/24"}
            }
        }
    }
    response = client.put(f"/api/v1/configurations/{config_id}", json=update_data)
    assert response.status_code == 200

    # Create new version
    version_data = {
        "content": {
            "interfaces": {
                "eth0": {"enabled": True, "ip": "192.168.1.300/24"}
            }
        },
        "version": "1.0.1"
    }
    response = client.post(
        f"/api/v1/configurations/{config_id}/versions",
        json=version_data
    )
    assert response.status_code == 201

    # Deploy configuration
    response = client.post(
        f"/api/v1/configurations/{config_id}/deploy",
        json={"device_ids": [str(uuid4())]}
    )
    assert response.status_code == 200

    # Delete configuration
    response = client.delete(f"/api/v1/configurations/{config_id}")
    assert response.status_code == 204

    # Verify configuration is deleted
    response = client.get(f"/api/v1/configurations/{config_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_list_configurations(client, test_configuration, db_session):
    """Test listing configurations."""
    # Add test configuration to database
    db_session.add(test_configuration)
    await db_session.commit()

    response = client.get("/api/v1/configurations")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == test_configuration.name

@pytest.mark.asyncio
async def test_create_configuration(client, db_session):
    """Test creating a configuration."""
    config_data = {
        "name": "new-config",
        "description": "New configuration",
        "component": "system",
        "version": "1.0.0",
        "is_active": True,
        "configuration": {
            "setting1": "value1",
            "setting2": "value2"
        }
    }

    response = client.post("/api/v1/configurations", json=config_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == config_data["name"]
    assert data["component"] == config_data["component"]

@pytest.mark.asyncio
async def test_get_configuration(client, test_configuration, db_session):
    """Test getting a configuration."""
    db_session.add(test_configuration)
    await db_session.commit()

    response = client.get(f"/api/v1/configurations/{test_configuration.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_configuration.name
    assert data["component"] == test_configuration.component

@pytest.mark.asyncio
async def test_update_configuration(client, test_configuration, db_session):
    """Test updating a configuration."""
    db_session.add(test_configuration)
    await db_session.commit()

    update_data = {
        "name": "updated-config",
        "version": "1.1.0",
        "configuration": {
            "setting1": "new-value1",
            "setting2": "new-value2"
        }
    }

    response = client.put(
        f"/api/v1/configurations/{test_configuration.id}",
        json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["version"] == update_data["version"]
    assert data["configuration"] == update_data["configuration"]

@pytest.mark.asyncio
async def test_delete_configuration(client, test_configuration, db_session):
    """Test deleting a configuration."""
    db_session.add(test_configuration)
    await db_session.commit()

    response = client.delete(f"/api/v1/configurations/{test_configuration.id}")
    assert response.status_code == 204

    # Verify configuration is deleted
    response = client.get(f"/api/v1/configurations/{test_configuration.id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_configuration_history(client, test_configuration, db_session):
    """Test getting configuration history."""
    # Add test configuration and history
    db_session.add(test_configuration)
    history = ConfigurationHistory(
        configuration_id=test_configuration.id,
        version=test_configuration.version,
        configuration=test_configuration.configuration,
        created_at=datetime.utcnow()
    )
    db_session.add(history)
    await db_session.commit()

    response = client.get(f"/api/v1/configurations/{test_configuration.id}/history")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["version"] == test_configuration.version

@pytest.mark.asyncio
async def test_get_active_configuration(client, test_configuration, db_session):
    """Test getting active configuration."""
    db_session.add(test_configuration)
    await db_session.commit()

    response = client.get(f"/api/v1/configurations/component/{test_configuration.component}/active")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_configuration.name
    assert data["is_active"] == True

@pytest.mark.asyncio
async def test_configuration_not_found(client):
    """Test getting non-existent configuration."""
    response = client.get(f"/api/v1/configurations/{uuid4()}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_invalid_configuration_data(client):
    """Test creating configuration with invalid data."""
    invalid_data = {
        "name": "invalid-config",
        "component": "invalid-component",
        "version": "1.0.0",
        "configuration": "invalid-configuration"  # Should be a dict
    }

    response = client.post("/api/v1/configurations", json=invalid_data)
    assert response.status_code == 422  # Validation error 