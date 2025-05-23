# OPMAS Management API Documentation

## Overview
The OPMAS Management API is a FastAPI-based service that provides a comprehensive interface for managing OPMAS components, including devices, agents, playbooks, and rules. This documentation provides detailed information about the system architecture, implementation, and usage.

## Documentation Structure

### 1. System Architecture
- [System Overview](architecture/system_overview.md)
- [Component Interactions](architecture/component_interactions.md)
- [Data Flow](architecture/data_flow.md)
- [Security Architecture](architecture/security.md)

### 2. API Documentation
- [API Overview](api/overview.md)
- [Authentication](api/authentication.md)
- [Device Management](api/devices.md)
- [Agent Management](api/agents.md)
- [Playbook Management](api/playbooks.md)
- [Rule Management](api/rules.md)
- [System Management](api/system.md)

### 3. Development Guide
- [Setup Guide](development/setup.md)
- [Development Workflow](development/workflow.md)
- [Testing Guide](development/testing.md)
- [Code Style Guide](development/code_style.md)

### 4. Deployment Guide
- [Deployment Overview](deployment/overview.md)
- [Environment Setup](deployment/environment.md)
- [Configuration](deployment/configuration.md)
- [Monitoring](deployment/monitoring.md)

### 5. Maintenance Guide
- [Maintenance Procedures](maintenance/procedures.md)
- [Troubleshooting](maintenance/troubleshooting.md)
- [Backup and Recovery](maintenance/backup_recovery.md)
- [Security Updates](maintenance/security_updates.md)

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 14+
- Redis
- NATS Server

### Installation
1. Clone the repository
2. Create a virtual environment
3. Install dependencies
4. Configure environment variables
5. Initialize the database
6. Start the service

For detailed instructions, see the [Setup Guide](development/setup.md).

### Basic Usage
1. Start the service
2. Access the API documentation at `/docs`
3. Authenticate using the `/api/v1/auth/token` endpoint
4. Use the API endpoints to manage your OPMAS components

For detailed API usage, see the [API Documentation](api/overview.md).

## Contributing
Please read our [Contributing Guide](development/contributing.md) for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## Support
For support, please:
1. Check the [Troubleshooting Guide](maintenance/troubleshooting.md)
2. Review the [FAQ](maintenance/faq.md)
3. Open an issue in the project repository
4. Contact the development team 