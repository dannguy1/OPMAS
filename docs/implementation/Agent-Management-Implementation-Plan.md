# Agent Management System Implementation Plan

## Overview
This document outlines the implementation plan for the OPMAS Agent Management System, focusing on the asyncio-based process management and multi-agent execution capabilities.

## Implementation Status
- [x] Core Infrastructure
  - [x] Database Schema Updates
  - [x] Agent Process Management
  - [x] Agent Controller Implementation
- [x] Agent Base Class
  - [x] Base Agent Implementation
  - [x] Error Handling
  - [x] Logging
  - [x] Monitoring
  - [x] Recovery
  - [x] Status Management
- [x] Management API
  - [x] API Endpoints
  - [x] Status Service
  - [x] Recovery Service
  - [x] Error Handling Service
- [x] Agent Package
  - [x] Package Structure
  - [x] Configuration Management
  - [x] Environment Setup
- [ ] Testing
  - [ ] Unit Tests
  - [ ] Integration Tests
  - [ ] Performance Tests
  - [ ] Recovery Tests
- [ ] Documentation
  - [ ] API Documentation
  - [ ] Configuration Guide
  - [ ] Deployment Guide
  - [ ] Troubleshooting Guide

## Remaining Tasks

### 1. Testing Infrastructure
- [ ] Unit tests for each component
- [ ] Integration tests for agent lifecycle
- [ ] Performance tests for monitoring
- [ ] Recovery scenario tests
- [ ] Mock services for testing

### 2. Documentation
- [ ] API documentation
- [ ] Usage examples
- [ ] Configuration guide
- [ ] Troubleshooting guide
- [ ] Architecture diagrams

### 3. Security Layer
- [ ] Agent authentication
- [ ] Command authorization
- [ ] Secure communication
- [ ] Resource isolation
- [ ] Audit logging

### 4. Enhanced Monitoring
- [ ] Custom metric collection
- [ ] Alert thresholds
- [ ] Metric aggregation
- [ ] Performance baselines
- [ ] Resource forecasting

### 5. Advanced Recovery
- [ ] Automatic recovery policies
- [ ] Strategy selection
- [ ] State persistence
- [ ] Recovery validation
- [ ] Rollback verification

### 6. Error Handling Improvements
- [ ] Specific error types
- [ ] Error correlation
- [ ] Error reporting
- [ ] Recovery suggestions
- [ ] Error analytics

### 7. Process Management Enhancements
- [ ] Process isolation
- [ ] Resource quotas
- [ ] Process supervision
- [ ] Graceful shutdown
- [ ] State persistence

### 8. Logging Improvements
- [ ] Log aggregation
- [ ] Log analysis
- [ ] Log retention
- [ ] Log search
- [ ] Log alerts

### 9. Status Management Enhancements
- [ ] Status transitions
- [ ] Status validation
- [ ] Status dependencies
- [ ] Status notifications
- [ ] Status analytics

### 10. Deployment & Operations
- [ ] Deployment scripts
- [ ] Health checks
- [ ] Backup procedures
- [ ] Rollback procedures
- [ ] Monitoring setup

### 11. Performance Optimization
- [ ] Database query optimization
- [ ] Connection pooling
- [ ] Caching strategy
- [ ] Resource usage optimization
- [ ] Async operation optimization

### 12. Integration Features
- [ ] External system integration
- [ ] API endpoints
- [ ] Webhook support
- [ ] Event streaming
- [ ] Data export/import

## Known Issues
- Circular dependencies in SQLAlchemy models need to be carefully managed
- Model relationships must be properly defined on both sides
- Table redefinition issues can occur if models are imported multiple times
- Need to ensure proper initialization order of models
- Need to handle bidirectional relationships carefully

## Lessons Learned
1. Model Design:
   - Use `__table_args__ = {"extend_existing": True}` to prevent table redefinition issues
   - Define bidirectional relationships explicitly on both sides
   - Use proper foreign key constraints and nullable flags
   - Consider using UUID for primary keys
   - Include timestamps for auditing

2. Agent Controller:
   - Implement proper process management with resource limits
   - Use asyncio for non-blocking operations
   - Implement robust error handling and recovery
   - Monitor agent health and resource usage
   - Support graceful shutdown

3. Agent Discovery:
   - Implement periodic discovery of new agent packages
   - Support automatic registration of new agents
   - Validate agent configurations
   - Handle agent versioning
   - Support agent updates

4. Process Management:
   - Implement proper process isolation
   - Set resource limits (CPU, memory)
   - Monitor process health
   - Handle process crashes
   - Support graceful shutdown

5. Status Management:
   - Track agent status changes
   - Monitor resource usage
   - Implement health checks
   - Support status notifications
   - Maintain status history

6. Error Handling:
   - Implement comprehensive error tracking
   - Support error recovery
   - Log errors with context
   - Notify on critical errors
   - Maintain error history

7. Logging:
   - Implement structured logging
   - Support log rotation
   - Include context in logs
   - Support different log levels
   - Maintain audit trail

8. Configuration:
   - Support multiple configuration sources
   - Validate configurations
   - Support runtime updates
   - Handle sensitive data
   - Support environment-specific configs

9. Security:
   - Implement proper authentication
   - Support authorization
   - Secure communication
   - Resource isolation
   - Audit logging

10. Monitoring:
    - Track resource usage
    - Monitor agent health
    - Support custom metrics
    - Implement alerts
    - Support dashboards

## Implementation Notes

### Model Relationships
```python
# Example of proper bidirectional relationship
class User(Base):
    # ...
    created_devices = relationship("Device", back_populates="created_by", foreign_keys="Device.created_by_id")
    updated_devices = relationship("Device", back_populates="updated_by", foreign_keys="Device.updated_by_id")
    owned_devices = relationship("Device", back_populates="owner", foreign_keys="Device.owner_id")

class Device(Base):
    # ...
    created_by_id = mapped_column(String(36), ForeignKey("users.id"))
    updated_by_id = mapped_column(String(36), ForeignKey("users.id"))
    owner_id = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="created_devices")
    updated_by = relationship("User", foreign_keys=[updated_by_id], back_populates="updated_devices")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_devices")
```

### Agent Controller Implementation
```python
class AgentController:
    def __init__(self, db: AsyncSession, nats: NATSManager):
        self.db = db
        self.nats = nats
        self.agent_processes: Dict[str, AgentProcess] = {}
        self._discovery_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the controller."""
        self._discovery_task = asyncio.create_task(self._discover_agents())
        self._monitor_task = asyncio.create_task(self._monitor_all_agents())

    async def _discover_agents(self):
        """Periodically discover new agent packages."""
        while True:
            try:
                discovered = await self.discover_agent_packages()
                for package in discovered:
                    agent = await self.get_agent_by_type(package.type)
                    if not agent:
                        agent = await self.register_agent(package)
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in discovery task: {e}")
                await asyncio.sleep(60)

    async def _monitor_all_agents(self):
        """Monitor all running agents."""
        while True:
            try:
                for agent_id, process in list(self.agent_processes.items()):
                    status = process.get_status()
                    await self.update_agent_status(agent_id, status)
                    if self._check_resource_limits(process):
                        await self.restart_agent(agent_id)
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Error in monitoring task: {e}")
                await asyncio.sleep(60)
```

### Process Management
```python
class AgentProcess:
    def __init__(self, agent_id: str, config: Dict):
        self.agent_id = agent_id
        self.config = config
        self.process: Optional[asyncio.subprocess.Process] = None
        self.monitor_task: Optional[asyncio.Task] = None
        self.status = "stopped"
        self.pid: Optional[int] = None
        self.start_time: Optional[datetime] = None
        self.last_heartbeat: Optional[datetime] = None
        self.execution_stats = {
            "restarts": 0,
            "total_runtime": 0,
            "last_error": None,
            "resource_usage": {}
        }

    async def start(self) -> bool:
        """Start the agent process."""
        try:
            self.process = await asyncio.create_subprocess_exec(
                sys.executable,
                f"backend/scripts/run_{self.config['type']}_agent.py",
                self.agent_id,
                env=self._prepare_environment(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=self._set_resource_limits
            )
            self.pid = self.process.pid
            self.start_time = datetime.utcnow()
            self.status = "starting"
            self.monitor_task = asyncio.create_task(self._monitor())
            return True
        except Exception as e:
            logger.error(f"Failed to start agent {self.agent_id}: {e}")
            return False
```

