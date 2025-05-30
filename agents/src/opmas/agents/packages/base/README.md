# OPMAS Base Agent Package

This package provides the foundation for implementing OPMAS agents. It includes the core `BaseAgent` class, data models, and exception handling.

## Features

- Asynchronous agent implementation
- NATS-based event communication
- Standardized finding model
- Configuration validation
- Health monitoring
- Metrics collection
- Comprehensive error handling

## Installation

```bash
pip install -r requirements.txt
```

## Usage

1. Create a new agent class that inherits from `BaseAgent`:

```python
from opmas.agents.base_agent_package.agent import BaseAgent
from opmas.agents.base_agent_package.models import AgentConfig

class MyAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)

    async def process_event(self, event: Dict[str, Any]) -> None:
        # Implement your event processing logic here
        pass
```

2. Configure your agent:

```python
config = AgentConfig(
    agent_id="my-agent-123",
    agent_type="my_agent",
    nats_url="nats://localhost:4222",
    heartbeat_interval=30,
    log_level="INFO",
    metrics_enabled=True,
)
```

3. Start the agent:

```python
agent = MyAgent(config)
await agent.start()
```

## Models

### Finding

The `Finding` model represents a detection or observation made by an agent:

```python
finding = Finding(
    finding_id="unique-id",
    agent_id="agent-123",
    agent_type="my_agent",
    severity=Severity.HIGH,
    title="Issue Detected",
    description="Detailed description",
    source="system_component",
    details={"key": "value"},
    remediation="How to fix",
    references=["https://docs.example.com"],
)
```

### AgentConfig

The `AgentConfig` model defines agent configuration:

```python
config = AgentConfig(
    agent_id="agent-123",
    agent_type="my_agent",
    nats_url="nats://localhost:4222",
    nats_credentials={"username": "user", "password": "pass"},
    heartbeat_interval=30,
    log_level="INFO",
    metrics_enabled=True,
    custom_config={"key": "value"},
)
```

## Error Handling

The package provides a hierarchy of custom exceptions:

- `AgentError`: Base exception for all agent errors
- `ValidationError`: Configuration validation errors
- `AuthenticationError`: Authentication failures
- `ResourceError`: Resource access issues
- `CommunicationError`: Communication failures
- `ProcessingError`: Event processing errors
- `ConfigurationError`: Configuration issues
- `DependencyError`: Missing dependencies
- `StateError`: Invalid agent state

## Testing

Run the test suite:

```bash
pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This package is part of OPMAS and is subject to the same license terms.

## Configuration

The `.env` file is used to configure the agent. Here are the available configuration options:

### Required Configuration

#### Agent Identity
- `AGENT_NAME`: Display name of the agent
- `AGENT_TYPE`: Type of agent (e.g., security, network, system)
- `AGENT_VERSION`: Version of the agent
- `AGENT_DESCRIPTION`: Description of the agent's purpose

#### Agent Configuration
- `AGENT_ID`: Unique identifier (optional, will be auto-generated)
- `AGENT_PORT`: Port for agent communication
- `AGENT_HOST`: Host binding address
- `AGENT_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

#### NATS Configuration
- `NATS_URL`: NATS server URL
- `NATS_USER`: NATS username
- `NATS_PASSWORD`: NATS password
- `NATS_TLS_VERIFY`: Enable TLS verification

#### Agent Capabilities
- `DEFAULT_SUBSCRIBED_TOPICS`: Comma-separated list of topics to subscribe to
- `DEFAULT_FINDINGS_TOPIC`: Topic for publishing findings
- `DEFAULT_METRICS_TOPIC`: Topic for publishing metrics

### Optional Configuration

#### Resource Limits
- `MAX_MEMORY_MB`: Maximum memory usage in MB
- `MAX_CPU_PERCENT`: Maximum CPU usage percentage
- `MAX_DISK_MB`: Maximum disk usage in MB

#### Security Settings
- `TLS_ENABLED`: Enable TLS
- `TLS_CERT_PATH`: Path to TLS certificate
- `TLS_KEY_PATH`: Path to TLS key
- `TLS_CA_PATH`: Path to TLS CA

#### Monitoring Settings
- `HEARTBEAT_INTERVAL_SECONDS`: Interval between heartbeats
- `METRICS_INTERVAL_SECONDS`: Interval between metrics reports
- `LOG_RETENTION_DAYS`: Number of days to retain logs

## Usage

1. Copy this directory to create a new agent:
   ```bash
   cp -r base_agent_package my_new_agent
   ```

2. Copy the example environment file:
   ```bash
   cp example.env .env
   ```

3. Edit the `.env` file with your agent's configuration

4. Implement your agent logic in `agent.py`

5. Add any required dependencies to `requirements.txt`

## Development

The agent package includes:

- `agent.py`: Main agent implementation
- `models.py`: Data models
- `exceptions.py`: Custom exceptions
- `requirements.txt`: Python dependencies
- `example.env`: Example configuration
- `README.md`: This documentation

## Testing

Add your tests to the `tests` directory:

```bash
mkdir tests
touch tests/__init__.py
touch tests/test_agent.py
```

## Deployment

The agent can be deployed as a standalone process or in a container. See the deployment guide for more details.
