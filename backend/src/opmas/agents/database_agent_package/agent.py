#!/usr/bin/env python3

"""Contains the core logic for the DatabaseAgent.
This agent runs as a process, subscribes to NATS topics, and processes database-related logs.
"""

import asyncio
import atexit
import logging
import os
import re
import time
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, Tuple

from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..base_agent import BaseAgent
from ..data_models import AgentFinding, ParsedLogEvent
from ..db_models import Agent as AgentModel
from ..db_models import AgentRule
from ..db_utils import get_db_session

# Get logger
logger = logging.getLogger(__name__)

# Path Definitions
AGENT_PACKAGE_DIR = Path(__file__).resolve().parent
CORE_DIR = AGENT_PACKAGE_DIR.parent.parent.parent.parent
PIDS_DIR = CORE_DIR / "pids"
DATABASE_AGENT_PID_FILE = PIDS_DIR / "DatabaseAgent.pid"


def _ensure_pids_dir_exists():
    try:
        PIDS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create PID directory {PIDS_DIR}: {e}")


def _remove_database_agent_pid_file():
    """Ensures the DatabaseAgent PID file is removed on exit."""
    try:
        if DATABASE_AGENT_PID_FILE.is_file():
            logger.info(f"Removing PID file: {DATABASE_AGENT_PID_FILE}")
            DATABASE_AGENT_PID_FILE.unlink()
    except Exception as e:
        logger.error(f"Error removing PID file {DATABASE_AGENT_PID_FILE}: {e}")


