# Agent Implementation Plan for OPMAS

## 1. Project Setup

### 1.1 Directory Structure
```
backend/src/opmas/agents/[agent_name]/
├── __init__.py
├── agent.py              # Main agent implementation
├── .env.discovery        # Discovery metadata
├── requirements.txt      # Package dependencies
├── README.md            # Documentation
├── setup.py             # Package configuration
├── .env.example         # Example environment variables
└── tests/               # Test directory
    ├── __init__.py
    ├── test_agent.py
    └── test_integration.py
```

### 1.2 Initial Files

1. **setup.py**
```python
from setuptools import setup, find_packages

setup(
    name="opmas-[agent_name]",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "opmas-base-agent>=1.0.0",
        "nats-py>=2.3.1",
        "prometheus-client>=0.11.0",
        "python-dotenv>=0.19.0"
    ],
    entry_points={
        "opmas.agents": [
            "[agent_name]=agent:SpecificAgent"
        ]
    }
)
```

2. **.env.discovery**
```ini
# Required fields
AGENT_NAME=[AgentName]
AGENT_VERSION=1.0.0
AGENT_DESCRIPTION=[Agent description]

# Default Topics
DEFAULT_SUBSCRIBED_TOPICS=[topic1],[topic2]
DEFAULT_FINDINGS_TOPIC=findings.[agent_name]

# Agent Metadata
AGENT_TYPE=[type]
AGENT_CATEGORY=[category]
AGENT_AUTHOR=OPMAS Team
AGENT_LICENSE=MIT
AGENT_WEBSITE=https://opmas.example.com/agents/[agent_name]
AGENT_TAGS=[tag1],[tag2]

# Resource Requirements
AGENT_MIN_MEMORY=256MB
AGENT_MAX_MEMORY=1GB
AGENT_CPU_LIMIT=1
AGENT_DISK_SPACE=100MB

# Dependencies
AGENT_DEPENDENCIES=opmas-base-agent>=1.0.0,nats-py>=2.3.1
```

3. **requirements.txt**
```txt
opmas-base-agent>=1.0.0
nats-py>=2.3.1
prometheus-client>=0.11.0
python-dotenv>=0.19.0
pytest>=7.0.0
pytest-asyncio>=0.18.0
```

4. **.env.example**
```ini
# Required
OPMAS_AGENT_ID=[agent_name]-123
OPMAS_MANAGEMENT_API_URL=http://api.opmas
OPMAS_NATS_URL=nats://nats:4222

# Optional
OPMAS_LOG_LEVEL=INFO
OPMAS_METRICS_ENABLED=true
OPMAS_HEARTBEAT_INTERVAL=30
OPMAS_METRICS_INTERVAL=60
```

## 2. Core Implementation

