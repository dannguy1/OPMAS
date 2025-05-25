# OPMAS Architecture Overview

## 1. Introduction

This document outlines the software architecture of the OpenWRT Proactive Monitoring Agentic System (OPMAS), reflecting the refactoring towards a database-centric design and a modular monorepo structure. OPMAS ingests and analyzes logs from network devices, storing configuration and results in a PostgreSQL database, and provides a web interface for management and monitoring.

The system is divided into three primary parts, managed within a single monorepo:

1.  **Core Backend:** Handles real-time log processing, analysis, and event orchestration.
2.  **Management API:** Provides a RESTful interface for configuration management and data retrieval.
3.  **Frontend UI:** A web-based graphical interface for users to interact with the system via the Management API.

These components rely on shared services (NATS and PostgreSQL) managed via Docker Compose.

## 2. Directory Structure

The monorepo is organized as follows:

```
OPMAS/
├── core/               # Core backend components (log processing, agents, orchestrator)
│   ├── src/opmas/
│   │   ├── agents/     # Domain-specific agents
│   │   ├── api/        # Log API and other endpoints
│   │   ├── db/         # Database models and utilities
│   │   ├── executor/   # Action executor implementation
│   │   └── utils/      # Shared utilities
│   ├── scripts/        # Utility scripts
│   ├── config/         # Configuration files
│   │   ├── opmas_config.yaml
│   │   └── ssh_keys/   # Encrypted SSH keys
│   ├── logs/          # Application logs
│   ├── tests/         # Test suite
│   ├── requirements.txt
│   ├── start_opmas.sh
│   └── docker-compose.yaml # Manages NATS & Postgres
├── management_api/     # Backend API for the Management UI
│   ├── src/opmas_mgmt_api/
│   │   ├── api/        # API endpoints
│   │   ├── models/     # Data models
│   │   └── services/   # Business logic
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── ui/                 # Frontend UI (React application)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   ├── public/
│   ├── tests/
│   ├── Dockerfile
│   └── package.json
├── docs/              # Project documentation and specifications
│   ├── OPMAS-DS.md    # Design Specification
│   ├── ARCHITECTURE.md # This file
│   ├── OPMAS-UI-DS.md # UI Design Specification
│   ├── backend-tasks.md
│   ├── frontend-tasks.md
│   └── diagrams/      # Architecture and flow diagrams
├── .github/           # GitHub workflows and templates
│   └── workflows/
├── scripts/           # Project-wide utility scripts
│   ├── setup.sh
│   └── deploy.sh
├── .gitignore
├── README.md
└── LICENSE
```

Key changes from previous structure:
1. All design specifications and documentation moved to `docs/` directory
2. Added more detailed subdirectory structure for each component
3. Added `.github/` for CI/CD workflows
4. Added project-wide `scripts/` directory
5. Added `diagrams/` subdirectory in docs for architecture diagrams
6. Expanded component-specific directory structures

## 3. Core Backend Implementation (`backend/`)

