#!/bin/bash

# Setup script for Cursor rules

# Create necessary directories if they don't exist
mkdir -p .cursor/rules
mkdir -p .cursor/checkpoints
mkdir -p .cursor/logs

# Copy rules to .cursor directory
cp docs/CURSOR_RULES.md .cursor/rules/

# Create initial checkpoint
echo "Creating initial checkpoint..."
cat > .cursor/checkpoints/initial.json << EOF
{
  "checkpoint_id": "$(uuidgen)",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "phase": "setup",
  "task": "cursor_rules_setup",
  "status": "completed",
  "environment": {
    "os": "$(uname -s)",
    "shell": "$SHELL",
    "cursor_version": "latest"
  }
}
EOF

# Create initial implementation log
echo "Creating initial implementation log..."
cat > .cursor/logs/implementation.log << EOF
# Implementation Log

## Initial Setup
- Date: $(date -u +"%Y-%m-%d")
- Session ID: $(uuidgen)
- Current Phase: setup
- Current Task: cursor_rules_setup
- Status: completed
- Notes: Initial setup of Cursor rules and checkpoints
EOF

# Create .cursorignore file
echo "Creating .cursorignore file..."
cat > .cursorignore << EOF
# Ignore checkpoint data
.cursor/checkpoints/*.json
!initial.json

# Ignore logs
.cursor/logs/*.log
!implementation.log

# Ignore temporary files
*.tmp
*.temp
EOF

# Create README for .cursor directory
echo "Creating README for .cursor directory..."
cat > .cursor/README.md << EOF
# Cursor Rules and Checkpoints

This directory contains the Cursor rules and checkpoint system for the OPMAS project.

## Directory Structure
- \`rules/\`: Contains the Cursor rules documentation
- \`checkpoints/\`: Stores implementation checkpoints
- \`logs/\`: Contains implementation logs

## Usage
1. Review the rules in \`rules/CURSOR_RULES.md\`
2. Check the latest checkpoint in \`checkpoints/\`
3. Update the implementation log in \`logs/\`

## Maintenance
- Keep checkpoints up to date
- Update implementation logs regularly
- Review and update rules as needed
EOF

# Set up git hooks for checkpoint management
echo "Setting up git hooks..."
mkdir -p .git/hooks

cat > .git/hooks/pre-commit << EOF
#!/bin/bash

# Create checkpoint before commit
TIMESTAMP=\$(date -u +"%Y-%m-%dT%H:%M:%SZ")
CHECKPOINT_ID=\$(uuidgen)

# Get current phase and task from implementation log
PHASE=\$(grep "Current Phase:" .cursor/logs/implementation.log | tail -n 1 | cut -d':' -f2 | xargs)
TASK=\$(grep "Current Task:" .cursor/logs/implementation.log | tail -n 1 | cut -d':' -f2 | xargs)

# Create checkpoint
cat > .cursor/checkpoints/\${CHECKPOINT_ID}.json << EOC
{
  "checkpoint_id": "\${CHECKPOINT_ID}",
  "timestamp": "\${TIMESTAMP}",
  "phase": "\${PHASE}",
  "task": "\${TASK}",
  "status": "in_progress",
  "environment": {
    "os": "\$(uname -s)",
    "shell": "\$SHELL",
    "cursor_version": "latest"
  }
}
EOC

# Update implementation log
echo -e "\n## Checkpoint Created\n- Date: \$(date -u +"%Y-%m-%d")\n- Checkpoint ID: \${CHECKPOINT_ID}\n- Phase: \${PHASE}\n- Task: \${TASK}\n- Status: in_progress" >> .cursor/logs/implementation.log
EOF

chmod +x .git/hooks/pre-commit

echo "Cursor rules setup complete!"
echo "Please review the rules in .cursor/rules/CURSOR_RULES.md"
echo "Initial checkpoint and implementation log have been created"
echo "Git hooks have been set up for automatic checkpoint creation" 