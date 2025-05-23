import pytest
from datetime import datetime
from opmas_mgmt_api.models.playbook import Playbook
from opmas_mgmt_api.models.playbook_execution import PlaybookExecution, ExecutionStatus
from opmas_mgmt_api.schemas.playbook import (
    PlaybookBase, PlaybookCreate, PlaybookUpdate,
    PlaybookInDB, PlaybookExecutionBase, PlaybookExecutionCreate
)

def test_playbook_model():
    # Test playbook creation
    playbook = Playbook(
        name="test-playbook",
        description="Test playbook description",
        steps=[{"type": "command", "action": "test-action"}],
        version="1.0.0",
        is_active=True
    )
    
    assert playbook.name == "test-playbook"
    assert playbook.description == "Test playbook description"
    assert len(playbook.steps) == 1
    assert playbook.version == "1.0.0"
    assert playbook.is_active is True
    assert isinstance(playbook.created_at, datetime)

def test_playbook_execution_model():
    # Test execution creation
    execution = PlaybookExecution(
        playbook_id=1,
        status=ExecutionStatus.PENDING
    )
    
    assert execution.playbook_id == 1
    assert execution.status == ExecutionStatus.PENDING
    assert execution.started_at is None
    assert execution.completed_at is None
    assert execution.results is None
    assert execution.error_message is None
    assert isinstance(execution.created_at, datetime)

def test_playbook_schema_validation():
    # Test valid playbook creation
    valid_playbook = PlaybookCreate(
        name="valid-playbook",
        description="Valid playbook",
        steps=[{"type": "command", "action": "test-action"}],
        version="1.0.0"
    )
    assert valid_playbook.name == "valid-playbook"
    
    # Test invalid name format
    with pytest.raises(ValueError, match="Invalid playbook name format"):
        PlaybookCreate(
            name="invalid name",
            description="Invalid playbook",
            steps=[{"type": "command", "action": "test-action"}],
            version="1.0.0"
        )
    
    # Test invalid version format
    with pytest.raises(ValueError, match="Version must be in format x.y.z"):
        PlaybookCreate(
            name="valid-playbook",
            description="Invalid version",
            steps=[{"type": "command", "action": "test-action"}],
            version="1.0"
        )
    
    # Test empty steps
    with pytest.raises(ValueError, match="Playbook must have at least one step"):
        PlaybookCreate(
            name="valid-playbook",
            description="No steps",
            steps=[],
            version="1.0.0"
        )
    
    # Test invalid step format
    with pytest.raises(ValueError, match="Each step must have a type field"):
        PlaybookCreate(
            name="valid-playbook",
            description="Invalid step",
            steps=[{"action": "test-action"}],
            version="1.0.0"
        )

def test_playbook_update_schema():
    # Test partial update
    update = PlaybookUpdate(
        name="updated-name",
        is_active=False
    )
    assert update.name == "updated-name"
    assert update.is_active is False
    assert update.description is None
    assert update.steps is None
    assert update.version is None

def test_playbook_execution_schema():
    # Test execution creation
    execution = PlaybookExecutionCreate(
        playbook_id=1,
        status=ExecutionStatus.PENDING
    )
    assert execution.playbook_id == 1
    assert execution.status == ExecutionStatus.PENDING
    assert execution.started_at is None
    assert execution.completed_at is None
    assert execution.results is None
    assert execution.error_message is None 