# Agent Management System Implementation Plan for OPMAS

## 15. Agent Package Requirements

### 15.1 Package Structure
```
backend/src/opmas/agents/[agent_name]/
├── __init__.py
├── agent.py              # Main agent implementation
├── .env.discovery        # Discovery metadata
├── requirements.txt      # Package dependencies
├── README.md            # Documentation
└── tests/               # Test directory
    ├── __init__.py
    ├── test_agent.py
    └── test_config.py
```

### 15.2 Required Files

1. **agent.py**
   ```python
   from opmas.base_agent import BaseAgent
   from typing import Dict, Optional

   class SpecificAgent(BaseAgent):
       def __init__(self, agent_id: str, management_api_url: str, initial_token: Optional[str] = None):
           super().__init__(agent_id, management_api_url, initial_token)
           self.config = {}

       async def start(self):
           """Initialize and start the agent."""
           await super().start()
           await self._load_config()
           await self.subscribe_to_topics(self.config.get('SUBSCRIBED_TOPICS', []))
           self.logger.info(f"Agent {self.agent_name} started successfully.")

       async def process_event(self, event: Dict):
           """Process incoming events."""
           try:
               # Implement event processing logic
               self.metrics.increment('events_processed')
           except Exception as e:
               self.logger.error(f"Error processing event: {str(e)}")
               self.metrics.increment('errors')
   ```

2. **.env.discovery**
   ```ini
   # Required fields
   AGENT_NAME=SecurityAgent
   AGENT_VERSION=1.0.0
   AGENT_DESCRIPTION=Security monitoring agent for OPMAS

   # Default Topics
   DEFAULT_SUBSCRIBED_TOPICS=logs.security,logs.auth
   DEFAULT_FINDINGS_TOPIC=findings.security

   # Optional fields
   AGENT_TYPE=security
   AGENT_CATEGORY=monitoring
   AGENT_AUTHOR=OPMAS Team
   AGENT_LICENSE=MIT
   ```

3. **requirements.txt**
   ```txt
   opmas-base-agent>=1.0.0
   nats-py>=2.3.1
   prometheus-client>=0.11.0
   python-dotenv>=0.19.0
   ```

4. **README.md**
   ```markdown
   # Security Agent

   ## Description
   Security monitoring agent for OPMAS that processes security-related events and generates findings.

   ## Installation
   ```bash
   pip install -r requirements.txt
   ```

   ## Configuration
   The agent can be configured through the OPMAS Management System.

   ## Topics
   - Subscribes to: logs.security, logs.auth
   - Publishes to: findings.security

   ## Metrics
   - events_processed: Total number of events processed
   - errors: Number of processing errors
   - processing_time: Event processing duration
   ```

### 15.3 Implementation Requirements

1. **BaseAgent Inheritance**
   - Must inherit from `opmas.base_agent.BaseAgent`
   - Implement required abstract methods
   - Follow lifecycle management protocol

2. **Configuration Management**
   ```python
   async def _load_config(self):
       """Load agent configuration."""
       self.config = await self.get_config()
       self.logger.info(f"Loaded configuration: {self.config}")
   ```

3. **Event Processing**
   ```python
   async def process_event(self, event: Dict):
       """Process incoming events."""
       try:
           # Validate event
           if not self._validate_event(event):
               return

           # Process event
           result = await self._process_event(event)

           # Publish findings
           if result:
               await self.publish_finding(result)

           # Update metrics
           self.metrics.increment('events_processed')

       except Exception as e:
           self.logger.error(f"Error processing event: {str(e)}")
           self.metrics.increment('errors')
   ```

4. **Metrics Collection**
   ```python
   def _setup_metrics(self):
       """Setup agent metrics."""
       self.metrics.register_counter('events_processed', 'Total events processed')
       self.metrics.register_counter('errors', 'Total processing errors')
       self.metrics.register_histogram('processing_time', 'Event processing time')
   ```

