# OPMAS Architecture Specification

## 1. System Overview

OPMAS (Open Platform for Multi-Agent Security) is a distributed security monitoring system that uses multiple specialized agents to collect, analyze, and respond to security events. The system is designed to be:
- Scalable: Can handle large volumes of security events
- Extensible: Easy to add new agent types
- Resilient: Fault-tolerant and self-healing
- Secure: End-to-end encryption and authentication

## 2. System Architecture

### 2.1 High-Level Architecture
```mermaid
graph TD
    A[Security Agents] --> B[NATS]
    B --> C[Management System]
    B --> D[Analysis Engine]
    D --> E[Database]
    C --> E
    C --> F[API Gateway]
    F --> G[Web UI]
```

### 2.2 Component Interaction
```mermaid
sequenceDiagram
    participant A as Agent
    participant N as NATS
    participant M as Management
    participant D as Database
    participant E as Engine

    A->>N: Publish Event
    N->>E: Forward Event
    E->>D: Store Event
    E->>N: Publish Finding
    N->>M: Forward Finding
    M->>D: Update Status
```

## 3. Core Components

### 3.1 Security Agents
```python
class SecurityAgent:
    """Base class for security agents."""

    def __init__(self, agent_id: str, config: Dict):
        self.agent_id = agent_id
        self.config = config
        self.nats_client = None
        self.management_client = None

    async def start(self):
        """Start the agent."""
        await self._connect_nats()
        await self._connect_management()
        await self._start_monitoring()

    async def stop(self):
        """Stop the agent."""
        await self._stop_monitoring()
        await self._disconnect_management()
        await self._disconnect_nats()
```

### 3.2 NATS Communication
```python
class NATSClient:
    """NATS client for agent communication."""

    def __init__(self, url: str, credentials: Dict):
        self.url = url
        self.credentials = credentials
        self.client = None

    async def connect(self):
        """Connect to NATS server."""
        self.client = await nats.connect(
            self.url,
            credentials=self.credentials
        )

    async def publish(self, subject: str, data: Dict):
        """Publish message to NATS."""
        await self.client.publish(
            subject,
            json.dumps(data).encode()
        )

    async def subscribe(self, subject: str, callback: Callable):
        """Subscribe to NATS subject."""
        await self.client.subscribe(
            subject,
            cb=callback
        )
```

### 3.3 Management System
```python
class ManagementSystem:
    """Management system for agents."""

    def __init__(self, db_url: str):
        self.db = Database(db_url)
        self.agents = {}

    async def register_agent(self, agent: Dict) -> str:
        """Register new agent."""
        agent_id = str(uuid.uuid4())
        await self.db.store_agent(agent_id, agent)
        self.agents[agent_id] = agent
        return agent_id

    async def update_agent(self, agent_id: str, update: Dict):
        """Update agent configuration."""
        await self.db.update_agent(agent_id, update)
        self.agents[agent_id].update(update)
```

### 3.4 Analysis Engine
```python
class AnalysisEngine:
    """Engine for analyzing security events."""

    def __init__(self, db_url: str):
        self.db = Database(db_url)
        self.rules = []

    async def process_event(self, event: Dict) -> List[Dict]:
        """Process security event."""
        findings = []
        for rule in self.rules:
            if await rule.matches(event):
                finding = await rule.generate_finding(event)
                findings.append(finding)
        return findings

    async def add_rule(self, rule: Dict):
        """Add analysis rule."""
        self.rules.append(rule)
        await self.db.store_rule(rule)
```

## 4. Data Flow

### 4.1 Event Flow
```mermaid
graph LR
    A[Agent] -->|Event| B[NATS]
    B -->|Event| C[Engine]
    C -->|Finding| B
    B -->|Finding| D[Management]
    D -->|Status| E[Database]
```

### 4.2 Control Flow
```mermaid
graph LR
    A[Management] -->|Config| B[NATS]
    B -->|Config| C[Agent]
    C -->|Status| B
    B -->|Status| A
```

## 5. Security Architecture

