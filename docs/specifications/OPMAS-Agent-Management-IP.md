# Agent Management System Implementation Plan for OPMAS

## 15. Agent Package Requirements

### 15.1 Package Structure
```
backend/src/opmas/agents/[agent_name]/
├── __init__.py
├── agent.py              # Main agent implementation
├── .env.discovery        # Discovery metadata
├── requirements.txt      # Package dependencies
├── README.md            # Documentation
└── tests/               # Test directory
    ├── __init__.py
    ├── test_agent.py
    └── test_config.py
```

### 15.2 Required Files

1. **agent.py**
   ```python
   from opmas.base_agent import BaseAgent
   from typing import Dict, Optional

   class SpecificAgent(BaseAgent):
       def __init__(self, agent_id: str, management_api_url: str, initial_token: Optional[str] = None):
           super().__init__(agent_id, management_api_url, initial_token)
           self.config = {}

       async def start(self):
           """Initialize and start the agent."""
           await super().start()
           await self._load_config()
           await self.subscribe_to_topics(self.config.get('SUBSCRIBED_TOPICS', []))
           self.logger.info(f"Agent {self.agent_name} started successfully.")

       async def process_event(self, event: Dict):
           """Process incoming events."""
           try:
               # Implement event processing logic
               self.metrics.increment('events_processed')
           except Exception as e:
               self.logger.error(f"Error processing event: {str(e)}")
               self.metrics.increment('errors')
   ```

2. **.env.discovery**
   ```ini
   # Required fields
   AGENT_NAME=SecurityAgent
   AGENT_VERSION=1.0.0
   AGENT_DESCRIPTION=Security monitoring agent for OPMAS

   # Default Topics
   DEFAULT_SUBSCRIBED_TOPICS=logs.security,logs.auth
   DEFAULT_FINDINGS_TOPIC=findings.security

   # Optional fields
   AGENT_TYPE=security
   AGENT_CATEGORY=monitoring
   AGENT_AUTHOR=OPMAS Team
   AGENT_LICENSE=MIT
   ```

3. **requirements.txt**
   ```txt
   opmas-base-agent>=1.0.0
   nats-py>=2.3.1
   prometheus-client>=0.11.0
   python-dotenv>=0.19.0
   ```

4. **README.md**
   ```markdown
   # Security Agent

   ## Description
   Security monitoring agent for OPMAS that processes security-related events and generates findings.

   ## Installation
   ```bash
   pip install -r requirements.txt
   ```

   ## Configuration
   The agent can be configured through the OPMAS Management System.

   ## Topics
   - Subscribes to: logs.security, logs.auth
   - Publishes to: findings.security

   ## Metrics
   - events_processed: Total number of events processed
   - errors: Number of processing errors
   - processing_time: Event processing duration
   ```

### 15.3 Implementation Requirements

1. **BaseAgent Inheritance**
   - Must inherit from `opmas.base_agent.BaseAgent`
   - Implement required abstract methods
   - Follow lifecycle management protocol

2. **Configuration Management**
   ```python
   async def _load_config(self):
       """Load agent configuration."""
       self.config = await self.get_config()
       self.logger.info(f"Loaded configuration: {self.config}")
   ```

3. **Event Processing**
   ```python
   async def process_event(self, event: Dict):
       """Process incoming events."""
       try:
           # Validate event
           if not self._validate_event(event):
               return

           # Process event
           result = await self._process_event(event)

           # Publish findings
           if result:
               await self.publish_finding(result)

           # Update metrics
           self.metrics.increment('events_processed')

       except Exception as e:
           self.logger.error(f"Error processing event: {str(e)}")
           self.metrics.increment('errors')
   ```

4. **Metrics Collection**
   ```python
   def _setup_metrics(self):
       """Setup agent metrics."""
       self.metrics.register_counter('events_processed', 'Total events processed')
       self.metrics.register_counter('errors', 'Total processing errors')
       self.metrics.register_histogram('processing_time', 'Event processing time')
   ```