### Status Management
```python
class StatusService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._status_cache: Dict[str, Dict] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    async def update_agent_status(
        self,
        agent_id: str,
        process_status: ProcessStatus,
        health_status: HealthStatus,
        recovery_status: RecoveryStatus,
        metrics: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        """Update agent status."""
        try:
            status = {
                "process_status": process_status,
                "health_status": health_status,
                "recovery_status": recovery_status,
                "last_heartbeat": datetime.utcnow(),
                "last_error": error,
                "updated_at": datetime.utcnow()
            }
            await self.db.execute(
                """
                INSERT INTO agent_status (
                    agent_id, process_status, health_status, recovery_status,
                    last_heartbeat, last_error, updated_at
                ) VALUES (
                    :agent_id, :process_status, :health_status, :recovery_status,
                    :last_heartbeat, :last_error, :updated_at
                )
                ON CONFLICT (agent_id) DO UPDATE SET
                    process_status = :process_status,
                    health_status = :health_status,
                    recovery_status = :recovery_status,
                    last_heartbeat = :last_heartbeat,
                    last_error = :last_error,
                    updated_at = :updated_at
                """,
                {**status, "agent_id": agent_id}
            )
            self._status_cache[agent_id] = status
            await self._record_status_change(agent_id, status)
        except Exception as e:
            logger.error(f"Failed to update agent status: {e}")
            raise
```

## Future Improvements
1. Add resource usage graphs
2. Implement agent dependencies
3. Add configuration versioning
4. Create agent templates
5. Add deployment automation
6. Add advanced recovery strategies
7. Implement metric aggregation
8. Add alerting system
9. Create status dashboard
10. Add audit logging
11. Add log aggregation
12. Add error pattern analysis
13. Add automated error resolution
14. Add log retention policies
15. Add log search capabilities
16. Add agent performance profiling
17. Add agent dependency management
18. Add agent configuration validation
19. Add agent state persistence
20. Add agent upgrade mechanism
21. Add interactive documentation
22. Add video tutorials
23. Add example implementations
24. Add best practices guide
25. Add security guide

## 1. Core Infrastructure

### 1.1 Database Schema Updates
```sql
-- Add new status values
ALTER TYPE agent_status ADD VALUE IF NOT EXISTS 'starting';
ALTER TYPE agent_status ADD VALUE IF NOT EXISTS 'stopping';

-- Add new columns
ALTER TABLE agents ADD COLUMN IF NOT EXISTS pid INTEGER;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS process_status VARCHAR(20);
ALTER TABLE agents ADD COLUMN IF NOT EXISTS last_error TEXT;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS resource_limits JSONB;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS execution_stats JSONB;
```

### 1.2 Agent Process Management
Location: `backend/src/opmas/agents/process.py`

```python
from typing import Dict, Optional, List
import asyncio
import psutil
import logging
from datetime import datetime
import json

class AgentProcess:
    def __init__(self, agent_id: str, config: Dict):
        self.agent_id = agent_id
        self.config = config
        self.process: Optional[asyncio.subprocess.Process] = None
        self.monitor_task: Optional[asyncio.Task] = None
        self.status = "stopped"
        self.pid: Optional[int] = None
        self.start_time: Optional[datetime] = None
        self.last_heartbeat: Optional[datetime] = None
        self.execution_stats = {
            "restarts": 0,
            "total_runtime": 0,
            "last_error": None,
            "resource_usage": {}
        }
        self.logger = logging.getLogger(__name__)

    async def start(self) -> bool:
        """Start the agent process."""
        try:
            # Create process with resource limits
            self.process = await asyncio.create_subprocess_exec(
                sys.executable,
                f"backend/scripts/run_{self.config['type']}_agent.py",
                self.agent_id,
                env=self._prepare_environment(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=self._set_resource_limits
            )

            self.pid = self.process.pid
            self.start_time = datetime.utcnow()
            self.status = "starting"

            # Start monitoring
            self.monitor_task = asyncio.create_task(self._monitor())

            return True

        except Exception as e:
            self.logger.error(f"Failed to start agent {self.agent_id}: {e}")
            self.execution_stats["last_error"] = str(e)
            return False

    def _set_resource_limits(self):
        """Set resource limits for the process."""
        import resource
        limits = self.config.get("resource_limits", {})

        if "cpu_percent" in limits:
            # Set CPU affinity
            psutil.Process().cpu_affinity([0])  # Example: Use first CPU core

        if "memory_mb" in limits:
            # Set memory limit
            resource.setrlimit(
                resource.RLIMIT_AS,
                (limits["memory_mb"] * 1024 * 1024, limits["memory_mb"] * 1024 * 1024)
            )

    def _prepare_environment(self) -> Dict[str, str]:
        """Prepare environment variables for the process."""
        env = os.environ.copy()
        env.update({
            "AGENT_ID": self.agent_id,
            "MANAGEMENT_API_URL": self.config["management_api_url"],
            "NATS_URL": self.config["nats_url"],
            "LOG_LEVEL": self.config.get("log_level", "INFO"),
            "METRICS_ENABLED": str(self.config.get("metrics_enabled", True))
        })
        return env

    async def _monitor(self):
        """Monitor process health and resource usage."""
        try:
            while True:
                if not self.process:
                    break

                # Check if process is still running
                if self.process.returncode is not None:
                    self.logger.error(
                        f"Agent {self.agent_id} process exited with code {self.process.returncode}"
                    )
                    self.status = "error"
                    self.execution_stats["last_error"] = f"Process exited with code {self.process.returncode}"
                    break

                # Update resource usage
                try:
                    p = psutil.Process(self.pid)
                    self.execution_stats["resource_usage"] = {
                        "cpu_percent": p.cpu_percent(),
                        "memory_percent": p.memory_percent(),
                        "num_threads": p.num_threads(),
                        "open_files": len(p.open_files()),
                        "connections": len(p.connections())
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    self.status = "error"
                    break

                # Read output
                stdout = await self.process.stdout.read(1024)
                if stdout:
                    self.logger.info(f"Agent {self.agent_id} stdout: {stdout.decode()}")

                stderr = await self.process.stderr.read(1024)
                if stderr:
                    self.logger.error(f"Agent {self.agent_id} stderr: {stderr.decode()}")

                await asyncio.sleep(1)

        except asyncio.CancelledError:
            self.logger.info(f"Monitoring task for agent {self.agent_id} cancelled")
        except Exception as e:
            self.logger.error(f"Error monitoring agent {self.agent_id}: {e}")
            self.status = "error"
            self.execution_stats["last_error"] = str(e)

    async def stop(self) -> bool:
        """Stop the agent process."""
        try:
            if not self.process:
                return True

            self.status = "stopping"

            # Send SIGTERM
            self.process.terminate()

            # Wait for graceful shutdown
            try:
                await asyncio.wait_for(self.process.wait(), timeout=10)
            except asyncio.TimeoutError:
                # Force kill if graceful shutdown fails
                self.process.kill()
                await self.process.wait()

            # Cancel monitoring task
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass

            self.status = "stopped"
            self.process = None
            self.monitor_task = None
            self.pid = None

            return True

        except Exception as e:
            self.logger.error(f"Failed to stop agent {self.agent_id}: {e}")
            self.execution_stats["last_error"] = str(e)
            return False

    def get_status(self) -> Dict:
        """Get current process status."""
        return {
            "status": self.status,
            "pid": self.pid,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "execution_stats": self.execution_stats
        }
```

### 1.3 Agent Controller Implementation
Location: `backend/src/opmas/agents/controller.py`

