#!/usr/bin/env python3

"""Contains the core logic for the SystemAgent.
This agent runs as a process, subscribes to NATS topics, and processes system-related logs.
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
SYSTEM_AGENT_PID_FILE = PIDS_DIR / "SystemAgent.pid"

def _ensure_pids_dir_exists():
    try:
        PIDS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create PID directory {PIDS_DIR}: {e}")

def _remove_system_agent_pid_file():
    """Ensures the SystemAgent PID file is removed on exit."""
    try:
        if SYSTEM_AGENT_PID_FILE.is_file():
            logger.info(f"Removing PID file: {SYSTEM_AGENT_PID_FILE}")
            SYSTEM_AGENT_PID_FILE.unlink()
    except Exception as e:
        logger.error(f"Error removing PID file {SYSTEM_AGENT_PID_FILE}: {e}")

class SystemAgent(BaseAgent):
    """Agent specializing in system analysis."""

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
        """Initialize state variables specific to the System agent."""
        self.logger.debug("Initializing System agent state...")
        
        # State for CPUIssues rule
        self.cpu_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_cpu_findings: Dict[str, float] = {}
        
        # State for MemoryIssues rule
        self.memory_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_memory_findings: Dict[str, float] = {}
        
        # State for ProcessIssues rule
        self.process_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_process_findings: Dict[str, float] = {}
        
        # State for ConfigurationIssues rule
        self.config_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_config_findings: Dict[str, float] = {}
        
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
            if rule_name == "CPUIssues":
                patterns_to_compile.extend(rule_config.get('cpu_patterns', []))
            elif rule_name == "MemoryIssues":
                patterns_to_compile.extend(rule_config.get('memory_patterns', []))
            elif rule_name == "ProcessIssues":
                patterns_to_compile.extend(rule_config.get('process_patterns', []))
            elif rule_name == "ConfigurationIssues":
                patterns_to_compile.extend(rule_config.get('config_patterns', []))
            
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
        """Process a system-related log event based on defined rules."""
        self.logger.debug(f"Processing event {event.event_id} from {event.hostname or event.source_ip}")
        
        # Check all rules
        await self._check_cpu_issues(event)
        await self._check_memory_issues(event)
        await self._check_process_issues(event)
        await self._check_configuration_issues(event)

    async def _check_cpu_issues(self, event: ParsedLogEvent):
        """Check for CPU-related issues."""
        rule_name = "CPUIssues"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config
        time_window_seconds = rule_config.get('time_window_seconds', 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 600)  # 10 minutes
        
        hostname = event.hostname
        cpu_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    cpu_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting CPU issue from pattern: {e}")
                    continue
        
        if cpu_issue is None:
            return
            
        # Record the CPU issue
        current_time = time.time()
        cpu_key = f"{hostname}"
        cpu_times = self.cpu_timestamps[cpu_key]
        cpu_times.append((cpu_issue, current_time))
        
        # Remove old timestamps
        while cpu_times and cpu_times[0][1] < current_time - time_window_seconds:
            cpu_times.popleft()
            
        # Check threshold
        if len(cpu_times) >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_cpu_findings.get(cpu_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_cpu_findings[cpu_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=cpu_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"CPU issues detected on {hostname}: {len(cpu_times)} occurrences in {time_window_seconds}s",
                    details={
                        "issue_count": len(cpu_times),
                        "time_window_seconds": time_window_seconds,
                        "cpu_issues": list(set(c[0] for c in cpu_times)),
                        "hostname": hostname,
                        "first_occurrence_time": cpu_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_memory_issues(self, event: ParsedLogEvent):
        """Check for memory-related issues."""
        rule_name = "MemoryIssues"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config
        time_window_seconds = rule_config.get('time_window_seconds', 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 600)  # 10 minutes
        
        hostname = event.hostname
        memory_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    memory_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting memory issue from pattern: {e}")
                    continue
        
        if memory_issue is None:
            return
            
        # Record the memory issue
        current_time = time.time()
        memory_key = f"{hostname}"
        memory_times = self.memory_timestamps[memory_key]
        memory_times.append((memory_issue, current_time))
        
        # Remove old timestamps
        while memory_times and memory_times[0][1] < current_time - time_window_seconds:
            memory_times.popleft()
            
        # Check threshold
        if len(memory_times) >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_memory_findings.get(memory_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_memory_findings[memory_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=memory_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"Memory issues detected on {hostname}: {len(memory_times)} occurrences in {time_window_seconds}s",
                    details={
                        "issue_count": len(memory_times),
                        "time_window_seconds": time_window_seconds,
                        "memory_issues": list(set(m[0] for m in memory_times)),
                        "hostname": hostname,
                        "first_occurrence_time": memory_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_process_issues(self, event: ParsedLogEvent):
        """Check for process-related issues."""
        rule_name = "ProcessIssues"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config
        time_window_seconds = rule_config.get('time_window_seconds', 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 600)  # 10 minutes
        
        hostname = event.hostname
        process_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    process_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting process issue from pattern: {e}")
                    continue
        
        if process_issue is None:
            return
            
        # Record the process issue
        current_time = time.time()
        process_key = f"{hostname}"
        process_times = self.process_timestamps[process_key]
        process_times.append((process_issue, current_time))
        
        # Remove old timestamps
        while process_times and process_times[0][1] < current_time - time_window_seconds:
            process_times.popleft()
            
        # Check threshold
        if len(process_times) >= rule_config.get('occurrence_threshold', 1):
            # Check cooldown
            last_finding_time = self.recent_process_findings.get(process_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_process_findings[process_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=process_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"Process issues detected on {hostname}: {process_issue}",
                    details={
                        "issue_count": len(process_times),
                        "time_window_seconds": time_window_seconds,
                        "process_issues": list(set(p[0] for p in process_times)),
                        "hostname": hostname,
                        "first_occurrence_time": process_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_configuration_issues(self, event: ParsedLogEvent):
        """Check for system configuration issues."""
        rule_name = "ConfigurationIssues"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config
        time_window_seconds = rule_config.get('time_window_seconds', 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 600)  # 10 minutes
        
        hostname = event.hostname
        config_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    config_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting config issue from pattern: {e}")
                    continue
        
        if config_issue is None:
            return
            
        # Record the config issue
        current_time = time.time()
        config_key = f"{hostname}"
        config_times = self.config_timestamps[config_key]
        config_times.append((config_issue, current_time))
        
        # Remove old timestamps
        while config_times and config_times[0][1] < current_time - time_window_seconds:
            config_times.popleft()
            
        # Check threshold
        if len(config_times) >= rule_config.get('occurrence_threshold', 1):
            # Check cooldown
            last_finding_time = self.recent_config_findings.get(config_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_config_findings[config_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=config_key,
                    severity=rule_config.get('severity', 'Medium'),
                    message=f"System configuration issues detected on {hostname}: {config_issue}",
                    details={
                        "issue_count": len(config_times),
                        "time_window_seconds": time_window_seconds,
                        "config_issues": list(set(c[0] for c in config_times)),
                        "hostname": hostname,
                        "first_occurrence_time": config_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

# --- Main Execution / Entry Point ---
async def main():
    """Main entry point for the System agent process."""
    # Ensure PID directory exists before writing PID file
    _ensure_pids_dir_exists()

    # Check if PID file already exists
    if SYSTEM_AGENT_PID_FILE.is_file():
        print(f"ERROR: PID file {SYSTEM_AGENT_PID_FILE} already exists. Is another SystemAgent process running? Exiting.", flush=True)
        exit(1)

    # Write PID file
    try:
        with open(SYSTEM_AGENT_PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        print(f"SystemAgent started with PID {os.getpid()}. PID file: {SYSTEM_AGENT_PID_FILE}", flush=True)
    except IOError as e:
        print(f"ERROR: Failed to write PID file {SYSTEM_AGENT_PID_FILE}: {e}. Exiting.", flush=True)
        exit(1)

    # Register cleanup function to remove PID file on exit
    atexit.register(_remove_system_agent_pid_file)

    # Get configuration from environment
    agent_name = os.getenv("AGENT_NAME", "SystemAgent")
    subscribed_topics = ["logs.system"]
    findings_topic = "findings.system"

    agent = SystemAgent(
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
    logger.info(f"Starting {SystemAgent.AGENT_NAME} in standalone mode...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("SystemAgent interrupted by user. Exiting.")
    finally:
        # Ensure cleanup runs even if asyncio loop exits unexpectedly
        _remove_system_agent_pid_file() 