*   **Purpose:** The Core Backend is responsible for ingesting logs from various sources, parsing and analyzing these logs using specialized agents, identifying potential issues (findings), and recording these findings. It is designed for asynchronous processing and relies heavily on NATS for internal messaging and PostgreSQL for storing agent configurations and operational results.
*   **Key Components and Data Flow:**

    *   **Log Ingestion Layer:** OPMAS supports multiple log ingestion paths:
        1.  **HTTP API Ingestion (Default Active Path):**
            *   **Component:** `backend/src/opmas/api/log_api.py` (FastAPI application).
            *   **Flow:**
                *   Receives raw log strings via HTTP POST requests to `/api/v1/logs`.
                *   Utilizes `backend/src/opmas/parsing_utils.py` (`parse_syslog_line`) for initial parsing of each log line into a structured format. If direct parsing fails, it creates a generic event structure.
                *   Determines the appropriate NATS subject (e.g., `logs.wifi`, `logs.auth`, `logs.generic`) using `parsing_utils.classify_nats_subject` based on the parsed process name.
                *   Publishes a `ParsedLogEvent` (see `backend/src/opmas/data_models.py`) as a JSON message to the determined NATS subject using shared NATS utilities in `backend/src/opmas/utils/mq.py`.
            *   This path is activated by `backend/start_opmas.sh`.

        2.  **Syslog UDP Ingestion (Potentially Inactive by Default):**
            *   **Component:** `backend/src/opmas/log_ingestor.py`.
            *   **Flow (Designed):**
                *   Listens for syslog messages on a configured UDP port.
                *   The `SyslogUDPProtocol` places the raw message string, source IP, and arrival timestamp into an internal `asyncio.Queue`.
                *   A consumer component (currently an example `consume_logs_example` within `log_ingestor.py`, but intended to be a more robust NATS publisher) would dequeue these messages.
                *   This consumer would then parse the message (likely using `parsing_utils.py`), classify it to a NATS subject, and publish a `ParsedLogEvent` to NATS (e.g., `logs.wifi`) using `utils/mq.py`.
            *   This component is *not* started by the default `backend/start_opmas.sh` script and would need to be run as a separate service.

        3.  **Syslog TCP Ingestion (Potentially Inactive by Default):**
            *   **Component:** `backend/src/opmas/api/log_ingestion.py` (TCP server).
            *   **Flow (Designed):**
                *   Listens for syslog messages on a configured TCP port.
                *   Parses messages using its internal `SyslogMessage` class.
                *   Publishes the parsed event as a JSON dictionary to a fixed NATS subject: `logs.parsed.raw`.
                *   This path is designed to be processed further by the `LogParser` component (see below).
            *   This component is *not* started by the default `backend/start_opmas.sh` script.

    *   **Log Parsing Service (for TCP Syslog Path):**
        *   **Component:** `backend/src/opmas/parsers/log_parser.py` (run by `backend/scripts/run_log_parser.py`).
        *   **Flow:**
            *   Subscribes to the `logs.parsed.raw` NATS subject (fed by the TCP Syslog Ingestor).
            *   Performs further parsing, classification (determines `log_source_type`), and enrichment of the log event.
            *   Publishes the processed `ParsedLogEvent` to a dynamic NATS subject based on its type (e.g., `logs.wifi`, `logs.security`).
        *   This component is *not* started by the default `backend/start_opmas.sh` script.

    *   **Agent System:**
        *   **Base Class:** `backend/src/opmas/agents/base_agent.py`.
        *   **Specific Agents:** Implementations derived from `BaseAgent` (e.g., `WiFiAgent`, potentially located in `backend/src/opmas/agents/wifi_agent_package/agent.py`).
        *   **Flow:**
            *   Agents are loaded and started by the Orchestrator based on configurations in the `agents` database table.
            *   Each agent connects to NATS and subscribes to relevant `ParsedLogEvent` topics (e.g., `logs.wifi`).
            *   Upon receiving a `ParsedLogEvent`, the agent's `process_log_event` method is invoked. This method applies analytical rules to the event data.
            *   Agent rules are currently loaded from YAML configuration files (e.g., `config/rules.yaml`) and/or environment variables, as defined in `BaseAgent`. (Note: This differs from the previous architecture description which stated rules are loaded from the database).
            *   If an agent's logic identifies an issue, it constructs an `AgentFinding` data object (see `backend/src/opmas/data_models.py`).
            *   The agent publishes this `AgentFinding` to a NATS subject specific to the agent (e.g., `findings.wifi`).

    *   **Orchestrator:**
        *   **Component:** `backend/src/opmas/orchestrator.py`.
        *   **Flow:**
            *   Started by `backend/start_opmas.sh`.
            *   On startup, queries the `agents` table from PostgreSQL to determine which agents to load and run. It dynamically imports and starts these agent modules.
            *   Subscribes to all agent finding topics on NATS (`findings.>` wildcard).
            *   When an `AgentFinding` is received:
                *   The Orchestrator writes the finding details to the `findings` table in the PostgreSQL database.
                *   It includes a basic notification cooldown mechanism.
                *   Currently, the Orchestrator's primary role is to log these findings. The previously documented functionality of consulting playbooks and creating `intended_actions` in the database is not present in the current version of `orchestrator.py`. Action determination and execution are future enhancements.
        *   **Database Interaction:** Primarily reads agent configurations and writes findings.

*   **NATS Messaging Infrastructure:**
    *   **Role:** NATS (`nats://localhost:4222`, configured in `backend/src/opmas/utils/mq.py` and agent base) serves as the central nervous system for the Core Backend.
    *   **Usage:**
        *   **Decoupling & Asynchronicity:** Log ingestion components publish `ParsedLogEvent` messages to NATS without needing direct knowledge of the consuming agents. Agents process these messages asynchronously. Similarly, agents publish `AgentFinding` messages without direct coupling to the Orchestrator.
        *   **Topic-Based Routing:**
            *   `ParsedLogEvent` messages are published to topics like `logs.wifi`, `logs.security`, `logs.generic`, allowing agents to subscribe only to relevant data streams.
            *   `AgentFinding` messages are published to topics like `findings.wifi`, `findings.security`. The Orchestrator uses a wildcard subscription (`findings.>`) to capture all findings.
        *   **Shared Utilities:** `backend/src/opmas/utils/mq.py` provides helper functions like `publish_message` and `get_shared_nats_client` for simplified NATS interaction, particularly for components like the HTTP API that publish messages. Agents typically manage their own NATS connection lifecycle.

*   **Database (PostgreSQL):**
    *   **Models:** Defined in `backend/src/opmas/db_models.py`.
    *   **Utilities:** Session management via `backend/src/opmas/db_utils.py`.
    *   **Usage:**
        *   Stores agent configurations (loaded by the Orchestrator).
        *   Stores findings reported by agents (written by the Orchestrator).
        *   (Future: Intended to store playbook definitions, intended actions, and potentially agent rules).

*   **Configuration:**
    *   Core component configurations (like NATS URL, DB connection details) are typically managed via `backend/config/opmas_config.yaml` and loaded by `backend/src/opmas/config.py`.
    *   Agent-specific rules are currently loaded via `config/rules.yaml` and environment variables by the `BaseAgent`.

*   **Startup Script (`backend/start_opmas.sh`):**
    *   Manages the startup of NATS and PostgreSQL via Docker Compose (from `backend/docker-compose.yaml`).
    *   Starts the HTTP Log API (`log_api.py`), the Orchestrator (`orchestrator.py`), and currently, a `WiFiAgent` (though the specific agent started might evolve).
    *   It does *not* currently start the Syslog UDP ingestor, TCP ingestor, or the dedicated `LogParser` service by default. These would need to be managed as separate services if activated.

*   **Technology Stack:** Python, AsyncIO, FastAPI (for HTTP API), NATS (via `nats-py`), PostgreSQL (via SQLAlchemy), Pydantic (for data models).

## 4. Management API Implementation (`management_api/`)

