#!/usr/bin/env python3

"""Contains the core logic for the ApplicationAgent.
This agent runs as a process, subscribes to NATS topics, and processes application-related logs.
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
APPLICATION_AGENT_PID_FILE = PIDS_DIR / "ApplicationAgent.pid"

def _ensure_pids_dir_exists():
    try:
        PIDS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create PID directory {PIDS_DIR}: {e}")

def _remove_application_agent_pid_file():
    """Ensures the ApplicationAgent PID file is removed on exit."""
    try:
        if APPLICATION_AGENT_PID_FILE.is_file():
            logger.info(f"Removing PID file: {APPLICATION_AGENT_PID_FILE}")
            APPLICATION_AGENT_PID_FILE.unlink()
    except Exception as e:
        logger.error(f"Error removing PID file {APPLICATION_AGENT_PID_FILE}: {e}")

class ApplicationAgent(BaseAgent):
    """Agent specializing in application-level analysis."""

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
        """Initialize state variables specific to the Application agent."""
        self.logger.debug("Initializing Application agent state...")
        
        # State for ApplicationErrors rule
        self.error_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_error_findings: Dict[str, float] = {}
        
        # State for PerformanceDegradation rule
        self.performance_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_performance_findings: Dict[str, float] = {}
        
        # State for DatabaseIssues rule
        self.database_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_database_findings: Dict[str, float] = {}
        
        # State for APIFailures rule
        self.api_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_api_findings: Dict[str, float] = {}
        
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
            if rule_name == "ApplicationErrors":
                patterns_to_compile.extend(rule_config.get('error_patterns', []))
            elif rule_name == "PerformanceDegradation":
                patterns_to_compile.extend(rule_config.get('performance_patterns', []))
            elif rule_name == "DatabaseIssues":
                patterns_to_compile.extend(rule_config.get('database_patterns', []))
            elif rule_name == "APIFailures":
                patterns_to_compile.extend(rule_config.get('api_patterns', []))
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
        """Process an application-related log event based on defined rules."""
        self.logger.debug(f"Processing event {event.event_id} from {event.hostname or event.source_ip}")
        
        # Check all rules
        await self._check_application_errors(event)
        await self._check_performance_degradation(event)
        await self._check_database_issues(event)
        await self._check_api_failures(event)
        await self._check_configuration_issues(event)

    async def _check_application_errors(self, event: ParsedLogEvent):
        """Check for application errors and exceptions."""
        rule_name = "ApplicationErrors"
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
        error_type = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    error_type = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting error type from pattern: {e}")
                    continue
        
        if error_type is None:
            return
            
        # Record the error
        current_time = time.time()
        error_key = f"{hostname}"
        error_times = self.error_timestamps[error_key]
        error_times.append((error_type, current_time))
        
        # Remove old timestamps
        while error_times and error_times[0][1] < current_time - time_window_seconds:
            error_times.popleft()
            
        # Check threshold
        if len(error_times) >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_error_findings.get(error_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_error_findings[error_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=error_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"Application errors detected on {hostname}: {len(error_times)} occurrences in {time_window_seconds}s",
                    details={
                        "error_count": len(error_times),
                        "time_window_seconds": time_window_seconds,
                        "error_types": list(set(e[0] for e in error_times)),
                        "hostname": hostname,
                        "first_occurrence_time": error_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_performance_degradation(self, event: ParsedLogEvent):
        """Check for performance degradation."""
        rule_name = "PerformanceDegradation"
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
        performance_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    performance_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting performance issue from pattern: {e}")
                    continue
        
        if performance_issue is None:
            return
            
        # Record the performance issue
        current_time = time.time()
        perf_key = f"{hostname}"
        perf_times = self.performance_timestamps[perf_key]
        perf_times.append((performance_issue, current_time))
        
        # Remove old timestamps
        while perf_times and perf_times[0][1] < current_time - time_window_seconds:
            perf_times.popleft()
            
        # Check threshold
        if len(perf_times) >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_performance_findings.get(perf_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_performance_findings[perf_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=perf_key,
                    severity=rule_config.get('severity', 'Medium'),
                    message=f"Performance degradation detected on {hostname}: {len(perf_times)} occurrences in {time_window_seconds}s",
                    details={
                        "issue_count": len(perf_times),
                        "time_window_seconds": time_window_seconds,
                        "performance_issues": list(set(p[0] for p in perf_times)),
                        "hostname": hostname,
                        "first_occurrence_time": perf_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_database_issues(self, event: ParsedLogEvent):
        """Check for database connection issues."""
        rule_name = "DatabaseIssues"
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
        db_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    db_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting database issue from pattern: {e}")
                    continue
        
        if db_issue is None:
            return
            
        # Record the database issue
        current_time = time.time()
        db_key = f"{hostname}"
        db_times = self.database_timestamps[db_key]
        db_times.append((db_issue, current_time))
        
        # Remove old timestamps
        while db_times and db_times[0][1] < current_time - time_window_seconds:
            db_times.popleft()
            
        # Check threshold
        if len(db_times) >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_database_findings.get(db_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_database_findings[db_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=db_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"Database issues detected on {hostname}: {len(db_times)} occurrences in {time_window_seconds}s",
                    details={
                        "issue_count": len(db_times),
                        "time_window_seconds": time_window_seconds,
                        "database_issues": list(set(d[0] for d in db_times)),
                        "hostname": hostname,
                        "first_occurrence_time": db_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_api_failures(self, event: ParsedLogEvent):
        """Check for API failures."""
        rule_name = "APIFailures"
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
        api_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    api_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting API issue from pattern: {e}")
                    continue
        
        if api_issue is None:
            return
            
        # Record the API failure
        current_time = time.time()
        api_key = f"{hostname}"
        api_times = self.api_timestamps[api_key]
        api_times.append((api_issue, current_time))
        
        # Remove old timestamps
        while api_times and api_times[0][1] < current_time - time_window_seconds:
            api_times.popleft()
            
        # Check threshold
        if len(api_times) >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_api_findings.get(api_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_api_findings[api_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=api_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"API failures detected on {hostname}: {len(api_times)} occurrences in {time_window_seconds}s",
                    details={
                        "failure_count": len(api_times),
                        "time_window_seconds": time_window_seconds,
                        "api_issues": list(set(a[0] for a in api_times)),
                        "hostname": hostname,
                        "first_occurrence_time": api_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_configuration_issues(self, event: ParsedLogEvent):
        """Check for application configuration problems."""
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
                    self.logger.warning(f"Error extracting configuration issue from pattern: {e}")
                    continue
        
        if config_issue is None:
            return
            
        # Record the configuration issue
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
                    message=f"Configuration issues detected on {hostname}: {config_issue}",
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
    """Main entry point for the Application agent process."""
    # Ensure PID directory exists before writing PID file
    _ensure_pids_dir_exists()

    # Check if PID file already exists
    if APPLICATION_AGENT_PID_FILE.is_file():
        print(f"ERROR: PID file {APPLICATION_AGENT_PID_FILE} already exists. Is another ApplicationAgent process running? Exiting.", flush=True)
        exit(1)

    # Write PID file
    try:
        with open(APPLICATION_AGENT_PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        print(f"ApplicationAgent started with PID {os.getpid()}. PID file: {APPLICATION_AGENT_PID_FILE}", flush=True)
    except IOError as e:
        print(f"ERROR: Failed to write PID file {APPLICATION_AGENT_PID_FILE}: {e}. Exiting.", flush=True)
        exit(1)

    # Register cleanup function to remove PID file on exit
    atexit.register(_remove_application_agent_pid_file)

    # Get configuration from environment
    agent_name = os.getenv("AGENT_NAME", "ApplicationAgent")
    subscribed_topics = ["logs.application"]
    findings_topic = "findings.application"

    agent = ApplicationAgent(
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
    logger.info(f"Starting {ApplicationAgent.AGENT_NAME} in standalone mode...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("ApplicationAgent interrupted by user. Exiting.")
    finally:
        # Ensure cleanup runs even if asyncio loop exits unexpectedly
        _remove_application_agent_pid_file() 