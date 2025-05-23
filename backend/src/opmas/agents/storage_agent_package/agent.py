#!/usr/bin/env python3

"""Contains the core logic for the StorageAgent.
This agent runs as a process, subscribes to NATS topics, and processes storage-related logs.
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
STORAGE_AGENT_PID_FILE = PIDS_DIR / "StorageAgent.pid"

def _ensure_pids_dir_exists():
    try:
        PIDS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create PID directory {PIDS_DIR}: {e}")

def _remove_storage_agent_pid_file():
    """Ensures the StorageAgent PID file is removed on exit."""
    try:
        if STORAGE_AGENT_PID_FILE.is_file():
            logger.info(f"Removing PID file: {STORAGE_AGENT_PID_FILE}")
            STORAGE_AGENT_PID_FILE.unlink()
    except Exception as e:
        logger.error(f"Error removing PID file {STORAGE_AGENT_PID_FILE}: {e}")

class StorageAgent(BaseAgent):
    """Agent specializing in storage analysis."""

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
        """Initialize state variables specific to the Storage agent."""
        self.logger.debug("Initializing Storage agent state...")
        
        # State for DiskSpaceIssues rule
        self.disk_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_disk_findings: Dict[str, float] = {}
        
        # State for IOIssues rule
        self.io_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_io_findings: Dict[str, float] = {}
        
        # State for FileSystemIssues rule
        self.fs_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_fs_findings: Dict[str, float] = {}
        
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
            if rule_name == "DiskSpaceIssues":
                patterns_to_compile.extend(rule_config.get('disk_patterns', []))
            elif rule_name == "IOIssues":
                patterns_to_compile.extend(rule_config.get('io_patterns', []))
            elif rule_name == "FileSystemIssues":
                patterns_to_compile.extend(rule_config.get('fs_patterns', []))
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
        """Process a storage-related log event based on defined rules."""
        self.logger.debug(f"Processing event {event.event_id} from {event.hostname or event.source_ip}")
        
        # Check all rules
        await self._check_disk_space_issues(event)
        await self._check_io_issues(event)
        await self._check_file_system_issues(event)
        await self._check_configuration_issues(event)

    async def _check_disk_space_issues(self, event: ParsedLogEvent):
        """Check for disk space issues."""
        rule_name = "DiskSpaceIssues"
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
        disk_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    disk_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting disk issue from pattern: {e}")
                    continue
        
        if disk_issue is None:
            return
            
        # Record the disk issue
        current_time = time.time()
        disk_key = f"{hostname}"
        disk_times = self.disk_timestamps[disk_key]
        disk_times.append((disk_issue, current_time))
        
        # Remove old timestamps
        while disk_times and disk_times[0][1] < current_time - time_window_seconds:
            disk_times.popleft()
            
        # Check threshold
        if len(disk_times) >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_disk_findings.get(disk_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_disk_findings[disk_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=disk_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"Disk space issues detected on {hostname}: {len(disk_times)} occurrences in {time_window_seconds}s",
                    details={
                        "issue_count": len(disk_times),
                        "time_window_seconds": time_window_seconds,
                        "disk_issues": list(set(d[0] for d in disk_times)),
                        "hostname": hostname,
                        "first_occurrence_time": disk_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_io_issues(self, event: ParsedLogEvent):
        """Check for I/O performance issues."""
        rule_name = "IOIssues"
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
        io_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    io_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting I/O issue from pattern: {e}")
                    continue
        
        if io_issue is None:
            return
            
        # Record the I/O issue
        current_time = time.time()
        io_key = f"{hostname}"
        io_times = self.io_timestamps[io_key]
        io_times.append((io_issue, current_time))
        
        # Remove old timestamps
        while io_times and io_times[0][1] < current_time - time_window_seconds:
            io_times.popleft()
            
        # Check threshold
        if len(io_times) >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_io_findings.get(io_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_io_findings[io_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=io_key,
                    severity=rule_config.get('severity', 'Medium'),
                    message=f"I/O performance issues detected on {hostname}: {len(io_times)} occurrences in {time_window_seconds}s",
                    details={
                        "issue_count": len(io_times),
                        "time_window_seconds": time_window_seconds,
                        "io_issues": list(set(i[0] for i in io_times)),
                        "hostname": hostname,
                        "first_occurrence_time": io_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_file_system_issues(self, event: ParsedLogEvent):
        """Check for file system issues."""
        rule_name = "FileSystemIssues"
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
        fs_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    fs_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting file system issue from pattern: {e}")
                    continue
        
        if fs_issue is None:
            return
            
        # Record the file system issue
        current_time = time.time()
        fs_key = f"{hostname}"
        fs_times = self.fs_timestamps[fs_key]
        fs_times.append((fs_issue, current_time))
        
        # Remove old timestamps
        while fs_times and fs_times[0][1] < current_time - time_window_seconds:
            fs_times.popleft()
            
        # Check threshold
        if len(fs_times) >= rule_config.get('occurrence_threshold', 1):
            # Check cooldown
            last_finding_time = self.recent_fs_findings.get(fs_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_fs_findings[fs_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=fs_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"File system issues detected on {hostname}: {fs_issue}",
                    details={
                        "issue_count": len(fs_times),
                        "time_window_seconds": time_window_seconds,
                        "fs_issues": list(set(f[0] for f in fs_times)),
                        "hostname": hostname,
                        "first_occurrence_time": fs_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_configuration_issues(self, event: ParsedLogEvent):
        """Check for storage configuration issues."""
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
                    message=f"Storage configuration issues detected on {hostname}: {config_issue}",
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
    """Main entry point for the Storage agent process."""
    # Ensure PID directory exists before writing PID file
    _ensure_pids_dir_exists()

    # Check if PID file already exists
    if STORAGE_AGENT_PID_FILE.is_file():
        print(f"ERROR: PID file {STORAGE_AGENT_PID_FILE} already exists. Is another StorageAgent process running? Exiting.", flush=True)
        exit(1)

    # Write PID file
    try:
        with open(STORAGE_AGENT_PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        print(f"StorageAgent started with PID {os.getpid()}. PID file: {STORAGE_AGENT_PID_FILE}", flush=True)
    except IOError as e:
        print(f"ERROR: Failed to write PID file {STORAGE_AGENT_PID_FILE}: {e}. Exiting.", flush=True)
        exit(1)

    # Register cleanup function to remove PID file on exit
    atexit.register(_remove_storage_agent_pid_file)

    # Get configuration from environment
    agent_name = os.getenv("AGENT_NAME", "StorageAgent")
    subscribed_topics = ["logs.storage"]
    findings_topic = "findings.storage"

    agent = StorageAgent(
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
    logger.info(f"Starting {StorageAgent.AGENT_NAME} in standalone mode...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("StorageAgent interrupted by user. Exiting.")
    finally:
        # Ensure cleanup runs even if asyncio loop exits unexpectedly
        _remove_storage_agent_pid_file() 