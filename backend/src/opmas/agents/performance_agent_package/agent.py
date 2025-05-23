#!/usr/bin/env python3

"""Contains the core logic for the PerformanceAgent.
This agent runs as a process, subscribes to NATS topics, and processes performance-related logs.
"""

import asyncio
import logging
import re
import time
from collections import defaultdict, deque
from typing import Dict, Deque, Tuple, Any
import os
from pathlib import Path
import atexit
from dotenv import load_dotenv
from datetime import datetime

from ..db_utils import get_db_session
from ..db_models import Agent as AgentModel, AgentRule
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..base_agent import BaseAgent
from ..data_models import ParsedLogEvent, AgentFinding

# Get logger
logger = logging.getLogger(__name__)

# Path Definitions
AGENT_PACKAGE_DIR = Path(__file__).resolve().parent
CORE_DIR = AGENT_PACKAGE_DIR.parent.parent.parent.parent
PIDS_DIR = CORE_DIR / 'pids'
PERFORMANCE_AGENT_PID_FILE = PIDS_DIR / "PerformanceAgent.pid"

def _ensure_pids_dir_exists():
    try:
        PIDS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create PID directory {PIDS_DIR}: {e}")

def _remove_performance_agent_pid_file():
    """Ensures the PerformanceAgent PID file is removed on exit."""
    try:
        if PERFORMANCE_AGENT_PID_FILE.is_file():
            logger.info(f"Removing PID file: {PERFORMANCE_AGENT_PID_FILE}")
            PERFORMANCE_AGENT_PID_FILE.unlink()
    except Exception as e:
        logger.error(f"Error removing PID file {PERFORMANCE_AGENT_PID_FILE}: {e}")

