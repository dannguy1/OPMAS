# OPMAS Component Interactions

## Component Communication Flow

This diagram illustrates the sequence of interactions between the major components of the OPMAS system, reflecting the current architecture and designed flows.

```mermaid
sequenceDiagram
    actor User
    participant UI as Frontend UI
    participant MgmtAPI as Management API
    participant HostSystem as Host System (via Mgmt API)
    participant LogAPI_HTTP as Log Ingestion API (HTTP)
    participant NATS as NATS Message Bus
    participant Agent as Domain Agent (e.g., WiFiAgent)
    participant Orch_Active as Orchestrator (Active - backend/orchestrator.py)
    participant Orch_Core as Orchestrator (Designed - core/orchestrator.py)
    participant ActionExecutor as Action Executor (Future Scope)
    participant DB as PostgreSQL Database
    participant Device as OpenWRT Device

    %% User Login & UI Interaction
    User->>UI: Interacts with UI
    UI->>MgmtAPI: HTTP Request (e.g., /login with credentials)
    MgmtAPI->>MgmtAPI: Validate Credentials (vs DB)
    MgmtAPI->>DB: Query User Table
    DB-->>MgmtAPI: User Info
    MgmtAPI->>MgmtAPI: Generate JWT
    MgmtAPI-->>UI: HTTP Response (JWT Token)
    UI->>UI: Store JWT

    UI->>MgmtAPI: HTTP Request (e.g., GET /agents, with JWT)
    MgmtAPI->>MgmtAPI: Validate JWT / AuthZ Checks
    MgmtAPI->>DB: Query/Update (Agents, Rules, Findings etc.)
    DB-->>MgmtAPI: Data
    MgmtAPI-->>UI: HTTP Response (Data)

    %% Log Flow - HTTP Path (Default Active)
    Device->>LogAPI_HTTP: Syslog Message
    LogAPI_HTTP->>LogAPI_HTTP: Parse & Classify (using parsing_utils.py)
    LogAPI_HTTP->>NATS: ParsedLogEvent (e.g., logs.wifi)

    %% Optional: Log Flow - TCP Path (Designed, if explicitly run)
    Note over Device, NATS: TCP Ingestion Path (If active)
    Device->>SyslogTCP_Ingestor(Designed): Syslog Message
    SyslogTCP_Ingestor(Designed)->>NATS: Raw Log JSON (logs.parsed.raw)
    NATS->>Parser_TCP(Designed): Raw Log JSON
    Parser_TCP(Designed)->>NATS: ParsedLogEvent (e.g., logs.security)

    %% Agent Processing
    NATS-->>Agent: ParsedLogEvent
    Agent->>Agent: Load Rules (from YAML/env for BaseAgent; DB for specific agents like WiFiAgent - future/enhancement)
    opt Agent-specific DB Rule Loading
        Agent->>DB: Load Rules from agent_rules table
        DB-->>Agent: Rules Config
    end
    Agent->>Agent: Process Log based on Rules
    Agent->>NATS: AgentFinding (e.g., findings.wifi)

    %% Orchestrator Processing (Active - backend/orchestrator.py)
    NATS-->>Orch_Active: AgentFinding
    Orch_Active->>DB: Load Agent Configuration (agents table)
    DB-->>Orch_Active: Agent Config
    Orch_Active->>DB: Store Finding (findings table)
    DB-->>Orch_Active: Store Confirmation

    %% Orchestrator Processing (Designed - core/orchestrator.py - Future/Alternative)
    Note over NATS, DB: Designed Orchestrator Flow (core/orchestrator.py)
    NATS-->>Orch_Core: AgentFinding
    Orch_Core->>DB: Load Agent Configuration
    DB-->>Orch_Core: Agent Config
    Orch_Core->>DB: Load Playbooks (playbooks, playbook_steps tables)
    DB-->>Orch_Core: Playbook Data
    Orch_Core->>Orch_Core: Evaluate Finding against Playbooks
    Orch_Core->>DB: Store Finding (findings table)
    Orch_Core->>DB: Store IntendedAction (intended_actions table)
    DB-->>Orch_Core: Store Confirmation
    Orch_Core-.->NATS: Action Command (actions.execute - Future)

    %% Action Execution (Future Scope)
    Note over ActionExecutor, Device: Action Execution (Future Scope / Not Implemented)
    NATS-.->ActionExecutor: Action Command (actions.execute)
    ActionExecutor-.->DB: Load Device Info & Credentials
    DB-.->ActionExecutor: Device Info
    ActionExecutor-.->Device: SSH Command
    Device-.->ActionExecutor: Command Result
    ActionExecutor-.->NATS: Action Result (actions.results)
    ActionExecutor-.->DB: Store Action Result

    %% Management Control Flow
    UI->>MgmtAPI: Control Command (e.g., /api/v1/control/start)
    MgmtAPI->>MgmtAPI: Validate JWT / AuthZ Checks
    MgmtAPI->>HostSystem: exec(backend/start_opmas.sh component)
    HostSystem-->>MgmtAPI: Script Execution Result (async via DB update by ControlService)
    MgmtAPI-->>UI: HTTP Response (e.g., Action ID, Accepted)

    %% Management API to NATS (Potential for real-time updates or commands)
    MgmtAPI-->>NATS: Publish (e.g., config update event, command)
    NATS-->>MgmtAPI: Subscribe (e.g., live findings, agent heartbeats for UI via WebSocket)
```

## Message Types and Topics

### NATS Topics