```python
from typing import Dict, List, Optional
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import json
from .process import AgentProcess

class AgentController:
    def __init__(self, db: AsyncSession, nats: NATSManager):
        self.db = db
        self.nats = nats
        self.agent_processes: Dict[str, AgentProcess] = {}
        self.logger = logging.getLogger(__name__)
        self._discovery_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the controller."""
        # Start discovery task
        self._discovery_task = asyncio.create_task(self._discover_agents())

        # Start global monitoring task
        self._monitor_task = asyncio.create_task(self._monitor_all_agents())

    async def stop(self):
        """Stop the controller."""
        # Stop all agents
        for agent_id in list(self.agent_processes.keys()):
            await self.stop_agent(agent_id)

        # Cancel tasks
        if self._discovery_task:
            self._discovery_task.cancel()
        if self._monitor_task:
            self._monitor_task.cancel()

    async def _discover_agents(self):
        """Periodically discover new agent packages."""
        while True:
            try:
                discovered = await self.discover_agent_packages()
                for package in discovered:
                    # Check if agent already exists
                    agent = await self.get_agent_by_type(package.type)
                    if not agent:
                        # Register new agent
                        agent = await self.register_agent(package)
                        self.logger.info(f"Registered new agent: {agent.id}")

                await asyncio.sleep(300)  # Check every 5 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in discovery task: {e}")
                await asyncio.sleep(60)  # Wait before retry

    async def _monitor_all_agents(self):
        """Monitor all running agents."""
        while True:
            try:
                for agent_id, process in list(self.agent_processes.items()):
                    status = process.get_status()

                    # Update agent status in database
                    await self.update_agent_status(agent_id, status)

                    # Check for resource limits
                    if self._check_resource_limits(process):
                        self.logger.warning(
                            f"Agent {agent_id} exceeded resource limits, restarting"
                        )
                        await self.restart_agent(agent_id)

                    # Check for heartbeat timeout
                    if self._check_heartbeat_timeout(process):
                        self.logger.warning(
                            f"Agent {agent_id} heartbeat timeout, restarting"
                        )
                        await self.restart_agent(agent_id)

                await asyncio.sleep(10)  # Check every 10 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring task: {e}")
                await asyncio.sleep(60)  # Wait before retry

    def _check_resource_limits(self, process: AgentProcess) -> bool:
        """Check if agent has exceeded resource limits."""
        limits = process.config.get("resource_limits", {})
        usage = process.execution_stats["resource_usage"]

        if "cpu_percent" in limits and usage["cpu_percent"] > limits["cpu_percent"]:
            return True

        if "memory_percent" in limits and usage["memory_percent"] > limits["memory_percent"]:
            return True

        return False

    def _check_heartbeat_timeout(self, process: AgentProcess) -> bool:
        """Check if agent heartbeat has timed out."""
        if not process.last_heartbeat:
            return True

        timeout = process.config.get("heartbeat_timeout", 60)  # Default 60 seconds
        return (datetime.utcnow() - process.last_heartbeat).total_seconds() > timeout

    async def restart_agent(self, agent_id: str) -> bool:
        """Restart an agent."""
        try:
            process = self.agent_processes.get(agent_id)
            if not process:
                return False

            # Stop the agent
            await process.stop()

            # Update stats
            process.execution_stats["restarts"] += 1

            # Start the agent
            return await process.start()

        except Exception as e:
            self.logger.error(f"Failed to restart agent {agent_id}: {e}")
            return False

    async def get_agent_status(self, agent_id: str) -> Dict:
        """Get agent status."""
        process = self.agent_processes.get(agent_id)
        if not process:
            return {"status": "stopped"}

        return process.get_status()

    async def list_agents(self) -> List[Dict]:
        """List all agents with their status."""
        agents = []
        for agent_id, process in self.agent_processes.items():
            agents.append({
                "id": agent_id,
                **process.get_status()
            })
        return agents
```

## 2. Agent Base Class Updates

### 2.1 BaseAgent Implementation
Location: `backend/src/opmas/agents/base_agent.py`

```python
from typing import Dict, Optional, Any
import asyncio
import logging
from datetime import datetime
import json
from .error_handler import ErrorHandler, ErrorSeverity, ErrorCategory
from .logging import AgentLogger
from .status import StatusService

class BaseAgent:
    def __init__(
        self,
        agent_id: str,
        management_api_url: str,
        nats_url: str,
        log_dir: str
    ):
        self.agent_id = agent_id
        self.management_api_url = management_api_url
        self.nats_url = nats_url
        self.nats_client = None
        self.running = False

        # Initialize services
        self.logger = AgentLogger(agent_id, log_dir)
        self.error_handler = ErrorHandler(db, nats)
        self.status_service = StatusService(db)

        # Agent state
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._status_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        self._last_heartbeat: Optional[datetime] = None
        self._start_time: Optional[datetime] = None
        self._metrics: Dict[str, Any] = {}

    async def start(self):
        """Initialize and start the agent."""
        try:
            self._start_time = datetime.utcnow()
            self.logger.info("Starting agent", {"start_time": self._start_time})

            # Connect to NATS
            await self._connect_nats()

            # Start background tasks
            self.running = True
            self._heartbeat_task = asyncio.create_task(self._heartbeat())
            self._status_task = asyncio.create_task(self._status_monitor())
            self._metrics_task = asyncio.create_task(self._collect_metrics())

            # Update status
            await self.status_service.update_agent_status(
                self.agent_id,
                process_status="running",
                health_status="healthy"
            )

            self.logger.info("Agent started successfully")

        except Exception as e:
            self.logger.error("Failed to start agent", {"error": str(e)})
            await self.error_handler.handle_error(
                self.agent_id,
                e,
                ErrorSeverity.ERROR,
                ErrorCategory.PROCESS,
                {"stage": "startup"}
            )
            raise

    async def stop(self):
        """Stop the agent."""
        try:
            self.logger.info("Stopping agent")
            self.running = False

            # Cancel background tasks
            for task in [self._heartbeat_task, self._status_task, self._metrics_task]:
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            # Close NATS connection
            if self.nats_client:
                await self.nats_client.close()

            # Update status
            await self.status_service.update_agent_status(
                self.agent_id,
                process_status="stopped",
                health_status="unknown"
            )

            self.logger.info("Agent stopped successfully")

        except Exception as e:
            self.logger.error("Failed to stop agent", {"error": str(e)})
            await self.error_handler.handle_error(
                self.agent_id,
                e,
                ErrorSeverity.ERROR,
                ErrorCategory.PROCESS,
                {"stage": "shutdown"}
            )
            raise

    async def _connect_nats(self):
        """Connect to NATS server."""
        try:
            self.nats_client = await nats.connect(self.nats_url)

            # Subscribe to control topic
            await self.nats_client.subscribe(
                f"agent.{self.agent_id}.control",
                cb=self._handle_control_message
            )

            self.logger.info("Connected to NATS server")

        except Exception as e:
            self.logger.error("Failed to connect to NATS", {"error": str(e)})
            await self.error_handler.handle_error(
                self.agent_id,
                e,
                ErrorSeverity.ERROR,
                ErrorCategory.NETWORK,
                {"service": "nats"}
            )
            raise

    async def _heartbeat(self):
        """Send periodic heartbeat."""
        while self.running:
            try:
                self._last_heartbeat = datetime.utcnow()
                await self.nats_client.publish(
                    "agent.heartbeat",
                    json.dumps({
                        "agent_id": self.agent_id,
                        "timestamp": self._last_heartbeat.isoformat(),
                        "uptime": (self._last_heartbeat - self._start_time).total_seconds()
                    }).encode()
                )
                self.logger.debug("Heartbeat sent")

            except Exception as e:
                self.logger.error("Failed to send heartbeat", {"error": str(e)})
                await self.error_handler.handle_error(
                    self.agent_id,
                    e,
                    ErrorSeverity.WARNING,
                    ErrorCategory.NETWORK,
                    {"service": "heartbeat"}
                )

            await asyncio.sleep(self.heartbeat_interval)

    async def _status_monitor(self):
        """Monitor agent status."""
        while self.running:
            try:
                # Check resource usage
                resource_usage = await self._check_resources()

                # Update metrics
                self._metrics.update(resource_usage)

                # Update status
                health_status = self._determine_health_status()
                await self.status_service.update_agent_status(
                    self.agent_id,
                    process_status="running",
                    health_status=health_status,
                    metrics=self._metrics
                )

            except Exception as e:
                self.logger.error("Failed to update status", {"error": str(e)})
                await self.error_handler.handle_error(
                    self.agent_id,
                    e,
                    ErrorSeverity.WARNING,
                    ErrorCategory.PROCESS,
                    {"stage": "status_monitor"}
                )

            await asyncio.sleep(self.status_interval)

    async def _collect_metrics(self):
        """Collect agent metrics."""
        while self.running:
            try:
                metrics = await self._gather_metrics()
                self._metrics.update(metrics)

                # Publish metrics
                await self.nats_client.publish(
                    "agent.metrics",
                    json.dumps({
                        "agent_id": self.agent_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "metrics": metrics
                    }).encode()
                )

            except Exception as e:
                self.logger.error("Failed to collect metrics", {"error": str(e)})
                await self.error_handler.handle_error(
                    self.agent_id,
                    e,
                    ErrorSeverity.WARNING,
                    ErrorCategory.PROCESS,
                    {"stage": "metrics_collection"}
                )

            await asyncio.sleep(self.metrics_interval)

    async def _handle_control_message(self, msg):
        """Handle control messages."""
        try:
            data = json.loads(msg.data.decode())
            command = data.get("command")

            self.logger.info("Received control message", {"command": command})

            if command == "stop":
                await self.stop()
            elif command == "reload":
                await self.reload_config()
            elif command == "restart":
                await self.stop()
                await self.start()
            else:
                self.logger.warning("Unknown command", {"command": command})

        except Exception as e:
            self.logger.error("Failed to handle control message", {"error": str(e)})
            await self.error_handler.handle_error(
                self.agent_id,
                e,
                ErrorSeverity.ERROR,
                ErrorCategory.PROCESS,
                {"stage": "control_message", "command": command}
            )

    async def _check_resources(self) -> Dict[str, float]:
        """Check resource usage."""
        try:
            process = psutil.Process()
            return {
                "cpu_percent": process.cpu_percent(),
                "memory_percent": process.memory_percent(),
                "num_threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections())
            }
        except Exception as e:
            self.logger.error("Failed to check resources", {"error": str(e)})
            return {}

    def _determine_health_status(self) -> str:
        """Determine agent health status."""
        try:
            # Check resource usage
            if self._metrics.get("cpu_percent", 0) > 90:
                return "warning"
            if self._metrics.get("memory_percent", 0) > 90:
                return "warning"

            # Check heartbeat
            if not self._last_heartbeat:
                return "critical"
            if (datetime.utcnow() - self._last_heartbeat).total_seconds() > 60:
                return "critical"

            return "healthy"

        except Exception as e:
            self.logger.error("Failed to determine health status", {"error": str(e)})
            return "unknown"

    async def _gather_metrics(self) -> Dict[str, Any]:
        """Gather agent-specific metrics."""
        # To be implemented by specific agents
        return {}
```