*   **Purpose:** The Management API serves as the primary interface for the Frontend UI and potentially other external management tools. It provides a secure RESTful API to manage system configurations, view operational data, and control the lifecycle of OPMAS backend services. It decouples the UI from the direct complexities of the Core Backend's database and internal messaging.

*   **API Structure and Key Functionalities:**
    *   **Framework:** Built using FastAPI, located under `management_api/src/opmas_mgmt_api/`.
    *   **Main Application:** `main.py` initializes the FastAPI app, includes routers, sets up CORS, database connections (via `db/init_db.py`), and NATS connectivity (via `core/nats.py:NATSManager`).
    *   **Versioning:** API endpoints are versioned under the `/api/v1/` prefix.
    *   **Authentication & Authorization:**
        *   Implemented via JWT (JSON Web Tokens). The `auth/` directory (`jwt.py`, `models.py`, `schemas.py`, `dependencies.py`, `routers.py`) contains the full implementation.
        *   `POST /api/v1/auth/login`: Authenticates users against credentials stored in the `users` database table and issues access/refresh tokens.
        *   Most API endpoints are protected using FastAPI dependency injection (e.g., `Depends(get_current_active_user)`), ensuring that only authenticated users can access them. Some endpoints may require superuser privileges.
    *   **Endpoint Routers:** Located primarily in `routers/` and `api/v1/endpoints/`. Key resource management includes:
        *   **Agents (`routers/agents.py`):**
            *   CRUD operations for agent configurations (which agents are defined, their package paths, descriptions, enabled status). These configurations are stored in the `agents` table in PostgreSQL and are read by the Core Backend Orchestrator.
            *   `GET /discover`: Scans the Core Backend's agent package directory (`core/src/opmas/agents/`) to find agents not yet configured in the database by reading their embedded `.env` files.
            *   CRUD operations for agent-specific rules (`agent_rules` table). (Note: This allows for database-driven rule configuration, though the `BaseAgent` in the Core Backend currently loads rules from YAML/env. This suggests a future direction or alternative rule source).
            *   Endpoints to get/set agent status, runtime configuration, and subscribed NATS topics. Changes made here are stored in the database; a mechanism (potentially NATS messages published by this API, or polling by agents) would be needed for running agents to dynamically update.
        *   **Results (`routers/results.py`):**
            *   `GET /findings`: Provides paginated read access to historical findings generated by agents and stored in the `findings` table.
            *   `GET /actions`: Provides paginated read access to historical intended actions (from the `intended_actions` table). (Note: The Core Orchestrator version analyzed currently does not populate this table).
        *   **Devices (`routers/devices.py` - *assumed, not explicitly read*):** Likely provides CRUD for managing monitored devices.
        *   **Playbooks (`routers/playbooks.py` - *assumed, not explicitly read*):** Likely provides CRUD for managing playbook definitions.
        *   **Configuration (`routers/config.py` - *assumed, not explicitly read*):** Likely manages global system configurations (`opmas_config` table).
        *   **Control (`routers/control.py`):**
            *   Provides endpoints (`/start`, `/stop`, `/restart`, `/reload`) to manage the lifecycle of OPMAS backend components.
            *   These endpoints execute the main system script (`backend/start_opmas.sh`) to perform the requested actions. This is a direct involvement in runtime control of backend services.
            *   Control actions and their statuses are logged in the database.
        *   **System (`routers/system.py`):**
            *   `GET /status`: Reports the operational status of the Management API itself, including its connectivity to NATS and the database.
        *   **WebSocket (`api/v1/endpoints/websocket.py` - *assumed, not explicitly read*):** Likely provides WebSocket endpoints for real-time communication with the UI, possibly relaying live data received via NATS subscriptions (e.g., new findings, agent heartbeats).

*   **Database Interaction (PostgreSQL with SQLAlchemy):**
    *   **Shared Database Models:** The Management API directly utilizes the SQLAlchemy ORM models defined in the Core Backend's `backend/src/opmas/db_models.py` (e.g., `AgentModel`, `AgentRuleModel`, `FindingModel`). This ensures data consistency between the Core Backend and the Management API as they operate on the same database schema.
    *   **Session Management:** Database sessions are managed via FastAPI dependencies (`Depends(get_db)` from `db/session.py`), providing sessions to endpoint functions.
    *   **Pydantic Schemas:** Located in `management_api/src/opmas_mgmt_api/schemas/`, these Pydantic models are used for:
        *   Validating incoming request bodies.
        *   Serializing database ORM objects into JSON responses, often using `Config.from_attributes = True`.
    *   The API performs standard CRUD operations using SQLAlchemy against the shared PostgreSQL database.

*   **NATS Connectivity (`core/nats.py`):**
    *   The Management API maintains its own NATS connection via the `NATSManager` class.
    *   **Publishing:** It has the capability to publish messages to NATS. This could be used to send commands or notifications to Core Backend components (e.g., instructing an agent to reload its configuration after an update via the API).
    *   **Subscribing:** It can also subscribe to NATS topics. This would allow the Management API to receive real-time events from the Core Backend (e.g., live findings, agent status updates) and potentially relay these to the UI via WebSockets.

*   **Role as a Gateway and Service Controller:**
    *   **Data Management Gateway for UI:** It abstracts the database and backend complexities, offering a clean, versioned REST API for the UI to consume and manage system data.
    *   **Runtime Control:** Contrary to a purely passive data management role, the Management API, through its `control.py` router, actively participates in the runtime control of backend services by invoking the system's main start/stop/restart shell script. It also has endpoints that can influence running agent configurations, statuses, and topic subscriptions, implying a degree of dynamic interaction.

