import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from opmas_mgmt_api.main import app
from opmas_mgmt_api.models.playbook import Playbook
from opmas_mgmt_api.models.playbook_execution import PlaybookExecution, ExecutionStatus
from opmas_mgmt_api.database import Base, get_db
from opmas_mgmt_api.auth.jwt import create_access_token

client = TestClient(app)

# Test data
TEST_PLAYBOOK = {
    "name": "test-playbook",
    "description": "Test playbook description",
    "steps": [{"type": "command", "action": "test-action"}],
    "version": "1.0.0"
}

@pytest.fixture
def test_db():
    # Create test database and tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user_token():
    return create_access_token({"sub": "testuser"})

@pytest.fixture
def test_playbook(test_db):
    playbook = Playbook(**TEST_PLAYBOOK)
    test_db.add(playbook)
    test_db.commit()
    test_db.refresh(playbook)
    return playbook

def test_create_playbook(test_db, test_user_token):
    response = client.post(
        "/api/v1/playbooks",
        json=TEST_PLAYBOOK,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == TEST_PLAYBOOK["name"]
    assert data["description"] == TEST_PLAYBOOK["description"]
    assert len(data["steps"]) == len(TEST_PLAYBOOK["steps"])
    assert data["version"] == TEST_PLAYBOOK["version"]
    assert data["is_active"] is True

def test_get_playbook(test_db, test_user_token, test_playbook):
    response = client.get(
        f"/api/v1/playbooks/{test_playbook.id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_playbook.name
    assert data["description"] == test_playbook.description
    assert len(data["steps"]) == len(test_playbook.steps)
    assert data["version"] == test_playbook.version

def test_update_playbook(test_db, test_user_token, test_playbook):
    update_data = {
        "name": "updated-playbook",
        "description": "Updated description",
        "is_active": False
    }
    response = client.put(
        f"/api/v1/playbooks/{test_playbook.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["is_active"] == update_data["is_active"]

def test_delete_playbook(test_db, test_user_token, test_playbook):
    response = client.delete(
        f"/api/v1/playbooks/{test_playbook.id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Playbook deleted successfully"
    
    # Verify playbook is deleted
    response = client.get(
        f"/api/v1/playbooks/{test_playbook.id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 404

def test_execute_playbook(test_db, test_user_token, test_playbook):
    response = client.post(
        f"/api/v1/playbooks/{test_playbook.id}/execute",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["playbook_id"] == test_playbook.id
    assert data["status"] == ExecutionStatus.PENDING
    assert data["started_at"] is None
    assert data["completed_at"] is None

def test_list_playbook_executions(test_db, test_user_token, test_playbook):
    # Create some test executions
    executions = [
        PlaybookExecution(playbook_id=test_playbook.id, status=ExecutionStatus.PENDING),
        PlaybookExecution(playbook_id=test_playbook.id, status=ExecutionStatus.COMPLETED)
    ]
    for execution in executions:
        test_db.add(execution)
    test_db.commit()
    
    response = client.get(
        f"/api/v1/playbooks/{test_playbook.id}/executions",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["status"] == ExecutionStatus.COMPLETED
    assert data[1]["status"] == ExecutionStatus.PENDING

def test_update_execution(test_db, test_user_token, test_playbook):
    # Create test execution
    execution = PlaybookExecution(playbook_id=test_playbook.id, status=ExecutionStatus.PENDING)
    test_db.add(execution)
    test_db.commit()
    test_db.refresh(execution)
    
    update_data = {
        "status": ExecutionStatus.COMPLETED,
        "results": {"output": "Test completed successfully"}
    }
    response = client.put(
        f"/api/v1/playbooks/executions/{execution.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == ExecutionStatus.COMPLETED
    assert data["results"] == update_data["results"] 