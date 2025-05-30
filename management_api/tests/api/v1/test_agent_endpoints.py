"""Tests for agent management endpoints."""

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from opmas_mgmt_api.models.agents import Agent, AgentRule
from opmas_mgmt_api.schemas.agent import AgentCreate, AgentRuleCreate
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def test_agent_data():
    """Test agent data fixture."""
    return {
        "name": "test-agent",
        "type": "wifi",
        "config": {"key": "value"},
        "metadata": {"version": "1.0.0"},
    }


@pytest.fixture
def test_rule_data():
    """Test rule data fixture."""
    return {
        "name": "test-rule",
        "description": "Test rule description",
        "condition": {"type": "threshold", "value": 80},
        "action": {"type": "alert", "message": "Threshold exceeded"},
        "priority": 1,
        "enabled": True,
    }


@pytest.fixture
async def test_agent(db: AsyncSession, test_agent_data: dict) -> Agent:
    """Create test agent fixture."""
    agent = Agent(
        id=str(uuid4()),
        name=test_agent_data["name"],
        type=test_agent_data["type"],
        config=test_agent_data["config"],
        metadata=test_agent_data["metadata"],
        status="active",
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@pytest.fixture
async def test_rule(db: AsyncSession, test_agent: Agent, test_rule_data: dict) -> AgentRule:
    """Create test rule fixture."""
    rule = AgentRule(
        id=str(uuid4()),
        agent_id=test_agent.id,
        name=test_rule_data["name"],
        description=test_rule_data["description"],
        condition=test_rule_data["condition"],
        action=test_rule_data["action"],
        priority=test_rule_data["priority"],
        enabled=test_rule_data["enabled"],
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@pytest.mark.asyncio
async def test_list_agents(client: TestClient, test_agent: Agent):
    """Test listing agents."""
    response = client.get("/api/v1/agents/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == test_agent.id
    assert data[0]["name"] == test_agent.name
    assert data[0]["type"] == test_agent.type


@pytest.mark.asyncio
async def test_list_agents_with_type_filter(client: TestClient, test_agent: Agent):
    """Test listing agents with type filter."""
    response = client.get("/api/v1/agents/?agent_type=wifi")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == test_agent.id

    response = client.get("/api/v1/agents/?agent_type=security")
    assert response.status_code == 200
    assert len(response.json()) == 0


@pytest.mark.asyncio
async def test_create_agent(client: TestClient, test_agent_data: dict):
    """Test creating an agent."""
    response = client.post("/api/v1/agents/", json=test_agent_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_agent_data["name"]
    assert data["type"] == test_agent_data["type"]
    assert data["config"] == test_agent_data["config"]
    assert data["metadata"] == test_agent_data["metadata"]
    assert data["status"] == "inactive"


@pytest.mark.asyncio
async def test_create_agent_invalid_type(client: TestClient, test_agent_data: dict):
    """Test creating an agent with invalid type."""
    test_agent_data["type"] = "invalid"
    response = client.post("/api/v1/agents/", json=test_agent_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_agent(client: TestClient, test_agent: Agent):
    """Test getting an agent."""
    response = client.get(f"/api/v1/agents/{test_agent.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_agent.id
    assert data["name"] == test_agent.name
    assert data["type"] == test_agent.type


@pytest.mark.asyncio
async def test_get_nonexistent_agent(client: TestClient):
    """Test getting a nonexistent agent."""
    response = client.get(f"/api/v1/agents/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_agent(client: TestClient, test_agent: Agent):
    """Test updating an agent."""
    update_data = {"name": "updated-name", "config": {"new_key": "new_value"}}
    response = client.put(f"/api/v1/agents/{test_agent.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["config"] == update_data["config"]
    assert data["type"] == test_agent.type  # Unchanged field


@pytest.mark.asyncio
async def test_update_nonexistent_agent(client: TestClient):
    """Test updating a nonexistent agent."""
    response = client.put(f"/api/v1/agents/{uuid4()}", json={"name": "new-name"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_agent(client: TestClient, test_agent: Agent):
    """Test deleting an agent."""
    response = client.delete(f"/api/v1/agents/{test_agent.id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify agent is deleted
    response = client.get(f"/api/v1/agents/{test_agent.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_agent(client: TestClient):
    """Test deleting a nonexistent agent."""
    response = client.delete(f"/api/v1/agents/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_discover_agents(client: TestClient):
    """Test discovering agents."""
    response = client.get("/api/v1/agents/discover")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_agent_rules(client: TestClient, test_agent: Agent, test_rule: AgentRule):
    """Test listing agent rules."""
    response = client.get(f"/api/v1/agents/{test_agent.id}/rules")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == test_rule.id
    assert data[0]["name"] == test_rule.name


@pytest.mark.asyncio
async def test_create_agent_rule(client: TestClient, test_agent: Agent, test_rule_data: dict):
    """Test creating an agent rule."""
    response = client.post(f"/api/v1/agents/{test_agent.id}/rules", json=test_rule_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_rule_data["name"]
    assert data["description"] == test_rule_data["description"]
    assert data["condition"] == test_rule_data["condition"]
    assert data["action"] == test_rule_data["action"]
    assert data["priority"] == test_rule_data["priority"]
    assert data["enabled"] == test_rule_data["enabled"]


@pytest.mark.asyncio
async def test_create_rule_for_nonexistent_agent(client: TestClient, test_rule_data: dict):
    """Test creating a rule for a nonexistent agent."""
    response = client.post(f"/api/v1/agents/{uuid4()}/rules", json=test_rule_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_agent_rule(client: TestClient, test_agent: Agent, test_rule: AgentRule):
    """Test getting an agent rule."""
    response = client.get(f"/api/v1/agents/{test_agent.id}/rules/{test_rule.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_rule.id
    assert data["name"] == test_rule.name
    assert data["description"] == test_rule.description


@pytest.mark.asyncio
async def test_get_nonexistent_rule(client: TestClient, test_agent: Agent):
    """Test getting a nonexistent rule."""
    response = client.get(f"/api/v1/agents/{test_agent.id}/rules/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_agent_rule(client: TestClient, test_agent: Agent, test_rule: AgentRule):
    """Test updating an agent rule."""
    update_data = {"name": "updated-rule", "priority": 2, "enabled": False}
    response = client.put(f"/api/v1/agents/{test_agent.id}/rules/{test_rule.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["priority"] == update_data["priority"]
    assert data["enabled"] == update_data["enabled"]
    assert data["description"] == test_rule.description  # Unchanged field


@pytest.mark.asyncio
async def test_update_nonexistent_rule(client: TestClient, test_agent: Agent):
    """Test updating a nonexistent rule."""
    response = client.put(
        f"/api/v1/agents/{test_agent.id}/rules/{uuid4()}", json={"name": "new-rule"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_agent_rule(client: TestClient, test_agent: Agent, test_rule: AgentRule):
    """Test deleting an agent rule."""
    response = client.delete(f"/api/v1/agents/{test_agent.id}/rules/{test_rule.id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify rule is deleted
    response = client.get(f"/api/v1/agents/{test_agent.id}/rules/{test_rule.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_rule(client: TestClient, test_agent: Agent):
    """Test deleting a nonexistent rule."""
    response = client.delete(f"/api/v1/agents/{test_agent.id}/rules/{uuid4()}")
    assert response.status_code == 404