## 3. Management API Updates

### 3.1 API Endpoints
Location: `management_api/src/opmas_mgmt_api/routes/agents.py`

```python
@router.post("/agents/{agent_id}/start")
async def start_agent(agent_id: str):
    """Start an agent."""
    return await agent_service.controller.start_agent(agent_id)

@router.post("/agents/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """Stop an agent."""
    return await agent_service.controller.stop_agent(agent_id)

@router.post("/agents/{agent_id}/restart")
async def restart_agent(agent_id: str):
    """Restart an agent."""
    return await agent_service.controller.restart_agent(agent_id)

@router.get("/agents/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """Get agent status."""
    return await agent_service.controller.get_agent_status(agent_id)

@router.get("/agents")
async def list_agents():
    """List all agents."""
    return await agent_service.controller.list_agents()

@router.post("/agents/discover")
async def discover_agents():
    """Discover new agents."""
    return await agent_service.controller.discover_agent_packages()
```

## 4. Testing

### 4.1 Unit Tests
Location: `backend/tests/agents/test_controller.py`

```python
@pytest.mark.asyncio
async def test_agent_lifecycle():
    """Test agent lifecycle management."""
    controller = AgentController(db, nats)
    await controller.start()

    # Register and start agent
    agent = await controller.register_agent(package)
    assert await controller.start_agent(agent.id)

    # Check status
    status = await controller.get_agent_status(agent.id)
    assert status["status"] == "running"

    # Stop agent
    assert await controller.stop_agent(agent.id)
    status = await controller.get_agent_status(agent.id)
    assert status["status"] == "stopped"

    await controller.stop()

@pytest.mark.asyncio
async def test_agent_monitoring():
    """Test agent monitoring."""
    controller = AgentController(db, nats)
    await controller.start()

    # Start agent
    agent = await controller.register_agent(package)
    await controller.start_agent(agent.id)

    # Check resource monitoring
    status = await controller.get_agent_status(agent.id)
    assert "resource_usage" in status["execution_stats"]

    # Check heartbeat
    assert status["last_heartbeat"] is not None

    await controller.stop()
```

### 4.2 Integration Tests
Location: `backend/tests/integration/test_agent_management.py`

```python
@pytest.mark.integration
async def test_multi_agent_execution():
    """Test multiple agent execution."""
    controller = AgentController(db, nats)
    await controller.start()

    # Start multiple agents
    agents = []
    for i in range(3):
        agent = await controller.register_agent(package)
        await controller.start_agent(agent.id)
        agents.append(agent)

    # Check all agents are running
    statuses = await controller.list_agents()
    assert len(statuses) == 3
    assert all(s["status"] == "running" for s in statuses)

    # Stop all agents
    for agent in agents:
        await controller.stop_agent(agent.id)

    # Verify all stopped
    statuses = await controller.list_agents()
    assert len(statuses) == 0

    await controller.stop()
```

## 5. Deployment

### 5.1 Configuration
```yaml
# config/agent_management.yaml
controller:
  discovery_interval: 300  # seconds
  monitoring_interval: 10  # seconds
  heartbeat_timeout: 60   # seconds

default_limits:
  cpu_percent: 50
  memory_percent: 30
  max_restarts: 3
  restart_delay: 5  # seconds
```

### 5.2 Startup Script
```bash
#!/bin/bash
# scripts/start_agent_controller.sh

# Start the agent controller
python -m opmas.agents.controller \
    --config config/agent_management.yaml \
    --log-level INFO
```

## 6. Status Tracking and Recovery Implementation

### 6.1 Status Service
Location: `backend/src/opmas/agents/status.py`

