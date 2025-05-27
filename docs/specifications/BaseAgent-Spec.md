# Base Agent Specification for OPMAS

## 1. Overview

The BaseAgent class provides the foundation for all OPMAS agents. It handles common functionality such as:
- NATS communication
- Configuration management
- Health monitoring
- Metrics collection
- Resource management
- Security controls

## 2. Class Definition

```python
class BaseAgent:
    def __init__(self, agent_id: str, management_api_url: str, initial_token: Optional[str] = None):
        self.agent_id = agent_id
        self.management_api_url = management_api_url
        self.initial_token = initial_token
        self.config = {}
        self.metrics = {}
        self.logger = None
        self.nats_client = None
        self.is_running = False
        self._setup_logging()
        self._setup_metrics()
```

## 3. Core Methods

### 3.1 Lifecycle Methods
```python
async def start(self):
    """Initialize and start the agent."""
    await self._connect_nats()
    await self._fetch_config()
    await self._setup_subscriptions()
    self.is_running = True
    await self._start_heartbeat()

async def stop(self):
    """Gracefully stop the agent."""
    self.is_running = False
    await self._stop_heartbeat()
    await self._close_subscriptions()
    await self._disconnect_nats()
```

### 3.2 Configuration Methods
```python
async def _fetch_config(self):
    """Fetch configuration from management API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{self.management_api_url}/agents/{self.agent_id}/config",
            headers={"Authorization": f"Bearer {self.initial_token}"}
        ) as response:
            if response.status == 200:
                self.config = await response.json()
            else:
                raise ConfigurationError("Failed to fetch configuration")

async def update_config(self, new_config: Dict):
    """Update agent configuration."""
    self.config.update(new_config)
    await self._validate_config()
    await self._apply_config()
```

### 3.3 Communication Methods
```python
async def _connect_nats(self):
    """Connect to NATS server."""
    self.nats_client = await nats.connect(
        self.config.get("NATS_URL"),
        credentials=self.config.get("NATS_CREDENTIALS")
    )

async def subscribe_to_topics(self, topics: List[str]):
    """Subscribe to NATS topics."""
    for topic in topics:
        await self.nats_client.subscribe(
            topic,
            cb=self._handle_message
        )

async def publish_finding(self, finding: Finding):
    """Publish finding to NATS."""
    await self.nats_client.publish(
        self.config.get("FINDINGS_TOPIC"),
        finding.to_json().encode()
    )
```

### 3.4 Monitoring Methods
```python
async def _start_heartbeat(self):
    """Start heartbeat publishing."""
    while self.is_running:
        await self._publish_heartbeat()
        await asyncio.sleep(self.config.get("HEARTBEAT_INTERVAL", 30))

async def _publish_heartbeat(self):
    """Publish heartbeat message."""
    heartbeat = {
        "agent_id": self.agent_id,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy" if self._check_health() else "unhealthy"
    }
    await self.nats_client.publish(
        f"opmas.heartbeat.{self.agent_id}",
        json.dumps(heartbeat).encode()
    )
```

### 3.5 Resource Management Methods
```python
async def _check_resources(self):
    """Check resource usage."""
    resources = {
        "cpu": psutil.cpu_percent(),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent
    }
    return resources

async def _enforce_limits(self):
    """Enforce resource limits."""
    resources = await self._check_resources()
    if resources["cpu"] > self.config.get("CPU_LIMIT", 80):
        self.logger.warning("CPU usage exceeded limit")
    if resources["memory"] > self.config.get("MEMORY_LIMIT", 80):
        self.logger.warning("Memory usage exceeded limit")
```

### 3.6 Security Methods
```python
async def _validate_token(self):
    """Validate authentication token."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{self.management_api_url}/auth/validate",
            headers={"Authorization": f"Bearer {self.initial_token}"}
        ) as response:
            if response.status != 200:
                raise AuthenticationError("Invalid token")

async def _refresh_token(self):
    """Refresh authentication token."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{self.management_api_url}/auth/refresh",
            headers={"Authorization": f"Bearer {self.initial_token}"}
        ) as response:
            if response.status == 200:
                data = await response.json()
                self.initial_token = data["token"]
            else:
                raise AuthenticationError("Failed to refresh token")
```

## 4. Error Handling

### 4.1 Error Types
```python
class AgentError(Exception):
    """Base class for agent errors."""
    pass

class ConfigurationError(AgentError):
    """Configuration related errors."""
    pass

class CommunicationError(AgentError):
    """Communication related errors."""
    pass

class AuthenticationError(AgentError):
    """Authentication related errors."""
    pass

class ResourceError(AgentError):
    """Resource related errors."""
    pass
```

### 4.2 Error Handling Methods
```python
async def handle_error(self, error: Exception):
    """Handle agent errors."""
    self.logger.error(f"Agent error: {str(error)}")
    self.metrics.increment('errors')

    if isinstance(error, ConfigurationError):
        await self._handle_config_error(error)
    elif isinstance(error, CommunicationError):
        await self._handle_communication_error(error)
    elif isinstance(error, AuthenticationError):
        await self._handle_authentication_error(error)
    elif isinstance(error, ResourceError):
        await self._handle_resource_error(error)
    else:
        await self._handle_unexpected_error(error)

async def _handle_config_error(self, error: ConfigurationError):
    """Handle configuration errors."""
    self.logger.error(f"Configuration error: {str(error)}")
    await self.report_error({
        'type': 'configuration_error',
        'error': str(error),
        'timestamp': datetime.utcnow().isoformat()
    })
```

