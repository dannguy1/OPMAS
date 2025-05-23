# OPMAS WAN Connectivity Domain Agent

import asyncio
import logging
import re
import time
from collections import defaultdict, deque
from typing import Dict, Deque, Tuple

# OPMAS Imports
from opmas.agents.base_agent import BaseAgent
from opmas.data_models import ParsedLogEvent, AgentFinding

# Get logger specific to this agent module
logger = logging.getLogger(__name__.split('.')[-1])

class WANConnectivityAgent(BaseAgent):
    """Agent specializing in WAN/Internet connectivity related log analysis."""

    AGENT_NAME = "WANConnectivityAgent"
    SUBSCRIBED_TOPICS = ["logs.connectivity"] # Subscribe to logs classified as connectivity
    FINDINGS_TOPIC = "findings.connectivity"

    def __init__(self):
        super().__init__(self.AGENT_NAME, self.SUBSCRIBED_TOPICS, self.FINDINGS_TOPIC)

    def _initialize_state(self):
        """Initialize state variables specific to the WAN Connectivity agent."""
        self.logger.debug(f"[{self.agent_name}] Entering _initialize_state...") # Log start
        # State for InterfaceFlapping rule (tracking up/down events per interface)
        self.interface_event_timestamps: Dict[Tuple[str, str], Deque[float]] = defaultdict(lambda: deque())
        self.recent_flap_findings: Dict[Tuple[str, str], float] = {}

        # Compile regex patterns from rules
        self._compile_rule_patterns()
        self.logger.debug(f"[{self.agent_name}] Exiting _initialize_state.") # Log end

    def _compile_rule_patterns(self):
        """Compile regex patterns defined in the agent rules."""
        self.logger.debug(f"[{self.agent_name}] Entering _compile_rule_patterns...") # Log start
        self.compiled_patterns = {}
        for rule_name, rule_config in self.agent_rules.items():
            if isinstance(rule_config, dict) and rule_config.get('enabled', False):
                 down_patterns_cfg = rule_config.get('down_patterns', [])
                 up_patterns_cfg = rule_config.get('up_patterns', [])
                 # Add other pattern keys if needed (e.g., 'dhcp_failure_patterns')

                 compiled_down = []
                 for pattern_str in down_patterns_cfg:
                     try:
                         compiled_down.append(re.compile(pattern_str))
                     except re.error as e:
                         self.logger.error(f"Failed to compile down_pattern for rule '{rule_name}': '{pattern_str}'. Error: {e}")

                 compiled_up = []
                 for pattern_str in up_patterns_cfg:
                     try:
                         compiled_up.append(re.compile(pattern_str))
                     except re.error as e:
                          self.logger.error(f"Failed to compile up_pattern for rule '{rule_name}': '{pattern_str}'. Error: {e}")

                 if compiled_down or compiled_up:
                     self.compiled_patterns[rule_name] = {'down': compiled_down, 'up': compiled_up}
                     self.logger.debug(f"Compiled {len(compiled_down)} down / {len(compiled_up)} up patterns for rule '{rule_name}'")

        self.logger.debug(f"[{self.agent_name}] Exiting _compile_rule_patterns.") # Log end

    async def process_log_event(self, event: ParsedLogEvent):
        """Process a connectivity related log event based on defined rules."""
        self.logger.debug(f"Processing event {event.event_id} from {event.hostname or event.source_ip}")

        # --- Rule: Frequent WAN Interface Up/Down Events (Flapping) ---
        await self._check_interface_flapping(event)

        # --- Rule: DHCP Client Failures --- (Placeholder)
        # await self._check_dhcp_client_failure(event)

        # --- Rule: PPP Connection Failures --- (Placeholder)
        # await self._check_ppp_failure(event)

        # --- Rule: DNS Resolution Failures --- (Placeholder)
        # await self._check_dns_failure(event)

        # Add calls to other rule checks here

    async def _check_interface_flapping(self, event: ParsedLogEvent):
        """Check for frequent interface up/down state changes."""
        # --- Add Debug Log At Start ---
        self.logger.debug(f"_check_interface_flapping called for event_id: {event.event_id}, message: '{event.message}'")
        # -----------------------------
        rule_name = "InterfaceFlapping"
        rule_config = self.agent_rules.get(rule_name)
        if not rule_config or not rule_config.get('enabled', False):
            return

        patterns = self.compiled_patterns.get(rule_name, {})
        down_patterns = patterns.get('down', [])
        up_patterns = patterns.get('up', [])
        if not down_patterns and not up_patterns:
             self.logger.debug(f"No compiled up/down patterns found for rule '{rule_name}'")
             return

        flap_threshold = rule_config.get('flap_threshold', 5)
        time_window_seconds = rule_config.get('time_window_seconds', 300)
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 600)

        interface_name = None
        event_type = None # 'up' or 'down'

        # Check for down patterns first
        for pattern in down_patterns:
            # --- Add Debug Log For Pattern Matching ---
            self.logger.debug(f"Checking down_pattern '{pattern.pattern}' against message: '{event.message}'")
            # -----------------------------------------
            match = pattern.search(event.message)
            if match:
                event_type = 'down'
                # Try to extract interface name (might be group 1, depends on regex)
                try:
                    # Assuming interface name might be in group 1 or needs specific extraction
                    # Adjust group index or logic based on actual patterns used
                    interface_name = match.group(1) if len(match.groups()) >= 1 else "unknown_interface"
                    # Basic validation/cleaning if needed
                    if interface_name:
                        break
                except IndexError:
                     self.logger.warning(f"Regex down_pattern '{pattern.pattern}' matched but has no capture group for interface name.")
                     interface_name = "unknown_interface" # Set a default
                     break
                except Exception as e:
                     self.logger.error(f"Error extracting interface from down_pattern '{pattern.pattern}': {e}")
                     interface_name = "unknown_interface"
                     break

        # If not down, check for up patterns
        if not event_type:
            for pattern in up_patterns:
                # --- Add Debug Log For Pattern Matching ---
                self.logger.debug(f"Checking up_pattern '{pattern.pattern}' against message: '{event.message}'")
                # -----------------------------------------
                match = pattern.search(event.message)
                if match:
                    event_type = 'up'
                    try:
                        interface_name = match.group(1) if len(match.groups()) >= 1 else "unknown_interface"
                        if interface_name:
                            break
                    except IndexError:
                        self.logger.warning(f"Regex up_pattern '{pattern.pattern}' matched but has no capture group for interface name.")
                        interface_name = "unknown_interface"
                        break
                    except Exception as e:
                        self.logger.error(f"Error extracting interface from up_pattern '{pattern.pattern}': {e}")
                        interface_name = "unknown_interface"
                        break

        if interface_name and event_type:
            device_key = event.hostname or event.source_ip
            state_key = (device_key, interface_name)
            self.logger.debug(f"Interface event '{event_type}' detected for {interface_name} on {device_key}")
            current_time = time.time()

            # Add current timestamp and remove old ones for this device/interface
            timestamps = self.interface_event_timestamps[state_key]
            timestamps.append(current_time)
            while timestamps and current_time - timestamps[0] > time_window_seconds:
                timestamps.popleft()

            event_count = len(timestamps)
            # --- Add Debug Log For Event Count ---
            self.logger.debug(f"Interface event count check for {interface_name} on {device_key}: Count={event_count}, Threshold={flap_threshold}")
            # -------------------------------------

            # Check if threshold is exceeded
            if event_count >= flap_threshold:
                # Check cooldown for this specific device/interface
                last_finding_time = self.recent_flap_findings.get(state_key, 0)
                if current_time - last_finding_time > finding_cooldown_seconds:
                    self.logger.warning(f"Interface flapping detected for {interface_name} on {device_key} ({event_count} events in {time_window_seconds}s)")

                    # --- Generate Finding --- 
                    finding = AgentFinding(
                        device_hostname=event.hostname,
                        device_ip=event.source_ip,
                        severity="Warning",
                        finding_type=rule_name,
                        description=f"Interface {interface_name} on device {device_key} is flapping (frequent up/down events).",
                        details={
                            "interface": interface_name,
                            "event_count": event_count,
                            "time_window_seconds": time_window_seconds,
                            "last_event_type": event_type,
                            "triggering_event_id": event.event_id
                        },
                        evidence_event_ids=[event.event_id]
                    )
                    # --- Add Debug Log Before Publish ---
                    self.logger.debug(f"Attempting to publish finding: {finding.finding_type} ({finding.finding_id}) to {self.findings_topic}")
                    # -------------------------------------
                    await self.publish_finding(finding)

                    # Update last finding time for cooldown
                    self.recent_flap_findings[state_key] = current_time
                else:
                    self.logger.debug(f"Interface flapping for {interface_name} on {device_key} still active but within cooldown period.")

# --- Main execution --- (for running the agent standalone)
async def main():
    agent = WANConnectivityAgent()
    await agent.run()

if __name__ == "__main__":
    print("Ensure NATS server is running and config files exist before starting agent.")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("WANConnectivityAgent stopped by user.") 