from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from datetime import datetime
import re

class RuleBase(BaseModel):
    name: str
    description: str
    condition: Dict[str, Any]
    action: Dict[str, Any]
    priority: int = 0
    agent_id: int

    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]$', v):
            raise ValueError('Invalid rule name format')
        return v

    @validator('priority')
    def validate_priority(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Priority must be between 0 and 100')
        return v

    @validator('condition')
    def validate_condition(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Condition must be a dictionary')
        if 'type' not in v:
            raise ValueError('Condition must have a type field')
        return v

    @validator('action')
    def validate_action(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Action must be a dictionary')
        if 'type' not in v:
            raise ValueError('Action must have a type field')
        return v

class RuleCreate(RuleBase):
    pass

class RuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    condition: Optional[Dict[str, Any]] = None
    action: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    agent_id: Optional[int] = None

    @validator('name')
    def validate_name(cls, v):
        if v is not None and not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]$', v):
            raise ValueError('Invalid rule name format')
        return v

    @validator('priority')
    def validate_priority(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Priority must be between 0 and 100')
        return v

    @validator('condition')
    def validate_condition(cls, v):
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Condition must be a dictionary')
            if 'type' not in v:
                raise ValueError('Condition must have a type field')
        return v

    @validator('action')
    def validate_action(cls, v):
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Action must be a dictionary')
            if 'type' not in v:
                raise ValueError('Action must have a type field')
        return v

class RuleInDB(RuleBase):
    id: int
    enabled: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class RuleStatus(BaseModel):
    enabled: bool
    updated_at: datetime 