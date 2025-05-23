# OPMAS System Overview

## High-Level Architecture

```mermaid
graph TB
    subgraph "OpenWRT Devices"
        Device1[OpenWRT Device 1]
        Device2[OpenWRT Device 2]
        DeviceN[OpenWRT Device N]
    end

    subgraph "OPMAS Core"
        LogAPI[Log Ingestion API]
        Parser[Log Parser]
        subgraph "Domain Agents"
            WiFiAgent[WiFi Agent]
            SecurityAgent[Security Agent]
            HealthAgent[Health Agent]
            WANAgent[WAN Agent]
        end
        Orch[Orchestrator]
        Exec[Action Executor]
    end

    subgraph "Management Layer"
        MgmtAPI[Management API]
        Frontend[Frontend UI]
    end

    subgraph "Data Storage"
        DB[(PostgreSQL)]
        NATS[(NATS Message Bus)]
    end

    subgraph "Testing Framework"
        UnitTests[Unit Tests]
        IntegrationTests[Integration Tests]
        TestDB[(Test Database)]
    end

    %% Core Connections
    Device1 -->|Syslog| LogAPI
    Device2 -->|Syslog| LogAPI
    DeviceN -->|Syslog| LogAPI
    LogAPI -->|Raw Logs| Parser
    Parser -->|Parsed Logs| NATS
    NATS -->|Filtered Logs| WiFiAgent
    NATS -->|Filtered Logs| SecurityAgent
    NATS -->|Filtered Logs| HealthAgent
    NATS -->|Filtered Logs| WANAgent
    WiFiAgent -->|Findings| NATS
    SecurityAgent -->|Findings| NATS
    HealthAgent -->|Findings| NATS
    WANAgent -->|Findings| NATS
    NATS -->|Findings| Orch
    Orch -->|Actions| Exec
    Exec -->|Commands| Device1
    Exec -->|Commands| Device2
    Exec -->|Commands| DeviceN

    %% Storage Connections
    Orch -->|Findings| DB
    Exec -->|Results| DB
    MgmtAPI -->|Config| DB
    Frontend -->|Data| DB

    %% Testing Connections
    UnitTests -->|Test| LogAPI
    UnitTests -->|Test| Parser
    UnitTests -->|Test| WiFiAgent
    UnitTests -->|Test| SecurityAgent
    UnitTests -->|Test| HealthAgent
    UnitTests -->|Test| WANAgent
    IntegrationTests -->|Test| Orch
    IntegrationTests -->|Test| Exec
    UnitTests -->|Test| TestDB
    IntegrationTests -->|Test| TestDB

    classDef device fill:#f9f,stroke:#333,stroke-width:2px
    classDef core fill:#bbf,stroke:#333,stroke-width:2px
    classDef storage fill:#fbb,stroke:#333,stroke-width:2px
    classDef management fill:#bfb,stroke:#333,stroke-width:2px
    classDef testing fill:#fbf,stroke:#333,stroke-width:2px

    class Device1,Device2,DeviceN device
    class LogAPI,Parser,WiFiAgent,SecurityAgent,HealthAgent,WANAgent,Orch,Exec core
    class DB,NATS storage
    class MgmtAPI,Frontend management
    class UnitTests,IntegrationTests,TestDB testing
```

## Component Descriptions

### OpenWRT Devices
- Network devices running OpenWRT
- Configured to forward logs via syslog
- Accessible via SSH for action execution

### OPMAS Core
1. **Log Ingestion API**
   - Receives syslog messages from devices
   - Validates and timestamps incoming logs
   - Forwards to Log Parser

2. **Log Parser**
   - Parses raw log messages
   - Classifies logs by type
   - Publishes to NATS topics

3. **Domain Agents**
   - Subscribe to relevant log topics
   - Apply domain-specific rules
   - Generate findings

4. **Orchestrator**
   - Processes agent findings
   - Consults playbooks
   - Decides on actions

5. **Action Executor**
   - Executes commands on devices
   - Manages SSH connections
   - Reports results

### Management Layer
1. **Management API**
   - RESTful API for system control
   - Configuration management
   - Status monitoring

2. **Frontend UI**
   - Web-based interface
   - Real-time monitoring
   - Configuration management

### Data Storage
- **PostgreSQL**
  - Stores system configuration
  - Maintains device inventory
  - Records findings and actions
  - Manages playbooks and rules
