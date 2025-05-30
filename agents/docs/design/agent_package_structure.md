# Agent Package Structure

## Overview

The OPMAS agent system is organized into two main components:
1. **Management** - Core agent management functionality
2. **Packages** - Individual agent implementations

## Directory Structure

```
agents/src/opmas/agents/
├── management/        # Agent management
│   ├── __init__.py
│   ├── manager.py    # Agent lifecycle management
│   ├── discovery.py  # Agent discovery
│   └── registry.py   # Agent registry
├── packages/         # Agent packages
│   ├── base/        # Base agent implementation
│   │   ├── agent.py
│   │   ├── exceptions.py
│   │   ├── models.py
│   │   └── README.md
│   └── example_agent/ # Example implementation
│       ├── agent.py
│       ├── .env
│       └── README.md
└── __init__.py
```

## Agent Package Structure

Each agent package should have the following structure:

```
packages/agent_name/
├── .env                 # Agent configuration
├── agent.py            # Agent implementation
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container definition
└── README.md          # Package documentation
```

## Configuration

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
1. Scanning the `packages` directory for agent packages
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
- `test`

## Creating a New Agent

1. Create a new directory in `packages/` for your agent
2. Copy the required files from `packages/base`
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

1. Place your agent package in the `packages` directory
2. Ensure it has a valid `.env` file
3. The system will discover and register it automatically
4. You can verify registration using the management API

## Best Practices

1. **Error Handling**
   - Use custom exceptions from `base.exceptions`
   - Provide meaningful error messages
   - Include context in errors
   - Handle both expected and unexpected errors
   - Implement proper error recovery mechanisms
   - Log errors with appropriate severity levels

2. **Testing**
   - Write unit tests for all components
   - Include integration tests
   - Maintain high coverage
   - Use test fixtures and mocks
   - Test error conditions
   - Test edge cases
   - Use parameterized tests for multiple scenarios

3. **Documentation**
   - Document all public APIs
   - Include usage examples
   - Keep README up to date
   - Document configuration options
   - Include troubleshooting guides
   - Document dependencies and requirements
   - Add inline code comments for complex logic

4. **Metrics**
   - Collect relevant metrics
   - Use standard formats
   - Include timestamps
   - Track performance metrics
   - Monitor resource usage
   - Log important events
   - Use appropriate metric types (counters, gauges, histograms)

5. **Logging**
   - Use structured logging
   - Include context
   - Set appropriate levels
   - Log state changes
   - Include correlation IDs
   - Use consistent log formats
   - Avoid logging sensitive data

6. **Code Organization**
   - Follow single responsibility principle
   - Keep files focused and concise
   - Use meaningful names
   - Implement proper abstractions
   - Separate concerns
   - Use type hints
   - Follow PEP 8 style guide

7. **Configuration Management**
   - Use environment variables for configuration
   - Validate configuration on startup
   - Provide default values
   - Document all configuration options
   - Use secure configuration practices
   - Support different environments (dev, test, prod)

8. **Security**
   - Follow security best practices
   - Validate all inputs
   - Sanitize outputs
   - Use secure communication
   - Implement proper authentication
   - Handle sensitive data appropriately
   - Regular security updates

9. **Performance**
   - Optimize resource usage
   - Implement caching where appropriate
   - Use async/await for I/O operations
   - Monitor memory usage
   - Profile code regularly
   - Handle backpressure
   - Implement rate limiting

10. **Maintenance**
    - Keep dependencies updated
    - Regular code reviews
    - Address technical debt
    - Monitor for deprecated features
    - Maintain backward compatibility
    - Document breaking changes
    - Version your releases

11. **Deployment**
    - Use containerization
    - Implement health checks
    - Support graceful shutdown
    - Handle configuration changes
    - Implement proper startup sequence
    - Support rolling updates
    - Monitor deployment health

12. **Monitoring**
    - Implement health checks
    - Monitor resource usage
    - Track error rates
    - Monitor performance metrics
    - Set up alerts
    - Log important events
    - Track business metrics

## Example Implementation

```python
from opmas.agents.packages.base.agent import BaseAgent
from opmas.agents.packages.base.models import AgentConfig

class MyAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)

    async def process_event(self, event: Dict[str, Any]) -> None:
        # Implement your event processing logic
        pass
```

## Testing Example

```python
# tests/test_agent.py
import pytest
from opmas.agents.packages.my_agent.agent import MyAgent

def test_my_agent():
    # Add your tests
    pass
``` 