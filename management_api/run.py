"""Run the Management API server."""
import os
import sys
from pathlib import Path

import uvicorn


def main():
    """Run the API server."""
    # Get the project root directory
    project_root = Path(__file__).parent

    # Add src directory to Python path
    src_path = str(project_root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    # Set PYTHONPATH environment variable
    os.environ["PYTHONPATH"] = src_path

    # Run the FastAPI application
    uvicorn.run(
        "opmas_mgmt_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[src_path],
        log_level="info",
    )


if __name__ == "__main__":
    main()