### 5.1 Authentication
```python
class Authentication:
    """Authentication service."""

    def __init__(self, secret: str):
        self.secret = secret

    def generate_token(self, agent_id: str) -> str:
        """Generate JWT token."""
        payload = {
            "agent_id": agent_id,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, self.secret, algorithm="HS256")

    def validate_token(self, token: str) -> bool:
        """Validate JWT token."""
        try:
            jwt.decode(token, self.secret, algorithms=["HS256"])
            return True
        except jwt.InvalidTokenError:
            return False
```

### 5.2 Authorization
```python
class Authorization:
    """Authorization service."""

    def __init__(self, db_url: str):
        self.db = Database(db_url)

    async def check_permission(self, agent_id: str, action: str) -> bool:
        """Check if agent has permission."""
        permissions = await self.db.get_permissions(agent_id)
        return action in permissions

    async def grant_permission(self, agent_id: str, action: str):
        """Grant permission to agent."""
        await self.db.add_permission(agent_id, action)
```

## 6. Database Schema

### 6.1 Events Table
```sql
CREATE TABLE events (
    id UUID PRIMARY KEY,
    agent_id UUID NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);
```

### 6.2 Findings Table
```sql
CREATE TABLE findings (
    id UUID PRIMARY KEY,
    event_id UUID NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    details JSONB,
    FOREIGN KEY (event_id) REFERENCES events(id)
);
```

### 6.3 Agents Table
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    config JSONB,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

## 7. API Design

### 7.1 REST API
```python
# Agent Management
POST /api/v1/agents
GET /api/v1/agents/{agent_id}
PUT /api/v1/agents/{agent_id}
DELETE /api/v1/agents/{agent_id}

# Event Management
POST /api/v1/events
GET /api/v1/events/{event_id}
GET /api/v1/events?agent_id={agent_id}

# Finding Management
GET /api/v1/findings
GET /api/v1/findings/{finding_id}
GET /api/v1/findings?event_id={event_id}
```

### 7.2 WebSocket API
```python
# Real-time Updates
ws://api/v1/ws/events
ws://api/v1/ws/findings
ws://api/v1/ws/agents
```

## 8. Deployment Architecture

### 8.1 Docker Compose
```yaml
version: '3'
services:
  nats:
    image: nats:latest
    ports:
      - "4222:4222"

  management:
    build: ./management
    depends_on:
      - nats
      - postgres
    environment:
      - NATS_URL=nats://nats:4222
      - DB_URL=postgresql://postgres:postgres@postgres:5432/opmas

  postgres:
    image: postgres:latest
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=opmas
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### 8.2 Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opmas
spec:
  replicas: 3
  selector:
    matchLabels:
      app: opmas
  template:
    metadata:
      labels:
        app: opmas
    spec:
      containers:
      - name: management
        image: opmas-management:latest
        ports:
        - containerPort: 8000
        env:
        - name: NATS_URL
          valueFrom:
            configMapKeyRef:
              name: opmas-config
              key: nats_url
        - name: DB_URL
          valueFrom:
            secretKeyRef:
              name: opmas-secrets
              key: db_url
```

## 9. Monitoring and Logging

### 9.1 Metrics
```python
class Metrics:
    """Metrics collection."""

    def __init__(self):
        self.events_processed = Counter()
        self.findings_generated = Counter()
        self.processing_time = Histogram()

    def record_event(self, event_type: str):
        """Record processed event."""
        self.events_processed.inc()

    def record_finding(self, severity: str):
        """Record generated finding."""
        self.findings_generated.inc()

    def record_processing_time(self, duration: float):
        """Record processing time."""
        self.processing_time.observe(duration)
```

### 9.2 Logging
```python
class Logger:
    """System logging."""

    def __init__(self, level: str):
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('opmas')

    def log_event(self, event: Dict):
        """Log event processing."""
        self.logger.info(
            f"Processing event {event['id']}",
            extra=event
        )

    def log_finding(self, finding: Dict):
        """Log finding generation."""
        self.logger.info(
            f"Generated finding {finding['id']}",
            extra=finding
        )
```

