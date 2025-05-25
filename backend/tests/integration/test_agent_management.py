import pytest

from opmas.core.agent import AgentManager
from opmas.core.exceptions import AgentError
from opmas.core.models import Agent, AgentStatus


def test_agent_creation(db_session, test_agent_data):
    """Test creating a new agent."""
    agent_manager = AgentManager(db_session)

    agent = agent_manager.create_agent(test_agent_data)

    assert agent.name == test_agent_data["name"]
    assert agent.type == test_agent_data["type"]
    assert agent.status == AgentStatus.ACTIVE
    assert agent.configuration == test_agent_data["configuration"]


def test_agent_retrieval(db_session, test_agent_data):
    """Test retrieving an agent."""
    agent_manager = AgentManager(db_session)
    created_agent = agent_manager.create_agent(test_agent_data)

    retrieved_agent = agent_manager.get_agent(created_agent.id)

    assert retrieved_agent.id == created_agent.id
    assert retrieved_agent.name == test_agent_data["name"]
    assert retrieved_agent.type == test_agent_data["type"]


def test_agent_update(db_session, test_agent_data):
    """Test updating an agent."""
    agent_manager = AgentManager(db_session)
    agent = agent_manager.create_agent(test_agent_data)

    update_data = {"status": AgentStatus.INACTIVE, "configuration": {"enabled": False}}

    updated_agent = agent_manager.update_agent(agent.id, update_data)

    assert updated_agent.status == AgentStatus.INACTIVE
    assert updated_agent.configuration["enabled"] is False


def test_agent_deletion(db_session, test_agent_data):
    """Test deleting an agent."""
    agent_manager = AgentManager(db_session)
    agent = agent_manager.create_agent(test_agent_data)

    agent_manager.delete_agent(agent.id)

    with pytest.raises(AgentError):
        agent_manager.get_agent(agent.id)


def test_agent_listing(db_session, test_agent_data):
    """Test listing all agents."""
    agent_manager = AgentManager(db_session)

    # Create multiple agents
    agent1 = agent_manager.create_agent(test_agent_data)
    agent2 = agent_manager.create_agent({**test_agent_data, "name": "test-agent-2"})

    agents = agent_manager.list_agents()

    assert len(agents) == 2
    assert any(a.id == agent1.id for a in agents)
    assert any(a.id == agent2.id for a in agents)


def test_agent_status_update(db_session, test_agent_data):
    """Test updating agent status."""
    agent_manager = AgentManager(db_session)
    agent = agent_manager.create_agent(test_agent_data)

    agent_manager.update_agent_status(agent.id, AgentStatus.ERROR)

    updated_agent = agent_manager.get_agent(agent.id)
    assert updated_agent.status == AgentStatus.ERROR


def test_agent_rule_management(db_session, test_agent_data):
    """Test managing agent rules."""
    agent_manager = AgentManager(db_session)
    agent = agent_manager.create_agent(test_agent_data)

    rule = {"name": "test-rule", "condition": "cpu_usage > 80", "action": "restart_service"}

    agent_manager.add_rule(agent.id, rule)

    updated_agent = agent_manager.get_agent(agent.id)
    assert len(updated_agent.configuration["rules"]) == 1
    assert updated_agent.configuration["rules"][0]["name"] == "test-rule"


def test_agent_heartbeat(db_session, test_agent_data):
    """Test agent heartbeat mechanism."""
    agent_manager = AgentManager(db_session)
    agent = agent_manager.create_agent(test_agent_data)

    agent_manager.update_heartbeat(agent.id)

    updated_agent = agent_manager.get_agent(agent.id)
    assert updated_agent.last_heartbeat is not None