```python
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import logging
from enum import Enum

class ProcessStatus(str, Enum):
    RUNNING = "running"
    STARTING = "starting"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    DEGRADED = "degraded"

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class RecoveryStatus(str, Enum):
    NONE = "none"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"

class StatusService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self._status_cache: Dict[str, Dict] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the status service."""
        self._cleanup_task = asyncio.create_task(self._cleanup_old_metrics())

    async def stop(self):
        """Stop the status service."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def update_agent_status(
        self,
        agent_id: str,
        process_status: ProcessStatus,
        health_status: HealthStatus,
        recovery_status: RecoveryStatus,
        metrics: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        """Update agent status."""
        try:
            # Update current status
            status = {
                "process_status": process_status,
                "health_status": health_status,
                "recovery_status": recovery_status,
                "last_heartbeat": datetime.utcnow(),
                "last_error": error,
                "updated_at": datetime.utcnow()
            }

            # Update database
            await self.db.execute(
                """
                INSERT INTO agent_status (
                    agent_id, process_status, health_status, recovery_status,
                    last_heartbeat, last_error, updated_at
                ) VALUES (
                    :agent_id, :process_status, :health_status, :recovery_status,
                    :last_heartbeat, :last_error, :updated_at
                )
                ON CONFLICT (agent_id) DO UPDATE SET
                    process_status = :process_status,
                    health_status = :health_status,
                    recovery_status = :recovery_status,
                    last_heartbeat = :last_heartbeat,
                    last_error = :last_error,
                    updated_at = :updated_at
                """,
                {**status, "agent_id": agent_id}
            )

            # Store metrics if provided
            if metrics:
                await self._store_metrics(agent_id, metrics)

            # Update cache
            self._status_cache[agent_id] = status

            # Record status change in history
            await self._record_status_change(agent_id, status)

        except Exception as e:
            self.logger.error(f"Failed to update agent status: {e}")
            raise

    async def get_agent_status(self, agent_id: str) -> Dict:
        """Get current agent status."""
        try:
            # Check cache first
            if agent_id in self._status_cache:
                return self._status_cache[agent_id]

            # Query database
            result = await self.db.execute(
                "SELECT * FROM agent_status WHERE agent_id = :agent_id",
                {"agent_id": agent_id}
            )
            status = result.fetchone()

            if status:
                self._status_cache[agent_id] = dict(status)
                return dict(status)

            return {
                "process_status": ProcessStatus.STOPPED,
                "health_status": HealthStatus.UNKNOWN,
                "recovery_status": RecoveryStatus.NONE
            }

        except Exception as e:
            self.logger.error(f"Failed to get agent status: {e}")
            raise

    async def get_agent_status_history(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """Get agent status history."""
        try:
            result = await self.db.execute(
                """
                SELECT * FROM agent_status_history
                WHERE agent_id = :agent_id
                ORDER BY created_at DESC
                LIMIT :limit
                """,
                {"agent_id": agent_id, "limit": limit}
            )
            return [dict(row) for row in result.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to get agent status history: {e}")
            raise

    async def _store_metrics(self, agent_id: str, metrics: Dict):
        """Store agent metrics."""
        try:
            for metric_type, value in metrics.items():
                await self.db.execute(
                    """
                    INSERT INTO agent_resource_metrics (
                        agent_id, metric_type, metric_value
                    ) VALUES (
                        :agent_id, :metric_type, :metric_value
                    )
                    """,
                    {
                        "agent_id": agent_id,
                        "metric_type": metric_type,
                        "metric_value": value
                    }
                )

        except Exception as e:
            self.logger.error(f"Failed to store metrics: {e}")
            raise

    async def _record_status_change(self, agent_id: str, status: Dict):
        """Record status change in history."""
        try:
            await self.db.execute(
                """
                INSERT INTO agent_status_history (
                    agent_id, event_type, from_status, to_status, details
                ) VALUES (
                    :agent_id, :event_type, :from_status, :to_status, :details
                )
                """,
                {
                    "agent_id": agent_id,
                    "event_type": "status_change",
                    "from_status": status.get("previous_status"),
                    "to_status": status["process_status"],
                    "details": status
                }
            )

        except Exception as e:
            self.logger.error(f"Failed to record status change: {e}")
            raise

    async def _cleanup_old_metrics(self):
        """Clean up old metrics data."""
        while True:
            try:
                # Delete metrics older than 7 days
                await self.db.execute(
                    """
                    DELETE FROM agent_resource_metrics
                    WHERE created_at < NOW() - INTERVAL '7 days'
                    """
                )

                # Delete status history older than 30 days
                await self.db.execute(
                    """
                    DELETE FROM agent_status_history
                    WHERE created_at < NOW() - INTERVAL '30 days'
                    """
                )

                await asyncio.sleep(3600)  # Run every hour

            except Exception as e:
                self.logger.error(f"Failed to cleanup old metrics: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
```

### 6.2 Recovery Service
Location: `backend/src/opmas/agents/recovery.py`

```python
from typing import Dict, Optional
from datetime import datetime
import asyncio
import logging
from .status import RecoveryStatus

class RecoveryService:
    def __init__(self, db: AsyncSession, status_service: StatusService):
        self.db = db
        self.status_service = status_service
        self.logger = logging.getLogger(__name__)
        self._recovery_tasks: Dict[str, asyncio.Task] = {}

    async def start_recovery(
        self,
        agent_id: str,
        strategy: str = "restart"
    ) -> bool:
        """Start agent recovery process."""
        try:
            # Check if recovery already in progress
            if agent_id in self._recovery_tasks:
                return False

            # Get current recovery attempt number
            result = await self.db.execute(
                """
                SELECT COUNT(*) FROM agent_recovery_attempts
                WHERE agent_id = :agent_id
                """,
                {"agent_id": agent_id}
            )
            attempt_number = result.scalar() + 1

            # Create recovery task
            self._recovery_tasks[agent_id] = asyncio.create_task(
                self._execute_recovery(agent_id, strategy, attempt_number)
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to start recovery: {e}")
            return False

    async def _execute_recovery(
        self,
        agent_id: str,
        strategy: str,
        attempt_number: int
    ):
        """Execute recovery process."""
        try:
            # Record recovery attempt
            await self.db.execute(
                """
                INSERT INTO agent_recovery_attempts (
                    agent_id, attempt_number, recovery_strategy,
                    status, started_at
                ) VALUES (
                    :agent_id, :attempt_number, :strategy,
                    'in_progress', :started_at
                )
                """,
                {
                    "agent_id": agent_id,
                    "attempt_number": attempt_number,
                    "strategy": strategy,
                    "started_at": datetime.utcnow()
                }
            )

            # Update status
            await self.status_service.update_agent_status(
                agent_id,
                process_status="starting",
                health_status="unknown",
                recovery_status=RecoveryStatus.IN_PROGRESS
            )

            # Execute recovery strategy
            success = await self._apply_recovery_strategy(agent_id, strategy)

            # Update recovery attempt status
            await self.db.execute(
                """
                UPDATE agent_recovery_attempts
                SET status = :status, completed_at = :completed_at
                WHERE agent_id = :agent_id AND attempt_number = :attempt_number
                """,
                {
                    "agent_id": agent_id,
                    "attempt_number": attempt_number,
                    "status": "success" if success else "failed",
                    "completed_at": datetime.utcnow()
                }
            )

            # Update agent status
            await self.status_service.update_agent_status(
                agent_id,
                process_status="running" if success else "failed",
                health_status="healthy" if success else "critical",
                recovery_status=RecoveryStatus.SUCCESS if success else RecoveryStatus.FAILED
            )

        except Exception as e:
            self.logger.error(f"Recovery failed: {e}")
            await self.status_service.update_agent_status(
                agent_id,
                process_status="failed",
                health_status="critical",
                recovery_status=RecoveryStatus.FAILED,
                error=str(e)
            )

        finally:
            # Clean up recovery task
            self._recovery_tasks.pop(agent_id, None)

    async def _apply_recovery_strategy(
        self,
        agent_id: str,
        strategy: str
    ) -> bool:
        """Apply recovery strategy."""
        try:
            if strategy == "restart":
                # Stop agent
                await self._stop_agent(agent_id)
                await asyncio.sleep(5)  # Wait for cleanup

                # Start agent
                return await self._start_agent(agent_id)

            elif strategy == "reload":
                # Reload configuration
                return await self._reload_config(agent_id)

            else:
                self.logger.error(f"Unknown recovery strategy: {strategy}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to apply recovery strategy: {e}")
            return False

    async def get_recovery_status(self, agent_id: str) -> Dict:
        """Get agent recovery status."""
        try:
            # Get latest recovery attempt
            result = await self.db.execute(
                """
                SELECT * FROM agent_recovery_attempts
                WHERE agent_id = :agent_id
                ORDER BY attempt_number DESC
                LIMIT 1
                """,
                {"agent_id": agent_id}
            )
            attempt = result.fetchone()

            if attempt:
                return {
                    "in_progress": attempt.status == "in_progress",
                    "last_attempt": {
                        "number": attempt.attempt_number,
                        "strategy": attempt.recovery_strategy,
                        "status": attempt.status,
                        "started_at": attempt.started_at,
                        "completed_at": attempt.completed_at,
                        "error": attempt.error
                    }
                }

            return {
                "in_progress": False,
                "last_attempt": None
            }

        except Exception as e:
            self.logger.error(f"Failed to get recovery status: {e}")
            raise
```

### 6.3 UI Components
Location: `frontend/src/components/AgentStatus`

