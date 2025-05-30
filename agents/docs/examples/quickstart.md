# Quickstart Guide

This guide will help you get started with the OPMAS agent system.

## Installation

1. Install the package:
```bash
pip install opmas_agents
```

2. Verify installation:
```bash
python -c "from opmas.agents.security.security_agent import SecurityAgent; print('Installation successful')"
```

## Basic Usage

### 1. Create Configuration

Create a file `config.yaml`:

```yaml
common:
  log_level: INFO
  heartbeat_interval: 30
  metrics_interval: 60

security:
  agent_id: security-001
  name: SecurityAgent
  type: security
  version: 1.0.0
  rules:
    - id: rule-001
      type: file_permission
      severity: high
      description: Check for world-writable files
      parameters:
        paths:
          - /tmp
        max_permissions: 0o644
```

### 2. Create Agent Script

Create a file `run_agent.py`:

```python
#!/usr/bin/env python3

import asyncio
import logging
import yaml
from opmas.agents.security.security_agent import SecurityAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    # Load configuration
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    
    # Create agent
    agent = SecurityAgent(
        config["security"]["agent_id"],
        config["security"]
    )
    
    # Start agent
    await agent.start()
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        # Stop agent
        await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Run Agent

```bash
python run_agent.py
```

## Examples

### 1. Basic Agent

```python
from opmas.agents.base.agent import BaseAgent

class SimpleAgent(BaseAgent):
    async def run(self):
        print("Agent is running")
        await asyncio.sleep(1)
    
    async def collect_metrics(self):
        return {
            "status": self.status,
            "custom_metric": 42
        }

# Create and run agent
agent = SimpleAgent("simple-001", {"name": "SimpleAgent"})
await agent.start()
```

### 2. Security Agent

```python
from opmas.agents.security.security_agent import SecurityAgent

# Create security agent
agent = SecurityAgent("security-001", {
    "rules": [
        {
            "id": "test-rule",
            "type": "file_permission",
            "severity": "high",
            "parameters": {
                "paths": ["/tmp"]
            }
        }
    ]
})

# Start agent
await agent.start()

# Check status
response = await agent.handle_command("status")
print(response["data"])

# Check rules
response = await agent.handle_command("check_rules")
print(response["data"]["findings"])
```

### 3. Custom Commands

```python
class CustomAgent(BaseAgent):
    async def handle_command(self, command, params=None):
        if command == "custom":
            return {
                "status": "success",
                "data": {"message": "Custom command executed"}
            }
        return await super().handle_command(command, params)

# Create and run agent
agent = CustomAgent("custom-001", {})
await agent.start()

# Execute custom command
response = await agent.handle_command("custom")
print(response["data"])
```

## Common Tasks

### 1. Monitoring Agent Status

```python
# Get agent status
response = await agent.handle_command("status")
print(f"Agent status: {response['data']['status']}")
print(f"Last heartbeat: {response['data']['last_heartbeat']}")
print(f"Metrics: {response['data']['metrics']}")
```

### 2. Collecting Metrics

```python
# Get agent metrics
metrics = await agent.collect_metrics()
print(f"Agent metrics: {metrics}")
```

### 3. Handling Errors

```python
try:
    await agent.start()
except Exception as e:
    print(f"Failed to start agent: {e}")
    # Handle error
```

## Next Steps

1. Read the [Architecture Documentation](design/agent_architecture.md)
2. Check the [API Reference](api/agent_api.md)
3. Explore the [Examples](examples/)
4. Start developing your own agents 