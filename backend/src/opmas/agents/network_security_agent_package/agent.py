# OPMAS Network Security Domain Agent

import asyncio
import logging
import re
import time
from collections import defaultdict, deque
from typing import Dict, Deque

# OPMAS Imports
from opmas.agents.base_agent import BaseAgent
from opmas.data_models import ParsedLogEvent, AgentFinding

# Get logger specific to this agent module
logger = logging.getLogger(__name__.split('.')[-1])

class NetworkSecurityAgent(BaseAgent):
    """Agent specializing in Network Security related log analysis."""

    AGENT_NAME = "NetworkSecurityAgent"
    SUBSCRIBED_TOPICS = ["logs.security"] # Subscribe to logs classified as security
    FINDINGS_TOPIC = "findings.security"

    def __init__(self):
        super().__init__(self.AGENT_NAME, self.SUBSCRIBED_TOPICS, self.FINDINGS_TOPIC)

    def _initialize_state(self):
        """Initialize state variables specific to the Network Security agent."""
        # State for RepeatedSSHLoginFailure rule (tracking failures per source IP)
        self.ssh_failure_timestamps: Dict[str, Deque[float]] = defaultdict(lambda: deque())
        self.recent_ssh_failure_findings: Dict[str, float] = {}

        # Compile regex patterns from rules
        self._compile_rule_patterns()

    def _compile_rule_patterns(self):
        """Compile regex patterns defined in the agent rules."""
        self.logger.debug("Compiling regex patterns from rules...")
        self.compiled_patterns = {}
        for rule_name, rule_config in self.agent_rules.items():
            if isinstance(rule_config, dict) and rule_config.get('enabled', False):
                 patterns = []
                 if 'failure_patterns' in rule_config: # Common key used in YAML
                     patterns.extend(rule_config['failure_patterns'])
                 # Add other pattern keys if needed for other rules

                 compiled = []
                 for pattern_str in patterns:
                     try:
                         compiled.append(re.compile(pattern_str))
                     except re.error as e:
                         self.logger.error(f"Failed to compile regex for rule '{rule_name}': '{pattern_str}'. Error: {e}")
                 if compiled:
                     self.compiled_patterns[rule_name] = compiled
                     self.logger.debug(f"Compiled {len(compiled)} patterns for rule '{rule_name}'")

    async def process_log_event(self, event: ParsedLogEvent):
        """Process a security related log event based on defined rules."""
        self.logger.debug(f"Processing event {event.event_id} from {event.hostname or event.source_ip}")

        # --- Rule: Repeated SSH Login Failure (Brute-force detection) ---
        await self._check_repeated_ssh_failure(event)

        # --- Rule: Port Scan Detection --- (Placeholder)
        # await self._check_port_scan(event)

        # --- Rule: Denied Outbound Connection to Malicious IP --- (Placeholder)
        # await self._check_malicious_outbound(event)

        # Add calls to other rule checks here

    async def _check_repeated_ssh_failure(self, event: ParsedLogEvent):
        """Check for repeated failed SSH login attempts from the same source IP."""
        rule_name = "RepeatedSSHLoginFailure"
        rule_config = self.agent_rules.get(rule_name)
        if not rule_config or not rule_config.get('enabled', False):
            return

        patterns = self.compiled_patterns.get(rule_name, [])
        if not patterns:
             self.logger.debug(f"No compiled patterns found for rule '{rule_name}'")
             return

        failure_threshold = rule_config.get('failure_threshold', 5)
        time_window_seconds = rule_config.get('time_window_seconds', 120)
        finding_cooldown_seconds = rule_config.get('finding_cooldown_seconds', 600)

        source_ip = None

        for pattern in patterns:
            match = pattern.search(event.message)
            if match:
                # Try to extract source IP (assuming it's the first group)
                try:
                    source_ip = match.group(1)
                    if source_ip:
                         # Basic IP format validation (very basic)
                         if not re.fullmatch(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", source_ip):
                              self.logger.warning(f"Extracted potential IP '{source_ip}' does not look valid, skipping.")
                              source_ip = None
                         else:
                             break # Found match and extracted IP
                except IndexError:
                    self.logger.warning(f"Regex pattern '{pattern.pattern}' matched but has no capture group for source IP.")
                except Exception as e:
                     self.logger.error(f"Error extracting source IP using pattern '{pattern.pattern}': {e}")

        if source_ip:
            self.logger.debug(f"SSH failure detected from IP: {source_ip}")
            current_time = time.time()

            # Add current timestamp and remove old ones for this source IP
            timestamps = self.ssh_failure_timestamps[source_ip]
            timestamps.append(current_time)
            while timestamps and current_time - timestamps[0] > time_window_seconds:
                timestamps.popleft()

            failure_count = len(timestamps)
            self.logger.debug(f"SSH failure count for {source_ip} in window: {failure_count}")

            # Check if threshold is exceeded
            if failure_count >= failure_threshold:
                # Check cooldown for this specific source IP
                last_finding_time = self.recent_ssh_failure_findings.get(source_ip, 0)
                if current_time - last_finding_time > finding_cooldown_seconds:
                    self.logger.warning(f"Repeated SSH login failures detected from IP: {source_ip} ({failure_count} failures in {time_window_seconds}s)")

                    # --- Generate Finding --- 
                    finding = AgentFinding(
                        device_hostname=event.hostname,
                        device_ip=event.source_ip, # The IP of the OpenWRT device that logged the message
                        severity="Warning",
                        finding_type=rule_name,
                        description=f"Repeated failed SSH login attempts detected from source IP {source_ip}",
                        details={
                            "source_ip": source_ip,
                            "failure_count": failure_count,
                            "time_window_seconds": time_window_seconds,
                            "triggering_process": event.process_name,
                            "triggering_event_id": event.event_id
                        },
                        evidence_event_ids=[event.event_id]
                    )
                    await self.publish_finding(finding)

                    # Update last finding time for cooldown
                    self.recent_ssh_failure_findings[source_ip] = current_time
                else:
                    self.logger.debug(f"Repeated SSH failures from {source_ip} still active but within cooldown period.")

# --- Main execution --- (for running the agent standalone)
async def main():
    agent = NetworkSecurityAgent()
    await agent.run()

if __name__ == "__main__":
    print("Ensure NATS server is running and config files exist before starting agent.")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("NetworkSecurityAgent stopped by user.") 