# OPMAS Database Schema

## Overview

This document details the database schema for the OPMAS system, including table definitions, relationships, and constraints. The system uses PostgreSQL as its primary database.

## Core Tables

### 1. opmas_config
Stores system-wide configuration settings.

```sql
CREATE TABLE opmas_config (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 2. agents
Stores agent definitions and settings.

```sql
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 3. agent_rules
Stores rules for each agent.

```sql
CREATE TABLE agent_rules (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_type VARCHAR(50) NOT NULL,
    conditions JSONB NOT NULL,
    actions JSONB,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent_id, name)
);
```

### 4. playbooks
Stores action playbooks.

```sql
CREATE TABLE playbooks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    trigger_type VARCHAR(50) NOT NULL,
    trigger_conditions JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 5. playbook_steps
Stores steps within playbooks.

```sql
CREATE TABLE playbook_steps (
    id SERIAL PRIMARY KEY,
    playbook_id INTEGER REFERENCES playbooks(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    action_config JSONB NOT NULL,
    timeout_seconds INTEGER DEFAULT 30,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(playbook_id, step_number)
);
```

### 6. findings
Stores detected issues.

```sql
CREATE TABLE findings (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    device_id INTEGER REFERENCES devices(id),
    finding_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT,
    details JSONB,
    status VARCHAR(20) DEFAULT 'new',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 7. intended_actions
Stores planned actions.

```sql
CREATE TABLE intended_actions (
    id SERIAL PRIMARY KEY,
    finding_id INTEGER REFERENCES findings(id),
    playbook_id INTEGER REFERENCES playbooks(id),
    status VARCHAR(20) DEFAULT 'pending',
    action_type VARCHAR(50) NOT NULL,
    action_config JSONB NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    executed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 8. devices
Stores OpenWRT device information.

```sql
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    hostname VARCHAR(255) NOT NULL,
    ip_address INET NOT NULL,
    model VARCHAR(255),
    firmware_version VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    last_seen_at TIMESTAMP WITH TIME ZONE,
    config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hostname),
    UNIQUE(ip_address)
);
```

### 9. ssh_keys
Stores encrypted SSH keys.

```sql
CREATE TABLE ssh_keys (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    key_type VARCHAR(20) NOT NULL,
    encrypted_key TEXT NOT NULL,
    key_fingerprint VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Indexes

```sql
-- Performance indexes
CREATE INDEX idx_findings_device_id ON findings(device_id);
CREATE INDEX idx_findings_created_at ON findings(created_at);
CREATE INDEX idx_intended_actions_status ON intended_actions(status);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_agent_rules_agent_id ON agent_rules(agent_id);
CREATE INDEX idx_playbook_steps_playbook_id ON playbook_steps(playbook_id);
```

## Constraints

1. **Foreign Key Constraints**
   - All foreign keys have ON DELETE CASCADE where appropriate
   - Ensures referential integrity

2. **Unique Constraints**
   - Device hostnames and IP addresses must be unique
   - Agent names must be unique
   - Playbook names must be unique
   - Agent rule names must be unique within an agent

3. **Check Constraints**
   - Severity must be one of: 'info', 'warning', 'error', 'critical'
   - Status fields must be one of their allowed values
   - Timestamps must be in UTC

## Data Types

1. **JSONB Fields**
   - Used for flexible configuration storage
   - Allows querying of nested fields
   - Supports indexing on specific JSON paths

2. **Timestamps**
   - All timestamps use TIMESTAMP WITH TIME ZONE
   - Default to CURRENT_TIMESTAMP
   - Automatically updated on record modification

3. **Enums**
   - Status fields use VARCHAR with check constraints
   - Severity levels use VARCHAR with check constraints

## Maintenance

1. **Partitioning**
   - Findings table partitioned by date
   - Helps manage large volumes of historical data

2. **Vacuum Strategy**
   - Regular VACUUM ANALYZE on all tables
   - Aggressive VACUUM on findings table

3. **Backup Strategy**
   - Daily full backups
   - Continuous WAL archiving
   - Point-in-time recovery support

## Security

1. **Row Level Security**
   - Implemented for multi-tenant support
   - Based on device ownership

2. **Encryption**
   - SSH keys stored encrypted
   - Sensitive configuration encrypted at rest

## Migration Strategy

1. **Version Control**
   - Schema changes tracked in migration files
   - Version numbers for all schema changes

2. **Rollback Support**
   - All migrations include up and down paths
   - Tested rollback procedures

## Monitoring

1. **Performance Metrics**
   - Table sizes
   - Index usage
   - Query performance

2. **Health Checks**
   - Connection pool status
   - Replication lag
   - Disk space usage