*   **Noteworthy Points & Potential Clarifications:**
    *   **Agent Rule Management:** The API provides CRUD for agent rules in the database. However, the `BaseAgent` in the Core Backend currently loads rules from YAML files/environment variables. This indicates either a transitional state, a future intent for database-driven rules for agents, or support for multiple rule sources. The Orchestrator loads agent *definitions* from the DB, but agents themselves don't currently fetch their *rules* from the DB.
    *   **Agent Status (`AgentStatus` field):** The API allows getting/setting agent status, including `last_heartbeat`. The precise mechanism by which a running agent's status is updated in the database for the API to read (e.g., agent direct DB update, or agent NATS heartbeat consumed by Management API) is an operational detail of the Core Backend and its interaction with the shared DB or NATS.
    *   **Dynamic Updates to Running Agents:** When agent configuration, rules (if DB-driven in future), or subscribed topics are changed via the API, the mechanism for how a *running* agent in the Core Backend picks up these changes needs to be well-defined (e.g., periodic polling of DB by agent, or Management API publishing a NATS message to specific agent channels to trigger a reload).
    *   **`IntendedAction` Records:** The API can read `intended_actions`. The Core Orchestrator needs to be updated to populate this table as per the original design intent for this data to be meaningful.
    *   **Shared Code/Packaging:** The direct import of `opmas.db.models` from the Core Backend's path into the Management API implies a tight coupling or a monorepo structure where these paths are resolvable. For separate deployments, this would require careful packaging.

*   **Technology Stack:** Python, FastAPI, SQLAlchemy, Pydantic, NATS (via `nats-py`), JWT for authentication.

## 5. Frontend UI Implementation (`ui/`)

*   **Purpose:** The Frontend UI provides a web-based graphical interface for users to interact with the OPMAS system. It allows for monitoring system status, managing configurations (agents, rules, playbooks), viewing operational results (findings, actions), and controlling backend services. It communicates exclusively with the Management API, ensuring a decoupled architecture.

*   **Main Technologies Used:**
    *   **React (v19):** The core JavaScript library for building the user interface.
    *   **TypeScript:** Used for static typing, enhancing code robustness and developer experience.
    *   **Vite:** Serves as the build tool and development server, providing a fast development experience.
    *   **React Router DOM (v7):** Handles client-side routing and navigation within the single-page application (SPA).
    *   **Axios:** Used for making HTTP requests from the UI to the Management API. A configured Axios instance (`apiClient.ts`) is used globally.
    *   **TanStack Query (React Query v5):** Manages server state, including data fetching, caching, synchronization, and updates. It simplifies data handling and provides features like loading states, error handling, and background updates.
    *   **Tailwind CSS:** A utility-first CSS framework used for styling the application, enabling rapid UI development.
    *   **Headless UI & Heroicons:** UI component libraries and icon sets, likely used in conjunction with Tailwind CSS.
    *   **React Hot Toast:** For displaying user-friendly toast notifications.

*   **Project Structure (`ui/src/`):**
    *   **`main.tsx`:** Application entry point, renders the root `App` component.
    *   **`App.tsx`:** Main application component; sets up global providers (Query, Auth, WebSocket), router, and defines top-level routes.
    *   **`api/apiClient.ts`:** Centralized Axios instance configuration for all Management API communication.
    *   **`components/`:** Contains reusable UI elements, categorized into `auth`, `layout`, `common`, `forms`, `modals`, `tables`, etc.
    *   **`pages/`:** Top-level components representing distinct views or pages (e.g., `Login.tsx`, `Dashboard.tsx`, `AgentsPage.tsx`, `Findings.tsx`).
    *   **`services/`:** Contains modules (`api.ts`, `auth.ts`) that encapsulate API call logic, using the configured `apiClient`.
    *   **`providers/` & `context/`:**
        *   `AuthProvider.tsx`: Manages authentication state (user identity, token) and provides login/logout functionalities using React Context.
        *   `QueryProvider.tsx`: Configures and provides the TanStack Query client.
        *   `WebSocketContext.tsx`: Manages WebSocket connections for real-time features.
    *   **`hooks/`:** Intended for custom React hooks.
    *   **`types/`:** TypeScript type definitions for UI-specific data structures and API payloads.

*   **API Communication (`api/apiClient.ts`):**
    *   A global Axios instance (`apiClient`) is configured to interact with the Management API.
    *   **Base URL:** Determined by the `VITE_API_URL` environment variable, defaulting to `http://192.168.10.8:8000` (the likely address of the Management API).
    *   **Request Interceptor:** Automatically attaches the JWT token (retrieved from `localStorage`) to the `Authorization` header (`Bearer ${token}`) of outgoing requests.
    *   **Response Interceptor:** Provides global error handling. Specifically, if a 401 (Unauthorized) response is received from the API, it clears the stored token and redirects the user to the `/login` page.
    *   `withCredentials` is set to `false` as authentication is token-based.

*   **Authentication State Management (`providers/AuthProvider.tsx`):**
    *   `AuthContext` provides authentication status (`isAuthenticated`, `user` object) and methods (`login`, `logout`) throughout the application.
    *   The JWT token received upon successful login is stored in `localStorage`.
    *   On application load, `AuthProvider` attempts to validate any existing token by fetching the user's profile from the Management API (`/api/v1/auth/me`).
    *   The `login` method sends credentials to the Management API's `/api/v1/auth/login` endpoint and, upon success, stores the token and user data.
    *   The `logout` method clears the token from `localStorage` and resets the authentication state.

