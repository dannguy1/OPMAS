"""Test system management models."""

import pytest
from datetime import datetime
from uuid import uuid4
from sqlalchemy import select

from opmas_mgmt_api.models.system import SystemConfig
from opmas_mgmt_api.db.base_class import Base
from opmas_mgmt_api.db.session import async_session

@pytest.fixture
def test_system_config():
    """Create test system config."""
    return SystemConfig(
        id=str(uuid4()),
        version="1.0.0",
        components={
            "database": {"pool_size": 10},
            "nats": {"max_reconnects": 5}
        },
        security={
            "jwt_secret": "test-secret",
            "token_expiry": 3600
        },
        logging={
            "level": "INFO",
            "format": "json"
        }
    )

async def test_create_system_config(test_system_config):
    """Test creating system config."""
    async with async_session() as session:
        session.add(test_system_config)
        await session.commit()
        await session.refresh(test_system_config)
        
        assert test_system_config.id is not None
        assert test_system_config.version == "1.0.0"
        assert test_system_config.components["database"]["pool_size"] == 10
        assert test_system_config.components["nats"]["max_reconnects"] == 5
        assert test_system_config.security["jwt_secret"] == "test-secret"
        assert test_system_config.security["token_expiry"] == 3600
        assert test_system_config.logging["level"] == "INFO"
        assert test_system_config.logging["format"] == "json"
        assert test_system_config.created_at is not None
        assert test_system_config.updated_at is not None

async def test_read_system_config(test_system_config):
    """Test reading system config."""
    async with async_session() as session:
        session.add(test_system_config)
        await session.commit()
        
        query = select(SystemConfig).where(SystemConfig.id == test_system_config.id)
        result = await session.execute(query)
        config = result.scalar_one_or_none()
        
        assert config is not None
        assert config.id == test_system_config.id
        assert config.version == test_system_config.version
        assert config.components == test_system_config.components
        assert config.security == test_system_config.security
        assert config.logging == test_system_config.logging

async def test_update_system_config(test_system_config):
    """Test updating system config."""
    async with async_session() as session:
        session.add(test_system_config)
        await session.commit()
        
        # Update config
        test_system_config.version = "1.0.1"
        test_system_config.components["database"]["pool_size"] = 20
        await session.commit()
        await session.refresh(test_system_config)
        
        assert test_system_config.version == "1.0.1"
        assert test_system_config.components["database"]["pool_size"] == 20
        assert test_system_config.updated_at > test_system_config.created_at

async def test_delete_system_config(test_system_config):
    """Test deleting system config."""
    async with async_session() as session:
        session.add(test_system_config)
        await session.commit()
        
        # Delete config
        await session.delete(test_system_config)
        await session.commit()
        
        # Verify deletion
        query = select(SystemConfig).where(SystemConfig.id == test_system_config.id)
        result = await session.execute(query)
        config = result.scalar_one_or_none()
        
        assert config is None

async def test_system_config_timestamps(test_system_config):
    """Test system config timestamps."""
    async with async_session() as session:
        session.add(test_system_config)
        await session.commit()
        await session.refresh(test_system_config)
        
        assert test_system_config.created_at is not None
        assert test_system_config.updated_at is not None
        assert test_system_config.created_at == test_system_config.updated_at
        
        # Update config
        test_system_config.version = "1.0.1"
        await session.commit()
        await session.refresh(test_system_config)
        
        assert test_system_config.updated_at > test_system_config.created_at

async def test_system_config_validation():
    """Test system config validation."""
    with pytest.raises(ValueError):
        SystemConfig(
            id=str(uuid4()),
            version=None,  # Required field
            components={},
            security={},
            logging={}
        )
    
    with pytest.raises(ValueError):
        SystemConfig(
            id=str(uuid4()),
            version="1.0.0",
            components=None,  # Required field
            security={},
            logging={}
        )
    
    with pytest.raises(ValueError):
        SystemConfig(
            id=str(uuid4()),
            version="1.0.0",
            components={},
            security=None,  # Required field
            logging={}
        )
    
    with pytest.raises(ValueError):
        SystemConfig(
            id=str(uuid4()),
            version="1.0.0",
            components={},
            security={},
            logging=None  # Required field
        ) 