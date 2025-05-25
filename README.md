# OPMAS (Open Platform for Multi-Agent Systems)

OPMAS is a distributed system for managing and orchestrating autonomous agents. It provides a robust platform for deploying, monitoring, and managing agent-based systems.

## Features

- **Agent Management**: Deploy, monitor, and manage autonomous agents
- **Rule Engine**: Define and enforce rules for agent behavior
- **Configuration Management**: Centralized configuration management
- **Monitoring**: Real-time monitoring and alerting
- **API**: RESTful API for system integration
- **UI**: React-based web interface

## Architecture

OPMAS follows a microservices architecture with the following components:

- **Core Engine**: Handles agent execution and coordination
- **Management API**: Provides REST API for system management
- **Frontend**: React-based web interface
- **Database**: PostgreSQL for persistent storage
- **Message Broker**: NATS for inter-service communication
- **Cache**: Redis for caching and pub/sub

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- NATS 2.8+
- Docker and Docker Compose

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/opmas.git
   cd opmas
   ```

2. Set up the development environment:
   ```bash
   docker-compose up -d
   ```

3. Install dependencies:
   ```bash
   # Management API
   cd management_api
   pip install -r requirements.txt
   pip install -r requirements-dev.txt

   # Frontend
   cd ../ui
   npm install
   ```

4. Start the services:
   ```bash
   # Management API
   cd management_api
   python run.py

   # Frontend
   cd ../ui
   npm run dev
   ```

## Development

### Project Structure

```
OPMAS/
├── .github/                    # GitHub workflows
├── docs/                       # Project documentation
│   ├── architecture/          # Architecture decisions
│   ├── api/                   # API documentation
│   └── development/           # Development guides
├── scripts/                    # Shared scripts
├── core/                      # Core automation engine
├── management_api/            # Management API
├── ui/                        # UI interface
├── docker-compose.yml         # Development environment
└── pyproject.toml            # Root Python config
```

### Development Guidelines

- Follow the coding standards in `docs/development/coding-standards.md`
- Write tests for all new features
- Update documentation for significant changes
- Use conventional commits for commit messages

### Testing

```bash
# Management API
cd management_api
pytest

# Frontend
cd ui
npm test
```

### Linting

```bash
# Management API
cd management_api
flake8 .
black .
isort .
mypy .

# Frontend
cd ui
npm run lint
npm run type-check
```

## Documentation

- [Architecture Documentation](docs/architecture/README.md)
- [API Documentation](docs/api/README.md)
- [Development Guide](docs/development/README.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Your Name - your.email@example.com

Project Link: [https://github.com/your-org/opmas](https://github.com/your-org/opmas)