1. **Log Topics**
   - `logs.parsed.raw`: Raw structured logs from specific ingestors (e.g., TCP Syslog Ingestor) requiring further parsing/classification by a dedicated Log Parser service.
   - `logs.wifi`: Parsed and classified WiFi-related log events.
   - `logs.security`: Parsed and classified security-related log events.
   - `logs.system`: Parsed and classified general system log events.
   - `logs.generic`: Log events that could not be specifically classified or originate from generic HTTP ingestion.
   - `logs.health`: (As per original, if still applicable for health-specific agents)
   - `logs.connectivity`: (As per original, if still applicable for connectivity-specific agents)

2. **Finding Topics**
   - `findings.>`: Wildcard topic the Orchestrator subscribes to.
   - `findings.wifi`: Findings from the WiFi agent.
   - `findings.security`: Findings from the Security agent.
   - (Other agent-specific finding topics like `findings.health`, `findings.connectivity`)

3. **Action Topics (Primarily for Future Scope with Action Executor)**
   - `actions.execute`: Commands intended for execution by the Action Executor.
   - `actions.results`: Results of commands executed by the Action Executor.

### Message Formats

1. **Parsed Log Event**
```json
{
  "event_id": "uuid",
  "arrival_ts_utc": "ISO-8601",
  "source_ip": "192.168.1.1",
  "original_ts": "Apr 18 15:02:17",
  "hostname": "OpenWRT-Router1",
  "process_name": "hostapd",
  "pid": "1234", // Optional
  "log_level": "INFO", // Optional, may be part of message or structured_fields
  "message": "wlan0: STA authenticated",
  "log_source_type": "wifi", // Added by parsing_utils or LogParser service
  "structured_fields": { // Optional, for more detailed structured data
    "interface": "wlan0",
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "event_type": "auth_success"
  }
}
```

2. **Agent Finding**
```json
{
  "finding_id": "uuid", // Generated by the agent
  "agent_name": "WiFiAgent",
  "timestamp_utc": "ISO-8601", // Time of finding generation
  "device_hostname": "OpenWRT-Router1", // Optional, if available from event
  "device_ip": "192.168.1.10", // Optional
  "finding_type": "HighAuthFailureRate", // Specific type defined by agent
  "severity": "Warning", // e.g., Info, Warning, Error, Critical
  "message": "High rate of authentication failures on wlan0", // Human-readable summary
  "details": { // Agent-specific structured data
    "interface": "wlan0",
    "failure_count": 25,
    "time_window_seconds": 60,
    "triggering_event_ids": ["uuid1", "uuid2"] // Optional: links to ParsedLogEvents
  }
}
```

3. **Action Command (Future Scope)**
```json
{
  "action_id": "uuid", // Unique ID for this action instance
  "command_ts_utc": "ISO-8601", // Timestamp of command generation
  "device_hostname": "OpenWRT-Router1", // Target device
  "action_type": "run_ssh_command", // Type of action
  "command_details": { // Specifics of the command
    "command_string": "/usr/sbin/hostapd_cli -i wlan0 deauthenticate aa:bb:cc:dd:ee:ff",
    "timeout_seconds": 30
  },
  "originating_finding_id": "uuid", // Optional: link to the finding that triggered this
  "playbook_id": "uuid", // Optional: link to the playbook
  "playbook_step_id": "uuid" // Optional: link to the playbook step
}
```

4. **Action Result (Future Scope)**
```json
{
  "result_id": "uuid",
  "action_id": "uuid", // Corresponds to the ActionCommand
  "result_ts_utc": "ISO-8601",
  "device_hostname": "OpenWRT-Router1",
  "status": "Success", // e.g., Success, Failure, Timeout
  "exit_code": 0, // If applicable
  "stdout": "Command output...", // If applicable
  "stderr": "", // If applicable
  "error_message": "" // If status is Failure
}
```

## Database Schema Overview

(This section can remain largely as is from the original document, as it describes the tables. Minor adjustments might be needed if the ORM models (`db_models.py`) are taken as the absolute source of truth for column names, which they should be for application interaction.)

### Core Tables

1. **opmas_config** (as per `db_models.py`)
   - `key` (String, PK)
   - `value` (JSONB)
2. **agents** (as per `db_models.py`)
   - `agent_id` (Integer, PK)
   - `name` (String, Unique)
   - `module_path` (String)
   - `description` (Text)
   - `is_enabled` (Boolean)
3. **agent_rules** (as per `db_models.py`)
   - `rule_id` (Integer, PK)
   - `agent_id` (FK to agents)
   - `rule_name` (String)
   - `rule_config` (JSONB)
4. **playbooks** (as per `db_models.py`)
   - `playbook_id` (Integer, PK)
   - `finding_type` (String, Unique)
   - `name` (String)
   - `description` (Text)
5. **playbook_steps** (as per `db_models.py`)
   - `step_id` (Integer, PK)
   - `playbook_id` (FK to playbooks)
   - `step_order` (Integer)
   - `action_type` (String)
   - `command_template` (Text)
   - `step_config` (JSONB)
6. **findings** (as per `db_models.py`)
   - `finding_id` (String, PK)
   - `agent_id` (FK to agents)
   - `timestamp_utc` (DateTime)
   - `finding_type` (String)
   - `device_hostname` (String)
   - `device_ip` (String)
   - `details` (JSONB)
7. **intended_actions** (as per `db_models.py`)
   - `action_id` (Integer, PK)
   - `finding_id` (FK to findings)
   - `playbook_step_id` (FK to playbook_steps)
   - `timestamp_utc` (DateTime)
   - `action_type` (String)
   - `rendered_command_context` (Text)
8. **users** (from Management API's `auth/models.py`, assumed schema)
    - `id` (Integer, PK)
    - `username` (String, Unique)
    - `email` (String, Unique)
    - `hashed_password` (String)
    - `is_active` (Boolean)
    - `is_superuser` (Boolean)

(Other tables like `devices`, `ssh_keys` from `DATABASE_SCHEMA.md` are also relevant but managed primarily by the Management API.)
```
