# OPMAS Architecture Documentation

## Overview
OPMAS (Open Platform for Multi-Agent Systems) is a distributed system for managing and orchestrating autonomous agents. This documentation provides a comprehensive overview of the system's architecture, components, and design decisions.

## Components

### Core Engine
- [Core Engine Architecture](core-engine.md)
- [Agent System Design](agent-system.md)
- [Rule Engine](rule-engine.md)

### Management API
- [API Architecture](management-api.md)
- [Database Schema](database-schema.md)
- [Authentication & Authorization](auth.md)

### Frontend
- [UI Architecture](ui-architecture.md)
- [Component Design](component-design.md)
- [State Management](state-management.md)

## Design Decisions
- [ADR-001: Microservices Architecture](adr-001-microservices.md)
- [ADR-002: Database Choice](adr-002-database.md)
- [ADR-003: Frontend Framework](adr-003-frontend.md)

## System Requirements
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- NATS 2.8+

## Development Guidelines
- [Coding Standards](coding-standards.md)
- [Testing Strategy](testing-strategy.md)
- [Deployment Process](deployment.md)
