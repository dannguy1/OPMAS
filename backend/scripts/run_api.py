#!/usr/bin/env python3

"""Script to run the Management API service."""

import os
import sys
import logging
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

from opmas.utils.logging import LogManager

# Initialize logger
logger = LogManager.get_logger(__name__)

def main():
    """Main function to run the Management API service."""
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    workers = int(os.getenv("API_WORKERS", "4"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    # Configure uvicorn logging
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logger.info(f"Starting Management API service on {host}:{port} with {workers} workers")
    
    try:
        # Run the API service
        uvicorn.run(
            "opmas.api.main:app",
            host=host,
            port=port,
            workers=workers,
            log_level=log_level,
            log_config=log_config,
            reload=os.getenv("API_RELOAD", "false").lower() == "true"
        )
    except Exception as e:
        logger.error(f"Error running Management API service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 