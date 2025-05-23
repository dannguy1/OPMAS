# OPMAS Log Parser Component
# Consumes raw logs, parses them, and publishes structured events to NATS.

import asyncio
import logging
import re
import datetime
from dataclasses import asdict

# OPMAS Imports
from .config import get_config
from .logging_config import setup_logging
from .data_models import ParsedLogEvent
from .mq import publish_message

logger = logging.getLogger(__name__)

# --- Regex for standard Syslog formats (Examples - Need Refinement) ---
# RFC 3164-like: <PRI>MMM DD HH:MM:SS HOSTNAME TAG[PID]: MESSAGE
# Example: <30>Apr 18 15:02:17 OpenWRT-Router1 hostapd[1234]: message
# Note: PRI is optional prefix for some messages received over network
RFC3164_RE = re.compile(
    r"(?:<(?P<pri>\d{1,3})>)?"
    r"(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<hostname>\S+)\s+"
    r"(?:(?P<process_name>\S+?)(?:\[(?P<pid>\d+)\])?):\s*"
    r"(?P<message>.*)"
)

# More modern RFC 5424-like might also appear, but often gets simplified by OpenWRT's logd
# Consider adding patterns if needed

# --- Log Source Classification ---
# Simple mapping based on process name (expand as needed)
PROCESS_TO_TYPE_MAP = {
    "hostapd": "wifi",
    "kernel": "health", # Or sometimes wifi/network depending on message
    "wpa_supplicant": "wifi",
    "dnsmasq": "dhcp", # Could also be DNS related -> connectivity?
    "firewall": "security",
    "dropbear": "security",
    "sshd": "security",
    "uhttpd": "security", # Web server access/auth
    "netifd": "connectivity",
    "pppd": "connectivity",
    "odhcp6c": "connectivity",
    "odhcpd": "dhcp",
    # 'logd', 'syslog-ng' are daemons, need content inspection maybe
}

def classify_log_source(process_name: str, message: str) -> str:
    """Classifies the log source type based on process name and message content."""
    if not process_name:
        # Try simple message checks if no process
        if "firewall" in message.lower() or "iptables" in message.lower():
            return "security"
        if "wifi" in message.lower() or "wlan" in message.lower() or "80211" in message.lower():
            return "wifi"
        return "system" # Default fallback

    source_type = PROCESS_TO_TYPE_MAP.get(process_name.lower(), "system")

    # Refine based on message content if needed (e.g., kernel messages)
    if process_name == "kernel":
        if any(keyword in message.lower() for keyword in ["oom-killer", "jffs2", "ubifs", "error", "warning"]):
             return "health"
        if any(keyword in message.lower() for keyword in ["ath10k", "mt76", "wlan", "wifi", "ieee80211"]):
             return "wifi"
        if any(keyword in message.lower() for keyword in ["iptables", "nf_conntrack", "firewall"]):
             return "security"
        # Could add network driver checks for connectivity

    return source_type

def parse_log_message(raw_message: str) -> dict:
    """Attempts to parse a raw syslog message string into structured fields."""
    parsed_data = {
        "original_ts": None,
        "hostname": None,
        "process_name": None,
        "pid": None,
        "log_level": None, # Initialize log_level to None
        "message": raw_message, # Default to the full message
        "parser_name": "default_fallback_parser_v1"
    }

    match = RFC3164_RE.match(raw_message)
    if match:
        fields = match.groupdict()
        parsed_data.update({
            "original_ts": fields.get("timestamp"),
            "hostname": fields.get("hostname"),
            "process_name": fields.get("process_name"),
            "pid": fields.get("pid"),
            "message": fields.get("message", raw_message).strip(),
            "parser_name": "rfc3164_parser_v1"
            # TODO: Extract log level from PRI if available
        })
        # Attempt basic level extraction from message content if PRI missing/unused
        if not parsed_data["log_level"]:
             msg_lower = parsed_data["message"].lower()
             if msg_lower.startswith(("error", "err:", "fail", "critical")):
                  parsed_data["log_level"] = "ERROR"
             elif msg_lower.startswith(("warning", "warn:")):
                  parsed_data["log_level"] = "WARNING"
             elif msg_lower.startswith(("info", "notice")):
                   parsed_data["log_level"] = "INFO"
             # Add more level checks if needed

    # TODO: Add other regex patterns for different formats if necessary

    return parsed_data

async def process_raw_log(log_data: dict):
    """Parses a raw log, classifies it, and prepares it for NATS."""
    raw_message = log_data.get('raw_message')
    source_ip = log_data.get('client_ip') # Get IP from the log_data dict
    source_identifier = log_data.get('source_identifier', source_ip) # Use identifier or fall back to IP

    if not raw_message:
        logger.warning("Received log data without 'raw_message'. Skipping.")
        return None, None # No topic, no payload

    # Parse the raw message
    parsed_fields = parse_log_message(raw_message)

    # Add source information
    parsed_fields['source_ip'] = source_ip
    # Create the structured event object
    try:
        event = ParsedLogEvent(
            arrival_ts_utc=log_data.get("arrival_ts_utc"),
            source_ip=source_ip,
            original_ts=parsed_fields.get("original_ts"),
            hostname=parsed_fields.get("hostname"),
            process_name=parsed_fields.get("process_name"),
            pid=parsed_fields.get("pid"),
            log_level=parsed_fields.get("log_level"),
            message=parsed_fields.get("message"),
            parser_name=parsed_fields.get("parser_name"),
            **parsed_fields
        )
    except Exception as e:
        logger.error(f"Failed to create ParsedLogEvent: {e}", exc_info=True)
        logger.debug(f"Failed event data: {parsed_fields}")
        return None, None

    # Classify the event to determine the NATS topic
    event.log_source_type = classify_log_source(event.process_name, event.message)
    if not event.log_source_type:
        logger.debug(f"Log event from {event.hostname or event.source_ip} could not be classified. Discarding. Message: {event.message[:100]}")
        return None, None # Discard unclassified logs

    nats_topic = f"logs.{event.log_source_type}"
    # Ensure timestamp is ISO format string for JSON serialization
    event_dict = asdict(event)
    event_dict['timestamp_utc'] = event.timestamp_utc.isoformat()

    return nats_topic, event_dict