### 2.1 Base Agent Class
```python
# agent.py
from opmas.base_agent import BaseAgent, Finding, AgentConfig
from typing import Dict, List, Optional
import asyncio
import logging
from datetime import datetime

class SpecificAgent(BaseAgent):
    def __init__(self, agent_id: str, management_api_url: str, initial_token: Optional[str] = None):
        super().__init__(agent_id, management_api_url, initial_token)
        self.rules = []
        self._setup_metrics()
        self._setup_logging()

    def _setup_metrics(self):
        """Setup agent metrics."""
        self.metrics.register_counter('events_processed', 'Total events processed')
        self.metrics.register_counter('errors', 'Total processing errors')
        self.metrics.register_histogram('processing_time', 'Event processing time')
        self.metrics.register_gauge('active_rules', 'Number of active rules')

    def _setup_logging(self):
        """Setup agent logging."""
        self.logger = logging.getLogger(self.agent_name)
        self.logger.setLevel(logging.INFO)

    async def start(self):
        """Initialize and start the agent."""
        await super().start()
        await self._load_rules()
        await self.subscribe_to_topics(self.config.get('SUBSCRIBED_TOPICS', []))
        self.logger.info(f"Agent {self.agent_name} started successfully.")

    async def stop(self):
        """Gracefully stop the agent."""
        self.logger.info(f"Agent {self.agent_name} stopping.")
        await super().stop()

    async def process_event(self, event: Dict):
        """Process incoming events."""
        start_time = datetime.utcnow()
        try:
            # Validate event
            if not self._validate_event(event):
                return

            # Process event
            findings = await self._process_event(event)

            # Publish findings
            if findings:
                await self.publish_findings(findings)

            # Update metrics
            self.metrics.increment('events_processed')
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.observe('processing_time', processing_time)

        except Exception as e:
            self.logger.error(f"Error processing event: {str(e)}", extra={'event_id': event.get('event_id')})
            self.metrics.increment('errors')
            await self.handle_error(e)

    def _validate_event(self, event: Dict) -> bool:
        """Validate incoming event."""
        required_fields = ['event_id', 'timestamp', 'type', 'message']
        return all(field in event for field in required_fields)

    async def _process_event(self, event: Dict) -> List[Finding]:
        """Process event and generate findings."""
        findings = []
        for rule in self.rules:
            if rule.get('pattern') in event.get('message', ''):
                finding = self.create_finding(
                    type=rule.get('type', 'generic_alert'),
                    severity=rule.get('severity', 'warning'),
                    description=f"Rule '{rule.get('name')}' matched",
                    details={
                        'event': self._sanitize_data(event),
                        'rule_id': rule.get('id'),
                        'matched_pattern': rule.get('pattern')
                    }
                )
                findings.append(finding)
        return findings

    def _sanitize_data(self, data: Dict) -> Dict:
        """Remove sensitive data before logging or publishing."""
        sanitized = data.copy()
        sensitive_fields = ['password', 'token', 'secret', 'key']
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '******'
        return sanitized

    async def handle_error(self, error: Exception):
        """Handle agent errors."""
        self.logger.error(f"Agent error: {str(error)}")
        self.metrics.increment('errors')

        # Report error to management system
        await self.report_error({
            'error': str(error),
            'timestamp': datetime.utcnow().isoformat(),
            'agent_id': self.agent_id
        })

    async def check_health(self) -> Dict:
        """Perform health check."""
        return {
            'status': 'healthy',
            'metrics': {
                'events_processed': self.metrics.get('events_processed'),
                'errors': self.metrics.get('errors'),
                'processing_time': self.metrics.get('processing_time'),
                'active_rules': self.metrics.get('active_rules')
            },
            'timestamp': datetime.utcnow().isoformat()
        }
```

## 3. Testing Implementation

### 3.1 Unit Tests
```python
# tests/test_agent.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from .agent import SpecificAgent

@pytest.fixture
def agent():
    return SpecificAgent("test-agent", "http://api.opmas")

@pytest.mark.asyncio
async def test_process_event(agent):
    event = {
        "event_id": "e-123",
        "timestamp": datetime.utcnow().isoformat(),
        "type": "test",
        "message": "Test event"
    }
    await agent.process_event(event)
    assert agent.metrics.get('events_processed') == 1

@pytest.mark.asyncio
async def test_validate_event(agent):
    valid_event = {
        "event_id": "e-123",
        "timestamp": datetime.utcnow().isoformat(),
        "type": "test",
        "message": "Test event"
    }
    assert agent._validate_event(valid_event) is True

    invalid_event = {
        "event_id": "e-123",
        "message": "Test event"
    }
    assert agent._validate_event(invalid_event) is False

@pytest.mark.asyncio
async def test_sanitize_data(agent):
    data = {
        "username": "test",
        "password": "secret",
        "message": "Test message"
    }
    sanitized = agent._sanitize_data(data)
    assert sanitized["password"] == "******"
    assert sanitized["username"] == "test"
```

### 3.2 Integration Tests
```python
# tests/test_integration.py
import pytest
from .agent import SpecificAgent

@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_lifecycle():
    agent = SpecificAgent("test-agent", "http://api.opmas")
    await agent.start()
    assert agent.is_running()
    await agent.stop()
    assert not agent.is_running()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_config_update():
    agent = SpecificAgent("test-agent", "http://api.opmas")
    await agent.start()

    new_config = {
        "rules": [
            {
                "id": "rule-1",
                "name": "Test Rule",
                "pattern": "test",
                "severity": "warning"
            }
        ]
    }

    await agent.update_config(new_config)
    assert len(agent.rules) == 1
    await agent.stop()
```

