"""Test agent management service."""

import pytest
from datetime import datetime
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from opmas_mgmt_api.models.agents import Agent, AgentStatusHistory, AgentConfigHistory
from opmas_mgmt_api.schemas.agents import AgentCreate, AgentUpdate, AgentStatus, AgentConfig
from opmas_mgmt_api.services.agents import AgentService
from opmas_mgmt_api.core.exceptions import NotFoundError, ValidationError

@pytest.fixture
def test_agent():
    """Create a test agent."""
    return Agent(
        id=uuid4(),
        name="test-agent",
        agent_type="wifi",
        hostname="test-agent.local",
        ip_address="192.168.1.100",
        port=8080,
        status="online",
        enabled=True,
        metadata={"version": "1.0.0"},
        config={"scan_interval": 300},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )

@pytest.fixture
def test_agent_create():
    """Create a test agent creation payload."""
    return AgentCreate(
        name="test-agent",
        agent_type="wifi",
        hostname="test-agent.local",
        ip_address="192.168.1.100",
        port=8080,
        status="online",
        enabled=True,
        metadata={"version": "1.0.0"},
        config={"scan_interval": 300}
    )

@pytest.fixture
def test_agent_update():
    """Create a test agent update payload."""
    return AgentUpdate(
        name="updated-agent",
        status="offline",
        metadata={"version": "1.1.0"}
    )

@pytest.fixture
def mock_db_session(test_agent):
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = test_agent
    session.execute.return_value.scalar_one_or_none.return_value = test_agent
    return session

@pytest.fixture
def mock_nats():
    """Create a mock NATS manager."""
    nats = AsyncMock()
    return nats

@pytest.fixture
def agent_service(mock_db_session, mock_nats):
    """Create an agent service instance."""
    return AgentService(mock_db_session, mock_nats)

@pytest.mark.asyncio
async def test_list_agents(agent_service, test_agent):
    """Test listing agents."""
    result = await agent_service.list_agents()
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].id == test_agent.id

@pytest.mark.asyncio
async def test_list_agents_with_filters(agent_service, test_agent):
    """Test listing agents with filters."""
    result = await agent_service.list_agents(
        agent_type="wifi",
        status="online",
        enabled=True
    )
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].id == test_agent.id

@pytest.mark.asyncio
async def test_create_agent(agent_service, test_agent_create):
    """Test creating an agent."""
    result = await agent_service.create_agent(test_agent_create)
    assert result.name == test_agent_create.name
    assert result.agent_type == test_agent_create.agent_type
    assert result.hostname == test_agent_create.hostname
    assert result.ip_address == test_agent_create.ip_address

@pytest.mark.asyncio
async def test_get_agent(agent_service, test_agent):
    """Test getting an agent."""
    result = await agent_service.get_agent(test_agent.id)
    assert result.id == test_agent.id
    assert result.name == test_agent.name

@pytest.mark.asyncio
async def test_update_agent(agent_service, test_agent, test_agent_update):
    """Test updating an agent."""
    result = await agent_service.update_agent(test_agent.id, test_agent_update)
    assert result.name == test_agent_update.name
    assert result.status == test_agent_update.status
    assert result.metadata == test_agent_update.metadata

@pytest.mark.asyncio
async def test_delete_agent(agent_service, test_agent):
    """Test deleting an agent."""
    await agent_service.delete_agent(test_agent.id)
    agent_service.db.delete.assert_called_once_with(test_agent)
    agent_service.db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_agent_status(agent_service, test_agent):
    """Test getting agent status."""
    result = await agent_service.get_agent_status(test_agent.id)
    assert result.status == test_agent.status
    assert result.last_seen == test_agent.last_seen
    assert result.device_status == test_agent.device_status
    assert result.details == test_agent.status_details

@pytest.mark.asyncio
async def test_update_agent_status(agent_service, test_agent):
    """Test updating agent status."""
    status = "offline"
    details = {"reason": "maintenance"}
    result = await agent_service.update_agent_status(test_agent.id, status, details)
    assert result.status == status
    assert result.status_details == details

@pytest.mark.asyncio
async def test_get_agent_config(agent_service, test_agent):
    """Test getting agent configuration."""
    result = await agent_service.get_agent_config(test_agent.id)
    assert result.config == test_agent.config
    assert result.version == test_agent.config_version
    assert result.last_updated == test_agent.config_updated_at

@pytest.mark.asyncio
async def test_update_agent_config(agent_service, test_agent):
    """Test updating agent configuration."""
    config = {"scan_interval": 600}
    version = "1.1.0"
    metadata = {"updated_by": "test"}
    result = await agent_service.update_agent_config(test_agent.id, config, version, metadata)
    assert result.config == config
    assert result.config_version == version
    assert result.config_metadata == metadata

@pytest.mark.asyncio
async def test_discover_agents(agent_service):
    """Test agent discovery."""
    result = await agent_service.discover_agents()
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_get_nonexistent_agent(agent_service):
    """Test getting a nonexistent agent."""
    with pytest.raises(NotFoundError):
        await agent_service.get_agent(uuid4())

@pytest.mark.asyncio
async def test_update_nonexistent_agent(agent_service, test_agent_update):
    """Test updating a nonexistent agent."""
    with pytest.raises(NotFoundError):
        await agent_service.update_agent(uuid4(), test_agent_update)

@pytest.mark.asyncio
async def test_delete_nonexistent_agent(agent_service):
    """Test deleting a nonexistent agent."""
    with pytest.raises(NotFoundError):
        await agent_service.delete_agent(uuid4())

@pytest.mark.asyncio
async def test_create_agent_validation(agent_service):
    """Test agent creation validation."""
    invalid_agent = AgentCreate(
        name="",  # Invalid empty name
        agent_type="invalid",  # Invalid agent type
        hostname="test-agent.local",
        ip_address="invalid-ip",  # Invalid IP address
        port=70000  # Invalid port
    )
    with pytest.raises(ValidationError):
        await agent_service.create_agent(invalid_agent)

@pytest.mark.asyncio
async def test_update_agent_validation(agent_service, test_agent):
    """Test agent update validation."""
    invalid_update = AgentUpdate(
        agent_type="invalid",  # Invalid agent type
        port=70000  # Invalid port
    )
    with pytest.raises(ValidationError):
        await agent_service.update_agent(test_agent.id, invalid_update)

@pytest.mark.asyncio
async def test_update_agent_status_validation(agent_service, test_agent):
    """Test agent status update validation."""
    with pytest.raises(ValidationError):
        await agent_service.update_agent_status(test_agent.id, "invalid_status")

@pytest.mark.asyncio
async def test_update_agent_config_validation(agent_service, test_agent):
    """Test agent config update validation."""
    with pytest.raises(ValidationError):
        await agent_service.update_agent_config(test_agent.id, {}, "", {}) 