*   **Routing (`App.tsx`, `components/auth/ProtectedRoute.tsx`):**
    *   Client-side routing is handled by `react-router-dom`.
    *   `App.tsx` defines public routes (e.g., `/login`) and protected routes.
    *   `ProtectedRoute` is a higher-order component that checks the `isAuthenticated` state from `AuthContext`. If the user is not authenticated, they are redirected to `/login`, preserving the intended destination for redirection after successful login. Authenticated users are allowed access to the wrapped routes (e.g., dashboard, configuration pages).

*   **State Management & Real-time Features:**
    *   **TanStack Query:** Used extensively for managing server state. Components use hooks like `useQuery` to fetch data from the Management API (as seen in `Dashboard.tsx`). This handles caching, background updates, loading states, and error states for data displayed in the UI.
    *   **WebSocketProvider (`context/WebSocketContext.tsx`):**
        *   Establishes and manages a WebSocket connection to the Management API (endpoint `/api/v1/ws/system`, authenticated with the JWT token).
        *   This enables real-time communication from the backend to the UI, likely used for features such as live status updates, notifications on new findings, or agent heartbeats. The `VITE_ENABLE_WEBSOCKET` environment variable controls its activation.

*   **Interaction with Management API:**
    *   **Data Display & Management:** The UI fetches and displays data by making GET requests to various Management API endpoints (e.g., for dashboard statistics, lists of agents, findings, actions, rules, playbooks, configurations). It uses forms and modals to send POST, PUT, and DELETE requests to create, update, or delete these entities.
    *   **System Control:** Through dedicated UI elements (e.g., buttons in a system control panel), the UI can trigger calls to the Management API's control endpoints (e.g., `/api/v1/control/start`, `/api/v1/control/stop`) to manage the lifecycle of the OPMAS backend services.
    *   All interactions are funneled through the `apiClient`, ensuring consistent token handling and error management. TanStack Query optimizes data fetching and state synchronization.

*   **User Experience:**
    *   Utilizes `react-hot-toast` for non-intrusive notifications (e.g., success/error messages for API operations).
    *   Loading states and error states managed by TanStack Query provide feedback to the user during data fetching operations.
    *   Responsive design is expected due to the use of Tailwind CSS.

## 6. Shared Services & Infrastructure Implementation Details

This section details the key shared services (PostgreSQL, NATS, Redis) and the Docker infrastructure used by OPMAS.

### 6.1. PostgreSQL Database

*   **Role:** PostgreSQL serves as the primary persistent data store for OPMAS. It holds system configurations, agent definitions, operational data like findings, and (in future iterations) playbook logic and intended actions. Both the Core Backend and the Management API interact with this database.
*   **Application Interaction & ORM:**
    *   The primary method of database interaction for both Core Backend and Management API is via SQLAlchemy, using ORM (Object Relational Mapper) models.
    *   The definitive ORM models are defined in `backend/src/opmas/db/models.py`. These include:
        *   `OpmasConfig`: For storing general key-value system configurations.
        *   `Agent`: Defines agent properties, including their module path and enabled status. Used by the Orchestrator to load agents.
        *   `AgentRule`: Stores rules for specific agents, with rule configurations in JSONB. (Note: Current `BaseAgent` loads rules from YAML/env; database-driven rules are a potential future enhancement or alternative loading mechanism supported by the Management API).
        *   `Playbook` & `PlaybookStep`: Define playbook structures and their individual steps, including action types and configurations.
        *   `Finding`: Stores detailed records of issues detected by agents.
        *   `IntendedAction`: Designed to log actions the Orchestrator plans to execute based on findings/playbooks (currently not populated by the Core Orchestrator).
    *   These models define tables, columns, relationships (with cascades), and constraints.
*   **Schema Context:**
    *   `docs/architecture/DATABASE_SCHEMA.md` provides additional context with raw SQL DDL statements, details on indexing, constraints, and considerations for maintenance and security.
    *   Minor discrepancies exist between the ORM model definitions (e.g., table/column naming like `agent_id` vs `id`, specific timestamp column names) and the `DATABASE_SCHEMA.md`. The ORM models in `backend/src/opmas/db/models.py` are the source of truth for application-level database interaction.
    *   The `DATABASE_SCHEMA.md` also describes tables like `devices` and `ssh_keys` which are not in `backend/src/opmas/db/models.py` and are likely used primarily by the Management API or other system aspects.
*   **Deployment:** PostgreSQL is typically deployed as a Docker container, managed by Docker Compose (see Docker Setup section).

### 6.2. NATS Messaging
*   **Role:** NATS is a high-performance messaging system that acts as the central communication bus for the OPMAS Core Backend. It enables asynchronous communication and decouples various components.
*   **Core Backend Usage:**
    *   **Log Event Ingestion:** Log ingestion components (HTTP API, potential UDP/TCP Syslog ingestors) publish `ParsedLogEvent` messages to NATS topics (e.g., `logs.wifi`, `logs.security`, `logs.generic`, or `logs.parsed.raw` for further processing).
    *   **Agent Subscriptions:** Agents subscribe to relevant NATS topics to receive `ParsedLogEvent` messages.
    *   **Finding Publication:** Agents publish `AgentFinding` messages to agent-specific NATS topics (e.g., `findings.wifi`).
    *   **Orchestrator Subscriptions:** The Orchestrator subscribes to all finding topics (`findings.>`) to process them.
    *   NATS client utilities are found in `backend/src/opmas/utils/mq.py`. The NATS server URL is typically `nats://localhost:4222` in development.
