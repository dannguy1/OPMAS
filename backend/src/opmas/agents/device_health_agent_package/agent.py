# OPMAS Device Health Domain Agent

import asyncio
import logging
import re
import time
from collections import defaultdict
from typing import Dict

# OPMAS Imports
from opmas.agents.base_agent import BaseAgent
from opmas.data_models import AgentFinding, ParsedLogEvent

# Get logger specific to this agent module
logger = logging.getLogger(__name__.split(".")[-1])


class DeviceHealthAgent(BaseAgent):
    """Agent specializing in Device Health related log analysis (memory, storage, etc.)."""

    AGENT_NAME = "DeviceHealthAgent"
    SUBSCRIBED_TOPICS = ["logs.health"]  # Subscribe to logs classified as health
    FINDINGS_TOPIC = "findings.health"

    def __init__(self):
        super().__init__(self.AGENT_NAME, self.SUBSCRIBED_TOPICS, self.FINDINGS_TOPIC)

    def _initialize_state(self):
        """Initialize state variables specific to the Device Health agent."""
        # State for OOMKillerInvoked rule (tracking last finding time per device)
        self.recent_oom_findings: Dict[str, float] = {}
        # State for FilesystemErrors rule (tracking last finding time per device)
        self.recent_fs_error_findings: Dict[str, float] = {}

        # Compile regex patterns (though OOM might use simple string contains)
        self._compile_rule_patterns()

    def _compile_rule_patterns(self):
        """Compile regex patterns defined in the agent rules."""
        self.logger.debug("Compiling regex patterns from rules...")
        self.compiled_patterns = {}
        # OOM rule might just use string checking, but compile if patterns are provided
        oom_rule = self.agent_rules.get("OOMKillerInvoked", {})
        if isinstance(oom_rule, dict) and oom_rule.get("enabled", False):
            patterns = oom_rule.get("oom_patterns", [])  # Can be simple strings or regex
            compiled = []
            is_regex = []
            for pattern_str in patterns:
                try:
                    # Try compiling as regex, if fails, treat as plain string
                    compiled.append(re.compile(pattern_str))
                    is_regex.append(True)
                except re.error:
                    compiled.append(pattern_str)  # Store as plain string
                    is_regex.append(False)
            if compiled:
                self.compiled_patterns["OOMKillerInvoked"] = list(zip(compiled, is_regex))
                self.logger.debug(
                    f"Stored {len(compiled)} patterns/strings for rule 'OOMKillerInvoked'"
                )

        # Compile patterns for FilesystemErrors if rule exists
        # fs_rule = self.agent_rules.get("FilesystemErrors", {})
        # ... compile patterns for JFFS2/UBIFS errors ...

    async def process_log_event(self, event: ParsedLogEvent):
        """Process a health related log event based on defined rules."""
        self.logger.debug(
            f"Processing event {event.event_id} from {event.hostname or event.source_ip}"
        )

        # --- Rule: OOM Killer Invoked ---
        await self._check_oom_killer(event)

        # --- Rule: Filesystem Errors --- (Placeholder)
        # await self._check_filesystem_errors(event)

        # --- Rule: Unexpected Reboots --- (More complex state needed)
        # await self._check_unexpected_reboot(event)

        # Add calls to other rule checks here

    async def _check_oom_killer(self, event: ParsedLogEvent):
        """Check if the log message indicates the OOM killer was invoked."""
        rule_name = "OOMKillerInvoked"
        rule_config = self.agent_rules.get(rule_name)
        if not rule_config or not rule_config.get("enabled", False):
            return

        patterns_config = self.compiled_patterns.get(rule_name, [])
        if not patterns_config:
            self.logger.debug(f"No patterns/strings found for rule '{rule_name}'")
            return

        # Cooldown per device for OOM findings (don't want one per related log line)
        finding_cooldown_seconds = rule_config.get("finding_cooldown_seconds", 3600)  # E.g., 1 hour

        message_lower = event.message.lower()
        oom_detected = False
        matched_pattern = ""

        for pattern, is_regex in patterns_config:
            if is_regex:
                if pattern.search(event.message):  # Use original case for regex
                    oom_detected = True
                    matched_pattern = pattern.pattern
                    break
            elif isinstance(pattern, str):
                if pattern.lower() in message_lower:  # Use lower case for string contains
                    oom_detected = True
                    matched_pattern = pattern
                    break

        if oom_detected:
            device_key = event.hostname or event.source_ip  # Use hostname if available, else IP
            self.logger.warning(
                f"OOM Killer message detected on device {device_key}: '{event.message[:100]}...'"
            )
            current_time = time.time()

            # Check cooldown for this device
            last_finding_time = self.recent_oom_findings.get(device_key, 0)
            if current_time - last_finding_time > finding_cooldown_seconds:
                self.logger.info(f"Generating OOMKillerInvoked finding for device {device_key}")

                # --- Generate Finding ---
                finding = AgentFinding(
                    device_hostname=event.hostname,
                    device_ip=event.source_ip,
                    severity="Critical",  # OOM is generally critical
                    finding_type=rule_name,
                    description=f"Out Of Memory (OOM) killer invoked on device {device_key}.",
                    details={
                        "triggering_log_message": event.message,
                        "matched_pattern": matched_pattern,
                        "triggering_event_id": event.event_id,
                        "process_name": event.process_name,  # Often kernel
                    },
                    evidence_event_ids=[event.event_id],
                )
                await self.publish_finding(finding)

                # Update last finding time for cooldown
                self.recent_oom_findings[device_key] = current_time
            else:
                self.logger.debug(
                    f"OOM event for {device_key} occurred but within cooldown period."
                )


# --- Main execution --- (for running the agent standalone)
async def main():
    agent = DeviceHealthAgent()
    await agent.run()


if __name__ == "__main__":
    print("Ensure NATS server is running and config files exist before starting agent.")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("DeviceHealthAgent stopped by user.")
