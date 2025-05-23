# OPMAS Documentation

This directory contains comprehensive documentation for the OpenWRT Proactive Monitoring Agentic System (OPMAS). The documentation is organized into several categories to help you find the information you need quickly.

## Directory Structure

```
docs/
├── specifications/     # Design specifications and requirements
├── api/                # API documentation
├── guides/             # Implementation and setup guides
├── architecture/       # Architecture and system design
└── diagrams/           # System diagrams and visual documentation
```

## Documentation Categories & Cross-References

### Specifications

Core design specifications and requirements for the system:

- [`specifications/OPMAS-DS.md`](specifications/OPMAS-DS.md) — Main design specification document outlining the system's goals, architecture, and components. See also: [`architecture/ARCHITECTURE.md`](../architecture/ARCHITECTURE.md), [`guides/DEVELOPMENT_SETUP.md`](../guides/DEVELOPMENT_SETUP.md)
- [`specifications/OPMAS-Backend-DS.md`](specifications/OPMAS-Backend-DS.md) — Detailed specification for the core backend components. See also: [`architecture/DATABASE_SCHEMA.md`](../architecture/DATABASE_SCHEMA.md), [`api/API_DOCUMENTATION.md`](../api/API_DOCUMENTATION.md)
- [`specifications/OPMAS-Frontend-DS.md`](specifications/OPMAS-Frontend-DS.md) — Frontend UI design specification. See also: [`guides/UI-Implementation-Guidelines.md`](../guides/UI-Implementation-Guidelines.md), [`api/API_DOCUMENTATION.md`](../api/API_DOCUMENTATION.md)
- [`specifications/OPMAS-Management-API-DS.md`](specifications/OPMAS-Management-API-DS.md) — Management API design specification. See also: [`api/API_DOCUMENTATION.md`](../api/API_DOCUMENTATION.md)

### API Documentation

API-related documentation:

- [`api/API_DOCUMENTATION.md`](api/API_DOCUMENTATION.md) — Main API reference documentation. See also: [`specifications/OPMAS-Management-API-DS.md`](../specifications/OPMAS-Management-API-DS.md)
- [`api/LOG_INGESTION_API.md`](api/LOG_INGESTION_API.md) — Detailed documentation for the Log Ingestion API. See also: [`specifications/OPMAS-Backend-DS.md`](../specifications/OPMAS-Backend-DS.md)

### Guides

Implementation and setup guides:

- [`guides/DEVELOPMENT_SETUP.md`](guides/DEVELOPMENT_SETUP.md) — Guide for setting up the development environment. See also: [`guides/DEPLOYMENT.md`](DEPLOYMENT.md), [`specifications/OPMAS-DS.md`](../specifications/OPMAS-DS.md)
- [`guides/DEPLOYMENT.md`](guides/DEPLOYMENT.md) — Deployment procedures and strategies. See also: [`guides/DEVELOPMENT_SETUP.md`](DEVELOPMENT_SETUP.md), [`guides/SECURITY.md`](SECURITY.md)
- [`guides/MONITORING.md`](guides/MONITORING.md) — System monitoring and alerting configuration. See also: [`guides/DEPLOYMENT.md`](DEPLOYMENT.md)
- [`guides/TESTING_STRATEGY.md`](guides/TESTING_STRATEGY.md) — Testing approach and procedures. See also: [`guides/DEVELOPMENT_SETUP.md`](DEVELOPMENT_SETUP.md)
- [`guides/SECURITY.md`](guides/SECURITY.md) — Security guidelines and best practices. See also: [`architecture/ARCHITECTURE.md`](../architecture/ARCHITECTURE.md)
- [`guides/OPENWRT_SETUP.md`](guides/OPENWRT_SETUP.md) — Guide for setting up OpenWRT devices. See also: [`specifications/OPMAS-DS.md`](../specifications/OPMAS-DS.md)
- [`guides/UI-Implementation-Guidelines.md`](guides/UI-Implementation-Guidelines.md) — Frontend implementation guidelines. See also: [`specifications/OPMAS-Frontend-DS.md`](../specifications/OPMAS-Frontend-DS.md)

### Architecture

System architecture and design documentation:

- [`architecture/ARCHITECTURE.md`](architecture/ARCHITECTURE.md) — Comprehensive system architecture overview. See also: [`specifications/OPMAS-DS.md`](../specifications/OPMAS-DS.md), [`architecture/DATABASE_SCHEMA.md`](DATABASE_SCHEMA.md)
- [`architecture/DATABASE_SCHEMA.md`](architecture/DATABASE_SCHEMA.md) — Database schema and data models. See also: [`specifications/OPMAS-Backend-DS.md`](../specifications/OPMAS-Backend-DS.md)

### Diagrams

Visual documentation and diagrams:

- System architecture diagrams
- Component interaction diagrams
- Data flow diagrams
- Deployment diagrams

## Documentation Maintenance

- All documentation should be kept up-to-date with code changes
- Use Markdown format for all documentation files
- Include diagrams in the `diagrams/` directory
- Update this README when adding new documentation

## Contributing

When adding new documentation:

1. Place it in the appropriate category directory
2. Update this README to include the new document
3. Ensure it follows the established format and style
4. Include any necessary diagrams in the `diagrams/` directory 