5. **Health Checks**
   ```python
   async def check_health(self) -> Dict:
       """Perform health check."""
       return {
           'status': 'healthy',
           'metrics': {
               'events_processed': self.metrics.get('events_processed'),
               'errors': self.metrics.get('errors'),
               'processing_time': self.metrics.get('processing_time')
           },
           'timestamp': datetime.utcnow().isoformat()
       }
   ```

6. **Error Handling**
   ```python
   async def handle_error(self, error: Exception):
       """Handle agent errors."""
       self.logger.error(f"Agent error: {str(error)}")
       self.metrics.increment('errors')

       # Report error to management system
       await self.report_error({
           'error': str(error),
           'timestamp': datetime.utcnow().isoformat(),
           'agent_id': self.agent_id
       })
   ```

### 15.4 Testing Requirements

1. **Unit Tests**
   ```python
   # tests/test_agent.py
   import pytest
   from unittest.mock import Mock, patch
   from .agent import SpecificAgent

   @pytest.fixture
   def agent():
       return SpecificAgent("test-agent", "http://api.opmas")

   async def test_process_event(agent):
       event = {"type": "security", "message": "Test event"}
       await agent.process_event(event)
       assert agent.metrics.get('events_processed') == 1
   ```

2. **Integration Tests**
   ```python
   # tests/test_integration.py
   import pytest
   from .agent import SpecificAgent

   @pytest.mark.integration
   async def test_agent_lifecycle():
       agent = SpecificAgent("test-agent", "http://api.opmas")
       await agent.start()
       assert agent.is_running()
       await agent.stop()
       assert not agent.is_running()
   ```

### 15.5 Documentation Requirements

1. **Code Documentation**
   - Docstrings for all classes and methods
   - Type hints for function parameters
   - Example usage in docstrings

2. **Configuration Documentation**
   - List of all configuration options
   - Default values
   - Environment variable overrides

3. **API Documentation**
   - Input/output formats
   - Error codes
   - Example requests/responses

### 15.6 Security Requirements

1. **Authentication**
   ```python
   async def authenticate(self):
       """Authenticate with management system."""
       token = await self.get_auth_token()
       self.nats_client.set_auth_token(token)
   ```

2. **Authorization**
   ```python
   async def check_permissions(self, action: str) -> bool:
       """Check if agent has permission for action."""
       return await self.management_api.check_permission(
           self.agent_id,
           action
       )
   ```

3. **Data Protection**
   ```python
   def _sanitize_data(self, data: Dict) -> Dict:
       """Remove sensitive data before logging."""
       sanitized = data.copy()
       if 'password' in sanitized:
           sanitized['password'] = '******'
       return sanitized
   ```

### 15.7 Monitoring Requirements

1. **Metrics**
   - Event processing metrics
   - Resource usage metrics
   - Error metrics
   - Performance metrics

2. **Logging**
   ```python
   def _setup_logging(self):
       """Setup agent logging."""
       self.logger = logging.getLogger(self.agent_name)
       self.logger.setLevel(logging.INFO)
   ```

3. **Health Checks**
   - Regular health status updates
   - Resource usage monitoring
   - Error rate monitoring
   - Performance monitoring

### 15.8 Deployment Requirements

1. **Package Distribution**
   ```python
   # setup.py
   from setuptools import setup, find_packages

   setup(
       name="opmas-security-agent",
       version="1.0.0",
       packages=find_packages(),
       install_requires=[
           "opmas-base-agent>=1.0.0",
           "nats-py>=2.3.1"
       ],
       entry_points={
           "opmas.agents": [
               "security=agent:SpecificAgent"
           ]
       }
   )
   ```

