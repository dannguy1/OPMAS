# OPMAS Example Agent

This package provides an example implementation of an OPMAS agent, demonstrating best practices and common patterns.

## Overview

The example agent monitors system metrics and generates findings for:
- High CPU usage (>90%)
- High memory usage (>85%)

## Features

- Inherits from BaseAgent
- Demonstrates event processing
- Shows finding generation
- Includes comprehensive tests
- Provides metrics collection

## Installation

```bash
pip install -r requirements.txt
```

## Usage

1. Create an agent configuration:

```python
from opmas.agents.base_agent_package.models import AgentConfig

config = AgentConfig(
    agent_id="example-agent-123",
    agent_type="example",
    nats_url="nats://localhost:4222",
    heartbeat_interval=30,
    log_level="INFO",
    metrics_enabled=True,
)
```

2. Initialize and start the agent:

```python
from opmas.agents.example_agent.agent import ExampleAgent

agent = ExampleAgent(config)
await agent.start()
```

3. Process events:

```python
event = {
    "type": "system_metrics",
    "cpu_usage": 95,
    "memory_usage": 80,
    "timestamp": "2024-01-01T00:00:00Z",
    "host": "server-1",
}

await agent.process_event(event)
```

## Event Format

The agent expects events in the following format:

```python
{
    "type": "system_metrics",
    "cpu_usage": float,  # CPU usage percentage
    "memory_usage": float,  # Memory usage percentage
    "timestamp": str,  # ISO format timestamp
    "host": str,  # Host identifier
}
```

## Findings

The agent generates findings for:

1. High CPU Usage:
   - Severity: HIGH
   - Threshold: >90%
   - Includes CPU usage details

2. High Memory Usage:
   - Severity: MEDIUM
   - Threshold: >85%
   - Includes memory usage details

## Metrics

The agent provides the following metrics:

```python
{
    "processed_events": int,
    "last_event_time": str,  # ISO format timestamp
    "agent_id": str,
    "agent_type": str,
}
```

## Testing

Run the test suite:

```bash
# Unit tests
pytest tests/test_agent.py

# Integration tests
pytest tests/test_integration.py
```

## Development

1. Install development dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

2. Run tests with coverage:
```bash
pytest --cov=opmas.agents.example_agent tests/
```

3. Run linting:
```bash
flake8 opmas/agents/example_agent
mypy opmas/agents/example_agent
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This package is part of OPMAS and is subject to the same license terms.
