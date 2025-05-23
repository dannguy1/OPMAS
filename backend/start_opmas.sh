#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Change to script's directory --- Allows running from anywhere
cd "$(dirname "$0")"
# ------------------------------------

# --- Configuration ---
LOG_DIR="logs"
PID_FILE="opmas_pids.txt"
COMPOSE_FILE="docker-compose.yaml"

# --- Helper Functions ---
start_components() {
    echo "Starting OPMAS Components (using Docker Compose for NATS/Postgres)..."

    if ! command -v docker-compose &> /dev/null; then
        echo "Error: docker-compose command not found. Please install Docker Compose." >&2
        exit 1
    fi
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo "Error: $COMPOSE_FILE not found in the current directory." >&2
        exit 1
    fi

    # Create log directory if it doesn't exist
    mkdir -p "$LOG_DIR"
    echo "OPMAS Python component log files will be stored in '$LOG_DIR' directory."

    # Define log file paths (Python components only)
    API_LOG="$LOG_DIR/log_api_server.log"
    ORCH_LOG="$LOG_DIR/orchestrator_run.log"
    WIFI_LOG="$LOG_DIR/wifi_agent_run.log"

    # --- Start NATS & PostgreSQL (using Docker Compose) ---
    echo "Starting NATS and PostgreSQL containers via Docker Compose..."
    docker-compose -f "$COMPOSE_FILE" up -d nats postgres # Start in background
    echo "  -> NATS and PostgreSQL containers started (check with 'docker-compose ps')."
    echo "     (Allow a few moments for services to initialize...)"
    sleep 5 # Increased sleep to allow DB init

    # --- Start Log Ingestion API ---
    echo "Starting Log Ingestion API Server (Uvicorn)..."
    # Ensure VENV is active outside this script!
    uvicorn src.opmas.log_api:app --host 0.0.0.0 --port 8000 &> "$API_LOG" &
    API_PID=$!
    echo "  -> Log API PID: $API_PID (Log: $API_LOG)"
    sleep 2 # Give API server a moment

    # --- Start Orchestrator ---
    echo "Starting Orchestrator..."
    # Ensure VENV is active outside this script!
    python3 -m src.opmas.orchestrator &> "$ORCH_LOG" &
    ORCH_PID=$!
    echo "  -> Orchestrator PID: $ORCH_PID (Log: $ORCH_LOG)"

    # --- Start WiFi Agent ---
    echo "Starting WiFi Agent..."
    # Ensure VENV is active outside this script!
    # TODO: Modify this to start agents based on DB config later
    python3 -m src.opmas.agents.wifi_agent &> "$WIFI_LOG" &
    WIFI_PID=$!
    echo "  -> WiFi Agent PID: $WIFI_PID (Log: $WIFI_LOG)"

    # --- Store PIDs (Python Components Only) ---
    echo "Saving Python component PIDs to $PID_FILE..."
    # Overwrite or create the PID file
    echo "API_PID=$API_PID" > "$PID_FILE"
    echo "ORCH_PID=$ORCH_PID" >> "$PID_FILE"
    echo "WIFI_PID=$WIFI_PID" >> "$PID_FILE" # Add other agent PIDs here

    echo "-------------------------------------"
    echo "OPMAS Components Started Successfully"
    echo "-------------------------------------"
    echo "Use 'docker-compose logs nats' or 'docker-compose logs postgres' to view NATS/DB logs."
    echo "Check files in '$LOG_DIR' for Python component logs."
    echo "To stop components, run: ./start_opmas.sh stop"
}

stop_components() {
    echo "Stopping OPMAS Components..."

    # --- Stop NATS & PostgreSQL (using Docker Compose) ---
    if command -v docker-compose &> /dev/null && [ -f "$COMPOSE_FILE" ]; then
        echo "Stopping NATS and PostgreSQL containers via Docker Compose..."
        docker-compose -f "$COMPOSE_FILE" stop nats postgres || echo "  -> Failed to stop nats/postgres containers (maybe already stopped?)"
    else
        echo "Warning: docker-compose not found or $COMPOSE_FILE missing. Cannot stop NATS/Postgres containers via compose."
    fi

    # --- Stop Python Components --- 
    if [ ! -f "$PID_FILE" ]; then
        echo "PID file '$PID_FILE' not found. Cannot stop Python components based on PID file."
        echo "Attempting generic pkill for Python components..."
        pkill -f src.opmas || echo "No src.opmas processes found."
        pkill uvicorn || echo "No uvicorn processes found."
        echo "Generic pkill attempt finished."
        # Do not return here, still try docker compose stop
    else
        echo "Reading Python component PIDs from $PID_FILE..."
        declare -A pids
        while IFS='=' read -r key val; do
            if [[ -n "$val" ]]; then
                pids["$key"]="$val"
            fi
        done < "$PID_FILE"

        # Stop Python components
        PIDS_TO_KILL="${pids[@]}"
        if [ -n "$PIDS_TO_KILL" ]; then
            echo "Sending SIGTERM to OPMAS Python PIDs: $PIDS_TO_KILL"
            echo "$PIDS_TO_KILL" | xargs kill -- 2>/dev/null || echo "  -> Some Python processes may have already stopped."
        else
            echo "No Python component PIDs found in $PID_FILE to stop."
        fi

        echo "Removing PID file '$PID_FILE'..."
        rm -f "$PID_FILE"
    fi

    echo "-------------------------------------"
    echo "OPMAS Components Stop Signal Sent / Docker Compose Stop Called"
    echo "-------------------------------------"
    echo "Use 'ps', 'docker ps', and check logs to confirm termination."
    echo "(To fully remove stopped NATS/Postgres containers run: docker-compose down)"
}

show_usage() {
    echo "Usage: $0 [start|stop]"
    echo "  start : Starts NATS/Postgres (via Docker Compose) and OPMAS Python components."
    echo "  stop  : Stops NATS/Postgres (via Docker Compose) and kills Python components using PIDs from $PID_FILE."
}

# --- Main Script Logic ---
COMMAND=${1:-start} # Default to 'start' if no argument provided

case "$COMMAND" in
    start)
        start_components
        ;;
    stop)
        stop_components
        ;;
    *)
        echo "Error: Invalid command '$COMMAND'"
        show_usage
        exit 1
        ;;
esac

exit 0 