# Agent Services Architecture

## Overview

The OPMAS agent system consists of three main components:
1. **Management API** - HTTP/REST API for user interaction
2. **AgentManager Service** - Core agent lifecycle management
3. **Agent Packages** - Individual agent implementations

## Service Architecture

### 1. Service Components

```mermaid
graph TD
    A[Management API] -->|HTTP| B[Users/UI]
    A -->|NATS| C[AgentManager Service]
    C -->|NATS| D[Agent 1]
    C -->|NATS| E[Agent 2]
    C -->|NATS| F[Agent 3]
    C -->|DB| G[Agent State DB]
    A -->|DB| H[Business Logic DB]
```

### 2. Component Responsibilities

#### 2.1 Management API
- HTTP/REST API service
- User authentication and authorization
- Business logic and workflows
- NATS communication with AgentManager
- Business logic database management

#### 2.2 AgentManager Service
- Agent lifecycle management
- Agent discovery and registration
- Health monitoring
- Command routing
- State management
- Agent state database management

#### 2.3 Agent Packages
- Individual agent implementations
- Event processing
- Metrics collection
- Health reporting
- NATS communication

## Agent Management Layer

### 1. Core Components

#### 1.1 Agent Manager
```python
class AgentManager:
    def __init__(self):
        self.discovery = AgentDiscovery()
        self.registry = AgentRegistry()
        self._running = False

    async def start(self) -> None:
        """Start the agent manager."""
        self._running = True
        await self.discovery.start()
        await self.registry.start()
        await self._start_agents()

    async def stop(self) -> None:
        """Stop the agent manager."""
        self._running = False
        await self._stop_agents()
        await self.registry.stop()
        await self.discovery.stop()
```

#### 1.2 Agent Discovery
```python
class AgentDiscovery:
    def __init__(self):
        self._agents_dir = Path("packages")
        self._skip_patterns = {"__pycache__", "_template", "test"}

    async def discover_agents(self) -> List[Dict]:
        """Discover available agents."""
        agents = []
        for agent_dir in self._agents_dir.iterdir():
            if not self._should_skip(agent_dir):
                config = await self._load_agent_config(agent_dir)
                if config:
                    agents.append(config)
        return agents
```

#### 1.3 Agent Registry
```python
class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    async def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent."""
        self._agents[agent.agent_id] = agent

    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent."""
        if agent_id in self._agents:
            del self._agents[agent_id]
```

### 2. Communication

#### 2.1 Command Format
```python
{
    "command": str,  # "start", "stop", "restart", "status"
    "agent_id": str,
    "params": Dict[str, Any],
    "timestamp": datetime
}
```

#### 2.2 Response Format
```python
{
    "status": str,  # "success", "error"
    "command": str,
    "agent_id": str,
    "result": Optional[Dict[str, Any]],
    "error": Optional[Dict[str, Any]],
    "timestamp": datetime
}
```

### 3. Lifecycle Management

#### 3.1 Agent Startup
```python
async def start_agent(self, agent_id: str) -> None:
    """Start a specific agent."""
    agent = await self.registry.get_agent(agent_id)
    if agent:
        await agent.start()
        await self.registry.update_status(agent_id, AgentStatus.RUNNING)
```

#### 3.2 Agent Shutdown
```python
async def stop_agent(self, agent_id: str) -> None:
    """Stop a specific agent."""
    agent = await self.registry.get_agent(agent_id)
    if agent:
        await agent.stop()
        await self.registry.update_status(agent_id, AgentStatus.STOPPED)
```

### 4. Health Monitoring

#### 4.1 Health Checks
```python
async def check_agent_health(self, agent_id: str) -> Dict[str, Any]:
    """Check agent health."""
    agent = await self.registry.get_agent(agent_id)
    if agent:
        return await agent.health_check()
    return {"status": "unknown"}
```

#### 4.2 Metrics Collection
```python
async def collect_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
    """Collect agent metrics."""
    agent = await self.registry.get_agent(agent_id)
    if agent:
        return await agent.collect_metrics()
    return {}
```

## Service Configuration

### 1. Management API Configuration
```yaml
# config/management_api.yaml
service:
  name: opmas-management-api
  version: 1.0.0
  host: 0.0.0.0
  port: 8000
  log_level: INFO

database:
  url: postgresql+asyncpg://user:pass@localhost/opmas
  pool_size: 5
  max_overflow: 10

nats:
  url: nats://localhost:4222
  user: opmas
  password: your_secure_password
  tls_verify: false
```

### 2. AgentManager Configuration
```yaml
# config/agent_manager.yaml
service:
  name: opmas-agent-manager
  version: 1.0.0
  log_level: INFO
  discovery_interval: 300  # seconds
  monitoring_interval: 10  # seconds
  cleanup_interval: 3600  # seconds

database:
  url: postgresql+asyncpg://user:pass@localhost/opmas
  pool_size: 5
  max_overflow: 10

nats:
  url: nats://localhost:4222
  user: opmas
  password: your_secure_password
  tls_verify: false
```

## Service Interfaces

