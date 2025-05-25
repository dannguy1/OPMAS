# scripts/init_db.py

import logging
import os
import sys

# --- Add project root to path to allow importing OPMAS modules ---
# This assumes the script is run from the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# ------------------------------------------------------------------

try:
    from src.opmas.config import load_config
    from src.opmas.db_utils import init_db
    from src.opmas.logging_config import setup_logging
except ImportError as e:
    print(f"Error: Failed to import OPMAS modules: {e}", file=sys.stderr)
    print(
        "Please ensure you run this script from the OPMAS project root directory", file=sys.stderr
    )
    print("and that all dependencies (SQLAlchemy, psycopg2-binary) are installed.", file=sys.stderr)
    sys.exit(1)

# Configure basic logging for the script itself
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("init_db")


def main():
    logger.info("--- OPMAS Database Initializer ---")

    try:
        logger.info("Loading OPMAS configuration...")
        load_config()  # Load config to get DB connection details
        # setup_logging() # Optional: Set up full OPMAS logging if desired for DB init
        logger.info("Configuration loaded.")
    except Exception as e:
        logger.critical(f"Failed to load OPMAS configuration: {e}", exc_info=True)
        sys.exit(1)

    try:
        logger.info("Attempting to initialize database tables...")
        init_db()  # This function handles engine creation and table creation
        logger.info("--- Database initialization process completed successfully. ---")
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}", exc_info=True)
        logger.error(
            "Please check your PostgreSQL server is running and the connection details in config/opmas_config.yaml are correct."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
