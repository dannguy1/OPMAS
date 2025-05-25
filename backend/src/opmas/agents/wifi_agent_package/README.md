# OPMAS Agent Package: WiFiAgent

This directory contains the OPMAS agent package for the `WiFiAgent`.

## Structure

- **`.env`**: Contains required metadata (`AGENT_NAME`, `AGENT_DESCRIPTION`) used by OPMAS discovery. Can also contain optional environment variables used by the agent logic.
- **`__init__.py`**: Standard Python file to mark this directory as a package.
- **`agent.py`**: Contains the `WiFiAgent` class, inheriting from `BaseAgent`, which handles subscribing to NATS topics (`logs.wifi`) and processing log events based on rules loaded from the database.
- **`README.md`**: This file.

## Functionality

This agent monitors Wi-Fi related logs for patterns indicating potential issues, such as:
- High authentication failure rates.
- (Potentially other rules like DFS events, deauth floods, etc.)

It loads its specific rules and configurations from the OPMAS database based on the `AGENT_NAME` defined in the `.env` file.

## Usage

1.  **Deploy:** Place this entire `wifi_agent_package` directory into the designated OPMAS agents directory on the backend server (the backend discovery mechanism needs to be updated to find package-based agents).
2.  **Configure:** Use the OPMAS UI (Agents -> Rules) to define specific rules (providing the JSON `rule_config`) for the `WiFiAgent`.
3.  **Run:** The OPMAS backend should manage the lifecycle of this agent process (starting/stopping it based on its enabled status in the database).

## Testing

The agent can be run standalone for testing (requires NATS connection and database access):

```bash
# Ensure necessary dependencies and environment variables (like DB connection string, NATS URL) are set
# Optional: Install python-dotenv if testing .env loading
# pip install python-dotenv

# Make sure the relative imports in agent.py work from your execution context
# You might need to adjust PYTHONPATH or run as a module
python agent.py
```