### 1. Management API Endpoints
```python
# Agent Management
GET    /api/v1/agents              # List all agents
POST   /api/v1/agents              # Register new agent
GET    /api/v1/agents/{agent_id}   # Get agent details
PUT    /api/v1/agents/{agent_id}   # Update agent
DELETE /api/v1/agents/{agent_id}   # Delete agent

# Agent Control
POST   /api/v1/agents/{agent_id}/start     # Start agent
POST   /api/v1/agents/{agent_id}/stop      # Stop agent
POST   /api/v1/agents/{agent_id}/restart   # Restart agent

# Agent Monitoring
GET    /api/v1/agents/{agent_id}/status    # Get agent status
GET    /api/v1/agents/{agent_id}/metrics   # Get agent metrics
GET    /api/v1/agents/{agent_id}/logs      # Get agent logs
```

### 2. NATS Topics
```python
# Management API → AgentManager
AGENT_MANAGER_COMMAND = "agent.manager.command"
AGENT_MANAGER_QUERY = "agent.manager.query"
AGENT_MANAGER_RESPONSE = "agent.manager.response"

# AgentManager → Agents
AGENT_COMMAND = "agent.{agent_id}.command"
AGENT_QUERY = "agent.{agent_id}.query"
AGENT_RESPONSE = "agent.{agent_id}.response"
AGENT_STATUS = "agent.status"
AGENT_METRICS = "agent.metrics"
```

## Best Practices

### 1. Error Handling
- Handle agent failures gracefully
- Implement retry mechanisms
- Log all management operations
- Provide clear error messages

### 2. Performance
- Use async operations
- Implement caching
- Batch operations where possible
- Monitor resource usage

### 3. Security
- Validate all commands
- Implement access control
- Secure communication
- Audit all operations

### 4. Testing
- Test all management operations
- Mock agent behavior
- Test error conditions
- Verify state management

## Implementation Notes

### 1. Service Dependencies
- PostgreSQL 12+
- NATS Server 2.9+
- Python 3.8+
- Docker (optional)

### 2. Service Requirements
- System resources
- Network access
- File system access
- Security requirements

### 3. Service Limitations
- Resource constraints
- Network constraints
- Security constraints
- Performance constraints

### 4. Service Considerations
- Scalability
- Reliability
- Security
- Performance
- Maintainability

## Agent Lifecycle Management Implementation

### 1. Process Management
```python
class AgentManager:
    def __init__(self):
        self._running_agents: Dict[str, subprocess.Popen] = {}
        self._discovery_interval = 30  # seconds
        self._heartbeat_timeout = 60  # seconds

    async def _monitor_agents(self) -> None:
        """Monitor running agent processes."""
        while self._running:
            for agent_id, process in list(self._running_agents.items()):
                if process.poll() is not None:
                    await self._handle_agent_termination(agent_id, process.returncode)
                    del self._running_agents[agent_id]
            await asyncio.sleep(1)
```

### 2. Agent States
- **Starting**: Initial launch state
- **Running**: Active and healthy
- **Stopped**: Gracefully shut down
- **Error**: Crashed or failed to start
- **Inactive**: No heartbeat received

### 3. Lifecycle Operations

#### 3.1 Agent Launch
```python
async def launch_agent(self, agent_id: str) -> bool:
    """Launch an agent."""
    # Prepare environment
    env = os.environ.copy()
    env.update({
        "AGENT_ID": str(agent.id),
        "NATS_URL": self.nats_url,
        "AGENT_TYPE": agent.agent_type,
        "AGENT_NAME": agent.name,
        "AGENT_VERSION": agent.version
    })

    # Start process
    process = subprocess.Popen(
        [sys.executable, str(agent_script)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    self._running_agents[agent_id] = process
    await self.db.update_agent_status(agent_id, "starting")
```

#### 3.2 Agent Shutdown
```python
async def stop_agent(self, agent_id: str) -> bool:
    """Stop an agent."""
    process = self._running_agents.get(agent_id)
    if process:
        # Graceful shutdown
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        
        await self.db.update_agent_status(agent_id, "stopped")
        del self._running_agents[agent_id]
```

### 4. Health Monitoring

#### 4.1 Heartbeat Management
```python
async def _health_check_loop(self) -> None:
    """Periodically check agent health."""
    while self._running:
        agents = await self.db.get_all_agents()
        for agent in agents:
            if agent.last_heartbeat:
                time_since_heartbeat = (
                    datetime.utcnow() - agent.last_heartbeat
                ).total_seconds()
                
                if time_since_heartbeat > self._heartbeat_timeout:
                    await self.db.update_agent_status(
                        agent.id,
                        "inactive",
                        {"last_seen": agent.last_heartbeat.isoformat()}
                    )
```

#### 4.2 Status Updates
```python
async def _handle_status_update(self, msg) -> None:
    """Handle agent status update."""
    status = json.loads(msg.data.decode())
    agent_id = status.get("agent_id")
    new_status = status.get("status")
    
    await self.db.update_agent_status(
        agent_id,
        new_status,
        status.get("metadata", {})
    )
```

### 5. Error Handling

#### 5.1 Process Termination
```python
async def _handle_agent_termination(self, agent_id: str, return_code: int) -> None:
    """Handle agent process termination."""
    await self.db.update_agent_status(
        agent_id,
        "error" if return_code != 0 else "stopped",
        {
            "exit_code": return_code,
            "terminated_at": datetime.utcnow().isoformat()
        }
    )
    self.registry.unregister_agent(agent_id)
```

### 6. Environment Management
- Agent configuration via environment variables
- Process output capture (stdout/stderr)
- Resource cleanup on termination
- Status persistence in database

### 7. Best Practices
- Use async operations for non-blocking I/O
- Implement graceful shutdown
- Monitor process health
- Handle errors gracefully
- Maintain audit logs
- Clean up resources properly 