```typescript
// StatusDashboard.tsx
import React from 'react';
import { useAgentStatus } from '../hooks/useAgentStatus';
import { StatusTimeline } from './StatusTimeline';
import { RecoveryControls } from './RecoveryControls';
import { MetricsChart } from './MetricsChart';

interface StatusDashboardProps {
    agentId: string;
}

export const StatusDashboard: React.FC<StatusDashboardProps> = ({ agentId }) => {
    const { status, metrics, history, recovery } = useAgentStatus(agentId);

    return (
        <div className="status-dashboard">
            <div className="status-header">
                <h2>Agent Status</h2>
                <div className="status-indicators">
                    <StatusBadge status={status.processStatus} />
                    <HealthBadge status={status.healthStatus} />
                    <RecoveryBadge status={status.recoveryStatus} />
                </div>
            </div>

            <div className="status-metrics">
                <MetricsChart data={metrics} />
            </div>

            <div className="status-controls">
                <RecoveryControls
                    agentId={agentId}
                    recovery={recovery}
                />
            </div>

            <div className="status-history">
                <StatusTimeline events={history} />
            </div>
        </div>
    );
};

// StatusTimeline.tsx
interface StatusTimelineProps {
    events: StatusEvent[];
}

export const StatusTimeline: React.FC<StatusTimelineProps> = ({ events }) => {
    return (
        <div className="status-timeline">
            <h3>Status History</h3>
            <Timeline>
                {events.map(event => (
                    <TimelineItem key={event.id}>
                        <TimelineContent>
                            <div className="event-header">
                                <span className="timestamp">
                                    {formatDate(event.timestamp)}
                                </span>
                                <StatusBadge status={event.toStatus} />
                            </div>
                            <div className="event-details">
                                {event.details && (
                                    <pre>{JSON.stringify(event.details, null, 2)}</pre>
                                )}
                            </div>
                        </TimelineContent>
                    </TimelineItem>
                ))}
            </Timeline>
        </div>
    );
};

// RecoveryControls.tsx
interface RecoveryControlsProps {
    agentId: string;
    recovery: RecoveryStatus;
}

export const RecoveryControls: React.FC<RecoveryControlsProps> = ({
    agentId,
    recovery
}) => {
    const { triggerRecovery, isRecoveryInProgress } = useRecovery(agentId);

    return (
        <div className="recovery-controls">
            <h3>Recovery Controls</h3>

            <div className="recovery-status">
                <RecoveryBadge status={recovery.status} />
                {recovery.lastAttempt && (
                    <div className="last-attempt">
                        <span>Last attempt: {formatDate(recovery.lastAttempt.timestamp)}</span>
                        <span>Status: {recovery.lastAttempt.status}</span>
                    </div>
                )}
            </div>

            <div className="recovery-actions">
                <Button
                    onClick={() => triggerRecovery('restart')}
                    disabled={isRecoveryInProgress}
                >
                    Restart Agent
                </Button>
                <Button
                    onClick={() => triggerRecovery('reload')}
                    disabled={isRecoveryInProgress}
                >
                    Reload Configuration
                </Button>
            </div>

            <div className="recovery-policy">
                <h4>Recovery Policy</h4>
                <Switch
                    checked={recovery.policy.autoRecovery}
                    onChange={toggleAutoRecovery}
                />
                <span>Auto Recovery</span>
            </div>
        </div>
    );
};

// MetricsChart.tsx
interface MetricsChartProps {
    data: MetricsData;
}

export const MetricsChart: React.FC<MetricsChartProps> = ({ data }) => {
    return (
        <div className="metrics-chart">
            <h3>Resource Usage</h3>
            <LineChart
                data={data.resourceUsage}
                xAxis="timestamp"
                yAxis="value"
                series={['cpu', 'memory', 'disk', 'network']}
            />

            <h3>Health Metrics</h3>
            <LineChart
                data={data.healthMetrics}
                xAxis="timestamp"
                yAxis="value"
                series={['responseTime', 'errorRate', 'heartbeatLatency']}
            />
        </div>
    );
};
```

### 6.4 API Integration
Location: `management_api/src/opmas_mgmt_api/services/status.py`

```python
from typing import Dict, List, Optional
from datetime import datetime
from .base import BaseService
from ..models.status import (
    ProcessStatus,
    HealthStatus,
    RecoveryStatus,
    StatusEvent,
    RecoveryAttempt
)

class StatusService(BaseService):
    def __init__(self, db, nats):
        super().__init__(db, nats)
        self.status_service = StatusService(db)
        self.recovery_service = RecoveryService(db, self.status_service)

    async def get_agent_status(self, agent_id: str) -> Dict:
        """Get current agent status."""
        return await self.status_service.get_agent_status(agent_id)

    async def get_agent_status_history(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """Get agent status history."""
        return await self.status_service.get_agent_status_history(agent_id, limit)

    async def get_agent_recovery_status(self, agent_id: str) -> Dict:
        """Get agent recovery status."""
        return await self.recovery_service.get_recovery_status(agent_id)

    async def trigger_agent_recovery(
        self,
        agent_id: str,
        strategy: str = "restart"
    ) -> bool:
        """Trigger agent recovery."""
        return await self.recovery_service.start_recovery(agent_id, strategy)

    async def get_agent_metrics(
        self,
        agent_id: str,
        metric_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """Get agent metrics."""
        return await self.status_service.get_agent_metrics(
            agent_id,
            metric_type,
            start_time,
            end_time
        )
```

## 7. Error Handling and Logging Implementation

### 7.1 Error Handling Service
Location: `backend/src/opmas/agents/error_handler.py`

```python
from typing import Dict, Optional, List
from datetime import datetime
import logging
import traceback
from enum import Enum

class ErrorSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ErrorCategory(str, Enum):
    PROCESS = "process"
    RESOURCE = "resource"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    DATABASE = "database"
    UNKNOWN = "unknown"

class ErrorHandler:
    def __init__(self, db: AsyncSession, nats: NATSManager):
        self.db = db
        self.nats = nats
        self.logger = logging.getLogger(__name__)

    async def handle_error(
        self,
        agent_id: str,
        error: Exception,
        severity: ErrorSeverity,
        category: ErrorCategory,
        context: Optional[Dict] = None
    ):
        """Handle and log agent errors."""
        try:
            error_data = {
                "agent_id": agent_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "stack_trace": traceback.format_exc(),
                "severity": severity,
                "category": category,
                "context": context or {},
                "timestamp": datetime.utcnow()
            }

            # Log to database
            await self._log_error(error_data)

            # Publish error event
            await self._publish_error_event(error_data)

            # Handle based on severity
            if severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
                await self._handle_critical_error(agent_id, error_data)

        except Exception as e:
            self.logger.error(f"Failed to handle error: {e}")

    async def _log_error(self, error_data: Dict):
        """Log error to database."""
        try:
            await self.db.execute(
                """
                INSERT INTO agent_errors (
                    agent_id, error_type, error_message, stack_trace,
                    severity, category, context, created_at
                ) VALUES (
                    :agent_id, :error_type, :error_message, :stack_trace,
                    :severity, :category, :context, :timestamp
                )
                """,
                error_data
            )
        except Exception as e:
            self.logger.error(f"Failed to log error to database: {e}")

    async def _publish_error_event(self, error_data: Dict):
        """Publish error event to NATS."""
        try:
            await self.nats.publish(
                "agent.errors",
                json.dumps(error_data).encode()
            )
        except Exception as e:
            self.logger.error(f"Failed to publish error event: {e}")

    async def _handle_critical_error(self, agent_id: str, error_data: Dict):
        """Handle critical errors."""
        try:
            # Update agent status
            await self.status_service.update_agent_status(
                agent_id,
                process_status="failed",
                health_status="critical",
                error=error_data["error_message"]
            )

            # Trigger recovery if configured
            if self._should_trigger_recovery(error_data):
                await self.recovery_service.start_recovery(agent_id)

        except Exception as e:
            self.logger.error(f"Failed to handle critical error: {e}")

    def _should_trigger_recovery(self, error_data: Dict) -> bool:
        """Determine if recovery should be triggered."""
        # Check error category and severity
        if error_data["severity"] == ErrorSeverity.CRITICAL:
            return True

        # Check error type
        if error_data["error_type"] in [
            "ProcessError",
            "ResourceExhaustionError",
            "ConnectionError"
        ]:
            return True

        return False

    async def get_agent_errors(
        self,
        agent_id: str,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get agent error history."""
        try:
            query = """
                SELECT * FROM agent_errors
                WHERE agent_id = :agent_id
            """
            params = {"agent_id": agent_id}

            if severity:
                query += " AND severity = :severity"
                params["severity"] = severity

            if category:
                query += " AND category = :category"
                params["category"] = category

            query += " ORDER BY created_at DESC LIMIT :limit"
            params["limit"] = limit

            result = await self.db.execute(query, params)
            return [dict(row) for row in result.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to get agent errors: {e}")
            raise
```

### 7.2 Logging Configuration
Location: `backend/src/opmas/agents/logging.py`

