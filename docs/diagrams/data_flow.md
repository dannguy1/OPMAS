# OPMAS Data Flow

## System Data Flow

```mermaid
flowchart TB
    subgraph "Data Sources"
        Device[OpenWRT Device]
        Config[Configuration Files]
    end

    subgraph "Data Processing"
        LogAPI[Log Ingestion API]
        Parser[Log Parser]
        Agents[Domain Agents]
        Orch[Orchestrator]
    end

    subgraph "Data Storage"
        DB[(PostgreSQL)]
        NATS[(NATS Message Bus)]
    end

    subgraph "Data Consumers"
        UI[Frontend UI]
        Exec[Action Executor]
        Reports[Reports & Analytics]
    end

    subgraph "Testing Framework"
        UnitTests[Unit Tests]
        IntegrationTests[Integration Tests]
        TestDB[(Test Database)]
    end

    %% Data Input Flow
    Device -->|Syslog Messages| LogAPI
    Config -->|Initial Config| DB

    %% Processing Flow
    LogAPI -->|Raw Logs| Parser
    Parser -->|Parsed Logs| NATS
    NATS -->|Filtered Logs| Agents
    Agents -->|Findings| NATS
    NATS -->|Findings| Orch

    %% Storage Flow
    Orch -->|Findings| DB
    Orch -->|Actions| DB
    Exec -->|Results| DB

    %% Consumption Flow
    DB -->|Config| UI
    DB -->|Findings| UI
    DB -->|Actions| UI
    DB -->|Config| Exec
    DB -->|Historical Data| Reports

    %% Testing Flow
    UnitTests -->|Test Data| LogAPI
    UnitTests -->|Test Data| Parser
    UnitTests -->|Test Data| Agents
    IntegrationTests -->|Test Data| Orch
    IntegrationTests -->|Test Data| Exec
    UnitTests -->|Test Data| TestDB
    IntegrationTests -->|Test Data| TestDB

    classDef source fill:#f9f,stroke:#333,stroke-width:2px
    classDef process fill:#bbf,stroke:#333,stroke-width:2px
    classDef storage fill:#fbb,stroke:#333,stroke-width:2px
    classDef consumer fill:#bfb,stroke:#333,stroke-width:2px
    classDef testing fill:#fbf,stroke:#333,stroke-width:2px

    class Device,Config source
    class LogAPI,Parser,Agents,Orch process
    class DB,NATS storage
    class UI,Exec,Reports consumer
    class UnitTests,IntegrationTests,TestDB testing
```

## Data Types and Transformations

### 1. Log Data Flow

```mermaid
flowchart LR
    subgraph "Raw Log"
        Syslog[Syslog Message]
        Metadata[Source IP, Timestamp]
    end

    subgraph "Parsed Log"
        EventID[Event ID]
        Timestamps[Arrival & Original TS]
        DeviceInfo[Hostname, IP]
        LogInfo[Process, Level]
        Message[Structured Message]
    end

    subgraph "Agent Finding"
        FindingID[Finding ID]
        AgentInfo[Agent Name, Type]
        Severity[Severity Level]
        Details[Structured Details]
    end

    Syslog -->|Parse| EventID
    Metadata -->|Enrich| Timestamps
    Metadata -->|Lookup| DeviceInfo
    Syslog -->|Extract| LogInfo
    Syslog -->|Structure| Message

    EventID -->|Generate| FindingID
    LogInfo -->|Classify| AgentInfo
    Message -->|Analyze| Severity
    Message -->|Process| Details
```

### 2. Configuration Data Flow

```mermaid
flowchart LR
    subgraph "Configuration Sources"
        YAML[YAML Config]
        API[API Updates]
        UI[UI Changes]
    end

    subgraph "Configuration Processing"
        Validator[Config Validator]
        Migrator[Config Migrator]
    end

    subgraph "Configuration Storage"
        DB[(PostgreSQL)]
        Cache[In-Memory Cache]
    end

    YAML -->|Load| Validator
    API -->|Update| Validator
    UI -->|Change| Validator

    Validator -->|Valid Config| Migrator
    Migrator -->|Store| DB
    DB -->|Load| Cache
```

### 3. Action Data Flow

```mermaid
flowchart LR
    subgraph "Action Generation"
        Finding[Agent Finding]
        Playbook[Action Playbook]
        Decision[Action Decision]
    end

    subgraph "Action Execution"
        Command[SSH Command]
        Result[Command Result]
    end

    subgraph "Action Storage"
        DB[(PostgreSQL)]
        NATS[(NATS Message Bus)]
    end

    Finding -->|Trigger| Decision
    Playbook -->|Guide| Decision
    Decision -->|Generate| Command
    Command -->|Execute| Result
    Result -->|Store| DB
    Result -->|Publish| NATS
```

## Data Retention and Cleanup

### 1. Log Retention Policy

```mermaid
flowchart TB
    subgraph "Log Lifecycle"
        Ingest[Log Ingestion]
        Process[Log Processing]
        Store[Log Storage]
        Archive[Log Archive]
        Delete[Log Deletion]
    end

    Ingest -->|Real-time| Process
    Process -->|Immediate| Store
    Store -->|After 7 days| Archive
    Archive -->|After 30 days| Delete
```

### 2. Configuration Versioning

```mermaid
flowchart LR
    subgraph "Configuration Versioning"
        Current[Current Config]
        History[Config History]
        Backup[Config Backup]
    end

    Current -->|On Change| History
    Current -->|Daily| Backup
    History -->|Rollback| Current
    Backup -->|Restore| Current
```

## Data Security

### 1. Data Encryption Flow

```mermaid
flowchart LR
    subgraph "Data Protection"
        Input[Data Input]
        Encrypt[Encryption]
        Store[Secure Storage]
        Decrypt[Decryption]
        Output[Data Output]
    end

    Input -->|Encrypt| Encrypt
    Encrypt -->|Store| Store
    Store -->|Decrypt| Decrypt
    Decrypt -->|Use| Output
```

### 2. Access Control Flow

```mermaid
flowchart TB
    subgraph "Access Control"
        User[User/Service]
        Auth[Authentication]
        Authz[Authorization]
        Resource[Protected Resource]
    end

    User -->|Credentials| Auth
    Auth -->|Token| Authz
    Authz -->|Permission| Resource
```
