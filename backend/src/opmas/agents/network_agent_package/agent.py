#!/usr/bin/env python3

"""Contains the core logic for the NetworkAgent.
This agent runs as a process, subscribes to NATS topics, and processes network-related logs.
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
NETWORK_AGENT_PID_FILE = PIDS_DIR / "NetworkAgent.pid"

def _ensure_pids_dir_exists():
    try:
        PIDS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create PID directory {PIDS_DIR}: {e}")

def _remove_network_agent_pid_file():
    """Ensures the NetworkAgent PID file is removed on exit."""
    try:
        if NETWORK_AGENT_PID_FILE.is_file():
            logger.info(f"Removing PID file: {NETWORK_AGENT_PID_FILE}")
            NETWORK_AGENT_PID_FILE.unlink()
    except Exception as e:
        logger.error(f"Error removing PID file {NETWORK_AGENT_PID_FILE}: {e}")

class NetworkAgent(BaseAgent):
    """Agent specializing in network analysis."""

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
        """Initialize state variables specific to the Network agent."""
        self.logger.debug("Initializing Network agent state...")
        
        # State for ConnectivityIssues rule
        self.connectivity_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_connectivity_findings: Dict[str, float] = {}
        
        # State for BandwidthIssues rule
        self.bandwidth_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_bandwidth_findings: Dict[str, float] = {}
        
        # State for LatencyIssues rule
        self.latency_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_latency_findings: Dict[str, float] = {}
        
        # State for NetworkSecurityIssues rule
        self.security_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_security_findings: Dict[str, float] = {}
        
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
            if rule_name == "ConnectivityIssues":
                patterns_to_compile.extend(rule_config.get('connectivity_patterns', []))
            elif rule_name == "BandwidthIssues":
                patterns_to_compile.extend(rule_config.get('bandwidth_patterns', []))
            elif rule_name == "LatencyIssues":
                patterns_to_compile.extend(rule_config.get('latency_patterns', []))
            elif rule_name == "NetworkSecurityIssues":
                patterns_to_compile.extend(rule_config.get('security_patterns', []))
            
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
        """Process a network-related log event based on defined rules."""
        self.logger.debug(f"Processing event {event.event_id} from {event.hostname or event.source_ip}")
        
        # Check all rules
        await self._check_connectivity_issues(event)
        await self._check_bandwidth_issues(event)
        await self._check_latency_issues(event)
        await self._check_network_security_issues(event)

    async def _check_connectivity_issues(self, event: ParsedLogEvent):
        """Check for network connectivity issues."""
        rule_name = "ConnectivityIssues"
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
        connectivity_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    connectivity_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting connectivity issue from pattern: {e}")
                    continue
        
        if connectivity_issue is None:
            return
            
        # Record the connectivity issue
        current_time = time.time()
        connectivity_key = f"{hostname}"
        connectivity_times = self.connectivity_timestamps[connectivity_key]
        connectivity_times.append((connectivity_issue, current_time))
        
        # Remove old timestamps
        while connectivity_times and connectivity_times[0][1] < current_time - time_window_seconds:
            connectivity_times.popleft()
            
        # Check threshold
        if len(connectivity_times) >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_connectivity_findings.get(connectivity_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_connectivity_findings[connectivity_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=connectivity_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"Network connectivity issues detected on {hostname}: {len(connectivity_times)} occurrences in {time_window_seconds}s",
                    details={
                        "issue_count": len(connectivity_times),
                        "time_window_seconds": time_window_seconds,
                        "connectivity_issues": list(set(c[0] for c in connectivity_times)),
                        "hostname": hostname,
                        "first_occurrence_time": connectivity_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_bandwidth_issues(self, event: ParsedLogEvent):
        """Check for network bandwidth issues."""
        rule_name = "BandwidthIssues"
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
        bandwidth_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    bandwidth_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting bandwidth issue from pattern: {e}")
                    continue
        
        if bandwidth_issue is None:
            return
            
        # Record the bandwidth issue
        current_time = time.time()
        bandwidth_key = f"{hostname}"
        bandwidth_times = self.bandwidth_timestamps[bandwidth_key]
        bandwidth_times.append((bandwidth_issue, current_time))
        
        # Remove old timestamps
        while bandwidth_times and bandwidth_times[0][1] < current_time - time_window_seconds:
            bandwidth_times.popleft()
            
        # Check threshold
        if len(bandwidth_times) >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_bandwidth_findings.get(bandwidth_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_bandwidth_findings[bandwidth_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=bandwidth_key,
                    severity=rule_config.get('severity', 'Medium'),
                    message=f"Network bandwidth issues detected on {hostname}: {len(bandwidth_times)} occurrences in {time_window_seconds}s",
                    details={
                        "issue_count": len(bandwidth_times),
                        "time_window_seconds": time_window_seconds,
                        "bandwidth_issues": list(set(b[0] for b in bandwidth_times)),
                        "hostname": hostname,
                        "first_occurrence_time": bandwidth_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_latency_issues(self, event: ParsedLogEvent):
        """Check for network latency issues."""
        rule_name = "LatencyIssues"
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
        latency_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    latency_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting latency issue from pattern: {e}")
                    continue
        
        if latency_issue is None:
            return
            
        # Record the latency issue
        current_time = time.time()
        latency_key = f"{hostname}"
        latency_times = self.latency_timestamps[latency_key]
        latency_times.append((latency_issue, current_time))
        
        # Remove old timestamps
        while latency_times and latency_times[0][1] < current_time - time_window_seconds:
            latency_times.popleft()
            
        # Check threshold
        if len(latency_times) >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_latency_findings.get(latency_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_latency_findings[latency_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=latency_key,
                    severity=rule_config.get('severity', 'Medium'),
                    message=f"Network latency issues detected on {hostname}: {len(latency_times)} occurrences in {time_window_seconds}s",
                    details={
                        "issue_count": len(latency_times),
                        "time_window_seconds": time_window_seconds,
                        "latency_issues": list(set(l[0] for l in latency_times)),
                        "hostname": hostname,
                        "first_occurrence_time": latency_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_network_security_issues(self, event: ParsedLogEvent):
        """Check for network security issues."""
        rule_name = "NetworkSecurityIssues"
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
        security_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    security_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting security issue from pattern: {e}")
                    continue
        
        if security_issue is None:
            return
            
        # Record the security issue
        current_time = time.time()
        security_key = f"{hostname}"
        security_times = self.security_timestamps[security_key]
        security_times.append((security_issue, current_time))
        
        # Remove old timestamps
        while security_times and security_times[0][1] < current_time - time_window_seconds:
            security_times.popleft()
            
        # Check threshold
        if len(security_times) >= rule_config.get('occurrence_threshold', 1):
            # Check cooldown
            last_finding_time = self.recent_security_findings.get(security_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_security_findings[security_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=security_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"Network security issues detected on {hostname}: {security_issue}",
                    details={
                        "issue_count": len(security_times),
                        "time_window_seconds": time_window_seconds,
                        "security_issues": list(set(s[0] for s in security_times)),
                        "hostname": hostname,
                        "first_occurrence_time": security_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

# --- Main Execution / Entry Point ---
async def main():
    """Main entry point for the Network agent process."""
    # Ensure PID directory exists before writing PID file
    _ensure_pids_dir_exists()

    # Check if PID file already exists
    if NETWORK_AGENT_PID_FILE.is_file():
        print(f"ERROR: PID file {NETWORK_AGENT_PID_FILE} already exists. Is another NetworkAgent process running? Exiting.", flush=True)
        exit(1)

    # Write PID file
    try:
        with open(NETWORK_AGENT_PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        print(f"NetworkAgent started with PID {os.getpid()}. PID file: {NETWORK_AGENT_PID_FILE}", flush=True)
    except IOError as e:
        print(f"ERROR: Failed to write PID file {NETWORK_AGENT_PID_FILE}: {e}. Exiting.", flush=True)
        exit(1)

    # Register cleanup function to remove PID file on exit
    atexit.register(_remove_network_agent_pid_file)

    # Get configuration from environment
    agent_name = os.getenv("AGENT_NAME", "NetworkAgent")
    subscribed_topics = ["logs.network"]
    findings_topic = "findings.network"

    agent = NetworkAgent(
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
    logger.info(f"Starting {NetworkAgent.AGENT_NAME} in standalone mode...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("NetworkAgent interrupted by user. Exiting.")
    finally:
        # Ensure cleanup runs even if asyncio loop exits unexpectedly
        _remove_network_agent_pid_file() 