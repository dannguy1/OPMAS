#!/usr/bin/env python3

"""Contains the core logic for the SecurityAgent.
This agent runs as a process, subscribes to NATS topics, and processes security-related logs.
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
SECURITY_AGENT_PID_FILE = PIDS_DIR / "SecurityAgent.pid"

def _ensure_pids_dir_exists():
    try:
        PIDS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create PID directory {PIDS_DIR}: {e}")

def _remove_security_agent_pid_file():
    """Ensures the SecurityAgent PID file is removed on exit."""
    try:
        if SECURITY_AGENT_PID_FILE.is_file():
            logger.info(f"Removing PID file: {SECURITY_AGENT_PID_FILE}")
            SECURITY_AGENT_PID_FILE.unlink()
    except Exception as e:
        logger.error(f"Error removing PID file {SECURITY_AGENT_PID_FILE}: {e}")

class SecurityAgent(BaseAgent):
    """Agent specializing in security analysis."""

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
        """Initialize state variables specific to the Security agent."""
        self.logger.debug("Initializing Security agent state...")
        
        # State for AuthenticationFailures rule
        self.auth_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_auth_findings: Dict[str, float] = {}
        
        # State for SuspiciousAccess rule
        self.access_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_access_findings: Dict[str, float] = {}
        
        # State for SecurityBreach rule
        self.breach_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_breach_findings: Dict[str, float] = {}
        
        # State for PolicyViolation rule
        self.policy_timestamps: Dict[str, Deque[Tuple[str, float]]] = defaultdict(lambda: deque())
        self.recent_policy_findings: Dict[str, float] = {}
        
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
            if rule_name == "AuthenticationFailures":
                patterns_to_compile.extend(rule_config.get('auth_patterns', []))
            elif rule_name == "SuspiciousAccess":
                patterns_to_compile.extend(rule_config.get('access_patterns', []))
            elif rule_name == "SecurityBreach":
                patterns_to_compile.extend(rule_config.get('breach_patterns', []))
            elif rule_name == "PolicyViolation":
                patterns_to_compile.extend(rule_config.get('policy_patterns', []))
            
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
        """Process a security-related log event based on defined rules."""
        self.logger.debug(f"Processing event {event.event_id} from {event.hostname or event.source_ip}")
        
        # Check all rules
        await self._check_authentication_failures(event)
        await self._check_suspicious_access(event)
        await self._check_security_breach(event)
        await self._check_policy_violation(event)

    async def _check_authentication_failures(self, event: ParsedLogEvent):
        """Check for authentication failures."""
        rule_name = "AuthenticationFailures"
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
        auth_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    auth_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting auth issue from pattern: {e}")
                    continue
        
        if auth_issue is None:
            return
            
        # Record the auth failure
        current_time = time.time()
        auth_key = f"{hostname}"
        auth_times = self.auth_timestamps[auth_key]
        auth_times.append((auth_issue, current_time))
        
        # Remove old timestamps
        while auth_times and auth_times[0][1] < current_time - time_window_seconds:
            auth_times.popleft()
            
        # Check threshold
        if len(auth_times) >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_auth_findings.get(auth_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_auth_findings[auth_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=auth_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"Authentication failures detected on {hostname}: {len(auth_times)} occurrences in {time_window_seconds}s",
                    details={
                        "failure_count": len(auth_times),
                        "time_window_seconds": time_window_seconds,
                        "auth_issues": list(set(a[0] for a in auth_times)),
                        "hostname": hostname,
                        "first_occurrence_time": auth_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_suspicious_access(self, event: ParsedLogEvent):
        """Check for suspicious access patterns."""
        rule_name = "SuspiciousAccess"
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
        access_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    access_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting access issue from pattern: {e}")
                    continue
        
        if access_issue is None:
            return
            
        # Record the suspicious access
        current_time = time.time()
        access_key = f"{hostname}"
        access_times = self.access_timestamps[access_key]
        access_times.append((access_issue, current_time))
        
        # Remove old timestamps
        while access_times and access_times[0][1] < current_time - time_window_seconds:
            access_times.popleft()
            
        # Check threshold
        if len(access_times) >= rule_config.get('occurrence_threshold', 3):
            # Check cooldown
            last_finding_time = self.recent_access_findings.get(access_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_access_findings[access_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=access_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"Suspicious access patterns detected on {hostname}: {len(access_times)} occurrences in {time_window_seconds}s",
                    details={
                        "access_count": len(access_times),
                        "time_window_seconds": time_window_seconds,
                        "access_issues": list(set(a[0] for a in access_times)),
                        "hostname": hostname,
                        "first_occurrence_time": access_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_security_breach(self, event: ParsedLogEvent):
        """Check for potential security breaches."""
        rule_name = "SecurityBreach"
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
        breach_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    breach_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting breach issue from pattern: {e}")
                    continue
        
        if breach_issue is None:
            return
            
        # Record the security breach
        current_time = time.time()
        breach_key = f"{hostname}"
        breach_times = self.breach_timestamps[breach_key]
        breach_times.append((breach_issue, current_time))
        
        # Remove old timestamps
        while breach_times and breach_times[0][1] < current_time - time_window_seconds:
            breach_times.popleft()
            
        # Check threshold
        if len(breach_times) >= rule_config.get('occurrence_threshold', 1):
            # Check cooldown
            last_finding_time = self.recent_breach_findings.get(breach_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_breach_findings[breach_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=breach_key,
                    severity=rule_config.get('severity', 'Critical'),
                    message=f"Potential security breach detected on {hostname}: {breach_issue}",
                    details={
                        "breach_count": len(breach_times),
                        "time_window_seconds": time_window_seconds,
                        "breach_issues": list(set(b[0] for b in breach_times)),
                        "hostname": hostname,
                        "first_occurrence_time": breach_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_policy_violation(self, event: ParsedLogEvent):
        """Check for security policy violations."""
        rule_name = "PolicyViolation"
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
        policy_issue = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    policy_issue = match.group(1)
                    break
                except (IndexError, ValueError) as e:
                    self.logger.warning(f"Error extracting policy issue from pattern: {e}")
                    continue
        
        if policy_issue is None:
            return
            
        # Record the policy violation
        current_time = time.time()
        policy_key = f"{hostname}"
        policy_times = self.policy_timestamps[policy_key]
        policy_times.append((policy_issue, current_time))
        
        # Remove old timestamps
        while policy_times and policy_times[0][1] < current_time - time_window_seconds:
            policy_times.popleft()
            
        # Check threshold
        if len(policy_times) >= rule_config.get('occurrence_threshold', 1):
            # Check cooldown
            last_finding_time = self.recent_policy_findings.get(policy_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_policy_findings[policy_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=policy_key,
                    severity=rule_config.get('severity', 'High'),
                    message=f"Security policy violation detected on {hostname}: {policy_issue}",
                    details={
                        "violation_count": len(policy_times),
                        "time_window_seconds": time_window_seconds,
                        "policy_issues": list(set(p[0] for p in policy_times)),
                        "hostname": hostname,
                        "first_occurrence_time": policy_times[0][1],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

# --- Main Execution / Entry Point ---
async def main():
    """Main entry point for the Security agent process."""
    # Ensure PID directory exists before writing PID file
    _ensure_pids_dir_exists()

    # Check if PID file already exists
    if SECURITY_AGENT_PID_FILE.is_file():
        print(f"ERROR: PID file {SECURITY_AGENT_PID_FILE} already exists. Is another SecurityAgent process running? Exiting.", flush=True)
        exit(1)

    # Write PID file
    try:
        with open(SECURITY_AGENT_PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        print(f"SecurityAgent started with PID {os.getpid()}. PID file: {SECURITY_AGENT_PID_FILE}", flush=True)
    except IOError as e:
        print(f"ERROR: Failed to write PID file {SECURITY_AGENT_PID_FILE}: {e}. Exiting.", flush=True)
        exit(1)

    # Register cleanup function to remove PID file on exit
    atexit.register(_remove_security_agent_pid_file)

    # Get configuration from environment
    agent_name = os.getenv("AGENT_NAME", "SecurityAgent")
    subscribed_topics = ["logs.security"]
    findings_topic = "findings.security"

    agent = SecurityAgent(
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
    logger.info(f"Starting {SecurityAgent.AGENT_NAME} in standalone mode...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("SecurityAgent interrupted by user. Exiting.")
    finally:
        # Ensure cleanup runs even if asyncio loop exits unexpectedly
        _remove_security_agent_pid_file() 