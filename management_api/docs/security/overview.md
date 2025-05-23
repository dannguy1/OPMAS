# Security Guide

## Overview
This guide outlines the security measures and best practices for the OPMAS Management API, covering authentication, authorization, data protection, and system security.

## Security Architecture

### 1. Authentication
- JWT-based authentication
- Token refresh mechanism
- Password hashing with bcrypt
- Session management
- Rate limiting

### 2. Authorization
- Role-based access control (RBAC)
- Resource-level permissions
- API endpoint protection
- Audit logging

### 3. Data Protection
- TLS/SSL encryption
- Data encryption at rest
- Secure password storage
- Input validation
- Output sanitization

### 4. System Security
- Network security
- Firewall configuration
- Security headers
- CORS policies
- Rate limiting

## Implementation Details

### 1. Authentication Implementation

#### JWT Configuration
```python
# config.py
JWT_CONFIG = {
    "secret_key": os.getenv("JWT_SECRET"),
    "algorithm": "HS256",
    "access_token_expire_minutes": 30,
    "refresh_token_expire_days": 7
}
```

#### Password Hashing
```python
# auth/utils.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

### 2. Authorization Implementation

#### Role-Based Access Control
```python
# auth/rbac.py
from enum import Enum
from typing import List

class Role(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"

ROLE_PERMISSIONS = {
    Role.ADMIN: [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.EXECUTE],
    Role.OPERATOR: [Permission.READ, Permission.WRITE, Permission.EXECUTE],
    Role.VIEWER: [Permission.READ]
}
```

#### Permission Check
```python
# auth/dependencies.py
from fastapi import Depends, HTTPException, status
from .rbac import Role, Permission

async def check_permission(
    required_permission: Permission,
    current_user = Depends(get_current_user)
):
    user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
    if required_permission not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
```

### 3. Data Protection

#### Input Validation
```python
# schemas/device.py
from pydantic import BaseModel, validator, IPvAnyAddress
import re

class DeviceCreate(BaseModel):
    hostname: str
    ip_address: IPvAnyAddress
    device_type: str

    @validator('hostname')
    def validate_hostname(cls, v):
        if not re.match(r'^[a-zA-Z0-9-]+$', v):
            raise ValueError('Invalid hostname format')
        return v
```

#### Output Sanitization
```python
# utils/sanitize.py
import html

def sanitize_output(data: str) -> str:
    return html.escape(data)
```

### 4. System Security

#### Security Headers
```python
# middleware/security.py
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

def configure_security(app: FastAPI):
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("CORS_ORIGINS", "").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trusted Hosts
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=os.getenv("ALLOWED_HOSTS", "").split(",")
    )
```

#### Rate Limiting
```python
# middleware/rate_limit.py
from fastapi import Request, HTTPException
import time
from redis import Redis

class RateLimiter:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.requests_per_minute = int(os.getenv("RATE_LIMIT_REQUESTS", 60))

    async def check_rate_limit(self, request: Request):
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        current = self.redis.get(key)
        if current and int(current) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Too many requests"
            )
        
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, 60)
        pipe.execute()
```

## Security Best Practices

### 1. Password Policy
- Minimum length: 12 characters
- Require uppercase and lowercase
- Require numbers and special characters
- Prevent common passwords
- Regular password rotation

### 2. API Security
- Use HTTPS only
- Implement rate limiting
- Validate all inputs
- Sanitize all outputs
- Use secure headers

### 3. Database Security
- Use connection pooling
- Implement query parameterization
- Regular security updates
- Backup encryption
- Access control

### 4. Network Security
- Firewall configuration
- VPN access
- Network segmentation
- Regular security scans
- Intrusion detection

## Security Monitoring

### 1. Logging
```python
# logging/security.py
import structlog
from datetime import datetime

logger = structlog.get_logger()

def log_security_event(
    event_type: str,
    user_id: int,
    details: dict
):
    logger.info(
        "security_event",
        event_type=event_type,
        user_id=user_id,
        timestamp=datetime.utcnow().isoformat(),
        **details
    )
```

### 2. Audit Trail
```python
# models/audit.py
from sqlalchemy import Column, Integer, String, DateTime, JSON
from ..database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    action = Column(String)
    resource = Column(String)
    details = Column(JSON)
    timestamp = Column(DateTime(timezone=True))
```

### 3. Monitoring
- Failed login attempts
- API usage patterns
- Resource access
- System changes
- Security events

## Incident Response

### 1. Security Incidents
1. Unauthorized access
2. Data breaches
3. System compromise
4. Service disruption

### 2. Response Procedures
1. Identify the incident
2. Contain the threat
3. Eradicate the cause
4. Recover systems
5. Document lessons

### 3. Reporting
- Internal reporting
- External notification
- Regulatory compliance
- Documentation
- Follow-up actions

## Compliance

### 1. Standards
- OWASP Top 10
- NIST Cybersecurity Framework
- ISO 27001
- GDPR
- HIPAA

### 2. Requirements
- Data protection
- Access control
- Audit logging
- Incident response
- Security training

### 3. Documentation
- Security policies
- Procedures
- Guidelines
- Training materials
- Compliance reports

## Security Tools

### 1. Development
- Static code analysis
- Dependency scanning
- Security testing
- Code review
- Penetration testing

### 2. Operations
- Vulnerability scanning
- Intrusion detection
- Log analysis
- Network monitoring
- Security automation

### 3. Monitoring
- Security metrics
- Performance monitoring
- Alert management
- Incident tracking
- Compliance reporting

## Support Resources

### 1. Documentation
- [API Security](../api/security.md)
- [Deployment Security](../deployment/security.md)
- [Incident Response](../security/incident_response.md)

### 2. Tools
- [Security Checklist](../tools/security_checklist.md)
- [Audit Templates](../tools/audit_templates.md)
- [Compliance Guide](../tools/compliance_guide.md)

### 3. Contact
- Security Team: security@example.com
- Emergency Contact: emergency@example.com
- Compliance Officer: compliance@example.com 