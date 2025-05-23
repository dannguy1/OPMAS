#!/usr/bin/env python3

"""Contains the core logic for the ConnectivityAgent.
This agent runs as a process, subscribes to NATS topics, and processes connectivity-related logs.
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
CONNECTIVITY_AGENT_PID_FILE = PIDS_DIR / "ConnectivityAgent.pid"

def _ensure_pids_dir_exists():
    try:
        PIDS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create PID directory {PIDS_DIR}: {e}")

def _remove_connectivity_agent_pid_file():
    """Ensures the ConnectivityAgent PID file is removed on exit."""
    try:
        if CONNECTIVITY_AGENT_PID_FILE.is_file():
            logger.info(f"Removing PID file: {CONNECTIVITY_AGENT_PID_FILE}")
            CONNECTIVITY_AGENT_PID_FILE.unlink()
    except Exception as e:
        logger.error(f"Error removing PID file {CONNECTIVITY_AGENT_PID_FILE}: {e}")

class ConnectivityAgent(BaseAgent):
    """Agent specializing in network connectivity analysis."""

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
        """Initialize state variables specific to the Connectivity agent."""
        self.logger.debug("Initializing Connectivity agent state...")
        
        # State for InterfaceStatus rule
        self.interface_status_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_interface_findings: Dict[str, float] = {}
        
        # State for ConnectionTimeout rule
        self.timeout_timestamps: Dict[str, Deque[float]] = defaultdict(lambda: deque())
        self.recent_timeout_findings: Dict[str, float] = {}
        
        # State for DNSResolution rule
        self.dns_failure_timestamps: Dict[str, Deque[float]] = defaultdict(lambda: deque())
        self.recent_dns_findings: Dict[str, float] = {}
        
        # State for RoutingIssues rule
        self.routing_issue_timestamps: Dict[str, Deque[float]] = defaultdict(lambda: deque())
        self.recent_routing_findings: Dict[str, float] = {}
        
        # State for ServiceAvailability rule
        self.service_status_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_service_findings: Dict[str, float] = {}
        
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
            if rule_name == "InterfaceStatus":
                patterns_to_compile.extend(rule_config.get('interface_patterns', []))
            elif rule_name == "ConnectionTimeout":
                patterns_to_compile.extend(rule_config.get('timeout_patterns', []))
            elif rule_name == "DNSResolution":
                patterns_to_compile.extend(rule_config.get('dns_patterns', []))
            elif rule_name == "RoutingIssues":
                patterns_to_compile.extend(rule_config.get('routing_patterns', []))
            elif rule_name == "ServiceAvailability":
                patterns_to_compile.extend(rule_config.get('service_patterns', []))
            
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
        """Process a connectivity-related log event based on defined rules."""
        self.logger.debug(f"Processing event {event.event_id} from {event.hostname or event.source_ip}")
        
        # Check all rules
        await self._check_interface_status(event)
        await self._check_connection_timeouts(event)
        await self._check_dns_resolution(event)
        await self._check_routing_issues(event)
        await self._check_service_availability(event)

    async def _check_interface_status(self, event: ParsedLogEvent):
        """Check for network interface status changes."""
        rule_name = "InterfaceStatus"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config
        status_change_threshold = rule_config.get('status_change_threshold', 3)
        time_window_seconds = rule_config.get('time_window_seconds', 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 600)  # 10 minutes
        
        hostname = event.hostname
        interface_name = None
        new_status = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    interface_name = match.group(1)
                    new_status = match.group(2)
                    break
                except (IndexError, Exception) as e:
                    self.logger.warning(f"Error extracting interface details from pattern: {e}")
                    continue
        
        if not interface_name or not new_status:
            return
            
        # Record the status change
        current_time = time.time()
        interface_key = f"{hostname}:{interface_name}"
        status_times = self.interface_status_timestamps[interface_key]
        status_times.append((new_status, current_time))
        
        # Remove old timestamps
        while status_times and status_times[0][1] < current_time - time_window_seconds:
            status_times.popleft()
            
        # Check threshold
        status_changes = len(status_times)
        if status_changes >= status_change_threshold:
            # Check cooldown
            last_finding_time = self.recent_interface_findings.get(interface_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_interface_findings[interface_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=interface_key,
                    severity=rule_config.get('severity', 'Medium'),
                    message=f"Multiple interface status changes detected for {interface_name} on {hostname}: {status_changes} changes in {time_window_seconds}s",
                    details={
                        "status_changes": status_changes,
                        "time_window_seconds": time_window_seconds,
                        "interface_name": interface_name,
                        "hostname": hostname,
                        "current_status": new_status,
                        "first_change_time": status_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_connection_timeouts(self, event: ParsedLogEvent):
        """Check for connection timeouts."""
        rule_name = "ConnectionTimeout"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config
        timeout_threshold = rule_config.get('timeout_threshold', 5)
        time_window_seconds = rule_config.get('time_window_seconds', 60)  # 1 minute
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 300)  # 5 minutes
        
        hostname = event.hostname
        destination = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    destination = match.group(1)
                    break
                except (IndexError, Exception) as e:
                    self.logger.warning(f"Error extracting destination from pattern: {e}")
                    continue
        
        if not destination:
            return
            
        # Record the timeout
        current_time = time.time()
        timeout_key = f"{hostname}:{destination}"
        timeout_times = self.timeout_timestamps[timeout_key]
        timeout_times.append(current_time)
        
        # Remove old timestamps
        while timeout_times and timeout_times[0] < current_time - time_window_seconds:
            timeout_times.popleft()
            
        # Check threshold
        timeout_count = len(timeout_times)
        if timeout_count >= timeout_threshold:
            # Check cooldown
            last_finding_time = self.recent_timeout_findings.get(timeout_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_timeout_findings[timeout_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=timeout_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"Multiple connection timeouts to {destination} from {hostname}: {timeout_count} timeouts in {time_window_seconds}s",
                    details={
                        "timeout_count": timeout_count,
                        "time_window_seconds": time_window_seconds,
                        "destination": destination,
                        "hostname": hostname,
                        "first_timeout_time": timeout_times[0],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_dns_resolution(self, event: ParsedLogEvent):
        """Check for DNS resolution failures."""
        rule_name = "DNSResolution"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config
        failure_threshold = rule_config.get('failure_threshold', 3)
        time_window_seconds = rule_config.get('time_window_seconds', 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 600)  # 10 minutes
        
        hostname = event.hostname
        domain = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    domain = match.group(1)
                    break
                except (IndexError, Exception) as e:
                    self.logger.warning(f"Error extracting domain from pattern: {e}")
                    continue
        
        if not domain:
            return
            
        # Record the failure
        current_time = time.time()
        dns_key = f"{hostname}:{domain}"
        failure_times = self.dns_failure_timestamps[dns_key]
        failure_times.append(current_time)
        
        # Remove old timestamps
        while failure_times and failure_times[0] < current_time - time_window_seconds:
            failure_times.popleft()
            
        # Check threshold
        failure_count = len(failure_times)
        if failure_count >= failure_threshold:
            # Check cooldown
            last_finding_time = self.recent_dns_findings.get(dns_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_dns_findings[dns_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=dns_key,
                    severity=rule_config.get('severity', 'Medium'),
                    message=f"Multiple DNS resolution failures for {domain} on {hostname}: {failure_count} failures in {time_window_seconds}s",
                    details={
                        "failure_count": failure_count,
                        "time_window_seconds": time_window_seconds,
                        "domain": domain,
                        "hostname": hostname,
                        "first_failure_time": failure_times[0],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_routing_issues(self, event: ParsedLogEvent):
        """Check for routing issues."""
        rule_name = "RoutingIssues"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config
        issue_threshold = rule_config.get('issue_threshold', 2)
        time_window_seconds = rule_config.get('time_window_seconds', 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 600)  # 10 minutes
        
        hostname = event.hostname
        route_target = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    route_target = match.group(1)
                    break
                except (IndexError, Exception) as e:
                    self.logger.warning(f"Error extracting route target from pattern: {e}")
                    continue
        
        if not route_target:
            return
            
        # Record the issue
        current_time = time.time()
        route_key = f"{hostname}:{route_target}"
        issue_times = self.routing_issue_timestamps[route_key]
        issue_times.append(current_time)
        
        # Remove old timestamps
        while issue_times and issue_times[0] < current_time - time_window_seconds:
            issue_times.popleft()
            
        # Check threshold
        issue_count = len(issue_times)
        if issue_count >= issue_threshold:
            # Check cooldown
            last_finding_time = self.recent_routing_findings.get(route_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_routing_findings[route_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=route_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"Multiple routing issues detected for {route_target} on {hostname}: {issue_count} issues in {time_window_seconds}s",
                    details={
                        "issue_count": issue_count,
                        "time_window_seconds": time_window_seconds,
                        "route_target": route_target,
                        "hostname": hostname,
                        "first_issue_time": issue_times[0],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_service_availability(self, event: ParsedLogEvent):
        """Check for network service availability issues."""
        rule_name = "ServiceAvailability"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config
        issue_threshold = rule_config.get('issue_threshold', 2)
        time_window_seconds = rule_config.get('time_window_seconds', 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 600)  # 10 minutes
        
        hostname = event.hostname
        service_name = None
        service_status = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    service_name = match.group(1)
                    service_status = match.group(2)
                    break
                except (IndexError, Exception) as e:
                    self.logger.warning(f"Error extracting service details from pattern: {e}")
                    continue
        
        if not service_name or not service_status:
            return
            
        # Record the service status
        current_time = time.time()
        service_key = f"{hostname}:{service_name}"
        status_times = self.service_status_timestamps[service_key]
        status_times.append((service_status, current_time))
        
        # Remove old timestamps
        while status_times and status_times[0][1] < current_time - time_window_seconds:
            status_times.popleft()
            
        # Check threshold
        status_changes = len(status_times)
        if status_changes >= issue_threshold:
            # Check cooldown
            last_finding_time = self.recent_service_findings.get(service_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_service_findings[service_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=service_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"Multiple service status changes detected for {service_name} on {hostname}: {status_changes} changes in {time_window_seconds}s",
                    details={
                        "status_changes": status_changes,
                        "time_window_seconds": time_window_seconds,
                        "service_name": service_name,
                        "hostname": hostname,
                        "current_status": service_status,
                        "first_change_time": status_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

# --- Main Execution / Entry Point ---
async def main():
    """Main entry point for the Connectivity agent process."""
    # Ensure PID directory exists before writing PID file
    _ensure_pids_dir_exists()

    # Check if PID file already exists
    if CONNECTIVITY_AGENT_PID_FILE.is_file():
        print(f"ERROR: PID file {CONNECTIVITY_AGENT_PID_FILE} already exists. Is another ConnectivityAgent process running? Exiting.", flush=True)
        exit(1)

    # Write PID file
    try:
        with open(CONNECTIVITY_AGENT_PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        print(f"ConnectivityAgent started with PID {os.getpid()}. PID file: {CONNECTIVITY_AGENT_PID_FILE}", flush=True)
    except IOError as e:
        print(f"ERROR: Failed to write PID file {CONNECTIVITY_AGENT_PID_FILE}: {e}. Exiting.", flush=True)
        exit(1)

    # Register cleanup function to remove PID file on exit
    atexit.register(_remove_connectivity_agent_pid_file)

    # Get configuration from environment
    agent_name = os.getenv("AGENT_NAME", "ConnectivityAgent")
    subscribed_topics = ["logs.connectivity"]
    findings_topic = "findings.connectivity"

    agent = ConnectivityAgent(
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
    logger.info(f"Starting {ConnectivityAgent.AGENT_NAME} in standalone mode...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("ConnectivityAgent interrupted by user. Exiting.")
    finally:
        # Ensure cleanup runs even if asyncio loop exits unexpectedly
        _remove_connectivity_agent_pid_file() 