5. **Health Checks**
   ```python
   async def check_health(self) -> Dict:
       """Perform health check."""
       return {
           'status': 'healthy',
           'metrics': {
               'events_processed': self.metrics.get('events_processed'),
               'errors': self.metrics.get('errors'),
               'processing_time': self.metrics.get('processing_time')
           },
           'timestamp': datetime.utcnow().isoformat()
       }
   ```

6. **Error Handling**
   ```python
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
   ```

### 15.4 Testing Requirements

1. **Unit Tests**
   ```python
   # tests/test_agent.py
   import pytest
   from unittest.mock import Mock, patch
   from .agent import SpecificAgent

   @pytest.fixture
   def agent():
       return SpecificAgent("test-agent", "http://api.opmas")

   async def test_process_event(agent):
       event = {"type": "security", "message": "Test event"}
       await agent.process_event(event)
       assert agent.metrics.get('events_processed') == 1
   ```

2. **Integration Tests**
   ```python
   # tests/test_integration.py
   import pytest
   from .agent import SpecificAgent

   @pytest.mark.integration
   async def test_agent_lifecycle():
       agent = SpecificAgent("test-agent", "http://api.opmas")
       await agent.start()
       assert agent.is_running()
       await agent.stop()
       assert not agent.is_running()
   ```

### 15.5 Documentation Requirements

1. **Code Documentation**
   - Docstrings for all classes and methods
   - Type hints for function parameters
   - Example usage in docstrings

2. **Configuration Documentation**
   - List of all configuration options
   - Default values
   - Environment variable overrides

3. **API Documentation**
   - Input/output formats
   - Error codes
   - Example requests/responses

### 15.6 Security Requirements

1. **Authentication**
   ```python
   async def authenticate(self):
       """Authenticate with management system."""
       token = await self.get_auth_token()
       self.nats_client.set_auth_token(token)
   ```

2. **Authorization**
   ```python
   async def check_permissions(self, action: str) -> bool:
       """Check if agent has permission for action."""
       return await self.management_api.check_permission(
           self.agent_id,
           action
       )
   ```

3. **Data Protection**
   ```python
   def _sanitize_data(self, data: Dict) -> Dict:
       """Remove sensitive data before logging."""
       sanitized = data.copy()
       if 'password' in sanitized:
           sanitized['password'] = '******'
       return sanitized
   ```

### 15.7 Monitoring Requirements

1. **Metrics**
   - Event processing metrics
   - Resource usage metrics
   - Error metrics
   - Performance metrics

2. **Logging**
   ```python
   def _setup_logging(self):
       """Setup agent logging."""
       self.logger = logging.getLogger(self.agent_name)
       self.logger.setLevel(logging.INFO)
   ```

3. **Health Checks**
   - Regular health status updates
   - Resource usage monitoring
   - Error rate monitoring
   - Performance monitoring

### 15.8 Deployment Requirements

1. **Package Distribution**
   ```python
   # setup.py
   from setuptools import setup, find_packages

   setup(
       name="opmas-security-agent",
       version="1.0.0",
       packages=find_packages(),
       install_requires=[
           "opmas-base-agent>=1.0.0",
           "nats-py>=2.3.1"
       ],
       entry_points={
           "opmas.agents": [
               "security=agent:SpecificAgent"
           ]
       }
   )
   ```

2. **Environment Variables**
   ```bash
   # Required
   OPMAS_AGENT_ID=security-123
   OPMAS_MANAGEMENT_API_URL=http://api.opmas
   OPMAS_NATS_URL=nats://nats:4222

   # Optional
   OPMAS_LOG_LEVEL=INFO
   OPMAS_METRICS_ENABLED=true
   ```

3. **Resource Limits**
   ```yaml
   # Resource configuration
   resources:
     cpu: "100%"
     memory: "512MB"
     disk: "1GB"
   ```
