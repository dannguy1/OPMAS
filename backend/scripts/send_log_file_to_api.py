# scripts/send_log_file_to_api.py

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests  # Requires 'pip install requests'

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("send_log_file_to_api")


def send_batch(api_url: str, batch: List[str], source_id: str) -> bool:
    """Sends a single batch of log lines to the API."""
    payload: Dict[str, Any] = {"logs": batch}
    if source_id:
        payload["source_identifier"] = source_id

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)  # 30s timeout
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        if response.status_code == 202:
            logger.debug(
                f"Successfully sent batch of {len(batch)} lines. Response: {response.json()}"
            )
            return True
        else:
            # This case might not be reached often due to raise_for_status, but good practice
            logger.warning(
                f"API returned unexpected status code {response.status_code}. Response: {response.text}"
            )
            return False

    except requests.exceptions.Timeout:
        logger.error(f"Request timed out sending batch of {len(batch)} lines to {api_url}.")
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error sending batch to {api_url}: {e}")
        return False
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"HTTP error sending batch to {api_url}: {e.response.status_code} - {e.response.text}"
        )
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"An unexpected error occurred sending batch to {api_url}: {e}")
        return False


def main():
    # Load config early to potentially get API URL if needed
    try:
        from src.opmas.config import get_config, load_config
    except ImportError:
        pass

    parser = argparse.ArgumentParser(
        description="Read a log file and send its contents in batches to the OPMAS Log API."
    )
    parser.add_argument("logfile", help="Path to the raw log file.")
    parser.add_argument(
        "--api-base-url",
        default="http://localhost:8000",
        help="Base URL of the OPMAS Log API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--source-id", default=None, help="Optional source identifier to send with the logs."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of log lines per API request batch (default: 100)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0,
        help="Optional delay (in seconds) between sending batches (default: 0)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    log_file = Path(args.logfile)
    if not log_file.is_file():
        print(f"Error: Log file not found: {log_file}", file=sys.stderr)
        logger.error(f"Log file not found: {log_file}")
        sys.exit(1)

    api_endpoint = f"{args.api_base_url.rstrip('/')}/api/v1/logs"
    batch_size = args.batch_size
    if batch_size <= 0:
        logger.error("Batch size must be positive.")
        sys.exit(1)

    logger.info(f"Starting log ingestion from '{log_file}' to '{api_endpoint}'")
    logger.info(
        f"Batch size: {batch_size}, Source ID: '{args.source_id or 'Not Set'}', Delay: {args.delay}s"
    )

    total_lines_read = 0
    total_lines_sent = 0
    batches_sent = 0
    failed_batches = 0
    current_batch: List[str] = []

    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                total_lines_read += 1
                line = line.strip()  # Remove leading/trailing whitespace
                if line:  # Avoid sending empty lines
                    current_batch.append(line)

                if len(current_batch) >= batch_size:
                    logger.info(f"Sending batch {batches_sent + 1} ({len(current_batch)} lines)...")
                    success = send_batch(api_endpoint, current_batch, args.source_id)
                    if success:
                        batches_sent += 1
                        total_lines_sent += len(current_batch)
                    else:
                        failed_batches += 1
                    current_batch = []  # Reset batch
                    if args.delay > 0:
                        time.sleep(args.delay)  # Pause between batches

            # Send any remaining lines in the last batch
            if current_batch:
                logger.info(
                    f"Sending final batch {batches_sent + 1} ({len(current_batch)} lines)..."
                )
                success = send_batch(api_endpoint, current_batch, args.source_id)
                if success:
                    batches_sent += 1
                    total_lines_sent += len(current_batch)
                else:
                    failed_batches += 1

    except FileNotFoundError:
        logger.error(f"Log file disappeared during processing: {log_file}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during file reading: {e}", exc_info=True)

    # --- Summary ---
    logger.info("--- Sending Summary ---")
    logger.info(f"Total lines read:      {total_lines_read}")
    logger.info(f"Total lines sent:      {total_lines_sent}")
    logger.info(f"Batches sent ok:     {batches_sent}")
    logger.info(f"Batches failed:      {failed_batches}")
    logger.info("-----------------------")


if __name__ == "__main__":
    main()
