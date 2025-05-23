from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import re
from ..models.playbook_execution import ExecutionStatus

class PlaybookBase(BaseModel):
    name: str
    description: str
    steps: List[Dict[str, Any]]
    version: str

    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]$', v):
            raise ValueError('Invalid playbook name format')
        return v

    @validator('version')
    def validate_version(cls, v):
        if not re.match(r'^\d+\.\d+\.\d+$', v):
            raise ValueError('Version must be in format x.y.z')
        return v

    @validator('steps')
    def validate_steps(cls, v):
        if not v:
            raise ValueError('Playbook must have at least one step')
        for step in v:
            if not isinstance(step, dict):
                raise ValueError('Each step must be a dictionary')
            if 'type' not in step:
                raise ValueError('Each step must have a type field')
            if 'action' not in step:
                raise ValueError('Each step must have an action field')
        return v

class PlaybookCreate(PlaybookBase):
    pass

class PlaybookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None

    @validator('name')
    def validate_name(cls, v):
        if v is not None and not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]$', v):
            raise ValueError('Invalid playbook name format')
        return v

    @validator('version')
    def validate_version(cls, v):
        if v is not None and not re.match(r'^\d+\.\d+\.\d+$', v):
            raise ValueError('Version must be in format x.y.z')
        return v

    @validator('steps')
    def validate_steps(cls, v):
        if v is not None:
            if not v:
                raise ValueError('Playbook must have at least one step')
            for step in v:
                if not isinstance(step, dict):
                    raise ValueError('Each step must be a dictionary')
                if 'type' not in step:
                    raise ValueError('Each step must have a type field')
                if 'action' not in step:
                    raise ValueError('Each step must have an action field')
        return v

class PlaybookInDB(PlaybookBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class PlaybookStatus(BaseModel):
    is_active: bool
    updated_at: datetime

class PlaybookExecutionBase(BaseModel):
    playbook_id: int
    status: ExecutionStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class PlaybookExecutionCreate(PlaybookExecutionBase):
    pass

class PlaybookExecutionUpdate(BaseModel):
    status: Optional[ExecutionStatus] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class PlaybookExecutionInDB(PlaybookExecutionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True 