```python
import logging
import logging.handlers
import json
from datetime import datetime
from typing import Dict, Any

class AgentLogger:
    def __init__(self, agent_id: str, log_dir: str):
        self.agent_id = agent_id
        self.log_dir = log_dir
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Set up agent logger."""
        logger = logging.getLogger(f"agent.{self.agent_id}")
        logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.handlers.RotatingFileHandler(
            f"{self.log_dir}/agent_{self.agent_id}.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(self._get_formatter())
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self._get_formatter())
        logger.addHandler(console_handler)

        return logger

    def _get_formatter(self) -> logging.Formatter:
        """Get log formatter."""
        return logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _format_log(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        """Format log entry."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id,
            "level": level,
            "message": message,
            **kwargs
        }

    def info(self, message: str, **kwargs):
        """Log info message."""
        log_entry = self._format_log("INFO", message, **kwargs)
        self.logger.info(json.dumps(log_entry))

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        log_entry = self._format_log("WARNING", message, **kwargs)
        self.logger.warning(json.dumps(log_entry))

    def error(self, message: str, **kwargs):
        """Log error message."""
        log_entry = self._format_log("ERROR", message, **kwargs)
        self.logger.error(json.dumps(log_entry))

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        log_entry = self._format_log("CRITICAL", message, **kwargs)
        self.logger.critical(json.dumps(log_entry))

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        log_entry = self._format_log("DEBUG", message, **kwargs)
        self.logger.debug(json.dumps(log_entry))
```

### 7.3 Database Schema Updates
```sql
-- Error tracking
CREATE TABLE agent_errors (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    severity VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL,
    context JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- Log aggregation
CREATE TABLE agent_logs (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL,
    level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- Create indexes
CREATE INDEX idx_agent_errors_agent_id ON agent_errors(agent_id);
CREATE INDEX idx_agent_errors_severity ON agent_errors(severity);
CREATE INDEX idx_agent_errors_category ON agent_errors(category);
CREATE INDEX idx_agent_errors_created_at ON agent_errors(created_at);

CREATE INDEX idx_agent_logs_agent_id ON agent_logs(agent_id);
CREATE INDEX idx_agent_logs_level ON agent_logs(level);
CREATE INDEX idx_agent_logs_created_at ON agent_logs(created_at);
```

### 7.4 API Integration
Location: `management_api/src/opmas_mgmt_api/routes/errors.py`

```python
@router.get("/agents/{agent_id}/errors")
async def get_agent_errors(
    agent_id: str,
    severity: Optional[ErrorSeverity] = None,
    category: Optional[ErrorCategory] = None,
    limit: int = 100
):
    """Get agent error history."""
    return await error_service.get_agent_errors(
        agent_id,
        severity,
        category,
        limit
    )

@router.get("/agents/{agent_id}/logs")
async def get_agent_logs(
    agent_id: str,
    level: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100
):
    """Get agent logs."""
    return await log_service.get_agent_logs(
        agent_id,
        level,
        start_time,
        end_time,
        limit
    )
```

### 7.5 UI Components
Location: `frontend/src/components/AgentLogs`

```typescript
// ErrorList.tsx
interface ErrorListProps {
    agentId: string;
}

export const ErrorList: React.FC<ErrorListProps> = ({ agentId }) => {
    const { errors, loading } = useAgentErrors(agentId);

    return (
        <div className="error-list">
            <h3>Error History</h3>
            {loading ? (
                <LoadingSpinner />
            ) : (
                <Table>
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Type</th>
                            <th>Severity</th>
                            <th>Message</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {errors.map(error => (
                            <tr key={error.id}>
                                <td>{formatDate(error.timestamp)}</td>
                                <td>
                                    <ErrorTypeBadge type={error.error_type} />
                                </td>
                                <td>
                                    <SeverityBadge severity={error.severity} />
                                </td>
                                <td>{error.error_message}</td>
                                <td>
                                    <Button
                                        onClick={() => showErrorDetails(error)}
                                    >
                                        Details
                                    </Button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </Table>
            )}
        </div>
    );
};

// LogViewer.tsx
interface LogViewerProps {
    agentId: string;
}

export const LogViewer: React.FC<LogViewerProps> = ({ agentId }) => {
    const { logs, loading } = useAgentLogs(agentId);
    const [filter, setFilter] = useState({
        level: 'all',
        search: ''
    });

    return (
        <div className="log-viewer">
            <div className="log-controls">
                <LevelFilter
                    value={filter.level}
                    onChange={level => setFilter({ ...filter, level })}
                />
                <SearchInput
                    value={filter.search}
                    onChange={search => setFilter({ ...filter, search })}
                />
            </div>

            <div className="log-content">
                {loading ? (
                    <LoadingSpinner />
                ) : (
                    <LogStream
                        logs={logs}
                        filter={filter}
                    />
                )}
            </div>
        </div>
    );
};
```

## 9. Documentation Implementation

### 9.1 API Documentation
Location: `docs/api/agent_management.md`

```markdown
# Agent Management API Documentation

## Overview
The Agent Management API provides endpoints for managing agent lifecycle, monitoring, and configuration.

## Authentication
All API endpoints require authentication using JWT tokens. Include the token in the Authorization header:
```
Authorization: Bearer <token>
```

## Endpoints

### Agent Management

#### List Agents
```http
GET /api/v1/agents
```
Returns a list of all registered agents.

**Response**
```json
{
    "agents": [
        {
            "id": "security-123",
            "name": "SecurityAgent",
            "type": "security",
            "status": "running",
            "health": "healthy",
            "metrics": {
                "cpu_percent": 25.5,
                "memory_percent": 30.2
            }
        }
    ]
}
```

#### Get Agent Status
```http
GET /api/v1/agents/{agent_id}/status
```
Returns the current status of an agent.

**Response**
```json
{
    "process_status": "running",
    "health_status": "healthy",
    "recovery_status": "none",
    "last_heartbeat": "2025-05-27T12:00:00Z",
    "metrics": {
        "cpu_percent": 25.5,
        "memory_percent": 30.2
    }
}
```

#### Start Agent
```http
POST /api/v1/agents/{agent_id}/start
```
Starts an agent.

**Response**
```json
{
    "status": "success",
    "message": "Agent started successfully"
}
```

#### Stop Agent
```http
POST /api/v1/agents/{agent_id}/stop
```
Stops an agent.

**Response**
```json
{
    "status": "success",
    "message": "Agent stopped successfully"
}
```

### Error Handling
All endpoints return standard HTTP status codes and error responses:

```json
{
    "error": {
        "code": "AGENT_NOT_FOUND",
        "message": "Agent not found",
        "details": {
            "agent_id": "security-123"
        }
    }
}
```

## WebSocket Events
The API provides real-time updates via WebSocket:

```javascript
const ws = new WebSocket('ws://api.opmas/agents/ws');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Agent update:', data);
};
```

### Event Types
- `agent.status`: Agent status updates
- `agent.metrics`: Agent metric updates
- `agent.error`: Agent error events
```

### 9.2 Configuration Guide
Location: `docs/configuration/agent_configuration.md`

```markdown
# Agent Configuration Guide

## Overview
This guide explains how to configure agents in the OPMAS system.

## Configuration Sources
Agent configuration can be set through multiple sources:

1. Environment Variables
2. Configuration Files
3. Database Settings
4. Runtime Updates

## Environment Variables

### Required Variables
```bash
AGENT_ID=security-123
MANAGEMENT_API_URL=http://localhost:8000
NATS_URL=nats://localhost:4222
```

### Optional Variables
```bash
LOG_LEVEL=INFO
METRICS_ENABLED=true
HEARTBEAT_INTERVAL=30
```

## Configuration Files

### Base Configuration
```yaml
# config/base.yaml
agent:
  name: SecurityAgent
  type: security
  version: 1.0.0
  log_level: INFO
  metrics_enabled: true
  heartbeat_interval: 30
  resource_limits:
    cpu_percent: 50
    memory_percent: 30
```

### Environment-specific Configuration
```yaml
# config/production.yaml
agent:
  log_level: WARNING
  resource_limits:
    cpu_percent: 75
    memory_percent: 50
```

## Database Configuration
Configuration can be stored in the database for runtime updates:

```sql
INSERT INTO agent_configs (
    agent_id, key, value, updated_at
) VALUES (
    'security-123',
    'processing_interval',
    '1.0',
    CURRENT_TIMESTAMP
);
```

## Configuration Hierarchy
1. Runtime Updates (highest priority)
2. Environment Variables
3. Environment-specific Configuration
4. Base Configuration (lowest priority)

## Configuration Validation
All configuration values are validated against schemas:

```python
class AgentConfig(BaseModel):
    name: str
    type: str
    version: str
    log_level: str = "INFO"
    metrics_enabled: bool = True
    heartbeat_interval: int = 30
    resource_limits: Optional[Dict[str, float]] = None