## 4. Documentation

### 4.1 README.md
```markdown
# [Agent Name]

## Description
[Detailed description of the agent's purpose and functionality]

## Installation
```bash
pip install -r requirements.txt
```

## Configuration
The agent can be configured through the OPMAS Management System.

### Environment Variables
- OPMAS_AGENT_ID: Unique identifier for the agent
- OPMAS_MANAGEMENT_API_URL: URL of the OPMAS Management API
- OPMAS_NATS_URL: URL of the NATS server
- OPMAS_LOG_LEVEL: Logging level (default: INFO)
- OPMAS_METRICS_ENABLED: Enable metrics collection (default: true)

## Topics
- Subscribes to: [list of subscribed topics]
- Publishes to: [list of published topics]

## Metrics
- events_processed: Total number of events processed
- errors: Number of processing errors
- processing_time: Event processing duration
- active_rules: Number of active rules

## Development
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
flake8
```

## License
MIT
```

## 5. Implementation Steps

1. **Setup Project Structure**
   - Create directory structure
   - Initialize git repository
   - Create initial files

2. **Implement Core Functionality**
   - Implement agent class
   - Add metrics collection
   - Add logging
   - Add event processing
   - Add error handling

3. **Add Testing**
   - Write unit tests
   - Write integration tests
   - Add test fixtures
   - Add test utilities

4. **Add Documentation**
   - Write README
   - Add docstrings
   - Add type hints
   - Add examples

5. **Add Security**
   - Implement data sanitization
   - Add input validation
   - Add error handling
   - Add security logging

6. **Add Monitoring**
   - Add health checks
   - Add metrics collection
   - Add performance monitoring
   - Add resource monitoring

7. **Testing and Validation**
   - Run unit tests
   - Run integration tests
   - Run security tests
   - Run performance tests

8. **Documentation and Review**
   - Review code
   - Update documentation
   - Add examples
   - Add troubleshooting guide

## 6. Message Formats

### 6.1 Event Format
```json
{
    "event_id": "e-123",
    "timestamp": "2025-05-27T12:00:00Z",
    "type": "security",
    "message": "Failed login attempt",
    "source": "auth_server",
    "details": {
        "username": "test_user",
        "ip": "192.168.1.1",
        "attempts": 3
    }
}
```

### 6.2 Finding Format
```json
{
    "finding_id": "f-123",
    "agent_id": "security-123",
    "type": "security_alert",
    "severity": "warning",
    "timestamp": "2025-05-27T12:00:00Z",
    "description": "Failed login attempt detected",
    "details": {
        "event_id": "e-123",
        "rule_id": "rule-1",
        "matched_pattern": "Failed login",
        "source": "auth_server",
        "ip": "192.168.1.1"
    }
}
```

### 6.3 Metrics Format
```json
{
    "agent_id": "security-123",
    "timestamp": "2025-05-27T12:00:00Z",
    "metrics": {
        "events_processed": 1000,
        "errors": 5,
        "processing_time": 0.5,
        "active_rules": 10
    }
}
```

## 7. Error Handling

### 7.1 Error Types
```python
class AgentError(Exception):
    """Base class for agent errors."""
    pass

class ConfigurationError(AgentError):
    """Configuration related errors."""
    pass

class ProcessingError(AgentError):
    """Event processing related errors."""
    pass

class CommunicationError(AgentError):
    """Communication related errors."""
    pass