class DatabaseAgent(BaseAgent):
    """Agent specializing in database analysis."""

    def __init__(self, agent_name: str, subscribed_topics: list[str], findings_topic: str):
        """Initialize the agent instance."""
        # Load package .env before super().__init__
        package_env_path = AGENT_PACKAGE_DIR / ".env"
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
            load_rules_from_config=False,  # We load rules from DB
        )

        # Initialize state before loading rules
        self._initialize_state()

        # Load and save default rules to DB if they don't exist
        self._save_default_rules_to_db()

        # Then load all rules (including defaults) from DB
        self._load_rules_from_db()

    def _initialize_state(self):
        """Initialize state variables specific to the Database agent."""
        self.logger.debug("Initializing Database agent state...")

        # State for ConnectionIssues rule
        self.connection_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(
            lambda: deque()
        )
        self.recent_connection_findings: Dict[str, float] = {}

        # State for QueryPerformanceIssues rule
        self.query_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_query_findings: Dict[str, float] = {}

        # State for DataIntegrityIssues rule
        self.integrity_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(
            lambda: deque()
        )
        self.recent_integrity_findings: Dict[str, float] = {}

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
            if not isinstance(rule_config, dict) or not rule_config.get("enabled", False):
                continue

            patterns_to_compile = []

            # Add patterns based on rule type
            if rule_name == "ConnectionIssues":
                patterns_to_compile.extend(rule_config.get("connection_patterns", []))
            elif rule_name == "QueryPerformanceIssues":
                patterns_to_compile.extend(rule_config.get("query_patterns", []))
            elif rule_name == "DataIntegrityIssues":
                patterns_to_compile.extend(rule_config.get("integrity_patterns", []))
            elif rule_name == "ConfigurationIssues":
                patterns_to_compile.extend(rule_config.get("config_patterns", []))

            # Compile patterns
            compiled = []
            for pattern_str in patterns_to_compile:
                if isinstance(pattern_str, str):
                    try:
                        compiled.append(re.compile(pattern_str))
                    except re.error as e:
                        self.logger.error(
                            f"Failed to compile regex for rule '{rule_name}': '{pattern_str}'. Error: {e}"
                        )
                else:
                    self.logger.warning(
                        f"Invalid pattern type in rule '{rule_name}': {pattern_str}. Expected string."
                    )

            if compiled:
                self.compiled_patterns[rule_name] = compiled
                self.logger.debug(f"Compiled {len(compiled)} patterns for rule '{rule_name}'")

    async def process_log_event(self, event: ParsedLogEvent):
        """Process a database-related log event based on defined rules."""
        self.logger.debug(
            f"Processing event {event.event_id} from {event.hostname or event.source_ip}"
        )

        # Check all rules
        await self._check_connection_issues(event)
        await self._check_query_performance_issues(event)
        await self._check_data_integrity_issues(event)
        await self._check_configuration_issues(event)

    async def _check_connection_issues(self, event: ParsedLogEvent):
        """Check for database connection issues."""
        rule_name = "ConnectionIssues"
        if rule_name not in self.agent_rules:
            return

        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return

        # Parameters from rule config
        time_window_seconds = rule_config.get("time_window_seconds", 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get("finding_cooldown_seconds", 600)  # 10 minutes

        hostname = event.hostname
        connection_issue = None

        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    connection_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting connection issue from pattern: {e}")
                    continue

        if connection_issue is None:
            return

        # Record the connection issue
        current_time = time.time()
        connection_key = f"{hostname}"
        connection_times = self.connection_timestamps[connection_key]
        connection_times.append((connection_issue, current_time))

        # Remove old timestamps
        while connection_times and connection_times[0][1] < current_time - time_window_seconds:
            connection_times.popleft()

        # Check threshold
        if len(connection_times) >= rule_config.get("occurrence_threshold", 3):
            # Check cooldown
            last_finding_time = self.recent_connection_findings.get(connection_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_connection_findings[connection_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=connection_key,
                    severity=rule_config.get("severity", "High"),
                    message=f"Database connection issues detected on {hostname}: {len(connection_times)} occurrences in {time_window_seconds}s",
                    details={
                        "issue_count": len(connection_times),
                        "time_window_seconds": time_window_seconds,
                        "connection_issues": list(set(c[0] for c in connection_times)),
                        "hostname": hostname,
                        "first_occurrence_time": connection_times[0][1],
                        "last_event_message": event.message[:500],
                    },
                )
                await self.publish_finding(finding)

    async def _check_query_performance_issues(self, event: ParsedLogEvent):
        """Check for database query performance issues."""
        rule_name = "QueryPerformanceIssues"
        if rule_name not in self.agent_rules:
            return

        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return

        # Parameters from rule config
        time_window_seconds = rule_config.get("time_window_seconds", 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get("finding_cooldown_seconds", 600)  # 10 minutes

        hostname = event.hostname
        query_issue = None

        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    query_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting query issue from pattern: {e}")
                    continue

        if query_issue is None:
            return

        # Record the query issue
        current_time = time.time()
        query_key = f"{hostname}"
        query_times = self.query_timestamps[query_key]
        query_times.append((query_issue, current_time))

        # Remove old timestamps
        while query_times and query_times[0][1] < current_time - time_window_seconds:
            query_times.popleft()

        # Check threshold
        if len(query_times) >= rule_config.get("occurrence_threshold", 3):
            # Check cooldown
            last_finding_time = self.recent_query_findings.get(query_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_query_findings[query_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=query_key,
                    severity=rule_config.get("severity", "Medium"),
                    message=f"Database query performance issues detected on {hostname}: {len(query_times)} occurrences in {time_window_seconds}s",
                    details={
                        "issue_count": len(query_times),
                        "time_window_seconds": time_window_seconds,
                        "query_issues": list(set(q[0] for q in query_times)),
                        "hostname": hostname,
                        "first_occurrence_time": query_times[0][1],
                        "last_event_message": event.message[:500],
                    },
                )
                await self.publish_finding(finding)

    async def _check_data_integrity_issues(self, event: ParsedLogEvent):
        """Check for database data integrity issues."""
        rule_name = "DataIntegrityIssues"
        if rule_name not in self.agent_rules:
            return

        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return

        # Parameters from rule config
        time_window_seconds = rule_config.get("time_window_seconds", 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get("finding_cooldown_seconds", 600)  # 10 minutes

        hostname = event.hostname
        integrity_issue = None

        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    integrity_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting integrity issue from pattern: {e}")
                    continue

        if integrity_issue is None:
            return

        # Record the integrity issue
        current_time = time.time()
        integrity_key = f"{hostname}"
        integrity_times = self.integrity_timestamps[integrity_key]
        integrity_times.append((integrity_issue, current_time))

        # Remove old timestamps
        while integrity_times and integrity_times[0][1] < current_time - time_window_seconds:
            integrity_times.popleft()

        # Check threshold
        if len(integrity_times) >= rule_config.get("occurrence_threshold", 1):
            # Check cooldown
            last_finding_time = self.recent_integrity_findings.get(integrity_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_integrity_findings[integrity_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=integrity_key,
                    severity=rule_config.get("severity", "High"),
                    message=f"Database data integrity issues detected on {hostname}: {integrity_issue}",
                    details={
                        "issue_count": len(integrity_times),
                        "time_window_seconds": time_window_seconds,
                        "integrity_issues": list(set(i[0] for i in integrity_times)),
                        "hostname": hostname,
                        "first_occurrence_time": integrity_times[0][1],
                        "last_event_message": event.message[:500],
                    },
                )
                await self.publish_finding(finding)

    async def _check_configuration_issues(self, event: ParsedLogEvent):
        """Check for database configuration issues."""
        rule_name = "ConfigurationIssues"
        if rule_name not in self.agent_rules:
            return

        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return

        # Parameters from rule config
        time_window_seconds = rule_config.get("time_window_seconds", 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get("finding_cooldown_seconds", 600)  # 10 minutes

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
        if len(config_times) >= rule_config.get("occurrence_threshold", 1):
            # Check cooldown
            last_finding_time = self.recent_config_findings.get(config_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_config_findings[config_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=config_key,
                    severity=rule_config.get("severity", "Medium"),
                    message=f"Database configuration issues detected on {hostname}: {config_issue}",
                    details={
                        "issue_count": len(config_times),
                        "time_window_seconds": time_window_seconds,
                        "config_issues": list(set(c[0] for c in config_times)),
                        "hostname": hostname,
                        "first_occurrence_time": config_times[0][1],
                        "last_event_message": event.message[:500],
                    },
                )
                await self.publish_finding(finding)


# --- Main Execution / Entry Point ---
async def main():
    """Main entry point for the Database agent process."""
    # Ensure PID directory exists before writing PID file
    _ensure_pids_dir_exists()

    # Check if PID file already exists
    if DATABASE_AGENT_PID_FILE.is_file():
        print(
            f"ERROR: PID file {DATABASE_AGENT_PID_FILE} already exists. Is another DatabaseAgent process running? Exiting.",
            flush=True,
        )
        exit(1)

    # Write PID file
    try:
        with open(DATABASE_AGENT_PID_FILE, "w") as f:
            f.write(str(os.getpid()))
        print(
            f"DatabaseAgent started with PID {os.getpid()}. PID file: {DATABASE_AGENT_PID_FILE}",
            flush=True,
        )
    except IOError as e:
        print(
            f"ERROR: Failed to write PID file {DATABASE_AGENT_PID_FILE}: {e}. Exiting.", flush=True
        )
        exit(1)

    # Register cleanup function to remove PID file on exit
    atexit.register(_remove_database_agent_pid_file)

    # Get configuration from environment
    agent_name = os.getenv("AGENT_NAME", "DatabaseAgent")
    subscribed_topics = ["logs.database"]
    findings_topic = "findings.database"

    agent = DatabaseAgent(
        agent_name=agent_name, subscribed_topics=subscribed_topics, findings_topic=findings_topic
    )
    await agent.run()


if __name__ == "__main__":
    # Setup basic logging for standalone execution
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger.info(f"Starting {DatabaseAgent.AGENT_NAME} in standalone mode...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("DatabaseAgent interrupted by user. Exiting.")
    finally:
        # Ensure cleanup runs even if asyncio loop exits unexpectedly
        _remove_database_agent_pid_file()