## 10. Error Handling

### 10.1 Error Types
```python
class OPMASError(Exception):
    """Base class for OPMAS errors."""
    pass

class AgentError(OPMASError):
    """Agent related errors."""
    pass

class CommunicationError(OPMASError):
    """Communication related errors."""
    pass

class DatabaseError(OPMASError):
    """Database related errors."""
    pass
```

### 10.2 Error Handling
```python
class ErrorHandler:
    """Error handling service."""

    def __init__(self, logger: Logger):
        self.logger = logger

    async def handle_error(self, error: Exception):
        """Handle system error."""
        self.logger.error(f"Error: {str(error)}")

        if isinstance(error, AgentError):
            await self.handle_agent_error(error)
        elif isinstance(error, CommunicationError):
            await self.handle_communication_error(error)
        elif isinstance(error, DatabaseError):
            await self.handle_database_error(error)
        else:
            await self.handle_unexpected_error(error)
```

## 11. Testing Strategy

### 11.1 Unit Tests
```python
class TestAgent:
    """Unit tests for agent."""

    def test_initialization(self):
        """Test agent initialization."""
        agent = SecurityAgent("test-agent", {})
        assert agent.agent_id == "test-agent"

    def test_event_processing(self):
        """Test event processing."""
        agent = SecurityAgent("test-agent", {})
        event = {"type": "test", "data": {}}
        result = agent.process_event(event)
        assert result is not None
```

### 11.2 Integration Tests
```python
class TestSystem:
    """Integration tests for system."""

    async def test_event_flow(self):
        """Test event flow through system."""
        # Start system
        system = await start_system()

        # Send event
        event = {"type": "test", "data": {}}
        await system.send_event(event)

        # Check finding
        findings = await system.get_findings()
        assert len(findings) > 0
```

## 12. Documentation

### 12.1 API Documentation
```python
"""
# OPMAS API Documentation

## Authentication
All API requests require authentication using JWT tokens.

## Endpoints
- POST /api/v1/agents
  Register new agent
- GET /api/v1/agents/{agent_id}
  Get agent details
- POST /api/v1/events
  Submit security event
- GET /api/v1/findings
  Get security findings
"""
```

### 12.2 Agent Documentation
```python
"""
# OPMAS Agent Documentation

## Overview
OPMAS agents are responsible for collecting and analyzing security events.

## Implementation
Agents should:
1. Connect to NATS
2. Register with management system
3. Process events
4. Generate findings
5. Report status

## Configuration
Agents are configured using JSON configuration files.
"""
```

## 13. Maintenance

### 13.1 Backup Strategy
```bash
#!/bin/bash
# Backup script

# Backup database
pg_dump -U postgres opmas > backup/db_$(date +%Y%m%d).sql

# Backup configurations
cp config/* backup/config_$(date +%Y%m%d)/

# Backup logs
cp logs/* backup/logs_$(date +%Y%m%d)/
```

### 13.2 Update Strategy
```bash
#!/bin/bash
# Update script

# Pull latest changes
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Restart services
docker-compose restart
```

## 14. Support

### 14.1 Issue Tracking
```python
class IssueTracker:
    """Issue tracking system."""

    def __init__(self, db_url: str):
        self.db = Database(db_url)

    async def create_issue(self, issue: Dict):
        """Create new issue."""
        await self.db.store_issue(issue)

    async def update_issue(self, issue_id: str, update: Dict):
        """Update issue."""
        await self.db.update_issue(issue_id, update)
```

### 14.2 Support Process
```python
class SupportProcess:
    """Support process management."""

    def __init__(self, tracker: IssueTracker):
        self.tracker = tracker

    async def handle_support_request(self, request: Dict):
        """Handle support request."""
        # Create issue
        issue = await self.tracker.create_issue(request)

        # Notify support team
        await self.notify_support_team(issue)

        # Track resolution
        await self.track_resolution(issue)
```
