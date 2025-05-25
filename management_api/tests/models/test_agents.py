"""Test agent management models."""

from datetime import datetime
from uuid import UUID, uuid4

import pytest
from opmas_mgmt_api.core.exceptions import ValidationError
from opmas_mgmt_api.models.agents import Agent, AgentConfigHistory, AgentStatusHistory
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


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
        last_seen=datetime.utcnow(),
    )


@pytest.fixture
def test_status_history(test_agent):
    """Create a test status history entry."""
    return AgentStatusHistory(
        id=uuid4(),
        agent_id=test_agent.id,
        status="online",
        details={"reason": "startup"},
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def test_config_history(test_agent):
    """Create a test config history entry."""
    return AgentConfigHistory(
        id=uuid4(),
        agent_id=test_agent.id,
        config={"scan_interval": 300},
        version="1.0.0",
        metadata={"updated_by": "system"},
        created_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_create_agent(db: AsyncSession, test_agent: Agent):
    """Test creating an agent in the database."""
    db.add(test_agent)
    await db.commit()
    await db.refresh(test_agent)

    result = await db.execute(select(Agent).where(Agent.id == test_agent.id))
    agent = result.scalar_one_or_none()
    assert agent is not None
    assert agent.id == test_agent.id
    assert agent.name == test_agent.name
    assert agent.agent_type == test_agent.agent_type
    assert agent.hostname == test_agent.hostname
    assert agent.ip_address == test_agent.ip_address
    assert agent.port == test_agent.port
    assert agent.status == test_agent.status
    assert agent.enabled == test_agent.enabled
    assert agent.metadata == test_agent.metadata
    assert agent.config == test_agent.config


@pytest.mark.asyncio
async def test_create_agent_validation():
    """Test agent creation validation."""
    with pytest.raises(ValidationError):
        Agent(
            id=uuid4(),
            name="",  # Invalid empty name
            agent_type="invalid",  # Invalid agent type
            hostname="test-agent.local",
            ip_address="invalid-ip",  # Invalid IP address
            port=70000,  # Invalid port
        )


@pytest.mark.asyncio
async def test_create_status_history(
    db: AsyncSession, test_agent: Agent, test_status_history: AgentStatusHistory
):
    """Test creating a status history entry in the database."""
    db.add(test_status_history)
    await db.commit()
    await db.refresh(test_status_history)

    result = await db.execute(
        select(AgentStatusHistory).where(AgentStatusHistory.id == test_status_history.id)
    )
    history = result.scalar_one_or_none()
    assert history is not None
    assert history.id == test_status_history.id
    assert history.agent_id == test_status_history.agent_id
    assert history.status == test_status_history.status
    assert history.details == test_status_history.details


@pytest.mark.asyncio
async def test_create_config_history(
    db: AsyncSession, test_agent: Agent, test_config_history: AgentConfigHistory
):
    """Test creating a config history entry in the database."""
    db.add(test_config_history)
    await db.commit()
    await db.refresh(test_config_history)

    result = await db.execute(
        select(AgentConfigHistory).where(AgentConfigHistory.id == test_config_history.id)
    )
    history = result.scalar_one_or_none()
    assert history is not None
    assert history.id == test_config_history.id
    assert history.agent_id == test_config_history.agent_id
    assert history.config == test_config_history.config
    assert history.version == test_config_history.version
    assert history.metadata == test_config_history.metadata


@pytest.mark.asyncio
async def test_agent_relationships(
    db: AsyncSession,
    test_agent: Agent,
    test_status_history: AgentStatusHistory,
    test_config_history: AgentConfigHistory,
):
    """Test agent relationships."""
    db.add(test_agent)
    db.add(test_status_history)
    db.add(test_config_history)
    await db.commit()
    await db.refresh(test_agent)

    assert len(test_agent.status_history) == 1
    assert test_agent.status_history[0].id == test_status_history.id
    assert len(test_agent.config_history) == 1
    assert test_agent.config_history[0].id == test_config_history.id


@pytest.mark.asyncio
async def test_agent_cascade_delete(
    db: AsyncSession,
    test_agent: Agent,
    test_status_history: AgentStatusHistory,
    test_config_history: AgentConfigHistory,
):
    """Test agent cascade delete."""
    db.add(test_agent)
    db.add(test_status_history)
    db.add(test_config_history)
    await db.commit()

    await db.delete(test_agent)
    await db.commit()

    result = await db.execute(
        select(AgentStatusHistory).where(AgentStatusHistory.agent_id == test_agent.id)
    )
    assert result.scalar_one_or_none() is None

    result = await db.execute(
        select(AgentConfigHistory).where(AgentConfigHistory.agent_id == test_agent.id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_agent_status_validation():
    """Test agent status validation."""
    with pytest.raises(ValidationError):
        Agent(
            id=uuid4(),
            name="test-agent",
            agent_type="wifi",
            hostname="test-agent.local",
            ip_address="192.168.1.100",
            port=8080,
            status="invalid_status",  # Invalid status
            enabled=True,
        )


@pytest.mark.asyncio
async def test_agent_type_validation():
    """Test agent type validation."""
    with pytest.raises(ValidationError):
        Agent(
            id=uuid4(),
            name="test-agent",
            agent_type="invalid_type",  # Invalid agent type
            hostname="test-agent.local",
            ip_address="192.168.1.100",
            port=8080,
            status="online",
            enabled=True,
        )


@pytest.mark.asyncio
async def test_agent_port_validation():
    """Test agent port validation."""
    with pytest.raises(ValidationError):
        Agent(
            id=uuid4(),
            name="test-agent",
            agent_type="wifi",
            hostname="test-agent.local",
            ip_address="192.168.1.100",
            port=70000,  # Invalid port
            status="online",
            enabled=True,
        )


@pytest.mark.asyncio
async def test_agent_ip_validation():
    """Test agent IP validation."""
    with pytest.raises(ValidationError):
        Agent(
            id=uuid4(),
            name="test-agent",
            agent_type="wifi",
            hostname="test-agent.local",
            ip_address="invalid-ip",  # Invalid IP address
            port=8080,
            status="online",
            enabled=True,
        )