*   **Management API Usage:**
    *   The Management API also connects to NATS (see `management_api/src/opmas_mgmt_api/core/nats.py`).
    *   It can publish messages, potentially to send commands or notifications to Core Backend components (e.g., an agent needing to reload its rules or change its status).
    *   It can subscribe to NATS topics to receive real-time updates from the Core Backend (e.g., live findings, agent heartbeats), which can then be relayed to the UI via WebSockets.
*   **Deployment:** NATS is deployed as a Docker container, managed by Docker Compose, typically exposing client port 4222 and HTTP monitoring port 8222.

### 6.3. Redis
*   **Role:** Redis is an in-memory data structure store, typically used for caching and other speed-critical operations.
*   **Usage in OPMAS:**
    *   Redis is included as a service in the root `docker-compose.yaml`, suggesting it's available for use by the system.
    *   While the reviewed Core Backend and Management API Python code does not show explicit direct integration for their primary data flows, Redis is commonly used for:
        *   **Caching:** Reducing database load by caching frequently accessed data (e.g., user sessions for the Management API, results of expensive queries, or configuration data).
        *   **Rate Limiting:** The Management API could leverage Redis to implement request rate limiting.
        *   **Short-lived State:** Potentially for managing temporary state related to WebSocket connections or other real-time interactions, if not handled by other means.
    *   The `core` service in the root `docker-compose.yaml` lists `redis` in its `depends_on` section.
*   **Deployment:** Redis is deployed as a Docker container, managed by the root `docker-compose.yaml`, with data persistence enabled via AOF (Append Only File).

### 6.4. Docker Setup

OPMAS utilizes Docker and Docker Compose for containerizing its services and managing the development environment.

*   **Root `docker-compose.yaml`:**
    *   **Purpose:** Defines a comprehensive, multi-container environment for full-stack development and integration testing.
    *   **Services Included:**
        *   `core`: Builds and runs the Core Backend application (Note: build context is listed as `./core`, which might be a placeholder for the actual `backend/` directory). Depends on `nats`, `postgres`, and `redis`.
        *   `management_api`: Builds and runs the Management API. Exposes port 8000. Depends on `core`.
        *   `ui`: Builds and runs the Frontend UI. Exposes port 3000. Depends on `management_api`.
        *   `nats`: NATS message broker service.
        *   `postgres`: PostgreSQL database service. Uses `POSTGRES_USER=opmas`, `POSTGRES_PASSWORD=opmas`, `POSTGRES_DB=opmas`.
        *   `redis`: Redis caching service.
        *   `prometheus`: Prometheus monitoring service, configured via `config/prometheus/prometheus.yml`.
        *   `grafana`: Grafana dashboard service, depends on Prometheus.
    *   **Networking:** All services are connected via a custom bridge network (`opmas_network`).
    *   **Volumes:** Named volumes are used for persistent storage for PostgreSQL, Redis, Prometheus, and Grafana.
    *   **Discrepancy:** The `core` service build context (`./core`) in this file needs to match the actual project structure (likely `backend/`).

*   **`backend/docker-compose.yaml`:**
    *   **Purpose:** This file is specifically used by the `backend/start_opmas.sh` script to quickly stand up NATS and PostgreSQL services when running the Core Backend Python components directly on the host machine (i.e., not containerized themselves).
    *   **Services Included:**
        *   `nats`: NATS message broker service.
        *   `postgres`: PostgreSQL database service. Uses different credentials (`POSTGRES_USER=opmas_user`, `POSTGRES_PASSWORD=opmas_password`, `POSTGRES_DB=opmas_db`) compared to the root compose file. Port 5432 is mapped only to `127.0.0.1` on the host.
    *   **Discrepancy:** The database credentials and names differ between this file and the root `docker-compose.yaml`. The Core Backend configuration (`opmas_config.yaml`) must align with the credentials used by the compose file that launches its database.

*   **Dockerfiles:**
    *   Individual Dockerfiles (`backend/Dockerfile`, `management_api/Dockerfile`, `ui/Dockerfile`) define how the images for the Core Backend, Management API, and UI applications are built, respectively. These are referenced by the root `docker-compose.yaml`.

## 7. High-Level Interaction Flow Diagram

```mermaid
graph LR
    subgraph User Browser
        UI[Frontend UI (React)]
    end

    subgraph OPMAS System
        subgraph Management API Server
            MgmtAPI[Management API (FastAPI)]
        end

        subgraph Core Backend Services
            LogAPI[Log API (FastAPI)]
            Parser[Log Parser]
            NATS[(NATS Message Bus)]
            AgentWifi[WiFi Agent]
            AgentOther[Other Agents]
            Orchestrator[Orchestrator]
        end

        subgraph Database Server
           DB[(PostgreSQL)]
        end
    end

    subgraph External
        Device[Network Device]
    end

    Device -- Syslog --> LogAPI;
    LogAPI -- Raw Log Event --> NATS;
    Parser -- Consumes --> NATS;
    Parser -- ParsedLogEvent --> NATS;
    AgentWifi -- Subscribes --> NATS;
    AgentOther -- Subscribes --> NATS;
    AgentWifi -- AgentFinding --> NATS;
    AgentOther -- AgentFinding --> NATS;
    Orchestrator -- Subscribes --> NATS;

    AgentWifi -- Reads Rules --> DB;
    AgentOther -- Reads Rules --> DB;
    Orchestrator -- Reads Playbooks --> DB;
    Orchestrator -- Writes Finding --> DB;
    Orchestrator -- Writes IntendedAction --> DB;

    UI -- HTTP API Calls --> MgmtAPI;
    MgmtAPI -- Reads/Writes Config/Results --> DB;
    MgmtAPI -- Controls Processes --> Core Backend Services;
```