2. **Environment Variables**
   ```bash
   # Required
   OPMAS_AGENT_ID=security-123
   OPMAS_MANAGEMENT_API_URL=http://api.opmas
   OPMAS_NATS_URL=nats://nats:4222

   # Optional
   OPMAS_LOG_LEVEL=INFO
   OPMAS_METRICS_ENABLED=true
   ```

3. **Resource Limits**
   ```yaml
   # Resource configuration
   resources:
     cpu: "100%"
     memory: "512MB"
     disk: "1GB"
   ```

## 16. Asyncio-based Implementation

### 16.1 Agent Controller Implementation

1. **AgentController Class**
   ```python
   from typing import Dict, List, Optional
   import asyncio
   import psutil
   from datetime import datetime
   from pathlib import Path
   import logging
   import json

   class AgentController:
       def __init__(self, db: AsyncSession, nats: NATSManager):
           self.db = db
           self.nats = nats
           self.agent_processes: Dict[str, AgentProcess] = {}
           self.logger = logging.getLogger(__name__)

       async def discover_agent_packages(self) -> List[AgentPackage]:
           """Scan filesystem for agent packages."""
           discovered = []
           agents_dir = Path("backend/src/opmas/agents")

           for package_dir in agents_dir.iterdir():
               if not self._is_valid_agent_package(package_dir):
                   continue

               metadata = self._read_agent_metadata(package_dir)
               if metadata:
                   discovered.append(AgentPackage(
                       name=metadata["AGENT_NAME"],
                       type=metadata["AGENT_TYPE"],
                       version=metadata["AGENT_VERSION"],
                       path=package_dir,
                       metadata=metadata
                   ))
           return discovered

       async def register_agent(self, package: AgentPackage) -> Agent:
           """Register a new agent in the system."""
           agent_id = f"{package.type}-{uuid4()}"

           agent = Agent(
               id=agent_id,
               name=package.name,
               type=package.type,
               version=package.version,
               status="registered",
               config=package.metadata,
               created_at=datetime.utcnow()
           )

           self.db.add(agent)
           await self.db.commit()

           return agent

       async def start_agent(self, agent: Agent) -> None:
           """Start a registered agent as an asyncio process."""
           try:
               # Create agent process
               process = await asyncio.create_subprocess_exec(
                   sys.executable,
                   f"backend/scripts/run_{agent.type}_agent.py",
                   env={
                       "AGENT_ID": agent.id,
                       "MANAGEMENT_API_URL": os.getenv("MANAGEMENT_API_URL"),
                       "NATS_URL": os.getenv("NATS_URL")
                   },
                   stdout=asyncio.subprocess.PIPE,
                   stderr=asyncio.subprocess.PIPE
               )

               # Create agent process wrapper
               agent_process = AgentProcess(agent.id, agent.config)
               agent_process.process = process
               agent_process.pid = process.pid
               agent_process.status = "starting"

               # Store process
               self.agent_processes[agent.id] = agent_process

               # Start monitoring task
               monitor_task = asyncio.create_task(
                   self._monitor_agent(agent, agent_process)
               )
               agent_process.monitor_task = monitor_task

               agent.status = "starting"
               await self.db.commit()

               self.logger.info(f"Started agent {agent.id} with PID {process.pid}")

           except Exception as e:
               self.logger.error(f"Failed to start agent {agent.id}: {e}")
               agent.status = "error"
               await self.db.commit()
               raise

       async def stop_agent(self, agent: Agent) -> None:
           """Stop a running agent process."""
           if agent.id not in self.agent_processes:
               return

           try:
               agent_process = self.agent_processes[agent.id]
               agent_process.status = "stopping"
               agent.status = "stopping"
               await self.db.commit()

               # Send SIGTERM
               agent_process.process.terminate()

               # Wait for graceful shutdown
               try:
                   await asyncio.wait_for(agent_process.process.wait(), timeout=10)
               except asyncio.TimeoutError:
                   # Force kill if graceful shutdown fails
                   agent_process.process.kill()
                   await agent_process.process.wait()

               # Cancel monitoring task
               if agent_process.monitor_task:
                   agent_process.monitor_task.cancel()
                   try:
                       await agent_process.monitor_task
                   except asyncio.CancelledError:
                       pass

               del self.agent_processes[agent.id]

               agent.status = "stopped"
               await self.db.commit()

               self.logger.info(f"Stopped agent {agent.id}")

           except Exception as e:
               self.logger.error(f"Failed to stop agent {agent.id}: {e}")
               raise

       async def _monitor_agent(self, agent: Agent, agent_process: AgentProcess):
           """Monitor agent process health."""
           try:
               while True:
                   # Check if process is still running
                   if agent_process.process.returncode is not None:
                       self.logger.error(
                           f"Agent {agent.id} process exited with code {agent_process.process.returncode}"
                       )
                       agent.status = "error"
                       await self.db.commit()
                       break

                   # Read output
                   stdout = await agent_process.process.stdout.read(1024)
                   if stdout:
                       self.logger.info(f"Agent {agent.id} stdout: {stdout.decode()}")

                   stderr = await agent_process.process.stderr.read(1024)
                   if stderr:
                       self.logger.error(f"Agent {agent.id} stderr: {stderr.decode()}")

                   # Update status if starting
                   if agent_process.status == "starting":
                       agent_process.status = "running"
                       agent.status = "running"
                       await self.db.commit()

                   await asyncio.sleep(1)

           except asyncio.CancelledError:
               self.logger.info(f"Monitoring task for agent {agent.id} cancelled")
           except Exception as e:
               self.logger.error(f"Error monitoring agent {agent.id}: {e}")
               agent.status = "error"
               await self.db.commit()

       async def get_agent_status(self, agent: Agent) -> Dict[str, Any]:
           """Get agent process status."""
           if agent.id not in self.agent_processes:
               return {"status": "stopped"}

           try:
               agent_process = self.agent_processes[agent.id]

               # Get process info
               try:
                   p = psutil.Process(agent_process.pid)
                   return {
                       "status": agent_process.status,
                       "pid": agent_process.pid,
                       "cpu_percent": p.cpu_percent(),
                       "memory_percent": p.memory_percent(),
                       "create_time": p.create_time(),
                       "num_threads": p.num_threads()
                   }
               except (psutil.NoSuchProcess, psutil.AccessDenied):
                   return {"status": "error", "error": "Process not found"}

           except Exception as e:
               self.logger.error(f"Failed to get status for agent {agent.id}: {e}")
               return {"status": "error", "error": str(e)}
   ```

