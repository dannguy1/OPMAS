# OPMAS Agents

This directory contains the implementation of OPMAS agents, which are responsible for monitoring, analyzing, and reporting on various aspects of the system.

## Structure

```
agents/
├── base_agent_package/     # Core agent implementation
├── example_agent/         # Example implementation
├── wifi_agent/           # WiFi monitoring agent
└── README.md             # This file
```

## Base Agent Package

The `base_agent_package` provides the foundation for all OPMAS agents:

- Core `BaseAgent` class
- Standardized models
- Exception handling
- NATS communication
- Health monitoring
- Metrics collection

See [base_agent_package/README.md](base_agent_package/README.md) for details.

## Example Agent

The `example_agent` demonstrates how to implement a new agent:

- Inherits from `BaseAgent`
- Processes system metrics
- Generates findings
- Includes tests
- Provides documentation

See [example_agent/README.md](example_agent/README.md) for details.

## WiFi Agent

The `wifi_agent` is the first specialized agent implementation:

- Monitors WiFi networks
- Detects security issues
- Reports performance metrics
- Provides remediation steps

See [wifi_agent/README.md](wifi_agent/README.md) for details.

## Development

### Creating a New Agent

1. Create a new directory for your agent:
```bash
mkdir -p agents/my_agent/tests
```

2. Inherit from `BaseAgent`:
```python
from opmas.agents.base_agent_package.agent import BaseAgent
from opmas.agents.base_agent_package.models import AgentConfig

class MyAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)

    async def process_event(self, event: Dict[str, Any]) -> None:
        # Implement your event processing logic
        pass
```

3. Add tests:
```python
# tests/test_agent.py
import pytest
from opmas.agents.my_agent.agent import MyAgent

def test_my_agent():
    # Add your tests
    pass
```

4. Add documentation:
```markdown
# My Agent

Description of your agent's functionality.
```

### Best Practices

1. **Error Handling**
   - Use custom exceptions
   - Provide meaningful error messages
   - Include context in errors

2. **Testing**
   - Write unit tests
   - Include integration tests
   - Maintain high coverage

3. **Documentation**
   - Document all public APIs
   - Include usage examples
   - Keep README up to date

4. **Metrics**
   - Collect relevant metrics
   - Use standard formats
   - Include timestamps

5. **Logging**
   - Use structured logging
   - Include context
   - Set appropriate levels

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This package is part of OPMAS and is subject to the same license terms.