```

### 7.2 Error Handling Strategy
```python
async def handle_error(self, error: Exception):
    """Handle agent errors."""
    if isinstance(error, ConfigurationError):
        self.logger.error(f"Configuration error: {str(error)}")
        await self.report_error({
            'type': 'configuration_error',
            'error': str(error),
            'timestamp': datetime.utcnow().isoformat()
        })
    elif isinstance(error, ProcessingError):
        self.logger.error(f"Processing error: {str(error)}")
        await self.report_error({
            'type': 'processing_error',
            'error': str(error),
            'timestamp': datetime.utcnow().isoformat()
        })
    elif isinstance(error, CommunicationError):
        self.logger.error(f"Communication error: {str(error)}")
        await self.report_error({
            'type': 'communication_error',
            'error': str(error),
            'timestamp': datetime.utcnow().isoformat()
        })
    else:
        self.logger.error(f"Unexpected error: {str(error)}")
        await self.report_error({
            'type': 'unexpected_error',
            'error': str(error),
            'timestamp': datetime.utcnow().isoformat()
        })
```

## 8. Resource Management

### 8.1 Resource Limits
```python
class ResourceLimits:
    def __init__(self):
        self.cpu_limit = 1.0  # CPU cores
        self.memory_limit = 1024 * 1024 * 1024  # 1GB
        self.disk_limit = 100 * 1024 * 1024  # 100MB
        self.network_limit = 1024 * 1024  # 1MB/s
```

### 8.2 Resource Monitoring
```python
class ResourceMonitor:
    def __init__(self):
        self.cpu_usage = 0.0
        self.memory_usage = 0
        self.disk_usage = 0
        self.network_usage = 0

    async def check_resources(self):
        """Check resource usage."""
        # Implement resource checking logic
        pass

    async def enforce_limits(self):
        """Enforce resource limits."""
        # Implement limit enforcement logic
        pass
```

## 9. Security Implementation

### 9.1 Authentication
```python
class Authentication:
    def __init__(self, token: str):
        self.token = token
        self.expires_at = None

    async def validate_token(self):
        """Validate authentication token."""
        # Implement token validation
        pass

    async def refresh_token(self):
        """Refresh authentication token."""
        # Implement token refresh
        pass
```

### 9.2 Authorization
```python
class Authorization:
    def __init__(self, permissions: List[str]):
        self.permissions = permissions

    def check_permission(self, action: str) -> bool:
        """Check if action is permitted."""
        return action in self.permissions
```

## 10. Deployment

### 10.1 Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "agent"]
```

### 10.2 Docker Compose
```yaml
version: '3.8'

services:
  agent:
    build: .
    environment:
      - OPMAS_AGENT_ID=${OPMAS_AGENT_ID}
      - OPMAS_MANAGEMENT_API_URL=${OPMAS_MANAGEMENT_API_URL}
      - OPMAS_NATS_URL=${OPMAS_NATS_URL}
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

## 11. Monitoring and Logging

### 11.1 Logging Configuration
```python
def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('agent.log')
        ]
    )
```

### 11.2 Metrics Configuration
```python
def setup_metrics():
    """Setup metrics configuration."""
    metrics = {
        'events_processed': Counter('events_processed_total', 'Total events processed'),
        'errors': Counter('errors_total', 'Total errors'),
        'processing_time': Histogram('processing_time_seconds', 'Event processing time'),
        'active_rules': Gauge('active_rules', 'Number of active rules')
    }
    return metrics
