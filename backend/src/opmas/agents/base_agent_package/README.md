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
