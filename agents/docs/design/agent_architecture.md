# Agent Architecture

## Overview

The OPMAS agent system is built on a modular architecture that enables:
- Easy integration of new agent types
- Consistent behavior across agents
- Standardized communication
- Robust error handling
- Scalable performance

## Core Components

### 1. Base Agent

The `BaseAgent` class provides the foundation for all agents:

```python
class BaseAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.status = AgentStatus.INITIALIZING
        self.metrics = AgentMetrics()
        self.last_heartbeat = None

    async def start(self) -> None:
        """Start the agent."""
        pass

    async def stop(self) -> None:
        """Stop the agent."""
        pass

    async def process_event(self, event: Dict[str, Any]) -> None:
        """Process an incoming event."""
        pass

    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect agent metrics."""
        pass
```

### 2. Agent Configuration

Configuration is handled through environment variables and YAML:

```yaml
# config.yaml
agent:
  name: "Example Agent"
  description: "Example agent implementation"
  version: "1.0.0"
  settings:
    max_retries: 3
    timeout: 30
    batch_size: 100
```

### 3. Event Processing

Events are processed through a standardized pipeline:

1. **Validation**
   - Schema validation
   - Required fields check
   - Type checking

2. **Processing**
   - Business logic
   - Data transformation
   - External service calls

3. **Response**
   - Success/failure status
   - Result data
   - Error information

### 4. Error Handling

Standardized error handling through custom exceptions:

```python
class AgentError(Exception):
    """Base exception for agent errors."""
    pass

class ConfigurationError(AgentError):
    """Configuration related errors."""
    pass

class ProcessingError(AgentError):
    """Event processing errors."""
    pass
```

### 5. Metrics Collection

Standard metrics collection:

```python
class AgentMetrics:
    def __init__(self):
        self.events_processed = 0
        self.errors = 0
        self.processing_time = 0
        self.last_update = None
```

## Communication

### 1. Event Format

Standard event format:

```python
{
    "event_id": str,
    "timestamp": datetime,
    "type": str,
    "data": Dict[str, Any],
    "metadata": Dict[str, Any]
}
```

### 2. Response Format

Standard response format:

```python
{
    "status": str,
    "event_id": str,
    "timestamp": datetime,
    "result": Optional[Dict[str, Any]],
    "error": Optional[Dict[str, Any]]
}
```

## Lifecycle Management

### 1. Initialization

```python
async def initialize(self) -> None:
    """Initialize the agent."""
    self.status = AgentStatus.INITIALIZING
    await self._load_config()
    await self._setup_connections()
    self.status = AgentStatus.READY
```

### 2. Health Checks

```python
async def health_check(self) -> Dict[str, Any]:
    """Perform health check."""
    return {
        "status": self.status,
        "last_heartbeat": self.last_heartbeat,
        "metrics": await self.collect_metrics()
    }
```

## Best Practices

### 1. Error Handling

- Use custom exceptions
- Include context in errors
- Implement retry mechanisms
- Log errors appropriately

### 2. Performance

- Use async/await for I/O
- Implement batching
- Cache where appropriate
- Monitor resource usage

### 3. Security

- Validate all inputs
- Sanitize outputs
- Use secure communication
- Handle sensitive data

### 4. Testing

- Unit test all components
- Integration test flows
- Test error conditions
- Mock external services

## Example Implementation

```python
from opmas.agents.packages.base.agent import BaseAgent
from opmas.agents.packages.base.models import AgentConfig

class ExampleAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.processed_events = 0

    async def process_event(self, event: Dict[str, Any]) -> None:
        try:
            # Validate event
            self._validate_event(event)

            # Process event
            result = await self._process_event(event)

            # Update metrics
            self.processed_events += 1

            return result
        except Exception as e:
            self.metrics.errors += 1
            raise ProcessingError(f"Failed to process event: {e}")

    async def collect_metrics(self) -> Dict[str, Any]:
        return {
            "processed_events": self.processed_events,
            "errors": self.metrics.errors,
            "status": self.status
        }
```

## Extending the Architecture

### 1. Adding New Agent Types

1. Create new agent class
2. Implement required methods
3. Add custom logic
4. Register with system

### 2. Adding New Features

1. Extend base classes
2. Add new methods
3. Update documentation
4. Add tests

### 3. Customizing Behavior

1. Override base methods
2. Add custom logic
3. Maintain compatibility
4. Update tests 