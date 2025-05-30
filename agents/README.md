# OPMAS Agent System

## Overview
The OPMAS Agent System provides a robust framework for managing and executing various types of agents in the OPMAS platform. It follows a three-tier architecture for clear separation of concerns and scalable operation.

## Architecture

### 1. Management API
- HTTP/REST API for user interaction
- Agent lifecycle management
- Status monitoring
- Configuration management
- Event handling

### 2. AgentManager Service
- Core agent lifecycle management
- Process supervision
- Health monitoring
- Resource management
- Recovery handling

### 3. Agent Packages
- Individual agent implementations
- Standardized interfaces
- Configuration management
- Event processing
- Metrics collection

## Implementation Status

### Completed Features
- [x] Core Infrastructure
  - Three-tier architecture
  - Component interfaces
  - Communication protocols
  - Process management
  - Health monitoring
- [x] Base Agent Implementation
  - Core agent class
  - Error handling
  - Logging system
  - Status management
  - Health checks
  - Resource tracking
  - Performance metrics
- [x] Management API
  - Agent management endpoints
  - Status monitoring
  - Configuration endpoints
  - Status service
  - Recovery service
  - Error handling
- [x] Agent Package Structure
  - Package format
  - Configuration system
  - Dependency management
  - Agent discovery

### In Progress
- [ ] Recovery System
  - Basic recovery implemented
  - State persistence pending
  - Rollback support pending
- [ ] Package Management
  - Discovery implemented
  - Installation pending
  - Updates pending

### Planned Features
- [ ] Testing Infrastructure
  - Unit tests
  - Integration tests
  - Performance tests
- [ ] Security Implementation
  - Authentication
  - Authorization
  - Secure communication
- [ ] Monitoring Enhancement
  - Custom metrics
  - Alert system
  - Dashboards
- [ ] Documentation
  - API documentation
  - Configuration guide
  - Deployment guide
- [ ] Performance Optimization
  - Database optimization
  - Resource usage
  - Async operations
- [ ] Integration Features
  - External system integration
  - Data management

## Getting Started

### Prerequisites
- Python 3.8+
- NATS server
- PostgreSQL database
- Docker (optional)

### Installation
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```
4. Start the services:
   ```bash
   # Start Management API
   python -m opmas_mgmt_api.main
   
   # Start AgentManager
   python -m opmas.agents.manager
   ```

### Configuration
- Agent configuration is managed through YAML files in `config/`
- Environment variables can override configuration
- Database settings in `config/database.yaml`
- NATS settings in `config/nats.yaml`

## Development

### Project Structure
```
agents/
├── config/             # Configuration files
├── docs/              # Documentation
├── src/               # Source code
│   ├── opmas/         # Core package
│   │   ├── agents/    # Agent implementations
│   │   └── common/    # Shared utilities
├── tests/             # Test files
└── requirements.txt   # Dependencies
```

### Adding New Agents
1. Create a new package in `src/opmas/agents/`
2. Extend the `BaseAgent` class
3. Implement required methods
4. Add configuration
5. Register the agent

### Testing
```bash
# Run unit tests
pytest tests/unit

# Run integration tests
pytest tests/integration

# Run all tests with coverage
pytest --cov=src tests/
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Support
For support, please open an issue in the GitHub repository or contact the development team. 