*(Note: Log API to Parser interaction might be via NATS or an internal queue depending on final implementation details)*

## 8. Action Executor (`core/src/opmas/action_executor.py`)

* **Purpose:** Securely executes commands on target OpenWRT devices based on commands received from the Orchestrator.
* **Key Components:**
    * `ActionExecutor`: Main class handling command execution
    * `SSHManager`: Manages SSH connections and key handling
    * `CommandValidator`: Validates and sanitizes commands
* **Implementation Details:**
    * **SSH Key Management:**
        * SSH keys stored in `core/config/ssh_keys/` (encrypted)
        * Key rotation and access control via Management API
        * Limited privilege SSH user on OpenWRT devices
    * **Command Validation:**
        * Allowlist of permitted commands in database
        * Command sanitization and parameter validation
        * Timeout handling and error recovery
    * **NATS Topics:**
        * Subscribes to `actions.execute` for new commands
        * Publishes results to `actions.results`
* **Security Measures:**
    * Command validation against allowlist
    * Input sanitization
    * Connection timeouts
    * Error logging and monitoring
    * Audit trail of executed commands

## 9. Knowledge Base Implementation

* **Purpose:** Centralized storage and management of system configuration, rules, and state.
* **Implementation:**
    * **Database Tables:**
        * `opmas_config`: System-wide configuration
        * `agents`: Agent definitions and settings
        * `agent_rules`: Rules for each agent
        * `playbooks`: Action playbooks
        * `playbook_steps`: Steps within playbooks
        * `findings`: Detected issues
        * `intended_actions`: Planned actions
        * `device_inventory`: OpenWRT device information
        * `ssh_keys`: Encrypted SSH key storage
    * **Configuration Management:**
        * Initial configuration via YAML/JSON files
        * Migration to database via `scripts/migrate_config_to_db.py`
        * Runtime configuration updates via Management API
    * **Access Control:**
        * Read-only access for agents
        * Read-write access for Orchestrator
        * Administrative access via Management API

## 10. Log Forwarder Implementation

* **Purpose:** Configure and manage log forwarding from OpenWRT devices.
* **Implementation:**
    * **OpenWRT Configuration:**
        * Syslog daemon configuration (logd or syslog-ng)
        * Remote server settings (IP, port, protocol)
        * Log facility selection
    * **Transport Security:**
        * TLS encryption for syslog transport
        * Authentication via certificates
        * Rate limiting and buffering
    * **Management:**
        * Configuration via Management API
        * Status monitoring
        * Error reporting

## 11. Error Handling and Recovery

* **Purpose:** Ensure system reliability and graceful failure handling.
* **Implementation:**
    * **Component Restartability:**
        * State persistence in database
        * Graceful shutdown handling
        * Automatic restart via systemd or Docker
    * **Error Recovery:**
        * Retry mechanisms for failed operations
        * Circuit breakers for external services
        * Fallback strategies
    * **Monitoring:**
        * Health checks for all components
        * Error rate tracking
        * Performance metrics
    * **Logging:**
        * Structured logging (JSON format)
        * Log levels and filtering
        * Log rotation and retention
        * Centralized log collection

## 12. System Monitoring

* **Purpose:** Monitor system health and performance.
* **Implementation:**
    * **Component Health:**
        * Process status monitoring
        * Resource usage tracking
        * Connection state monitoring
    * **Performance Metrics:**
        * Message processing rates
        * Database query performance
        * Action execution times
    * **Alerting:**
        * Threshold-based alerts
        * Anomaly detection
        * Notification channels
    * **Dashboard:**
        * Real-time status display
        * Historical trends
        * System configuration view

## 13. Integration Points and Dependencies

### 13.1. Core Backend Integration

* **Action Executor Integration:**
    * Orchestrator publishes to `actions.execute` topic
    * Action Executor subscribes to `actions.execute` and publishes to `actions.results`
    * Management API can query action history from database
    * SSH key management integrated with Management API's security features

* **Knowledge Base Integration:**
    * All components access configuration through database
    * Agents load rules on startup and cache them
    * Orchestrator loads playbooks on startup
    * Management API provides CRUD operations for all KB tables

* **Log Forwarder Integration:**
    * Log API receives forwarded logs
    * Management API configures forwarder settings
    * Device inventory tracks configured forwarders
    * Health monitoring includes forwarder status

### 13.2. Management API Integration

* **Configuration Management:**
    * CRUD operations for all KB tables
    * SSH key management interface
    * Log forwarder configuration
    * System-wide settings management

* **Monitoring Integration:**
    * Exposes health check endpoints
    * Provides performance metrics
    * Manages alerting configuration
    * Dashboard data endpoints

### 13.3. Frontend UI Integration

* **Action Management:**
    * View action history
    * Monitor action execution
    * Configure action allowlists
    * Manage SSH keys

* **Configuration Interface:**
    * Edit agent rules
    * Manage playbooks
    * Configure log forwarders
    * System settings

* **Monitoring Dashboard:**
    * Real-time system status
    * Performance metrics
    * Alert management
    * Log viewer

## 14. Security Implementation

* **Authentication & Authorization:**
    * JWT-based authentication for Management API
    * Role-based access control
    * SSH key management
    * API key management for external integrations

* **Data Security:**
    * Encrypted storage for sensitive data
    * TLS for all network communications
    * Secure credential management
    * Audit logging

