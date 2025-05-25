# OPMAS System Overview

## High-Level Architecture

```mermaid
graph TB
    subgraph "User Facing"
        Frontend_UI["Frontend UI (React, TypeScript)"]
    end

    subgraph "Management Layer"
        direction LR
        Mgmt_API["Management API (FastAPI, Python)"]
        subgraph "System Control"
            direction TB
            Start_Script["backend/start_opmas.sh"]
        end
    end

    subgraph "OPMAS Backend"
        direction TB
        subgraph "Log Ingestion"
            direction LR
            Log_API_HTTP["Log Ingestion API (HTTP)"]
            Parsing_Utils["(parsing_utils.py)"]
            Syslog_UDP["Syslog UDP Ingestor (Designed)"]
            Async_Queue["(asyncio.Queue)"]
            Parser_UDP["Parser (UDP Path - Designed)"]
            Syslog_TCP["Syslog TCP Ingestor (Designed)"]
            NATS_Raw_Logs["NATS (logs.parsed.raw)"]
            Parser_TCP["Parser (TCP Path - Designed)"]
        end
        subgraph "Agents System"
            direction LR
            subgraph "Domain Agents"
                direction TB
                WiFiAgent["WiFi Agent"]
                SecurityAgent["Security Agent"]
                OtherAgents["... Other Agents"]
            end
        end
        Orchestrator_Active["Orchestrator (Active)"]
        ActionExecutor["Action Executor (Future Scope)"]
    end

    subgraph "Shared Services"
        direction LR
        NATS_Bus["NATS Message Bus"]
        PostgreSQL_DB["PostgreSQL Database"]
    end

    subgraph "External Systems"
        Device1["OpenWRT Device 1"]
        Device2["OpenWRT Device 2"]
        DeviceN["... Device N"]
    end

    %% UI to Management API
    Frontend_UI -->|HTTP REST Calls| Mgmt_API

    %% Management API Interactions
    Mgmt_API -->|Reads/Writes Config, Findings, Users| PostgreSQL_DB
    Mgmt_API -->|Executes| Start_Script
    Mgmt_API <-->|Real-time updates / Commands?| NATS_Bus

    %% Log Ingestion Paths
    Device1 -->|Syslog| Log_API_HTTP
    Device2 -->|Syslog| Syslog_UDP
    DeviceN -->|Syslog| Syslog_TCP

    Log_API_HTTP -->|Uses| Parsing_Utils
    Parsing_Utils -->|ParsedLogEvent (logs.wifi, etc.)| NATS_Bus

    Syslog_UDP -->|Raw Log| Async_Queue
    Async_Queue -->|Raw Log| Parser_UDP
    Parser_UDP -->|ParsedLogEvent (logs.type)| NATS_Bus

    Syslog_TCP -->|Raw Log JSON| NATS_Raw_Logs
    NATS_Raw_Logs -->|Raw Log JSON| Parser_TCP
    Parser_TCP -->|ParsedLogEvent (logs.type)| NATS_Bus

    %% Agent Processing
    NATS_Bus --o|ParsedLogEvent (logs.wifi)| WiFiAgent
    NATS_Bus --o|ParsedLogEvent (logs.security)| SecurityAgent
    NATS_Bus --o|ParsedLogEvent (logs.type)| OtherAgents

    WiFiAgent -->|AgentFinding (findings.wifi)| NATS_Bus
    SecurityAgent -->|AgentFinding (findings.security)| NATS_Bus
    OtherAgents -->|AgentFinding (findings.type)| NATS_Bus

    %% Orchestrator (Active)
    NATS_Bus --o|AgentFinding (findings.>)| Orchestrator_Active
    Orchestrator_Active -->|Reads Agent Config| PostgreSQL_DB
    Orchestrator_Active -->|Writes Findings| PostgreSQL_DB
    %% Note: Current Orchestrator does not execute playbooks or create IntendedActions.

    %% Styling
    classDef userfacing fill:#D1E8E2,stroke:#333,stroke-width:2px
    classDef management fill:#A2D2FF,stroke:#333,stroke-width:2px
    classDef backend fill:#FFDAB9,stroke:#333,stroke-width:2px
    classDef shared fill:#BDE0FE,stroke:#333,stroke-width:2px
    classDef external fill:#E0E0E0,stroke:#333,stroke-width:2px
    classDef future fill:#lightgrey,stroke:#333,stroke-width:1px,stroke-dasharray: 5 5

    class Frontend_UI userfacing
    class Mgmt_API,Start_Script management
    class Log_API_HTTP,Parsing_Utils,Syslog_UDP,Async_Queue,Parser_UDP,Syslog_TCP,NATS_Raw_Logs,Parser_TCP,WiFiAgent,SecurityAgent,OtherAgents,Orchestrator_Active backend
    class ActionExecutor future
    class NATS_Bus,PostgreSQL_DB shared
    class Device1,Device2,DeviceN external
```

