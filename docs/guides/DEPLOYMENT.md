# OPMAS Deployment Guide

## Overview

This document outlines the deployment strategies and procedures for the OPMAS system across different environments, including development, staging, and production.

## 1. Deployment Environments

### 1.1 Development Environment
- **Purpose:** Local development and testing
- **Components:**
  - Docker Compose for local services
  - Development database
  - Mock services for testing
- **Configuration:**
  - Environment variables in `.env.development`
  - Debug logging enabled
  - Hot-reload for development

### 1.2 Staging Environment
- **Purpose:** Pre-production testing
- **Components:**
  - Kubernetes cluster
  - Production-like database
  - Full service stack
- **Configuration:**
  - Environment variables in `.env.staging`
  - Production-like settings
  - Monitoring enabled

### 1.3 Production Environment
- **Purpose:** Live system deployment
- **Components:**
  - Kubernetes cluster
  - Production database
  - High-availability setup
- **Configuration:**
  - Environment variables in `.env.production`
  - Production settings
  - Full monitoring and logging

## 2. Container Orchestration

### 2.1 Docker Compose (Development)
```yaml
version: '3.8'
services:
  nats:
    image: nats:latest
    ports:
      - "4222:4222"
  
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: opmas
      POSTGRES_USER: opmas
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  core:
    build: ./core
    depends_on:
      - nats
      - postgres
    environment:
      - NATS_URL=nats://nats:4222
      - DB_URL=postgresql://opmas:opmas@postgres:5432/opmas
  
  management_api:
    build: ./management_api
    depends_on:
      - postgres
    environment:
      - DB_URL=postgresql://opmas:opmas@postgres:5432/opmas
  
  ui:
    build: ./ui
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://localhost:8000

volumes:
  postgres_data:
```

### 2.2 Kubernetes (Production)
- **Namespaces:**
  - `opmas-core`: Core backend services
  - `opmas-api`: Management API
  - `opmas-ui`: Frontend UI
  - `opmas-db`: Database services

- **Deployments:**
  - Core backend components
  - Management API
  - Frontend UI
  - NATS cluster
  - PostgreSQL cluster

- **Services:**
  - Load balancers
  - Internal services
  - Database services

## 3. Scaling Considerations

### 3.1 Horizontal Scaling
- **Core Backend:**
  - Multiple agent instances
  - Load-balanced log ingestion
  - Distributed processing

- **Management API:**
  - Multiple API instances
  - Load balancer configuration
  - Session management

- **Frontend UI:**
  - CDN integration
  - Static asset caching
  - Load balancing

### 3.2 Vertical Scaling
- **Database:**
  - Resource allocation
  - Connection pooling
  - Query optimization

- **Message Queue:**
  - NATS cluster sizing
  - Message persistence
  - Queue monitoring

### 3.3 Auto-scaling
- **Metrics:**
  - CPU utilization
  - Memory usage
  - Request latency
  - Queue length

- **Policies:**
  - Scale-up thresholds
  - Scale-down thresholds
  - Cooldown periods

## 4. Backup and Recovery

### 4.1 Database Backup
- **Full Backups:**
  - Daily snapshots
  - Point-in-time recovery
  - Backup verification

- **Incremental Backups:**
  - WAL archiving
  - Transaction logs
  - Differential backups

### 4.2 Configuration Backup
- **Backup Scope:**
  - Environment variables
  - Kubernetes configs
  - SSL certificates
  - SSH keys

- **Backup Schedule:**
  - Daily configuration dumps
  - Version control
  - Change tracking

### 4.3 Recovery Procedures
- **Database Recovery:**
  - Full restore process
  - Point-in-time recovery
  - Data verification

- **Service Recovery:**
  - Component restart
  - State recovery
  - Health checks

## 5. Monitoring and Logging

### 5.1 System Monitoring
- **Metrics:**
  - CPU/Memory usage
  - Disk I/O
  - Network traffic
  - Service health

- **Alerts:**
  - Resource thresholds
  - Error rates
  - Service availability
  - Performance degradation

### 5.2 Log Management
- **Log Collection:**
  - Centralized logging
  - Log aggregation
  - Log rotation

- **Log Analysis:**
  - Error tracking
  - Performance analysis
  - Security monitoring

## 6. Security

### 6.1 Network Security
- **Firewall Rules:**
  - Inbound/outbound rules
  - Service isolation
  - Network policies

- **TLS Configuration:**
  - Certificate management
  - TLS version control
  - Cipher suite selection

### 6.2 Access Control
- **Authentication:**
  - Service accounts
  - API tokens
  - SSH keys

- **Authorization:**
  - Role-based access
  - Resource permissions
  - Audit logging

## 7. Deployment Process

### 7.1 Pre-deployment
- **Checks:**
  - Environment validation
  - Configuration review
  - Security scan
  - Performance test

- **Preparation:**
  - Backup creation
  - Resource allocation
  - Service notification

### 7.2 Deployment Steps
1. **Database Migration:**
   - Schema updates
   - Data migration
   - Index optimization

2. **Service Deployment:**
   - Core backend
   - Management API
   - Frontend UI

3. **Verification:**
   - Health checks
   - Integration tests
   - Performance validation

### 7.3 Post-deployment
- **Monitoring:**
  - Service health
  - Error rates
  - Performance metrics

- **Documentation:**
  - Deployment notes
  - Configuration changes
  - Known issues

## 8. Maintenance

### 8.1 Regular Maintenance
- **Updates:**
  - Security patches
  - Dependency updates
  - Configuration updates

- **Cleanup:**
  - Log rotation
  - Temporary files
  - Old backups

### 8.2 Emergency Procedures
- **Incident Response:**
  - Service restoration
  - Data recovery
  - Communication plan

- **Rollback:**
  - Version rollback
  - Configuration restore
  - State recovery 