```

## Configuration Updates
Configuration can be updated at runtime:

```http
PUT /api/v1/agents/{agent_id}/config
Content-Type: application/json

{
    "log_level": "DEBUG",
    "resource_limits": {
        "cpu_percent": 60
    }
}
```
```

### 9.3 Deployment Guide
Location: `docs/deployment/agent_deployment.md`

```markdown
# Agent Deployment Guide

## Overview
This guide explains how to deploy agents in the OPMAS system.

## Prerequisites
- Python 3.8+
- PostgreSQL 12+
- NATS Server 2.9+
- Docker (optional)

## Environment Setup

### 1. Database Setup
```bash
# Create database
createdb opmas

# Run migrations
alembic upgrade head
```

### 2. NATS Setup
```bash
# Start NATS server
nats-server -js
```

### 3. Management API Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start API server
uvicorn opmas_mgmt_api.main:app --host 0.0.0.0 --port 8000
```

## Agent Deployment

### 1. Package Agent
```bash
# Create agent package
python -m opmas.agents.package create security_agent

# Package structure
security_agent/
├── agent.py
├── config.py
├── requirements.txt
└── .env.discovery
```

### 2. Deploy Agent
```bash
# Copy agent package
cp -r security_agent backend/src/opmas/agents/

# Register agent
curl -X POST http://localhost:8000/api/v1/agents/discover
```

### 3. Start Agent
```bash
# Start agent
curl -X POST http://localhost:8000/api/v1/agents/security-123/start
```

## Docker Deployment

### 1. Build Images
```bash
# Build management API
docker build -t opmas/mgmt-api -f docker/mgmt-api.Dockerfile .

# Build agent
docker build -t opmas/security-agent -f docker/security-agent.Dockerfile .
```

### 2. Run Containers
```bash
# Start services
docker-compose up -d
```

## Monitoring Setup

### 1. Prometheus Configuration
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'opmas'
    static_configs:
      - targets: ['localhost:8000']
```

### 2. Grafana Dashboard
Import the OPMAS dashboard from `grafana/dashboards/opmas.json`

## Backup and Restore

### 1. Database Backup
```bash
# Backup database
pg_dump opmas > opmas_backup.sql
```

### 2. Configuration Backup
```bash
# Backup configuration
tar -czf config_backup.tar.gz config/
```

### 3. Restore
```bash
# Restore database
psql opmas < opmas_backup.sql

# Restore configuration
tar -xzf config_backup.tar.gz
```
```

### 9.4 Troubleshooting Guide
Location: `docs/troubleshooting/agent_troubleshooting.md`

```markdown
# Agent Troubleshooting Guide

## Common Issues

### 1. Agent Not Starting

#### Symptoms
- Agent process fails to start
- Error in agent logs
- Agent status remains "starting"

#### Diagnosis
1. Check agent logs:
```bash
tail -f logs/agent_security-123.log
```

2. Check system resources:
```bash
top -p $(pgrep -f "security_agent")
```

3. Check NATS connection:
```bash
nats-server -js -DV
```

#### Resolution
1. Verify environment variables
2. Check resource limits
3. Ensure NATS server is running
4. Check agent configuration

### 2. Agent Crashes

#### Symptoms
- Agent process terminates unexpectedly
- Error in agent logs
- Agent status changes to "failed"

#### Diagnosis
1. Check error logs:
```bash
grep ERROR logs/agent_security-123.log
```

2. Check system logs:
```bash
journalctl -u opmas-agent@security-123
```

3. Check resource usage:
```bash
ps aux | grep security_agent
```

#### Resolution
1. Review error logs
2. Check resource limits
3. Verify dependencies
4. Check for memory leaks

### 3. High Resource Usage

#### Symptoms
- High CPU usage
- High memory usage
- Slow response times

#### Diagnosis
1. Check resource metrics:
```bash
curl http://localhost:8000/api/v1/agents/security-123/metrics
```

2. Check process stats:
```bash
ps -o pid,ppid,cmd,%cpu,%mem --sort=-%cpu | grep security_agent
```

#### Resolution
1. Adjust resource limits
2. Optimize agent code
3. Scale horizontally
4. Check for resource leaks

### 4. Communication Issues

#### Symptoms
- Failed heartbeats
- Lost messages
- Connection errors

#### Diagnosis
1. Check NATS connection:
```bash
nats-server -js -DV
```

2. Check network connectivity:
```bash
netstat -an | grep 4222
```

#### Resolution
1. Verify NATS configuration
2. Check network connectivity
3. Adjust timeouts
4. Implement retry logic

## Recovery Procedures

### 1. Automatic Recovery
The system will attempt automatic recovery for:
- Process crashes
- Resource exhaustion
- Communication failures

### 2. Manual Recovery
If automatic recovery fails:

1. Stop the agent:
```bash
curl -X POST http://localhost:8000/api/v1/agents/security-123/stop
```

2. Check logs:
```bash
tail -f logs/agent_security-123.log
```

3. Restart the agent:
```bash
curl -X POST http://localhost:8000/api/v1/agents/security-123/start
```

## Monitoring and Alerts

### 1. Health Checks
Regular health checks monitor:
- Process status
- Resource usage
- Communication status
- Error rates

### 2. Alerts
Alerts are triggered for:
- Process crashes
- Resource exhaustion
- Communication failures
- Error rate thresholds

### 3. Alert Channels
Alerts are sent to:
- Email
- Slack
- PagerDuty
- Webhook endpoints

## Logging

### 1. Log Levels
- DEBUG: Detailed debugging
- INFO: General information
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical errors

### 2. Log Locations
- Agent logs: `logs/agent_{agent_id}.log`
- System logs: `logs/system.log`
- Error logs: `logs/errors.log`

### 3. Log Rotation
Logs are rotated:
- Max size: 10MB
- Backup count: 5
- Compression: enabled

## Performance Tuning

### 1. Resource Limits
Adjust resource limits in configuration:
```yaml
resource_limits:
  cpu_percent: 50
  memory_percent: 30
```

### 2. Timeouts
Adjust timeouts in configuration:
```yaml
timeouts:
  heartbeat: 30
  connection: 10
  operation: 60
```

### 3. Buffer Sizes
Adjust buffer sizes in configuration:
```yaml
buffers:
  message: 1024
  batch: 1000
  queue: 10000
```
```

## Progress Tracking

### Completed Tasks
- [ ] Database schema updates
- [ ] Agent process management
- [ ] Agent controller implementation
- [ ] Base agent updates
- [ ] Example agent updates
- [ ] Management API updates
- [ ] Status tracking implementation
- [ ] Recovery mechanism implementation
- [ ] Error handling implementation
- [ ] Logging implementation
- [ ] UI components
- [ ] Unit tests
- [ ] Integration tests
- [ ] API documentation
- [ ] Configuration guide
- [ ] Deployment guide
- [ ] Troubleshooting guide

### Next Steps
1. Implement database schema updates
2. Create agent process management
3. Implement agent controller
4. Update base agent class
5. Update example agent
6. Add management API endpoints
7. Implement status tracking
8. Implement recovery mechanism
9. Implement error handling
10. Implement logging
11. Create UI components
12. Write tests
13. Create API documentation
14. Create configuration guide
15. Create deployment guide
16. Create troubleshooting guide

### Known Issues
- None yet

### Future Improvements
1. Add resource usage graphs
2. Implement agent dependencies
3. Add configuration versioning
4. Create agent templates
5. Add deployment automation
6. Add advanced recovery strategies
7. Implement metric aggregation
8. Add alerting system
9. Create status dashboard
10. Add audit logging
11. Add log aggregation
12. Add error pattern analysis
13. Add automated error resolution
14. Add log retention policies
15. Add log search capabilities
16. Add agent performance profiling
17. Add agent dependency management
18. Add agent configuration validation
19. Add agent state persistence
20. Add agent upgrade mechanism
21. Add interactive documentation
22. Add video tutorials
23. Add example implementations
24. Add best practices guide
25. Add security guide
