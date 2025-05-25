# src/opmas/log_api.py

import asyncio
import atexit
import logging
import os
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field

# --- OPMAS Imports ---
# Assuming the script runs from the project root or src is in PYTHONPATH
try:
    from .config import get_config, load_config
    from .data_models import ParsedLogEvent
    from .logging_config import setup_logging
    from .mq import (  # Need get_shared_nats_client for startup
        get_shared_nats_client,
        publish_message,
    )
    from .parsing_utils import (  # Import DEFAULT_SUBJECT
        DEFAULT_SUBJECT,
        classify_nats_subject,
        parse_syslog_line,
    )
except ImportError as e:
    print(f"ERROR: Failed to import OPMAS modules in log_api.py: {e}")
    print("Ensure you run the API using uvicorn from the project root, e.g.:")
    print("uvicorn src.opmas.log_api:app --reload")
    import sys

    sys.exit(1)

# --- Path Definitions ---
LOG_API_FILE = Path(__file__).resolve()
OPMAS_DIR = LOG_API_FILE.parent
CORE_SRC_DIR = OPMAS_DIR.parent
CORE_DIR = CORE_SRC_DIR.parent
PIDS_DIR = CORE_DIR / "pids"
LOG_API_PID_FILE = PIDS_DIR / "LogAPI.pid"
# -----------------------


# --- PID File Cleanup Function ---
def _remove_pid_file():
    """Ensures the PID file is removed on exit."""
    try:
        if LOG_API_PID_FILE.is_file():
            logger.info(f"Removing PID file: {LOG_API_PID_FILE}")
            LOG_API_PID_FILE.unlink()
        else:
            # This might happen if startup failed before registration or file was manually removed
            logger.debug("PID file removal skipped: File not found.")
    except Exception as e:
        # Use logger if possible, otherwise print
        log_func = logger.error if "logger" in globals() else print
        log_func(f"Error removing PID file {LOG_API_PID_FILE}: {e}")


# -----------------------------

# --- Setup Logging ---
try:
    # Ensure logging is configured before creating the logger
    setup_logging()
    logger = logging.getLogger("LogAPI")
except Exception as e:
    print(f"ERROR: Failed to setup logging: {e}")
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("LogAPI_Fallback")
    logger.warning("Falling back to basic logging config for LogAPI.")

# --- FastAPI App Definition ---
app = FastAPI(
    title="OPMAS Log Ingestion API",
    description="API endpoint to receive logs and publish them to NATS.",
    version="0.1.0",
)


# --- API Request Model ---
class LogIngestionRequest(BaseModel):
    logs: List[str] = Field(..., description="A list of raw log strings.")
    source_identifier: Optional[str] = Field(
        None, description="Optional identifier for the log source (e.g., hostname or IP)."
    )
    explicit_source_ip: Optional[str] = Field(
        None, description="Optional: Explicit IP address of the original log source device."
    )


# --- Background Task for Processing ---
async def process_and_publish_logs(
    log_lines: List[str],
    source_identifier: Optional[str],
    client_ip: Optional[str],
    explicit_source_ip: Optional[str],
):
    """Parses log lines and publishes them to NATS in the background."""
    publish_tasks = []
    # Determine year once - assumes logs in a batch are from the same rough timeframe
    current_year = datetime.now().year

    # Determine the source IP to use: prioritize explicit, fallback to client
    final_source_ip = explicit_source_ip if explicit_source_ip else client_ip

    for line in log_lines:
        try:
            # Attempt parsing (currently assumes syslog format)
            parsed_data = parse_syslog_line(line, current_year)
            event_dict = None

            if not parsed_data:
                # Handle non-syslog format or parsing failure
                logger.debug(
                    f"Failed to parse log line via syslog regex (assuming generic): {line[:100]}..."
                )
                hostname = source_identifier or "unknown_api_source"
                subject = DEFAULT_SUBJECT  # logs.generic
                event = ParsedLogEvent(
                    event_id=str(uuid.uuid4()),
                    original_ts=datetime.now().astimezone().isoformat(),  # Use current time
                    hostname=hostname,
                    message=line.strip(),
                    source_ip=final_source_ip,  # Use determined source IP
                    # Other fields use defaults or None
                )
                event_dict = asdict(event)
            else:
                # Use parsed data
                process_name = parsed_data.get("process_name")
                subject = classify_nats_subject(process_name)
                # Use parsed hostname, fallback to source_identifier if needed
                hostname = parsed_data.get("hostname") or source_identifier or "unknown_api_source"
                event = ParsedLogEvent(
                    event_id=str(uuid.uuid4()),
                    original_ts=parsed_data.get("original_ts"),
                    source_ip=final_source_ip,  # Use determined source IP
                    hostname=hostname,
                    process_name=process_name,
                    pid=parsed_data.get("pid"),
                    message=parsed_data.get("message", ""),
                    structured_fields=None,  # Agents will add these if needed
                    # Other fields use defaults or None
                )
                event_dict = asdict(event)

            # Add publish task if event was created
            if event_dict:
                # Use the publish_message helper (handles NATS connection)
                publish_tasks.append(publish_message(subject, event_dict))

        except Exception as e:
            logger.error(f"Error processing log line '{line[:100]}...': {e}", exc_info=True)
            continue  # Skip this line on error, process others

    # Run all publish tasks concurrently
    if publish_tasks:
        results = await asyncio.gather(*publish_tasks, return_exceptions=True)
        # Log any exceptions that occurred during publishing
        success_count = 0
        failure_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # publish_message already logs errors, so just count here
                failure_count += 1
                # logger.error(f"Error during background NATS publish for log index {i}: {result}")
            else:
                success_count += 1

        logger.info(
            f"Background processing complete for {len(log_lines)} lines. Events published: {success_count}, Failures: {failure_count}."
        )
    else:
        logger.info(f"No valid events generated from {len(log_lines)} log lines for publishing.")