2. **Agent Process Class**
   ```python
   class AgentProcess:
       def __init__(self, agent_id: str, config: Dict):
           self.agent_id = agent_id
           self.config = config
           self.process: Optional[asyncio.subprocess.Process] = None
           self.monitor_task: Optional[asyncio.Task] = None
           self.status = "stopped"
           self.pid: Optional[int] = None
   ```

### 16.2 Agent Script Implementation

1. **Agent Runner Script**
   ```python
   # backend/scripts/run_agent.py
   import asyncio
   import os
   import sys
   import signal
   from typing import Optional
   import logging
   from opmas.agents.base_agent import BaseAgent

   class AgentRunner:
       def __init__(self, agent_id: str):
           self.agent_id = agent_id
           self.agent: Optional[BaseAgent] = None
           self.logger = logging.getLogger(__name__)
           self.running = True

       def handle_shutdown(self, signum, frame):
           """Handle shutdown signals."""
           self.logger.info("Received shutdown signal")
           self.running = False

       async def run(self):
           """Run the agent."""
           try:
               # Set up signal handlers
               signal.signal(signal.SIGTERM, self.handle_shutdown)
               signal.signal(signal.SIGINT, self.handle_shutdown)

               # Create and start agent
               self.agent = BaseAgent(
                   agent_id=self.agent_id,
                   management_api_url=os.getenv("MANAGEMENT_API_URL"),
                   nats_url=os.getenv("NATS_URL")
               )

               await self.agent.start()

               # Main loop
               while self.running:
                   await asyncio.sleep(1)

               # Graceful shutdown
               if self.agent:
                   await self.agent.stop()

           except Exception as e:
               self.logger.error(f"Agent error: {e}")
               sys.exit(1)

   if __name__ == "__main__":
       if len(sys.argv) != 2:
           print("Usage: run_agent.py <agent_id>")
           sys.exit(1)

       agent_id = sys.argv[1]
       runner = AgentRunner(agent_id)

       try:
           asyncio.run(runner.run())
       except KeyboardInterrupt:
           pass
   ```