class PerformanceAgent(BaseAgent):
    """Agent specializing in performance analysis."""

    def __init__(self, agent_name: str, subscribed_topics: list[str], findings_topic: str):
        """Initialize the agent instance."""
        # Load package .env before super().__init__
        package_env_path = AGENT_PACKAGE_DIR / '.env'
        if package_env_path.exists():
            load_dotenv(package_env_path)
            logger.info(f"Loaded environment from package: {package_env_path}")
        else:
            logger.warning(f"No .env file found at {package_env_path}")

        # Initialize base agent
        super().__init__(
            agent_name=agent_name,
            subscribed_topics=subscribed_topics,
            findings_topic=findings_topic,
            load_rules_from_config=False  # We load rules from DB
        )
        
        # Initialize state before loading rules
        self._initialize_state()
        
        # Load and save default rules to DB if they don't exist
        self._save_default_rules_to_db()
        
        # Then load all rules (including defaults) from DB
        self._load_rules_from_db()

    def _initialize_state(self):
        """Initialize state variables specific to the Performance agent."""
        self.logger.debug("Initializing Performance agent state...")
        
        # State for CPUUsage rule
        self.cpu_usage_timestamps: Dict[str, Deque[Tuple[float, float]]] = defaultdict(lambda: deque())
        self.recent_cpu_findings: Dict[str, float] = {}
        
        # State for MemoryPressure rule
        self.memory_pressure_timestamps: Dict[str, Deque[Tuple[float, float]]] = defaultdict(lambda: deque())
        self.recent_memory_findings: Dict[str, float] = {}
        
        # State for DiskIO rule
        self.disk_io_timestamps: Dict[str, Deque[Tuple[str, float, float]]] = defaultdict(lambda: deque())
        self.recent_disk_findings: Dict[str, float] = {}
        
        # State for ProcessResources rule
        self.process_resource_timestamps: Dict[str, Deque[Tuple[str, float, float]]] = defaultdict(lambda: deque())
        self.recent_process_findings: Dict[str, float] = {}
        
        # State for SystemLoad rule
        self.system_load_timestamps: Dict[str, Deque[Tuple[float, float]]] = defaultdict(lambda: deque())
        self.recent_load_findings: Dict[str, float] = {}
        
        self._compile_rule_patterns()

    def _compile_rule_patterns(self):
        """Compile regex patterns defined in the agent rules."""
        self.logger.debug("Compiling regex patterns from rules...")
        self.compiled_patterns: Dict[str, list[re.Pattern]] = {}
        
        # Compile patterns for each rule
        for rule_name, rule_config in self.agent_rules.items():
            if not isinstance(rule_config, dict) or not rule_config.get('enabled', False):
                continue
                
            patterns_to_compile = []
            
            # Add patterns based on rule type
            if rule_name == "CPUUsage":
                patterns_to_compile.extend(rule_config.get('cpu_patterns', []))
            elif rule_name == "MemoryPressure":
                patterns_to_compile.extend(rule_config.get('memory_patterns', []))
            elif rule_name == "DiskIO":
                patterns_to_compile.extend(rule_config.get('disk_patterns', []))
            elif rule_name == "ProcessResources":
                patterns_to_compile.extend(rule_config.get('process_patterns', []))
            elif rule_name == "SystemLoad":
                patterns_to_compile.extend(rule_config.get('load_patterns', []))
            
            # Compile patterns
            compiled = []
            for pattern_str in patterns_to_compile:
                if isinstance(pattern_str, str):
                    try:
                        compiled.append(re.compile(pattern_str))
                    except re.error as e:
                        self.logger.error(f"Failed to compile regex for rule '{rule_name}': '{pattern_str}'. Error: {e}")
                else:
                    self.logger.warning(f"Invalid pattern type in rule '{rule_name}': {pattern_str}. Expected string.")
            
            if compiled:
                self.compiled_patterns[rule_name] = compiled
                self.logger.debug(f"Compiled {len(compiled)} patterns for rule '{rule_name}'")

    async def process_log_event(self, event: ParsedLogEvent):
        """Process a performance-related log event based on defined rules."""
        self.logger.debug(f"Processing event {event.event_id} from {event.hostname or event.source_ip}")
        
        # Check all rules
        await self._check_cpu_usage(event)
        await self._check_memory_pressure(event)
        await self._check_disk_io(event)
        await self._check_process_resources(event)
        await self._check_system_load(event)

    async def _check_cpu_usage(self, event: ParsedLogEvent):
        """Check for high CPU usage."""
        rule_name = "CPUUsage"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config
        usage_threshold = rule_config.get('usage_threshold', 90.0)  # 90%
        time_window_seconds = rule_config.get('time_window_seconds', 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 600)  # 10 minutes
        
        hostname = event.hostname
        cpu_usage = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    cpu_usage = float(match.group(1))
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting CPU usage from pattern: {e}")
                    continue
        
        if cpu_usage is None:
            return
            
        # Record the CPU usage
        current_time = time.time()
        cpu_key = f"{hostname}"
        usage_times = self.cpu_usage_timestamps[cpu_key]
        usage_times.append((cpu_usage, current_time))
        
        # Remove old timestamps
        while usage_times and usage_times[0][1] < current_time - time_window_seconds:
            usage_times.popleft()
            
        # Check threshold
        high_usage_count = sum(1 for usage, _ in usage_times if usage >= usage_threshold)
        if high_usage_count >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_cpu_findings.get(cpu_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_cpu_findings[cpu_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=cpu_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"High CPU usage detected on {hostname}: {high_usage_count} occurrences above {usage_threshold}% in {time_window_seconds}s",
                    details={
                        "high_usage_count": high_usage_count,
                        "time_window_seconds": time_window_seconds,
                        "usage_threshold": usage_threshold,
                        "hostname": hostname,
                        "current_usage": cpu_usage,
                        "first_occurrence_time": usage_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_memory_pressure(self, event: ParsedLogEvent):
        """Check for memory pressure."""
        rule_name = "MemoryPressure"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config
        pressure_threshold = rule_config.get('pressure_threshold', 85.0)  # 85%
        time_window_seconds = rule_config.get('time_window_seconds', 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 600)  # 10 minutes
        
        hostname = event.hostname
        memory_usage = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    memory_usage = float(match.group(1))
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting memory usage from pattern: {e}")
                    continue
        
        if memory_usage is None:
            return
            
        # Record the memory usage
        current_time = time.time()
        memory_key = f"{hostname}"
        usage_times = self.memory_pressure_timestamps[memory_key]
        usage_times.append((memory_usage, current_time))
        
        # Remove old timestamps
        while usage_times and usage_times[0][1] < current_time - time_window_seconds:
            usage_times.popleft()
            
        # Check threshold
        high_pressure_count = sum(1 for usage, _ in usage_times if usage >= pressure_threshold)
        if high_pressure_count >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_memory_findings.get(memory_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_memory_findings[memory_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=memory_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"Memory pressure detected on {hostname}: {high_pressure_count} occurrences above {pressure_threshold}% in {time_window_seconds}s",
                    details={
                        "high_pressure_count": high_pressure_count,
                        "time_window_seconds": time_window_seconds,
                        "pressure_threshold": pressure_threshold,
                        "hostname": hostname,
                        "current_usage": memory_usage,
                        "first_occurrence_time": usage_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_disk_io(self, event: ParsedLogEvent):
        """Check for disk I/O bottlenecks."""
        rule_name = "DiskIO"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config
        iops_threshold = rule_config.get('iops_threshold', 1000)  # 1000 IOPS
        time_window_seconds = rule_config.get('time_window_seconds', 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 600)  # 10 minutes
        
        hostname = event.hostname
        disk_name = None
        iops = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    disk_name = match.group(1)
                    iops = float(match.group(2))
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting disk I/O details from pattern: {e}")
                    continue
        
        if not disk_name or iops is None:
            return
            
        # Record the disk I/O
        current_time = time.time()
        disk_key = f"{hostname}:{disk_name}"
        io_times = self.disk_io_timestamps[disk_key]
        io_times.append((disk_name, iops, current_time))
        
        # Remove old timestamps
        while io_times and io_times[0][2] < current_time - time_window_seconds:
            io_times.popleft()
            
        # Check threshold
        high_io_count = sum(1 for _, iops, _ in io_times if iops >= iops_threshold)
        if high_io_count >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_disk_findings.get(disk_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_disk_findings[disk_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=disk_key,
                    severity=rule_config.get('severity', 'Medium'),
                    message=f"Disk I/O bottleneck detected on {disk_name} ({hostname}): {high_io_count} occurrences above {iops_threshold} IOPS in {time_window_seconds}s",
                    details={
                        "high_io_count": high_io_count,
                        "time_window_seconds": time_window_seconds,
                        "iops_threshold": iops_threshold,
                        "disk_name": disk_name,
                        "hostname": hostname,
                        "current_iops": iops,
                        "first_occurrence_time": io_times[0][2],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_process_resources(self, event: ParsedLogEvent):
        """Check for process resource exhaustion."""
        rule_name = "ProcessResources"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config
        resource_threshold = rule_config.get('resource_threshold', 80.0)  # 80%
        time_window_seconds = rule_config.get('time_window_seconds', 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 600)  # 10 minutes
        
        hostname = event.hostname
        process_name = None
        resource_usage = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    process_name = match.group(1)
                    resource_usage = float(match.group(2))
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting process resource details from pattern: {e}")
                    continue
        
        if not process_name or resource_usage is None:
            return
            
        # Record the process resource usage
        current_time = time.time()
        process_key = f"{hostname}:{process_name}"
        resource_times = self.process_resource_timestamps[process_key]
        resource_times.append((process_name, resource_usage, current_time))
        
        # Remove old timestamps
        while resource_times and resource_times[0][2] < current_time - time_window_seconds:
            resource_times.popleft()
            
        # Check threshold
        high_usage_count = sum(1 for _, usage, _ in resource_times if usage >= resource_threshold)
        if high_usage_count >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_process_findings.get(process_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_process_findings[process_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=process_key,
                    severity=rule_config.get('severity', 'Medium'),
                    message=f"Process resource exhaustion detected for {process_name} on {hostname}: {high_usage_count} occurrences above {resource_threshold}% in {time_window_seconds}s",
                    details={
                        "high_usage_count": high_usage_count,
                        "time_window_seconds": time_window_seconds,
                        "resource_threshold": resource_threshold,
                        "process_name": process_name,
                        "hostname": hostname,
                        "current_usage": resource_usage,
                        "first_occurrence_time": resource_times[0][2],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_system_load(self, event: ParsedLogEvent):
        """Check for system load spikes."""
        rule_name = "SystemLoad"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config
        load_threshold = rule_config.get('load_threshold', 5.0)  # 5x CPU count
        time_window_seconds = rule_config.get('time_window_seconds', 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 600)  # 10 minutes
        
        hostname = event.hostname
        system_load = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    system_load = float(match.group(1))
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting system load from pattern: {e}")
                    continue
        
        if system_load is None:
            return
            
        # Record the system load
        current_time = time.time()
        load_key = f"{hostname}"
        load_times = self.system_load_timestamps[load_key]
        load_times.append((system_load, current_time))
        
        # Remove old timestamps
        while load_times and load_times[0][1] < current_time - time_window_seconds:
            load_times.popleft()
            
        # Check threshold
        high_load_count = sum(1 for load, _ in load_times if load >= load_threshold)
        if high_load_count >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_load_findings.get(load_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_load_findings[load_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=load_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"System load spike detected on {hostname}: {high_load_count} occurrences above {load_threshold} in {time_window_seconds}s",
                    details={
                        "high_load_count": high_load_count,
                        "time_window_seconds": time_window_seconds,
                        "load_threshold": load_threshold,
                        "hostname": hostname,
                        "current_load": system_load,
                        "first_occurrence_time": load_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

# --- Main Execution / Entry Point ---
async def main():
    """Main entry point for the Performance agent process."""
    # Ensure PID directory exists before writing PID file
    _ensure_pids_dir_exists()

    # Check if PID file already exists
    if PERFORMANCE_AGENT_PID_FILE.is_file():
        print(f"ERROR: PID file {PERFORMANCE_AGENT_PID_FILE} already exists. Is another PerformanceAgent process running? Exiting.", flush=True)
        exit(1)

    # Write PID file
    try:
        with open(PERFORMANCE_AGENT_PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        print(f"PerformanceAgent started with PID {os.getpid()}. PID file: {PERFORMANCE_AGENT_PID_FILE}", flush=True)
    except IOError as e:
        print(f"ERROR: Failed to write PID file {PERFORMANCE_AGENT_PID_FILE}: {e}. Exiting.", flush=True)
        exit(1)

    # Register cleanup function to remove PID file on exit
    atexit.register(_remove_performance_agent_pid_file)

    # Get configuration from environment
    agent_name = os.getenv("AGENT_NAME", "PerformanceAgent")
    subscribed_topics = ["logs.performance"]
    findings_topic = "findings.performance"

    agent = PerformanceAgent(
        agent_name=agent_name,
        subscribed_topics=subscribed_topics,
        findings_topic=findings_topic
    )
    await agent.run()

if __name__ == "__main__":
    # Setup basic logging for standalone execution
    log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info(f"Starting {PerformanceAgent.AGENT_NAME} in standalone mode...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("PerformanceAgent interrupted by user. Exiting.")
    finally:
        # Ensure cleanup runs even if asyncio loop exits unexpectedly
        _remove_performance_agent_pid_file() 