```

## 12. Testing Strategy

### 12.1 Test Categories
1. Unit Tests
   - Event processing
   - Rule matching
   - Finding creation
   - Error handling

2. Integration Tests
   - Agent lifecycle
   - Configuration updates
   - NATS communication
   - Management API interaction

3. Performance Tests
   - Event processing throughput
   - Resource usage
   - Memory leaks
   - CPU usage

4. Security Tests
   - Authentication
   - Authorization
   - Data sanitization
   - Error handling

### 12.2 Test Coverage
- Aim for >90% code coverage
- Test all error conditions
- Test all edge cases
- Test all security scenarios

## 13. Implementation Checklist

- [ ] Project setup
  - [ ] Create directory structure
  - [ ] Initialize git repository
  - [ ] Create initial files

- [ ] Core implementation
  - [ ] Implement agent class
  - [ ] Add metrics collection
  - [ ] Add logging
  - [ ] Add event processing
  - [ ] Add error handling

- [ ] Testing
  - [ ] Write unit tests
  - [ ] Write integration tests
  - [ ] Add test fixtures
  - [ ] Add test utilities

- [ ] Documentation
  - [ ] Write README
  - [ ] Add docstrings
  - [ ] Add type hints
  - [ ] Add examples

- [ ] Security
  - [ ] Implement data sanitization
  - [ ] Add input validation
  - [ ] Add error handling
  - [ ] Add security logging

- [ ] Monitoring
  - [ ] Add health checks
  - [ ] Add metrics collection
  - [ ] Add performance monitoring
  - [ ] Add resource monitoring

- [ ] Testing and validation
  - [ ] Run unit tests
  - [ ] Run integration tests
  - [ ] Run security tests
  - [ ] Run performance tests

- [ ] Documentation and review
  - [ ] Review code
  - [ ] Update documentation
  - [ ] Add examples
  - [ ] Add troubleshooting guide

## 14. Development Environment Setup

### 14.1 Development Tools
```bash
# Required tools
python3.9+
pip
virtualenv
git
docker
docker-compose
pytest
flake8
mypy
black
```

### 14.2 Development Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install
```

### 14.3 IDE Configuration
```json
{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.rulers": [88],
    "files.trimTrailingWhitespace": true
}
```

## 15. CI/CD Pipeline

### 15.1 GitHub Actions Workflow
```yaml
name: CI/CD

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    - name: Run tests
      run: |
        pytest
    - name: Run linting
      run: |
        flake8
        mypy .
        black --check .

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Build Docker image
      run: |
        docker build -t opmas-agent .
    - name: Push Docker image
      run: |
        docker push opmas-agent
```

## 16. Monitoring Setup

### 16.1 Prometheus Configuration
```yaml
scrape_configs:
  - job_name: 'opmas-agent'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scheme: 'http'
```

### 16.2 Grafana Dashboard
```json
{
  "dashboard": {
    "id": null,
    "title": "OPMAS Agent Dashboard",
    "tags": ["opmas", "agent"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Events Processed",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "rate(events_processed_total[5m])",
            "legendFormat": "Events/sec"
          }
        ]
      }
    ]
  }
}
```

## 17. Security Implementation

### 17.1 Security Headers
```python
SECURITY_HEADERS = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Content-Security-Policy': "default-src 'self'"
}
```

### 17.2 Rate Limiting
```python
RATE_LIMITS = {
    'events': {
        'rate': 1000,  # events per second
        'burst': 2000  # maximum burst
    },
    'api': {
        'rate': 100,   # requests per second
        'burst': 200   # maximum burst
    }
}
```

## 18. Error Handling Implementation

### 18.1 Error Codes
```python
ERROR_CODES = {
    'CONFIG_ERROR': 1000,
    'PROCESSING_ERROR': 2000,
    'COMMUNICATION_ERROR': 3000,
    'RESOURCE_ERROR': 4000,
    'SECURITY_ERROR': 5000
}
```

### 18.2 Error Responses
```python
ERROR_RESPONSES = {
    'CONFIG_ERROR': {
        'status': 'error',
        'code': 1000,
        'message': 'Configuration error',
        'details': {}
    },
    'PROCESSING_ERROR': {
        'status': 'error',
        'code': 2000,
        'message': 'Processing error',
        'details': {}
    }
}
```

## 19. Testing Implementation

### 19.1 Test Configuration
```python
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --cov=agent --cov-report=html
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    security: Security tests
```

### 19.2 Test Data
```python
# tests/fixtures/test_data.py
TEST_EVENTS = [
    {
        "event_id": "e-123",
        "timestamp": "2025-05-27T12:00:00Z",
        "type": "test",
        "message": "Test event"
    }
]

TEST_RULES = [
    {
        "id": "rule-1",
        "name": "Test Rule",
        "pattern": "test",
        "severity": "warning"
    }
]
```

## 20. Documentation Implementation

### 20.1 API Documentation
```python
# docs/api.md
"""
# OPMAS Agent API

## Endpoints

### GET /health
Health check endpoint.

### POST /events
Process events endpoint.

### GET /metrics
Metrics endpoint.
"""
```