# --- API Endpoint Definition ---
@app.post("/api/v1/logs", status_code=status.HTTP_202_ACCEPTED)
async def ingest_logs(
    request: Request, payload: LogIngestionRequest, background_tasks: BackgroundTasks
):
    """
    Receives a list of raw log strings, attempts to parse them,
    and publishes structured events to NATS topics.
    Processing happens in the background.
    """
    client_ip = request.client.host if request.client else None
    # Extract explicit_source_ip from payload
    explicit_ip = payload.explicit_source_ip

    if not payload.logs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No logs provided in the request body."
        )

    num_logs = len(payload.logs)
    source_id = payload.source_identifier or "unspecified"
    logger.info(
        f"Received API request to ingest {num_logs} log lines from '{source_id}' (Client: {client_ip}, Explicit Source: {explicit_ip or 'None'})."
    )

    # Add the processing task to run in the background
    background_tasks.add_task(
        process_and_publish_logs, payload.logs, payload.source_identifier, client_ip, explicit_ip
    )

    return {
        "message": f"Log ingestion request for {num_logs} lines accepted and queued for background processing."
    }


# --- API Root Endpoint (Optional) ---
@app.get("/")
async def read_root():
    return {"message": "Welcome to the OPMAS Log Ingestion API. POST logs to /api/v1/logs"}


# --- Application Startup Event (Optional but Recommended) ---
@app.on_event("startup")
async def startup_event():
    """Actions to perform on API startup."""
    logger.info("Log API starting up...")
    try:
        # Load OPMAS configuration on startup
        load_config()
        logger.info("OPMAS configuration loaded.")

        # Ensure the shared NATS client is initialized (important for publish_message)
        logger.info("Initializing shared NATS client connection...")
        await get_shared_nats_client()  # Call to connect if not already connected
        logger.info("Shared NATS client initialized.")

        # --- PID File Creation ---
        logger.info(f"Attempting to create PID file at {LOG_API_PID_FILE}")
        PIDS_DIR.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        pid = os.getpid()
        LOG_API_PID_FILE.write_text(str(pid))
        logger.info(f"PID file created successfully with PID: {pid}")

        # Register cleanup function AFTER successful PID write
        atexit.register(_remove_pid_file)
        logger.info("PID file removal registered for shutdown.")
        # -------------------------

    except Exception as e:
        logger.critical(f"CRITICAL ERROR during Log API startup: {e}", exc_info=True)
        # Attempt cleanup even if startup fails partially
        _remove_pid_file()
        # Depending on severity, might want to prevent startup or re-raise
        raise  # Re-raise the exception to potentially stop FastAPI startup


# --- Application Shutdown Event (Optional) ---
@app.on_event("shutdown")
async def shutdown_event():
    """Actions to perform on API shutdown."""
    logger.info("Log API shutting down...")
    # NATS connection closing is handled by individual components or shared client logic usually
    # PID file removal is handled by atexit


# --- Running the App (for direct execution testing) ---
# Use 'uvicorn src.opmas.log_api:app --reload --port 8000' from the project root
if __name__ == "__main__":
    print("ERROR: This script is not meant to be run directly.")
    print("Use uvicorn: uvicorn src.opmas.log_api:app --reload --host 0.0.0.0 --port 8000")