## 5. Metrics Collection

### 5.1 Metric Types
```python
class Metric:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.value = 0

class Counter(Metric):
    def increment(self, amount: int = 1):
        self.value += amount

class Gauge(Metric):
    def set(self, value: float):
        self.value = value

class Histogram(Metric):
    def observe(self, value: float):
        self.values.append(value)
        self.value = statistics.mean(self.values)
```

### 5.2 Metric Methods
```python
def _setup_metrics(self):
    """Setup agent metrics."""
    self.metrics = {
        'events_processed': Counter('events_processed', 'Total events processed'),
        'errors': Counter('errors', 'Total errors'),
        'processing_time': Histogram('processing_time', 'Event processing time'),
        'active_rules': Gauge('active_rules', 'Number of active rules')
    }

async def _publish_metrics(self):
    """Publish metrics to NATS."""
    metrics = {
        "agent_id": self.agent_id,
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            name: metric.value
            for name, metric in self.metrics.items()
        }
    }
    await self.nats_client.publish(
        f"opmas.metrics.{self.agent_id}",
        json.dumps(metrics).encode()
    )
```

## 6. Logging

### 6.1 Logging Configuration
```python
def _setup_logging(self):
    """Setup agent logging."""
    self.logger = logging.getLogger(self.agent_id)
    self.logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    self.logger.addHandler(handler)
```

### 6.2 Logging Methods
```python
def log_event(self, event: Dict):
    """Log event processing."""
    self.logger.info(
        f"Processing event {event.get('event_id')}",
        extra={
            'event_id': event.get('event_id'),
            'event_type': event.get('type'),
            'timestamp': event.get('timestamp')
        }
    )

def log_error(self, error: Exception, context: Dict = None):
    """Log error with context."""
    self.logger.error(
        f"Error: {str(error)}",
        extra=context or {}
    )
```

## 7. Security

### 7.1 Security Configuration
```python
SECURITY_CONFIG = {
    'token_refresh_interval': 3600,  # 1 hour
    'max_retries': 3,
    'retry_delay': 5,  # seconds
    'rate_limit': {
        'events': 1000,  # events per second
        'api': 100  # requests per second
    }
}
```

### 7.2 Security Methods
```python
async def _validate_input(self, data: Dict):
    """Validate input data."""
    if not isinstance(data, dict):
        raise ValueError("Input must be a dictionary")

    required_fields = ['event_id', 'timestamp', 'type']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

def _sanitize_output(self, data: Dict) -> Dict:
    """Sanitize output data."""
    sanitized = data.copy()
    sensitive_fields = ['password', 'token', 'secret', 'key']
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = '******'
    return sanitized
```

## 8. Resource Management

### 8.1 Resource Configuration
```python
RESOURCE_CONFIG = {
    'cpu_limit': 80,  # percentage
    'memory_limit': 80,  # percentage
    'disk_limit': 80,  # percentage
    'network_limit': 1024 * 1024  # 1MB/s
}
```

### 8.2 Resource Methods
```python
async def _monitor_resources(self):
    """Monitor resource usage."""
    while self.is_running:
        resources = await self._check_resources()
        await self._enforce_limits()
        await self._report_resources(resources)
        await asyncio.sleep(self.config.get("RESOURCE_CHECK_INTERVAL", 60))

async def _report_resources(self, resources: Dict):
    """Report resource usage."""
    await self.nats_client.publish(
        f"opmas.resources.{self.agent_id}",
        json.dumps({
            "agent_id": self.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "resources": resources
        }).encode()
    )
```

## 9. Testing

### 9.1 Test Configuration
```python
TEST_CONFIG = {
    'test_agent_id': 'test-agent',
    'test_management_url': 'http://test-api',
    'test_nats_url': 'nats://test-nats:4222',
    'test_token': 'test-token'
}
```

### 9.2 Test Methods
```python
async def _run_tests(self):
    """Run agent tests."""
    tests = [
        self._test_connection,
        self._test_config,
        self._test_processing,
        self._test_security
    ]

    results = []
    for test in tests:
        try:
            await test()
            results.append(True)
        except Exception as e:
            self.logger.error(f"Test failed: {str(e)}")
            results.append(False)

    return all(results)
```

## 10. Documentation

### 10.1 Method Documentation
```python
def process_event(self, event: Dict) -> List[Finding]:
    """
    Process an event and generate findings.

    Args:
        event (Dict): The event to process

    Returns:
        List[Finding]: List of findings generated from the event

    Raises:
        ProcessingError: If event processing fails
        ValidationError: If event validation fails
    """
    pass
```

### 10.2 Class Documentation
```python
class BaseAgent:
    """
    Base class for all OPMAS agents.

    This class provides common functionality for all agents:
    - NATS communication
    - Configuration management
    - Health monitoring
    - Metrics collection
    - Resource management
    - Security controls

    Attributes:
        agent_id (str): Unique identifier for the agent
        management_api_url (str): URL of the management API
        initial_token (str): Initial authentication token
        config (Dict): Agent configuration
        metrics (Dict): Agent metrics
        logger (Logger): Agent logger
        nats_client (NATS): NATS client
        is_running (bool): Agent running state
    """
    pass
```
