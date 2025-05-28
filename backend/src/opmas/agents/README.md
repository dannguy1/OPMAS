# OPMAS Agents

This directory contains agent packages for the OPMAS system. Each agent package should be a self-contained directory with its own configuration and implementation.

## Agent Package Structure

Each agent package should have the following structure:

```
agent_package/
├── .env                 # Agent configuration
├── agent.py            # Agent implementation
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container definition
└── README.md          # Package documentation
```

### .env File Configuration

The `.env` file is used to configure the agent. It must contain the following variables:

- `AGENT_NAME`: The display name of the agent
- `AGENT_DESCRIPTION`: A description of the agent's purpose and capabilities
- `AGENT_ID`: (Optional) A unique identifier for the agent. If not provided, the system will:
  - Generate a new UUID
  - Add it to the .env file automatically
  - Use it to register the agent in the database

Note: The `AGENT_ID` is used to maintain agent identity across restarts and updates. If you remove the `AGENT_ID` from the .env file, the system will treat it as a new agent and generate a new ID.

## Agent Discovery

The system automatically discovers agents by:
1. Scanning this directory for agent packages
2. Reading the .env file to get agent configuration
3. Checking if the agent is already registered in the database
4. If not registered:
   - Generates an ID if not present in .env
   - Creates a new database entry
   - Returns the agent in discovery results

## Skip Patterns

The following package names are automatically skipped during discovery:
- `__pycache__`
- `_template`
- `base`
- `example`
- `test`

## Creating a New Agent

1. Create a new directory for your agent
2. Copy the required files from `base_agent_package`
3. Create a `.env` file with at least:
   ```
   AGENT_NAME=Your Agent Name
   AGENT_DESCRIPTION=Description of your agent
   ```
4. Implement your agent logic in `agent.py`
5. Add any required dependencies to `requirements.txt`

The system will automatically:
- Generate an `AGENT_ID` if not provided
- Register the agent in the database
- Make it available for use

## Testing Your Agent

1. Place your agent package in this directory
2. Ensure it has a valid `.env` file
3. The system will discover and register it automatically
4. You can verify registration using the management API

## Best Practices

1. Always include a descriptive `AGENT_NAME` and `AGENT_DESCRIPTION`
2. Let the system generate the `AGENT_ID` unless you need to maintain a specific identity
3. Keep your agent package self-contained
4. Document any special requirements or configuration in your package's README.md

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
