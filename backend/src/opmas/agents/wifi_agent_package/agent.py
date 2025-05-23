# OPMAS WiFi Agent Logic File (agent.py)

"""Contains the core logic for the WiFiAgent.
This agent runs as a process, subscribes to NATS topics, and processes Wi-Fi logs.
Metadata is provided via the .env file in this package directory.
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

# --- Database Imports ---
# TODO: Verify these relative imports work when run by the backend loader.
# They might need to be absolute (e.g., from opmas.db_utils)
from ..db_utils import get_db_session
from ..db_models import Agent as AgentModel, AgentRule
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# --- OPMAS Imports ---
# TODO: Verify these relative imports.
from ..base_agent import BaseAgent
from ..data_models import ParsedLogEvent, AgentFinding

# Get logger - name might be adjusted by backend loader
logger = logging.getLogger(__name__)

# --- Path Definitions (Relative to this file if needed) ---
AGENT_PACKAGE_DIR = Path(__file__).resolve().parent
# Define other paths relative to AGENT_PACKAGE_DIR if needed internally

# --- PID File Logic (If agent runs as separate process) ---
CORE_DIR = AGENT_PACKAGE_DIR.parent.parent.parent.parent # Adjust based on deployment structure
PIDS_DIR = CORE_DIR / 'pids'
WIFI_AGENT_PID_FILE = PIDS_DIR / "WiFiAgent.pid"

def _ensure_pids_dir_exists():
    try:
        PIDS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create PID directory {PIDS_DIR}: {e}")

def _remove_wifi_agent_pid_file():
    """Ensures the WiFiAgent PID file is removed on exit."""
    try:
        if WIFI_AGENT_PID_FILE.is_file():
            logger.info(f"Removing PID file: {WIFI_AGENT_PID_FILE}")
            WIFI_AGENT_PID_FILE.unlink()
    except Exception as e:
        logger.error(f"Error removing PID file {WIFI_AGENT_PID_FILE}: {e}")
# ------------------------------------------------------------

class WiFiAgent(BaseAgent):
    """Agent specializing in Wi-Fi related log analysis.
    Instance managed by the OPMAS backend.
    """

    # AGENT_NAME is now read from .env by the discovery mechanism
    # SUBSCRIBED_TOPICS might be configured via DB or passed during init
    # FINDINGS_TOPIC might be configured via DB or passed during init

    def __init__(self, agent_name: str, subscribed_topics: list[str], findings_topic: str):
        """Initialize the agent instance.
        Agent Name, Topics are provided by the backend loader.
        """
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
        self.auth_failure_timestamps = defaultdict(lambda: deque())
        self.recent_failure_findings = {}
        
        # Load and save default rules to DB if they don't exist
        self._save_default_rules_to_db()
        
        # Then load all rules (including defaults) from DB
        self._load_rules_from_db()

    def _save_default_rules_to_db(self):
        """Save default rules from package environment to database."""
        env_rules = os.getenv('RULES')
        if not env_rules:
            self.logger.debug("No default RULES found in package environment.")
            return

        try:
            patterns = [p.strip() for p in env_rules.split(',') if p.strip()]
            if not patterns:
                return

            with get_db_session() as session:
                # Get agent ID
                agent = session.query(AgentModel).filter_by(name=self.agent_name).first()
                if not agent:
                    self.logger.error(f"Agent '{self.agent_name}' not found in database.")
                    return

                for pattern in patterns:
                    rule_name = f"default_{pattern.lower().replace(' ', '_')}"
                    
                    # Check if rule already exists
                    existing_rule = session.query(AgentRule).filter_by(
                        agent_id=agent.agent_id,
                        rule_name=rule_name
                    ).first()
                    
                    if not existing_rule:
                        # Create rule config
                        rule_config = {
                            'type': 'classification',
                            'patterns': [pattern],
                            'enabled': True,
                            'description': f"Default classification rule for pattern: {pattern}",
                            'is_default': True,
                            'created_ts': datetime.utcnow().isoformat(),
                            'modified_ts': datetime.utcnow().isoformat()
                        }
                        
                        # Create new rule
                        new_rule = AgentRule(
                            agent_id=agent.agent_id,
                            rule_name=rule_name,
                            rule_config=rule_config,
                            is_enabled=True  # Make sure the rule is enabled
                        )
                        session.add(new_rule)
                        self.logger.info(f"Added default rule '{rule_name}' to database")
                    else:
                        self.logger.debug(f"Default rule '{rule_name}' already exists in database")
                
                session.commit()
                self.logger.info("Finished saving default rules to database")
                
        except Exception as e:
            self.logger.error(f"Error saving default rules to database: {e}", exc_info=True)

    def _load_rules_from_db(self):
        """Loads agent configuration and rules from the database for this agent."""
        self.logger.info(f"Loading rules from database for agent '{self.agent_name}'...")
        try:
            with get_db_session() as session:
                agent_entry = session.query(AgentModel).filter_by(name=self.agent_name).first()
                if not agent_entry:
                    self.logger.error(f"Agent '{self.agent_name}' not found in the database.")
                    return
                if not agent_entry.is_enabled:
                    self.logger.warning(f"Agent '{self.agent_name}' is disabled. No rules loaded.")
                    return

                agent_id = agent_entry.agent_id
                self.logger.info(f"Agent '{self.agent_name}' (ID: {agent_id}) found and enabled.")
                db_rules = session.query(AgentRule).filter_by(agent_id=agent_id, is_enabled=True).all()

                loaded_count = 0
                temp_rules = {}
                for rule in db_rules:
                    if rule.rule_config and isinstance(rule.rule_config, dict):
                        rule_data = rule.rule_config.copy() # Avoid modifying original
                        rule_data['rule_name'] = rule.rule_name
                        rule_data['rule_db_id'] = rule.rule_id
                        temp_rules[rule.rule_name] = rule_data
                        loaded_count += 1
                        self.logger.debug(f"Loaded enabled rule '{rule.rule_name}' (ID: {rule.rule_id})")
                    else:
                         self.logger.warning(f"Rule '{rule.rule_name}' (ID: {rule.rule_id}) for agent {agent_id} is enabled but has invalid/missing config. Skipping.")
                
                self.agent_rules = temp_rules # Assign loaded rules
                self.logger.info(f"Successfully loaded {loaded_count} enabled rules for '{self.agent_name}'.")
                self._initialize_state()

        except SQLAlchemyError as e:
            self.logger.critical(f"Database error loading rules for '{self.agent_name}': {e}", exc_info=True)
            self.agent_rules = {}
        except Exception as e:
            self.logger.critical(f"Unexpected error loading rules from DB for '{self.agent_name}': {e}", exc_info=True)
            self.agent_rules = {}

    def _initialize_state(self):
        """Initialize state variables specific to the WiFi agent."""
        self.logger.debug("Initializing WiFi agent state...")
        # State for HighAuthFailureRate rule
        self.auth_failure_timestamps: Dict[str, Deque[float]] = defaultdict(lambda: deque())
        self.recent_failure_findings: Dict[str, float] = {}
        
        # State for DeauthFlood rule
        self.deauth_timestamps: Dict[str, Deque[float]] = defaultdict(lambda: deque())
        self.recent_deauth_findings: Dict[str, float] = {}
        
        # State for DFSRadarDetection rule
        self.dfs_event_timestamps: Dict[str, Deque[float]] = defaultdict(lambda: deque())
        self.recent_dfs_findings: Dict[str, float] = {}
        
        # State for LowSignalStrength rule
        self.signal_strength_readings: Dict[str, Deque[Tuple[float, float]]] = defaultdict(lambda: deque())
        self.recent_signal_findings: Dict[str, float] = {}
        
        # State for DriverCrash rule
        self.driver_crash_timestamps: Dict[str, Deque[float]] = defaultdict(lambda: deque())
        self.recent_crash_findings: Dict[str, float] = {}
        
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
            if rule_name == "HighAuthFailureRate":
                patterns_to_compile.extend(rule_config.get('failure_patterns', []))
            elif rule_name == "DeauthFlood":
                patterns_to_compile.extend(rule_config.get('deauth_patterns', []))
            elif rule_name == "DFSRadarDetection":
                patterns_to_compile.extend(rule_config.get('dfs_patterns', []))
            elif rule_name == "LowSignalStrength":
                patterns_to_compile.extend(rule_config.get('signal_patterns', []))
            elif rule_name == "DriverCrash":
                patterns_to_compile.extend(rule_config.get('crash_patterns', []))
            
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
        """Process a Wi-Fi related log event based on defined rules."""
        self.logger.debug(f"Processing event {event.event_id} from {event.hostname or event.source_ip}")
        
        # Check all rules
        await self._check_high_auth_failure(event)
        await self._check_deauth_flood(event)
        await self._check_dfs_radar(event)
        await self._check_low_signal(event)
        await self._check_driver_crash(event)

    async def _check_high_auth_failure(self, event: ParsedLogEvent):
        """Check for high rate of Wi-Fi authentication failures."""
        rule_name = "HighAuthFailureRate"
        if rule_name not in self.agent_rules:
            return # Rule not loaded/enabled

        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return # No patterns for this rule

        # Parameters from rule config (with defaults)
        failure_threshold = rule_config.get('failure_threshold', 10)
        time_window_seconds = rule_config.get('time_window_seconds', 60)
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 300)

        client_mac = None
        interface = event.structured_fields.get('interface') if event.structured_fields else None

        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    mac_from_match = match.group(1)
                    # Basic MAC address format validation/normalization
                    if re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", mac_from_match):
                        client_mac = mac_from_match.upper().replace('-', ':')
                        self.logger.debug(f"Rule '{rule_name}' matched failure pattern. MAC: {client_mac}")
                        break # Found MAC, process this event
                    else:
                         self.logger.warning(f"Rule '{rule_name}' matched pattern but group 1 ('{mac_from_match}') is not a valid MAC address.")
                except IndexError:
                    self.logger.warning(f"Rule '{rule_name}' matched pattern '{pattern.pattern}' but regex has no capture group for MAC address.")
                except Exception as e:
                    self.logger.error(f"Error processing match for rule '{rule_name}': {e}")
                # Continue checking other patterns if MAC extraction failed
        
        if not client_mac:
            return # No failure pattern matched or no MAC found

        # Record the failure time
        current_time = time.time()
        failure_times = self.auth_failure_timestamps[client_mac]
        failure_times.append(current_time)

        # Remove timestamps outside the time window
        while failure_times and failure_times[0] < current_time - time_window_seconds:
            failure_times.popleft()

        # Check if threshold is met
        failure_count = len(failure_times)
        if failure_count >= failure_threshold:
            self.logger.warning(f"High auth failure rate detected for MAC {client_mac} ({failure_count} failures in {time_window_seconds}s)")

            # Check cooldown period before creating a new finding
            last_finding_time = self.recent_failure_findings.get(client_mac, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_failure_findings[client_mac] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=client_mac, # Use MAC as the resource identifier
                    severity=rule_config.get('severity', 'Medium'),
                    message=f"High authentication failure rate: {failure_count} failures in {time_window_seconds}s for {client_mac}.",
                    details={
                        "failure_count": failure_count,
                        "time_window_seconds": time_window_seconds,
                        "mac_address": client_mac,
                        "interface": interface,
                        "source_hostname": event.hostname,
                        "source_ip": event.source_ip,
                        "first_failure_time_in_window": failure_times[0],
                        "last_event_message": event.message[:500] # Truncate long messages
                    }
                )
                await self.publish_finding(finding)
            else:
                 self.logger.info(f"Skipping finding for {client_mac} due to cooldown period.")
        else:
             self.logger.debug(f"Auth failure count for {client_mac} is {failure_count}, below threshold {failure_threshold}.")

    async def _check_deauth_flood(self, event: ParsedLogEvent):
        """Check for deauthentication flood attacks."""
        rule_name = "DeauthFlood"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config (with defaults)
        deauth_threshold = rule_config.get('deauth_threshold', 20)
        time_window_seconds = rule_config.get('time_window_seconds', 10)
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 300)
        
        client_mac = None
        interface = event.structured_fields.get('interface') if event.structured_fields else None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    mac_from_match = match.group(1)
                    if re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", mac_from_match):
                        client_mac = mac_from_match.upper().replace('-', ':')
                        break
                except (IndexError, Exception) as e:
                    self.logger.warning(f"Error extracting MAC from deauth pattern: {e}")
                    continue
        
        if not client_mac:
            return
            
        # Record the deauth time
        current_time = time.time()
        deauth_times = self.deauth_timestamps[client_mac]
        deauth_times.append(current_time)
        
        # Remove old timestamps
        while deauth_times and deauth_times[0] < current_time - time_window_seconds:
            deauth_times.popleft()
            
        # Check threshold
        deauth_count = len(deauth_times)
        if deauth_count >= deauth_threshold:
            # Check cooldown
            last_finding_time = self.recent_deauth_findings.get(client_mac, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_deauth_findings[client_mac] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=client_mac,
                    severity=rule_config.get('severity', 'High'),
                    message=f"Possible deauthentication flood attack: {deauth_count} deauths in {time_window_seconds}s from {client_mac}",
                    details={
                        "deauth_count": deauth_count,
                        "time_window_seconds": time_window_seconds,
                        "mac_address": client_mac,
                        "interface": interface,
                        "source_hostname": event.hostname,
                        "source_ip": event.source_ip,
                        "first_deauth_time": deauth_times[0],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_dfs_radar(self, event: ParsedLogEvent):
        """Check for DFS radar detection events."""
        rule_name = "DFSRadarDetection"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config
        event_threshold = rule_config.get('event_threshold', 3)
        time_window_seconds = rule_config.get('time_window_seconds', 3600)  # 1 hour
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 1800)  # 30 minutes
        
        interface = None
        channel = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    interface = match.group(1)
                    channel = match.group(2)
                    break
                except (IndexError, Exception) as e:
                    self.logger.warning(f"Error extracting interface/channel from DFS pattern: {e}")
                    continue
        
        if not interface or not channel:
            return
            
        # Record the DFS event
        current_time = time.time()
        event_key = f"{interface}:{channel}"
        dfs_times = self.dfs_event_timestamps[event_key]
        dfs_times.append(current_time)
        
        # Remove old timestamps
        while dfs_times and dfs_times[0] < current_time - time_window_seconds:
            dfs_times.popleft()
            
        # Check threshold
        event_count = len(dfs_times)
        if event_count >= event_threshold:
            # Check cooldown
            last_finding_time = self.recent_dfs_findings.get(event_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_dfs_findings[event_key] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=interface,
                    severity=rule_config.get('severity', 'Medium'),
                    message=f"Frequent DFS radar detection events on {interface} channel {channel}: {event_count} events in {time_window_seconds}s",
                    details={
                        "event_count": event_count,
                        "time_window_seconds": time_window_seconds,
                        "interface": interface,
                        "channel": channel,
                        "source_hostname": event.hostname,
                        "source_ip": event.source_ip,
                        "first_event_time": dfs_times[0],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)

    async def _check_low_signal(self, event: ParsedLogEvent):
        """Check for low signal strength issues."""
        rule_name = "LowSignalStrength"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config
        signal_threshold = rule_config.get('signal_threshold', -75)  # dBm
        reading_threshold = rule_config.get('reading_threshold', 5)
        time_window_seconds = rule_config.get('time_window_seconds', 300)  # 5 minutes
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 600)  # 10 minutes
        
        client_mac = None
        signal_strength = None
        interface = event.structured_fields.get('interface') if event.structured_fields else None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    mac_from_match = match.group(1)
                    signal_str = match.group(2)
                    if re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", mac_from_match):
                        client_mac = mac_from_match.upper().replace('-', ':')
                        signal_strength = float(signal_str)
                        break
                except (IndexError, ValueError, Exception) as e:
                    self.logger.warning(f"Error extracting MAC/signal from pattern: {e}")
                    continue
        
        if not client_mac or signal_strength is None:
            return
            
        # Record the signal reading
        current_time = time.time()
        readings = self.signal_strength_readings[client_mac]
        readings.append((current_time, signal_strength))
        
        # Remove old readings
        while readings and readings[0][0] < current_time - time_window_seconds:
            readings.popleft()
            
        # Check if we have enough readings
        if len(readings) >= reading_threshold:
            # Calculate average signal strength
            avg_signal = sum(r[1] for r in readings) / len(readings)
            
            if avg_signal < signal_threshold:
                # Check cooldown
                last_finding_time = self.recent_signal_findings.get(client_mac, 0)
                if current_time - last_finding_time > finding_cooldown_seconds:
                    self.recent_signal_findings[client_mac] = current_time
                    finding = AgentFinding(
                        finding_type=rule_name,
                        agent_name=self.agent_name,
                        resource_id=client_mac,
                        severity=rule_config.get('severity', 'Medium'),
                        message=f"Low signal strength for client {client_mac}: {avg_signal:.1f} dBm (threshold: {signal_threshold} dBm)",
                        details={
                            "average_signal": avg_signal,
                            "signal_threshold": signal_threshold,
                            "reading_count": len(readings),
                            "time_window_seconds": time_window_seconds,
                            "mac_address": client_mac,
                            "interface": interface,
                            "source_hostname": event.hostname,
                            "source_ip": event.source_ip,
                            "readings": [(t, s) for t, s in readings],
                            "last_event_message": event.message[:500]
                        }
                    )
                    await self.publish_finding(finding)

    async def _check_driver_crash(self, event: ParsedLogEvent):
        """Check for Wi-Fi driver crashes or errors."""
        rule_name = "DriverCrash"
        if rule_name not in self.agent_rules:
            return
            
        rule_config = self.agent_rules[rule_name]
        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
            return
            
        # Parameters from rule config
        crash_threshold = rule_config.get('crash_threshold', 2)
        time_window_seconds = rule_config.get('time_window_seconds', 3600)  # 1 hour
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 1800)  # 30 minutes
        
        interface = None
        
        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                try:
                    interface = match.group(1)
                    break
                except (IndexError, Exception) as e:
                    self.logger.warning(f"Error extracting interface from crash pattern: {e}")
                    continue
        
        if not interface:
            return
            
        # Record the crash event
        current_time = time.time()
        crash_times = self.driver_crash_timestamps[interface]
        crash_times.append(current_time)
        
        # Remove old timestamps
        while crash_times and crash_times[0] < current_time - time_window_seconds:
            crash_times.popleft()
            
        # Check threshold
        crash_count = len(crash_times)
        if crash_count >= crash_threshold:
            # Check cooldown
            last_finding_time = self.recent_crash_findings.get(interface, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.recent_crash_findings[interface] = current_time
                finding = AgentFinding(
                    finding_type=rule_name,
                    agent_name=self.agent_name,
                    resource_id=interface,
                    severity=rule_config.get('severity', 'High'),
                    message=f"Multiple Wi-Fi driver crashes detected on {interface}: {crash_count} crashes in {time_window_seconds}s",
                    details={
                        "crash_count": crash_count,
                        "time_window_seconds": time_window_seconds,
                        "interface": interface,
                        "source_hostname": event.hostname,
                        "source_ip": event.source_ip,
                        "first_crash_time": crash_times[0],
                        "last_event_message": event.message[:500]
                    }
                )
                await self.publish_finding(finding)


# --- Main Execution / Entry Point (if run as separate process) ---
async def main():
    """Main entry point for the WiFi agent process."""
    # Ensure PID directory exists before writing PID file
    _ensure_pids_dir_exists()

    # Check if PID file already exists
    if WIFI_AGENT_PID_FILE.is_file():
        print(f"ERROR: PID file {WIFI_AGENT_PID_FILE} already exists. Is another WiFiAgent process running? Exiting.", flush=True)
        exit(1)

    # Write PID file
    try:
        with open(WIFI_AGENT_PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        print(f"WiFiAgent started with PID {os.getpid()}. PID file: {WIFI_AGENT_PID_FILE}", flush=True)
    except IOError as e:
        print(f"ERROR: Failed to write PID file {WIFI_AGENT_PID_FILE}: {e}. Exiting.", flush=True)
        exit(1)

    # Register cleanup function to remove PID file on exit
    atexit.register(_remove_wifi_agent_pid_file)

    # TODO: Backend needs to provide these details, potentially from DB/config
    # These are placeholders for now
    agent_name = os.getenv("AGENT_NAME", "WiFiAgent") # Get from .env if testing locally
    subscribed_topics = ["logs.wifi"] 
    findings_topic = "findings.wifi"

    agent = WiFiAgent(
        agent_name=agent_name,
        subscribed_topics=subscribed_topics,
        findings_topic=findings_topic
    )
    await agent.run() # Connects to NATS and starts listening

if __name__ == "__main__":
    # Setup basic logging for standalone execution
    log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info(f"Starting {WiFiAgent.AGENT_NAME} in standalone mode...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("WiFiAgent interrupted by user. Exiting.")
    finally:
        # Ensure cleanup runs even if asyncio loop exits unexpectedly
        _remove_wifi_agent_pid_file() 