* **Network Security:**
    * Firewall rules for component communication
    * Rate limiting
    * IP allowlisting
    * TLS certificate management

## 15. Deployment and Operations

* **Deployment Options:**
    * Docker Compose for development
    * Kubernetes for production
    * Systemd services for traditional deployment
    * Hybrid deployment support

* **Configuration Management:**
    * Environment-based configuration
    * Secret management
    * Configuration validation
    * Version control for configurations

* **Backup and Recovery:**
    * Database backup procedures
    * Configuration backup
    * Disaster recovery plans
    * State recovery procedures

* **Scaling Considerations:**
    * Horizontal scaling of components
    * Database scaling
    * Message queue scaling
    * Load balancing

## 16. Development and Testing

* **Development Environment:**
    * Local development setup
    * Testing environment
    * CI/CD pipeline
    * Code quality tools

* **Testing Strategy:**
    * Unit testing
    * Integration testing
    * End-to-end testing
    * Performance testing

* **Monitoring and Debugging:**
    * Development logging
    * Debug tools
    * Performance profiling
    * Error tracking

## 17. Component-Specific Implementation Details

### 17.1 Core Backend Implementation

#### 17.1.1 Log Processing Pipeline
1. **Log Ingestion**
   - HTTP endpoint for receiving logs
   - NATS message publishing
   - Log validation and sanitization
   - Rate limiting and buffering

2. **Log Parsing**
   - Structured log parsing
   - Log classification
   - Field extraction
   - Error handling

3. **Agent Processing**
   - Rule evaluation
   - Pattern matching
   - State management
   - Finding generation

4. **Orchestration**
   - Playbook selection
   - Action determination
   - State tracking
   - Error recovery

#### 17.1.2 Agent System
1. **Base Agent**
   - Common functionality
   - Rule management
   - State handling
   - Error recovery

2. **Domain Agents**
   - WiFi Agent
   - Security Agent
   - Health Agent
   - WAN Agent

3. **Agent Communication**
   - NATS topics
   - Message formats
   - Error handling
   - State synchronization

### 17.2 Management API Implementation

#### 17.2.1 API Structure
1. **Authentication**
   - JWT-based auth
   - Role management
   - Session handling
   - Security measures

2. **Endpoints**
   - Device management
   - Agent configuration
   - Rule management
   - Playbook control

3. **Data Access**
   - Database models
   - Query optimization
   - Caching strategy
   - Error handling

#### 17.2.2 Security Implementation
1. **Authentication**
   - JWT token management
   - Password hashing
   - Session control
   - Token refresh

2. **Authorization**
   - Role-based access
   - Permission checking
   - Resource protection
   - Audit logging

### 17.3 Frontend UI Implementation

#### 17.3.1 Component Architecture
1. **Core Components**
   - Layout components
   - Form components
   - Table components
   - Modal components

2. **Page Components**
   - Dashboard
   - Device management
   - Agent configuration
   - Rule management

3. **State Management**
   - Redux store
   - Action creators
   - Reducers
   - Middleware

#### 17.3.2 UI/UX Implementation
1. **Design System**
   - Component library
   - Theme system
   - Responsive design
   - Accessibility

2. **User Experience**
   - Loading states
   - Error handling
   - Form validation
   - Feedback mechanisms

## 18. Development Workflow

### 18.1 Version Control
1. **Branch Strategy**
   - Feature branches
   - Release branches
   - Hotfix branches
   - Integration branches

2. **Commit Guidelines**
   - Conventional commits
   - Component prefixes
   - Message format
   - Review process

### 18.2 Testing Strategy
1. **Unit Testing**
   - Component tests
   - Service tests
   - Utility tests
   - Model tests

2. **Integration Testing**
   - API tests
   - Database tests
   - Message queue tests
   - End-to-end tests

3. **Performance Testing**
   - Load testing
   - Stress testing
   - Benchmarking
   - Profiling

### 18.3 Documentation
1. **Code Documentation**
   - API documentation
   - Component documentation
   - Architecture documentation
   - Setup guides

2. **User Documentation**
   - User guides
   - Admin guides
   - Troubleshooting guides
   - API reference

## 19. Deployment Strategy

### 19.1 Development Environment
1. **Local Setup**
   - Docker Compose
   - Development tools
   - Testing environment
   - Debugging tools

2. **CI/CD Pipeline**
   - Build process
   - Test automation
   - Deployment automation
   - Monitoring setup

### 19.2 Production Environment
1. **Infrastructure**
   - Kubernetes cluster
   - Database setup
   - Message queue setup
   - Monitoring setup

2. **Deployment Process**
   - Container builds
   - Database migrations
   - Configuration management
   - Health checks

## 20. Monitoring and Maintenance

### 20.1 System Monitoring
1. **Metrics Collection**
   - Performance metrics
   - Resource usage
   - Error rates
   - Response times

2. **Alerting**
   - Threshold alerts
   - Anomaly detection
   - Notification channels
   - Escalation paths

### 20.2 Maintenance Procedures
1. **Regular Maintenance**
   - Database maintenance
   - Log rotation
   - Backup verification
   - Security updates

2. **Emergency Procedures**
   - Incident response
   - System recovery
   - Data restoration
   - Communication plan

## Related Documents

- [OPMAS-DS.md](../specifications/OPMAS-DS.md): Main design specification
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md): Database schema and data models
- [DEVELOPMENT_SETUP.md](../guides/DEVELOPMENT_SETUP.md): Development environment setup
- [API_DOCUMENTATION.md](../api/API_DOCUMENTATION.md): API reference
