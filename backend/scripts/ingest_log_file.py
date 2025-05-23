import argparse
import asyncio
import logging
import sys
import uuid
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

# --- Add OPMAS src directory to sys.path ---
# This allows importing OPMAS modules from a script in a sibling directory
try:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    src_dir = project_root / 'src'
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from opmas.config import load_config, get_config
    from opmas.data_models import ParsedLogEvent
    from opmas.mq import publish_message # Import the publish helper
    # Import the refactored parsing functions
    from opmas.parsing_utils import (\
        parse_syslog_line, \
        classify_nats_subject, \
        infer_year_from_filename\
    )
except ImportError as e:
    print(f"Error importing OPMAS modules: {e}")
    print("Ensure the script is run from within the OPMAS project structure (e.g., python scripts/ingest_log_file.py ...)")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)

import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError

# Setup basic logging for the script
logger = logging.getLogger("ingest_log_file")
# setup_logging() # Call setup_logging if you want it configured like other agents

async def main():
    parser = argparse.ArgumentParser(description="Ingest a log file into OPMAS via NATS.")
    parser.add_argument("logfile", help="Path to the log file to ingest.")
    parser.add_argument("-y", "--year", type=int, help="Manually specify the year for log timestamps (if not in filename).")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    log_file = Path(args.logfile)
    if not log_file.is_file():
        logger.error(f"Log file not found: {log_file}")
        sys.exit(1)

    # --- Determine Year (using imported function) ---
    year = args.year
    if year is None:
        year = infer_year_from_filename(log_file.name) # Uses imported util
        if year:
            logger.info(f"Inferred year {year} from filename.")
        else:
            year = datetime.now().year
            logger.info(f"Could not infer year from filename, using current year: {year}.")
    else:
        logger.info(f"Using manually specified year: {year}")

    # --- Load OPMAS Config ---
    try:
        load_config() # Load from default location
        config_data = get_config() # Get the whole config dict
        nats_url = config_data.get("nats", {}).get("url") # Safely access nested key
        if not nats_url:
            raise ValueError("NATS URL (nats.url) not found in configuration.")
    except Exception as e:
        logger.error(f"Failed to load OPMAS configuration: {e}")
        sys.exit(1)

    # --- Process Log File ---
    total_lines = 0
    parsed_lines = 0
    published_events = 0
    failed_publish = 0

    logger.info(f"Processing log file: {log_file}")
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                total_lines += 1
                # Use imported parsing function
                parsed_data = parse_syslog_line(line, year)

                if parsed_data:
                    parsed_lines += 1
                    # Use imported classification function
                    subject = classify_nats_subject(parsed_data.get("process_name"))

                    # Create the event object (ensure field names match ParsedLogEvent)
                    event = ParsedLogEvent(
                        event_id=str(uuid.uuid4()),
                        original_ts=parsed_data.get("original_ts"),
                        source_ip=None, # Cannot determine IP from file
                        hostname=parsed_data.get("hostname"),
                        process_name=parsed_data.get("process_name"),
                        pid=parsed_data.get("pid"),
                        message=parsed_data.get("message", ""),
                        structured_fields=None, # Agents will add these if needed
                        # Other ParsedLogEvent fields will use defaults (arrival_ts_utc, etc.)
                    )

                    try:
                        # Convert dataclass to dict for publishing
                        event_dict = asdict(event)
                        # Use the publish_message helper from mq.py
                        # It handles the shared NATS client connection
                        await publish_message(subject, event_dict)
                        published_events += 1
                        if published_events % 100 == 0:
                            logger.info(f"Published {published_events} events...")
                    except Exception as e:
                        # publish_message logs its own errors, but we count failures
                        logger.error(f"Publishing failed for event derived from line: {line.strip()}")
                        failed_publish += 1
                else:
                    # Parsing failed, warning already logged in parse_syslog_line
                    pass # Count failed parsing implicitly (total - parsed)

    except FileNotFoundError:
        logger.error(f"Log file disappeared during processing: {log_file}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during file processing: {e}", exc_info=True)
    finally:
        # --- Cleanup and Summary ---
        # No need to explicitly close NATS connection as publish_message uses shared client
        logger.info("--- Ingestion Summary ---")
        logger.info(f"Total lines read:      {total_lines}")
        logger.info(f"Successfully parsed:   {parsed_lines}")
        logger.info(f"Failed parsing:        {total_lines - parsed_lines}") # Corrected calculation
        logger.info(f"Events published:      {published_events}")
        logger.info(f"Failed publications:   {failed_publish}")
        logger.info("-------------------------")

if __name__ == "__main__":
    # Ensure OPMAS environment (config files) is set up correctly
    print("Ensure NATS server is running and OPMAS config (config/opmas_config.yaml) exists.")
    asyncio.run(main()) 