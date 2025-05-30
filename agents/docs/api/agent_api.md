# Agent API Reference

## Base Agent

### Class: `BaseAgent`

Base class for all OPMAS agents.

#### Methods

##### `__init__(agent_id: str, config: Dict[str, Any])`

Initialize the agent.

**Parameters:**
- `agent_id`: Unique identifier for the agent
- `config`: Agent configuration

##### `async start()`

Start the agent. This will:
- Set status to "running"
- Start heartbeat task
- Start metrics task
- Start main task

##### `async stop()`

Stop the agent. This will:
- Set status to "stopped"
- Stop all tasks
- Clean up resources

##### `async run()`

Main agent logic. Must be implemented by subclasses.

##### `async collect_metrics() -> Dict[str, Any]`

Collect agent metrics. Can be overridden by subclasses.

**Returns:**
- Dictionary containing agent metrics

##### `async handle_command(command: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`

Handle commands from AgentManager.

**Parameters:**
- `command`: Command to execute
- `params`: Optional command parameters

**Returns:**
- Dictionary containing command response

## Security Agent

### Class: `SecurityAgent`

Security monitoring agent.

#### Methods

##### `__init__(agent_id: str, config: Dict[str, Any])`

Initialize the security agent.

**Parameters:**
- `agent_id`: Unique identifier for the agent
- `config`: Agent configuration

##### `async run()`

Main security agent logic. This will:
- Check security rules
- Generate findings
- Report violations

##### `async _check_rule(rule: Dict[str, Any]) -> bool`

Check if a security rule is violated.

**Parameters:**
- `rule`: Security rule to check

**Returns:**
- True if rule is violated, False otherwise

##### `async _create_finding(rule: Dict[str, Any]) -> Dict[str, Any]`

Create a security finding.

**Parameters:**
- `rule`: Security rule that was violated

**Returns:**
- Dictionary containing finding details

##### `async collect_metrics() -> Dict[str, Any]`

Collect security agent metrics.

**Returns:**
- Dictionary containing security metrics

## Command Reference

### Common Commands

#### `start`

Start the agent.

**Response:**
```python
{
    "status": "success",
    "message": "Agent started"
}
```

#### `stop`

Stop the agent.

**Response:**
```python
{
    "status": "success",
    "message": "Agent stopped"
}
```

#### `status`

Get agent status.

**Response:**
```python
{
    "status": "success",
    "data": {
        "agent_id": str,
        "status": str,
        "last_heartbeat": str,
        "metrics": Dict[str, Any]
    }
}
```

### Security Agent Commands

#### `check_rules`

Check all security rules.

**Response:**
```python
{
    "status": "success",
    "data": {
        "findings": List[Dict[str, Any]],
        "rules": List[Dict[str, Any]]
    }
}
```

## Configuration Reference

### Common Configuration

```yaml
common:
  log_level: str  # INFO, DEBUG, etc.
  heartbeat_interval: int  # seconds
  metrics_interval: int  # seconds
  max_retries: int
  retry_delay: int  # seconds
```

### Security Agent Configuration

```yaml
security:
  agent_id: str
  name: str
  type: str
  version: str
  rules:
    - id: str
      type: str
      severity: str
      description: str
      parameters:
        # Rule-specific parameters
```

## Error Reference

### Common Errors

#### Configuration Error
```python
{
    "status": "error",
    "message": "Invalid configuration",
    "details": Dict[str, Any]
}
```

#### Command Error
```python
{
    "status": "error",
    "message": "Unknown command",
    "command": str
}
```

#### Runtime Error
```python
{
    "status": "error",
    "message": "Runtime error",
    "error": str
}
```

## Examples

### Creating a Security Agent

```python
from opmas.agents.security.security_agent import SecurityAgent

# Load configuration
with open("config.yaml") as f:
    config = yaml.safe_load(f)

# Create agent
agent = SecurityAgent("security-001", config["security"])

# Start agent
await agent.start()
```

### Handling Commands

```python
# Get status
response = await agent.handle_command("status")
print(response["data"])

# Check rules
response = await agent.handle_command("check_rules")
print(response["data"]["findings"])
```

### Collecting Metrics

```python
# Get metrics
metrics = await agent.collect_metrics()
print(metrics)
``` 