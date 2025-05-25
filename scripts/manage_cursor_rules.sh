#!/bin/bash

# Management script for Cursor rules

function show_help {
    echo "Cursor Rules Management Script"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  init      - Initialize Cursor rules (first time setup)"
    echo "  status    - Show current implementation status"
    echo "  checkpoint - Create a new checkpoint"
    echo "  log       - Add entry to implementation log"
    echo "  list      - List all checkpoints"
    echo "  restore   - Restore from a checkpoint"
    echo "  help      - Show this help message"
}

function init_rules {
    if [ -d ".cursor" ]; then
        echo "Cursor rules already initialized"
        exit 1
    fi

    # Run setup script
    ./scripts/setup_cursor_rules.sh
}

function show_status {
    if [ ! -d ".cursor" ]; then
        echo "Cursor rules not initialized"
        exit 1
    fi

    echo "Current Implementation Status:"
    echo "-----------------------------"

    # Show current phase and task
    echo "Current Phase: $(grep "Current Phase:" .cursor/logs/implementation.log | tail -n 1 | cut -d':' -f2 | xargs)"
    echo "Current Task: $(grep "Current Task:" .cursor/logs/implementation.log | tail -n 1 | cut -d':' -f2 | xargs)"

    # Show last checkpoint
    LAST_CHECKPOINT=$(ls -t .cursor/checkpoints/*.json | head -n 1)
    if [ -n "$LAST_CHECKPOINT" ]; then
        echo "Last Checkpoint: $(basename $LAST_CHECKPOINT)"
        echo "Checkpoint Status: $(jq -r '.status' $LAST_CHECKPOINT)"
    fi
}

function create_checkpoint {
    if [ ! -d ".cursor" ]; then
        echo "Cursor rules not initialized"
        exit 1
    fi

    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    CHECKPOINT_ID=$(uuidgen)

    # Get current phase and task
    PHASE=$(grep "Current Phase:" .cursor/logs/implementation.log | tail -n 1 | cut -d':' -f2 | xargs)
    TASK=$(grep "Current Task:" .cursor/logs/implementation.log | tail -n 1 | cut -d':' -f2 | xargs)

    # Create checkpoint
    cat > .cursor/checkpoints/${CHECKPOINT_ID}.json << EOF
{
  "checkpoint_id": "${CHECKPOINT_ID}",
  "timestamp": "${TIMESTAMP}",
  "phase": "${PHASE}",
  "task": "${TASK}",
  "status": "in_progress",
  "environment": {
    "os": "$(uname -s)",
    "shell": "$SHELL",
    "cursor_version": "latest"
  }
}
EOF

    # Update implementation log
    echo -e "\n## Checkpoint Created\n- Date: $(date -u +"%Y-%m-%d")\n- Checkpoint ID: ${CHECKPOINT_ID}\n- Phase: ${PHASE}\n- Task: ${TASK}\n- Status: in_progress" >> .cursor/logs/implementation.log

    echo "Checkpoint created: ${CHECKPOINT_ID}"
}

function add_log_entry {
    if [ ! -d ".cursor" ]; then
        echo "Cursor rules not initialized"
        exit 1
    fi

    echo "Enter log entry (Ctrl+D to finish):"
    LOG_ENTRY=$(cat)

    echo -e "\n## Log Entry\n- Date: $(date -u +"%Y-%m-%d")\n${LOG_ENTRY}" >> .cursor/logs/implementation.log

    echo "Log entry added"
}

function list_checkpoints {
    if [ ! -d ".cursor" ]; then
        echo "Cursor rules not initialized"
        exit 1
    fi

    echo "Available Checkpoints:"
    echo "---------------------"

    for checkpoint in .cursor/checkpoints/*.json; do
        echo "ID: $(basename $checkpoint .json)"
        echo "Timestamp: $(jq -r '.timestamp' $checkpoint)"
        echo "Phase: $(jq -r '.phase' $checkpoint)"
        echo "Task: $(jq -r '.task' $checkpoint)"
        echo "Status: $(jq -r '.status' $checkpoint)"
        echo "---------------------"
    done
}

function restore_checkpoint {
    if [ ! -d ".cursor" ]; then
        echo "Cursor rules not initialized"
        exit 1
    fi

    if [ -z "$1" ]; then
        echo "Please provide checkpoint ID"
        exit 1
    fi

    CHECKPOINT=".cursor/checkpoints/$1.json"
    if [ ! -f "$CHECKPOINT" ]; then
        echo "Checkpoint not found"
        exit 1
    fi

    # Update implementation log
    echo -e "\n## Restored from Checkpoint\n- Date: $(date -u +"%Y-%m-%d")\n- Checkpoint ID: $1\n- Phase: $(jq -r '.phase' $CHECKPOINT)\n- Task: $(jq -r '.task' $CHECKPOINT)" >> .cursor/logs/implementation.log

    echo "Restored from checkpoint: $1"
}

# Main script
case "$1" in
    init)
        init_rules
        ;;
    status)
        show_status
        ;;
    checkpoint)
        create_checkpoint
        ;;
    log)
        add_log_entry
        ;;
    list)
        list_checkpoints
        ;;
    restore)
        restore_checkpoint "$2"
        ;;
    help|*)
        show_help
        ;;
esac
