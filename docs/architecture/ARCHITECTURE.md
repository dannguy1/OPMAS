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

## 3. Core Backend (`core/`)

*   **Purpose:** Responsible for ingesting logs, parsing them, analyzing them against rules defined in the database using specialized agents, publishing findings, and orchestrating responses based on playbooks stored in the database. It reads its dynamic configuration (rules, playbooks) from PostgreSQL and writes operational results (findings, intended actions) back to it.
*   **Key Components:**
    *   `src/opmas/log_api.py`: A FastAPI application serving an HTTP endpoint (e.g., `/api/v1/logs`) to receive log batches. It enqueues received logs (or publishes directly to NATS).
    *   `src/opmas/log_parser.py` / `parsing_utils.py`: Logic responsible for parsing raw log messages (dequeued or received from NATS), classifying them by source type (e.g., 'wifi', 'security'), and publishing structured `ParsedLogEvent` messages to corresponding NATS topics (e.g., `logs.wifi`).
    *   `src/opmas/agents/`: Contains the `BaseAgent` and specific domain agents (e.g., `WiFiAgent`). Agents subscribe to relevant `logs.<type>` topics on NATS. On startup, they query the database (using `db_utils`) to load their configuration and rules (`agents`, `agent_rules` tables). Upon detecting issues based on their rules, they publish `AgentFinding` messages to NATS (e.g., `findings.wifi`).
    *   `src/opmas/orchestrator.py`: Subscribes to all findings topics (`findings.>`) on NATS. On startup, it queries the database to load all playbooks and their steps (`playbooks`, `playbook_steps` tables). When a finding is received, it writes the finding details to the `findings` table in the database. It then consults the loaded playbooks, determines the appropriate action(s) based on the finding type, and writes the details of these *intended* actions to the `intended_actions` table in the database. (Note: Action execution is currently out of scope).
    *   `src/opmas/db_models.py`: Defines the SQLAlchemy ORM models mapping Python classes to the PostgreSQL database tables (`opmas_config`, `agents`, `agent_rules`, `playbooks`, `playbook_steps`, `findings`, `intended_actions`).
    *   `src/opmas/db_utils.py`: Provides utilities for creating the SQLAlchemy engine and managing database sessions (e.g., `get_db_session`).
    *   `src/opmas/config.py`: Loads the bootstrap configuration (NATS URL, Database connection string) from `core/config/opmas_config.yaml`.
    *   `scripts/`: Contains utility scripts like `init_db.py` (to create the DB schema) and `migrate_config_to_db.py` (to populate the DB with initial agent/rule/playbook definitions).
    *   `start_opmas.sh`: Script located within `core/` to start/stop the Python components (API, Orchestrator, Agents) and manage the NATS/PostgreSQL Docker containers via `core/docker-compose.yaml`.
*   **Interactions:**
    *   Receives logs via HTTP (Log API).
    *   Uses NATS extensively for internal asynchronous messaging (`ParsedLogEvent`, `AgentFinding`).
    *   Reads configuration (agents, rules, playbooks) from PostgreSQL.
    *   Writes results (findings, intended_actions) to PostgreSQL.
*   **Technology:** Python, AsyncIO, FastAPI, NATS (via `nats-py`), PostgreSQL (via SQLAlchemy), Pydantic.

## 4. Management API (`management_api/`)

*   **Purpose:** Provides a secure RESTful API for the Frontend UI. It acts as the sole gateway for the UI to interact with the system's configuration and view historical results stored in the database. It decouples the UI from the internal workings and data storage of the core backend.
*   **Key Components:**
    *   `src/opmas_mgmt_api/`: FastAPI application code.
    *   **Endpoints:** Exposes endpoints for:
        *   Reading system status and configuration
        *   CRUD operations for `agents`, `agent_rules`, `playbooks`, `playbook_steps` tables in the database
        *   Reading (with filtering/pagination) from `findings` and `intended_actions` tables
        *   Reading/Updating `opmas_config` table entries
        *   All list endpoints support:
            * Search functionality (filtering by name/description)
            * Sorting by any column
            * Pagination (skip/limit)
            * Direction control (asc/desc)
    *   **Common Features:**
        *   Consistent response format with pagination metadata
        *   Standardized error handling
        *   Input validation using Pydantic models
        *   Type safety with Python type hints
*   **Interactions:**
    *   Communicates with the Frontend UI via HTTP/REST
    *   Interacts directly with the PostgreSQL database using SQLAlchemy
    *   Uses dependency injection for database and NATS manager instances
*   **Technology:** Python, FastAPI, PostgreSQL (via SQLAlchemy), Pydantic, NATS (for event publishing)

## 5. Frontend UI (`ui/`)

*   **Purpose:** Presents a graphical interface to the user, allowing them to monitor OPMAS, manage configurations, and view results by interacting with the Management API.
*   **Key Components:**
    *   A single-page application (SPA) built with React and TypeScript
    *   Components for different views:
        *   Dashboard: System overview and metrics
        *   Rules: Rule management with search and sort
        *   Systems: System configuration management
        *   Agents: Agent management and monitoring
        *   Devices: Device inventory and status
        *   Findings: View and filter findings
        *   Playbooks: Playbook management
    *   Common UI Features:
        *   Search functionality across all list views
        *   Sortable columns with direction control
        *   Pagination controls
        *   Consistent layout with sidebar navigation
        *   Responsive design
    *   Uses Axios for HTTP requests to the Management API
*   **Interactions:**
    *   Sends HTTP requests to the Management API (`/api/...` endpoints)
    *   Renders data received from the API for the user
    *   Does **not** interact directly with the database, NATS, or the core backend components
*   **Technology:** React, TypeScript, Tailwind CSS, Axios, React Router

## 6. Shared Services (`core/docker-compose.yaml`)

*   **NATS:** High-performance message broker used for asynchronous communication between components in the Core Backend.
*   **PostgreSQL:** Relational database serving as the central store for all configuration data and operational results (findings, intended actions).

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