async def start_log_parser(log_queue: asyncio.Queue):
    """Starts the log parser, consuming from the provided queue."""
    setup_logging()
    config = get_config()
    logger.info("Starting Log Parser component...")
    logger.info(f"PARSER: Consuming logs from provided queue: {log_queue} (ID: {id(log_queue)})")

    while True:
        logger.debug("PARSER: Top of main loop, before sleep/get")
        try:
            await asyncio.sleep(0)
            log_data = await log_queue.get()
            # +++ Log the full dequeued data +++
            logger.debug(f"PARSER: Dequeued log data: {log_data}")
            # ++++++++++++++++++++++++++++++++++

            nats_topic, event_dict = await process_raw_log(log_data)
            if nats_topic and event_dict:
                # 1. Publish to the raw parsed log topic
                raw_topic = "logs.parsed.raw"
                # +++ Log Before Raw Publish +++
                logger.debug(f"Attempting publish to {raw_topic} for event {event_dict['event_id']}")
                # ++++++++++++++++++++++++++++
                await publish_message(raw_topic, event_dict)
                logger.debug(f"Published to {raw_topic}: {event_dict['event_id']}")

                # 2. Publish to the specific type topic
                if event_dict['log_source_type']:
                    specific_topic = f"logs.{event_dict['log_source_type']}"
                    # +++ Log Before Specific Publish +++
                    logger.debug(f"Attempting publish to {specific_topic} for event {event_dict['event_id']}")
                    # +++++++++++++++++++++++++++++++++
                    await publish_message(specific_topic, event_dict)
                    logger.debug(f"Published to {specific_topic}: {event_dict['event_id']}")
                else:
                    logger.warning(f"Log event {event_dict['event_id']} could not be classified, only published to raw topic.")

            log_queue.task_done() # Signal task completion to the passed queue

        except asyncio.CancelledError:
            logger.info("Log Parser shutting down.")
            break
        except Exception as e:
            logger.critical(f"Critical error in Log Parser main loop: {e}", exc_info=True)
            # Avoid tight loop on unexpected errors
            await asyncio.sleep(1)

if __name__ == '__main__':
    # Setup logging and config first
    setup_logging()
    get_config() # Load config

    async def main():
        logger.info("Starting OPMAS Log Parser Service...")

        # Simulate the ingestor putting items on the queue for testing
        async def simulate_ingestor():
            await asyncio.sleep(2) # Give parser time to start
            test_logs = [
                {"raw_message": "<30>Apr 18 15:02:17 OpenWRT-Router1 hostapd[1234]: wlan0: STA aa:bb:cc:dd:ee:ff IEEE 802.11: authenticated", "source_ip": "192.168.1.1", "arrival_ts_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()},
                {"raw_message": "<13>Apr 18 15:02:18 OpenWRT-Router1 kernel: [ 123.456] device eth0 entered promiscuous mode", "source_ip": "192.168.1.1", "arrival_ts_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()},
                {"raw_message": "<86>Apr 18 15:02:19 OpenWRT-Router1 dnsmasq[5678]: DHCPACK(br-lan) 192.168.1.100 aa:bb:cc:dd:ee:ff test-client", "source_ip": "192.168.1.1", "arrival_ts_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()},
                {"raw_message": "<29>Apr 18 15:02:20 OpenWRT-Router1 dropbear[9101]: Bad password attempt for root from 192.168.1.50:12345", "source_ip": "192.168.1.1", "arrival_ts_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()},
                {"raw_message": "Invalid message format", "source_ip": "192.168.1.2", "arrival_ts_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
            ]
            for log in test_logs:
                await log_queue.put(log)
                logger.info(f"[SIMULATOR] Added log to queue: {log['raw_message'][:50]}...")
                await asyncio.sleep(0.5)
            # Add sentinel or signal completion?
            logger.info("[SIMULATOR] Finished adding test logs.")

        parser_task = asyncio.create_task(start_log_parser(log_queue))
        simulator_task = asyncio.create_task(simulate_ingestor())

        # Wait for parser or simulator (simulator finishes first in this example)
        done, pending = await asyncio.wait(
            [parser_task, simulator_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # If parser finishes unexpectedly, log it
        if parser_task in done and parser_task.exception():
             logger.error(f"Parser task finished unexpectedly: {parser_task.exception()}")

        # Allow parser to process remaining items from simulator
        logger.info("Simulator finished, waiting for parser queue to empty...")
        await log_queue.join() # Wait until all items are gotten and processed
        logger.info("Queue empty.")

        # Cleanly shut down parser
        logger.info("Cancelling parser task...")
        parser_task.cancel()
        await asyncio.gather(parser_task, return_exceptions=True) # Wait for cancellation

        logger.info("Log Parser service stopped.")

    try:
        # Need running NATS server for publish to succeed
        print("Ensure NATS server is running (e.g., via Docker) before starting parser.")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user.") 