# OPMAS Core Backend Design Specification (OPMAS-Backend-DS)

## 1. Introduction

This document outlines the design for the core backend components of the OpenWRT Proactive Monitoring Agentic System (OPMAS). The core backend is responsible for log ingestion, parsing, analysis via specialized agents, and orchestration of responses based on playbooks. It utilizes a PostgreSQL database for configuration and results storage, with NATS as the message bus for component communication.

## 2. Goals

* Implement a modular, agent-based system for OpenWRT log analysis
* Provide real-time log processing and analysis
* Enable proactive detection of issues and anomalies
* Support rule-based analysis with future AI/ML integration
* Utilize database-driven configuration and results storage
* Ensure secure and reliable operation

## 3. Core Components

### 3.1. Database Models (`src/opmas/models/`)

* **Purpose:** Define data structures and relationships
* **Implementation:**
  * Base model with TimestampMixin for created_at/updated_at
  * LogEntry model for log storage
  * Agent model with type and status enums
  * Relationships and indexes for efficient querying
  * Comprehensive test suite

### 3.2. Log API (`src/opmas/api/log_api.py`)

* **Purpose:** Receive and process incoming logs from OpenWRT devices
* **Implementation:**
  * FastAPI application serving HTTP endpoint (`/api/v1/logs`)
  * Handles log batching and validation
  * Publishes raw logs to NATS topic `logs.raw`
  * Supports both UDP and TCP syslog reception
  * Adds metadata (arrival timestamp, source IP)

### 3.3. Log Parser (`src/opmas/parser/`)

* **Purpose:** Parse and structure raw log messages
* **Implementation:**
  * Subscribes to `logs.raw` NATS topic
  * Parses syslog messages into structured format
  * Classifies logs by source type (wifi, security, health, connectivity)
  * Publishes structured logs to domain-specific topics
  * Enriches logs with additional metadata

### 3.4. Domain Agents (`src/opmas/agents/`)

* **Purpose:** Analyze logs and detect issues
* **Implementation:**
  * Base agent class with common functionality
  * Specialized agents for different domains:
    * WiFi Agent (AgentType.WIFI)
    * Network Security Agent (AgentType.SECURITY)
    * Device Health Agent (AgentType.HEALTH)
    * WAN/Connectivity Agent (AgentType.WAN)
  * Rule-based analysis with future ML integration
  * Publishes findings to NATS

### 3.5. Orchestrator (`src/opmas/orchestrator.py`)

* **Purpose:** Correlate findings and determine actions
* **Implementation:**
  * Subscribes to all findings topics
  * Consults playbooks from database
  * Correlates related findings
  * Determines appropriate actions
  * Records findings and intended actions in database

### 3.6. Database Integration (`src/opmas/db/`)

* **Purpose:** Store configuration and results
* **Implementation:**
  * SQLAlchemy ORM models
  * Database session management
  * Configuration loading utilities
  * Results storage and retrieval

## 4. Data Flow

1. OpenWRT Device → Log API (HTTP)
2. Log API → NATS (`logs.raw`)
3. Log Parser → NATS (domain-specific topics)
4. Domain Agents → NATS (`findings.<domain>`)
5. Orchestrator → Database (findings, intended actions)

## 5. Database Schema

### 5.1. Core Models

* `LogEntry`: Stores log entries with metadata
  * id: Integer (Primary Key)
  * source: String (indexed)
  * level: String (indexed)
  * message: String
  * metadata: JSON
  * correlation_id: String (indexed)
  * created_at: DateTime
  * updated_at: DateTime

* `Agent`: Manages different types of agents
  * id: Integer (Primary Key)
  * name: String (unique, indexed)
  * type: Enum(AgentType) (indexed)
  * status: Enum(AgentStatus) (indexed)
  * configuration: JSON
  * last_heartbeat: String
  * created_at: DateTime
  * updated_at: DateTime

### 5.2. Enums

* `AgentType`:
  * WIFI
  * SECURITY
  * HEALTH
  * WAN

* `AgentStatus`:
  * ACTIVE
  * INACTIVE
  * ERROR
  * MAINTENANCE

## 6. Testing Framework

### 6.1. Test Configuration (`tests/conftest.py`)

* Database fixtures
  * Test database engine
  * Session management
  * Transaction handling
* Test data fixtures
  * Test agent
  * Test log entry
* Configuration fixtures
  * Database config
  * Logging config

### 6.2. Test Structure

* Unit tests for models
* Integration tests for workflows
* Performance tests
* Security tests

## 7. Message Formats

### 7.1. Parsed Log Event

```json
{
  "event_id": "uuid-...",
  "arrival_ts_utc": "2025-04-18T22:02:18.123Z",
  "source_ip": "192.168.1.1",
  "original_ts": "Apr 18 15:02:17",
  "hostname": "OpenWRT-Router1",
  "process_name": "hostapd",
  "pid": "1234",
  "log_level": "INFO",
  "message": "wlan0: STA aa:bb:cc:dd:ee:ff IEEE 802.11: authenticated",
  "parser_name": "hostapd_parser_v1",
  "log_source_type": "wifi",
  "structured_fields": {
    "interface": "wlan0",
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "event": "auth_success"
  }
}
```

### 7.2. Agent Finding

```json
{
  "finding_id": "uuid-...",
  "agent_name": "WiFiAgent",
  "finding_ts_utc": "2025-04-18T22:05:00.000Z",
  "device_hostname": "OpenWRT-Router1",
  "device_ip": "192.168.1.1",
  "severity": "Warning",
  "finding_type": "HighAuthFailureRate",
  "description": "High rate of authentication failures for client aa:bb:cc:dd:ee:ff on wlan0",
  "details": {
    "interface": "wlan0",
    "client_mac": "aa:bb:cc:dd:ee:ff",
    "failure_count": 25,
    "time_window_seconds": 60
  },
  "evidence_event_ids": ["uuid-...", "uuid-..."]
}
```

## 8. Configuration Management

* Bootstrap configuration in `config/opmas_config.yaml`
* Database-driven configuration for:
  * Agent rules
  * Playbooks
  * System settings
* Configuration migration from YAML to database

## 9. Security Considerations

* Secure log transport (TLS for syslog)
* Database access control
* NATS security
* Input validation and sanitization
* Error handling and logging

## 10. Error Handling

* Graceful component restart
* Error recovery mechanisms
* Circuit breakers for external services
* Comprehensive logging
* Health monitoring

## 11. Performance Considerations

* Asynchronous processing
* Connection pooling
* Message batching
* Database indexing
* Resource monitoring

## 12. Testing Strategy

* Unit tests for components
* Integration tests for workflows
* Performance testing
* Security testing
* Error handling validation

## 13. Deployment

* Docker Compose for development
* Kubernetes for production
* Systemd services for traditional deployment
* Configuration via environment variables

## 14. Monitoring

* Component health checks
* Performance metrics
* Error rate tracking
* Resource usage monitoring
* Log aggregation

## 15. Future Enhancements

* AI/ML model integration
* Advanced correlation rules
* Extended agent capabilities
* Enhanced monitoring
* Automated recovery actions 