### 16.3 Agent Base Class Updates

1. **BaseAgent Class**
   ```python
   class BaseAgent:
       def __init__(self, agent_id: str, management_api_url: str, nats_url: str):
           self.agent_id = agent_id
           self.management_api_url = management_api_url
           self.nats_url = nats_url
           self.nats_client = None
           self.running = False
           self.logger = logging.getLogger(self.__class__.__name__)

       async def start(self):
           """Initialize and start the agent."""
           try:
               # Connect to NATS
               self.nats_client = await nats.connect(self.nats_url)

               # Subscribe to control topic
               await self.nats_client.subscribe(
                   f"agent.{self.agent_id}.control",
                   cb=self._handle_control_message
               )

               # Start heartbeat
               self.running = True
               asyncio.create_task(self._heartbeat())

               self.logger.info(f"Agent {self.agent_id} started")

           except Exception as e:
               self.logger.error(f"Failed to start agent: {e}")
               raise

       async def stop(self):
           """Stop the agent."""
           self.running = False
           if self.nats_client:
               await self.nats_client.close()
           self.logger.info(f"Agent {self.agent_id} stopped")

       async def _heartbeat(self):
           """Send periodic heartbeat."""
           while self.running:
               try:
                   await self.nats_client.publish(
                       "agent.heartbeat",
                       json.dumps({
                           "agent_id": self.agent_id,
                           "timestamp": datetime.utcnow().isoformat()
                       }).encode()
                   )
               except Exception as e:
                   self.logger.error(f"Heartbeat error: {e}")
               await asyncio.sleep(30)

       async def _handle_control_message(self, msg):
           """Handle control messages."""
           try:
               data = json.loads(msg.data.decode())
               command = data.get("command")

               if command == "stop":
                   await self.stop()
               elif command == "reload":
                   await self.reload_config()

           except Exception as e:
               self.logger.error(f"Error handling control message: {e}")
   ```

### 16.4 Required Changes to Agent Implementation

1. **Agent Package Structure**
   ```
   backend/src/opmas/agents/[agent_name]/
   ├── __init__.py
   ├── agent.py              # Main agent implementation
   ├── .env.discovery        # Discovery metadata
   ├── requirements.txt      # Package dependencies
   ├── README.md            # Documentation
   └── tests/               # Test directory
   ```

2. **Agent Implementation Requirements**
   - Must inherit from `BaseAgent`
   - Must implement `start()` and `stop()`
   - Must handle control messages
   - Must send heartbeats
   - Must implement graceful shutdown

3. **Environment Variables**
   ```bash
   # Required
   AGENT_ID=security-123
   MANAGEMENT_API_URL=http://api.opmas
   NATS_URL=nats://nats:4222

   # Optional
   LOG_LEVEL=INFO
   METRICS_ENABLED=true
   ```

4. **Agent Discovery File**
   ```ini
   # .env.discovery
   AGENT_NAME=SecurityAgent
   AGENT_VERSION=1.0.0
   AGENT_TYPE=security
   AGENT_DESCRIPTION=Security monitoring agent
   DEFAULT_SUBSCRIBED_TOPICS=logs.security,logs.auth
   DEFAULT_FINDINGS_TOPIC=findings.security
   ```
