# src/opmas/parsing_utils.py

import re
import logging
from datetime import datetime
from typing import Dict, Optional, Union

logger = logging.getLogger(__name__)

# Regex to parse the syslog format found in the sample file
# <PRI>Timestamp Hostname Program[PID]: Message
# Example: <29>Nov 22 00:58:16 OpenWrt wpa_supplicant[1431]: wl1-sta0: RSN: Group rekeying completed...
LOG_LINE_REGEX = re.compile(
    r"<(\d+)>"                          # 1: Priority
    r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})" # 2: Timestamp (e.g., Nov 22 00:58:16)
    r"\s+(\S+)"                         # 3: Hostname
    # 4: Program name (allow almost anything except '[', ':', needs careful testing)
    # Corrected regex: Use raw string (r"") and avoid unnecessary escapes
    r"\s+([^\[:]+)"
    r"(?:\[(\d+)\])?"                   # 5: PID (optional)
    r":\s+(.*)"                         # 6: Message
)

# Simple classification rules based on program name
SUBJECT_CLASSIFICATION = {
    "wpa_supplicant": "logs.wifi",
    "hostapd": "logs.wifi",
    "dropbear": "logs.auth",
    "netifd": "logs.connectivity",
    "kernel": "logs.system",
    # Add more rules as needed
}
DEFAULT_SUBJECT = "logs.generic"

def parse_syslog_line(line: str, year: int) -> Optional[Dict[str, Union[str, int, None]]]:
    """Parses a syslog-formatted log line, returning key components."""
    match = LOG_LINE_REGEX.match(line)
    if not match:
        return None

    try:
        priority = int(match.group(1))
        timestamp_str = match.group(2)
        hostname = match.group(3)
        program = match.group(4).strip()
        pid_str = match.group(5) # Optional
        pid = int(pid_str) if pid_str else None
        message = match.group(6)

        # Attempt to parse timestamp and add the inferred/provided year
        dt_obj = datetime.strptime(f"{year} {timestamp_str}", "%Y %b %d %H:%M:%S")
        # Convert to ISO 8601 format string with timezone info (assuming local timezone)
        timestamp_iso = dt_obj.astimezone().isoformat()

        return {
            "original_ts": timestamp_iso,
            "hostname": hostname,
            "process_name": program,
            "pid": pid,
            "message": message,
            "raw": line.strip(), # Include raw line for reference if needed
            "priority": priority # Include priority if needed later
        }
    except (ValueError, IndexError) as e:
        logger.warning(f"Failed to parse syslog line: '{line.strip()}'. Error: {e}")
        return None
    except Exception as e: # Catch other potential errors during parsing
        logger.error(f"Unexpected error parsing syslog line '{line.strip()}': {e}", exc_info=True)
        return None

def classify_nats_subject(process_name: Optional[str]) -> str:
    """Determines the NATS subject based on program/process name."""
    if process_name is None:
        return DEFAULT_SUBJECT
    # Normalize process name (e.g., remove potential trailing colons seen sometimes)
    normalized_name = process_name.lower().strip(':')
    return SUBJECT_CLASSIFICATION.get(normalized_name, DEFAULT_SUBJECT)

# --- Helper functions from ingest script ---

def infer_year_from_filename(filename: str) -> Optional[int]:
    """Attempts to infer the year from filename patterns like YYYYMMDD."""
    # Look for YYYYMMDD format, ensuring it captures 4 digits for the year
    match = re.search(r"(\d{4})\d{2}\d{2}", filename)
    if match:
        try:
            year = int(match.group(1))
            # Basic sanity check for a plausible year range
            if 1970 < year < datetime.now().year + 5:
                return year
        except ValueError:
            pass # Ignore if conversion fails
    return None