## Component Descriptions

### External Systems (OpenWRT Devices)
- Network devices, typically running OpenWRT.
- Forward logs via Syslog to configured OPMAS ingestion points.
- Target for potential future actions executed by the `Action Executor`.

### OPMAS Backend
1.  **Log Ingestion (Multiple Paths):**
    *   **Log Ingestion API (HTTP):** The default active path. Receives logs via HTTP, uses `parsing_utils.py` for parsing, and publishes structured `ParsedLogEvent` messages to specific NATS topics (e.g., `logs.wifi`, `logs.generic`).
    *   **Syslog UDP Ingestor (Designed):** Listens for UDP Syslog messages, places them on an internal `asyncio.Queue`. A dedicated parser component (`Parser (UDP Path)`) would then process these queue messages and publish `ParsedLogEvent` messages to NATS. Not active by default.
    *   **Syslog TCP Ingestor (Designed):** Listens for TCP Syslog messages, publishes raw-ish JSON to a specific NATS topic (`logs.parsed.raw`). A dedicated parser component (`Parser (TCP Path)`) subscribes to this topic, processes the messages, and publishes `ParsedLogEvent` messages to NATS. Not active by default.
2.  **Domain Agents (e.g., WiFiAgent, SecurityAgent):**
    *   Specialized components that subscribe to relevant `ParsedLogEvent` topics on NATS (e.g., `logs.wifi`).
    *   Analyze these events based on configurable rules (currently loaded from YAML/env files).
    *   Publish `AgentFinding` messages to NATS (e.g., `findings.wifi`) when issues are detected.
3.  **Orchestrator (Active - `backend/src/opmas/orchestrator.py`):**
    *   Subscribes to all `AgentFinding` messages from NATS (`findings.>`).
    *   Loads agent configurations from the PostgreSQL database.
    *   Stores received findings in the PostgreSQL database.
    *   *Note: The current active orchestrator does not implement playbook processing or `IntendedAction` generation. A distinct `OrchestratorAgent` in `backend/src/opmas/core/orchestrator.py` has designs for these features but is not run by the default startup scripts.*
4.  **Action Executor (Future Scope):**
    *   Intended to execute commands on managed devices based on actions determined by the Orchestrator (via playbooks).
    *   This component is not yet fully implemented or integrated.

### Management Layer
1.  **Management API (`Mgmt_API`):**
    *   A RESTful API (FastAPI, Python) providing secure (JWT authenticated) endpoints for system management.
    *   Interacts with PostgreSQL to manage configurations (agents, rules, users, etc.) and retrieve operational data (findings).
    *   Can publish to and subscribe from NATS for real-time UI updates or sending commands to the backend.
    *   Controls the lifecycle of backend services by executing `backend/start_opmas.sh`.
2.  **Frontend UI:**
    *   A web-based Single Page Application (React, TypeScript).
    *   Communicates exclusively with the Management API for all data display, configuration, and control tasks.
    *   Utilizes WebSockets (via Management API) for real-time updates.

### Shared Services
1.  **PostgreSQL Database (`PostgreSQL_DB`):**
    *   The central persistent data store for OPMAS.
    *   Stores system configurations (e.g., `opmas_config`, `agents`, `agent_rules`, `playbooks`), operational data (`findings`, `intended_actions`), and user credentials.
2.  **NATS Message Bus (`NATS_Bus`):**
    *   High-performance messaging system used for asynchronous communication and decoupling within the OPMAS Backend.
    *   Facilitates the flow of `ParsedLogEvent` messages from ingestors to agents, and `AgentFinding` messages from agents to the Orchestrator.
    *   Also used by the Management API for potential command/event relay.
```