### 20.2 Configuration Documentation
```python
# docs/configuration.md
"""
# OPMAS Agent Configuration

## Environment Variables

### Required
- OPMAS_AGENT_ID
- OPMAS_MANAGEMENT_API_URL
- OPMAS_NATS_URL

### Optional
- OPMAS_LOG_LEVEL
- OPMAS_METRICS_ENABLED
"""
```

## 21. Deployment Implementation

### 21.1 Kubernetes Configuration
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opmas-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: opmas-agent
  template:
    metadata:
      labels:
        app: opmas-agent
    spec:
      containers:
      - name: opmas-agent
        image: opmas-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPMAS_AGENT_ID
          valueFrom:
            secretKeyRef:
              name: opmas-secrets
              key: agent-id
```

### 21.2 Helm Chart
```yaml
# helm/opmas-agent/values.yaml
replicaCount: 3
image:
  repository: opmas-agent
  tag: latest
  pullPolicy: IfNotPresent
resources:
  limits:
    cpu: 1
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi
```

## 22. Maintenance Implementation

### 22.1 Backup Script
```bash
#!/bin/bash
# scripts/backup.sh

# Backup configuration
cp .env.discovery backup/env.discovery.$(date +%Y%m%d)

# Backup state
cp state.json backup/state.$(date +%Y%m%d).json

# Backup logs
cp agent.log backup/logs.$(date +%Y%m%d).log
```

### 22.2 Update Script
```bash
#!/bin/bash
# scripts/update.sh

# Pull latest changes
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Restart service
systemctl restart opmas-agent
```

## 23. Support Implementation

### 23.1 Issue Template
```markdown
# Bug Report

## Description
[Detailed description of the bug]

## Steps to Reproduce
1. [First step]
2. [Second step]
3. [And so on...]

## Expected Behavior
[What you expected to happen]

## Actual Behavior
[What actually happened]

## Environment
- Agent Version: [Version]
- OS: [OS]
- Python Version: [Python Version]
```

### 23.2 Support Script
```bash
#!/bin/bash
# scripts/support.sh

# Collect system information
echo "System Information"
uname -a
python --version
pip list

# Collect agent information
echo "Agent Information"
cat .env.discovery
cat agent.log | tail -n 100

# Collect resource usage
echo "Resource Usage"
top -b -n 1
free -m
df -h
```

## 24. Implementation Timeline

### 24.1 Phase 1: Setup (Week 1)
- [ ] Project structure
- [ ] Development environment
- [ ] Basic implementation
- [ ] Unit tests

### 24.2 Phase 2: Core Features (Week 2)
- [ ] Event processing
- [ ] Rule matching
- [ ] Finding generation
- [ ] Integration tests

### 24.3 Phase 3: Security (Week 3)
- [ ] Authentication
- [ ] Authorization
- [ ] Data protection
- [ ] Security tests

### 24.4 Phase 4: Monitoring (Week 4)
- [ ] Metrics collection
- [ ] Health checks
- [ ] Resource monitoring
- [ ] Performance tests

### 24.5 Phase 5: Deployment (Week 5)
- [ ] Docker configuration
- [ ] Kubernetes configuration
- [ ] CI/CD pipeline
- [ ] Deployment tests

### 24.6 Phase 6: Documentation (Week 6)
- [ ] API documentation
- [ ] User guide
- [ ] Developer guide
- [ ] Troubleshooting guide

## 25. Success Criteria

### 25.1 Performance
- Event processing time < 100ms
- Memory usage < 1GB
- CPU usage < 1 core
- Network bandwidth < 1MB/s

### 25.2 Reliability
- Uptime > 99.9%
- Error rate < 0.1%
- Recovery time < 5 minutes
- Data loss = 0

### 25.3 Security
- No critical vulnerabilities
- All security tests pass
- Compliance with standards
- Secure communication

### 25.4 Quality
- Code coverage > 90%
- All tests pass
- No linting errors
- Documentation complete
