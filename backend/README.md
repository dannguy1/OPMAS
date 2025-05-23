# OPMAS Core

The Core component is the automation engine of OPMAS, responsible for log ingestion, parsing, analysis via specialized agents, and orchestration of responses based on playbooks.

## Documentation

### Design and Implementation
- [Design Specification](../docs/specifications/OPMAS-Backend-DS.md) - Detailed design of the Core component
- [Implementation Plan](../docs/implementation_plans/core_backend.md) - Step-by-step implementation guide

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- NATS Server
- Redis (for caching)

### Development Setup
1. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Initialize database:
   ```bash
   python scripts/init_db.py
   ```

5. Run the service:
   ```bash
   ./start_opmas.sh
   ```

### Docker Setup
1. Build the image:
   ```bash
   docker build -t opmas-core .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 --env-file .env opmas-core
   ```

## Project Structure
```
core/
├── src/
│   └── opmas/
│       ├── agents/           # Specialized analysis agents
│       ├── api/              # API endpoints
│       ├── core/             # Core functionality
│       ├── db/               # Database models and session
│       ├── parser/           # Log parsing and processing
│       └── orchestrator/     # Response orchestration
├── tests/                    # Test suite
├── docs/                     # Component documentation
├── config/                   # Configuration files
├── k8s/                      # Kubernetes manifests
├── logs/                     # Log files
├── scripts/                  # Utility scripts
├── .env.example             # Environment template
├── requirements.txt         # Dependencies
├── requirements-test.txt    # Test dependencies
└── start_opmas.sh          # Service entry point
```

## Development Guidelines

### Code Organization
- Keep files under 400 lines
- Use clear, descriptive names
- Follow PEP 8 style guide
- Use type hints for all functions

### Agent Development
- Follow agent interface contract
- Implement proper error handling
- Add comprehensive logging
- Write unit tests for all agents

### Testing
- Write unit tests for all new features
- Maintain minimum 80% test coverage
- Use pytest for testing
- Mock external dependencies

### Security
- Implement proper authentication
- Use role-based access control
- Validate all input data
- Follow security best practices

### Performance
- Optimize database queries
- Implement caching where appropriate
- Use connection pooling
- Monitor response times

## Common Tasks

### Adding New Agents
1. Create agent class in `agents/`
2. Implement agent interface
3. Add configuration in `config/`
4. Add tests in `tests/`
5. Update documentation

### Database Changes
1. Create migration:
   ```bash
   alembic revision --autogenerate -m "description"
   ```
2. Apply migration:
   ```bash
   alembic upgrade head
   ```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_file.py

# Run with coverage
pytest --cov=src/opmas
```

## Troubleshooting

### Common Issues
1. **Database Connection**
   - Check PostgreSQL is running
   - Verify connection settings in .env
   - Check network connectivity

2. **NATS Connection**
   - Verify NATS server is running
   - Check NATS connection settings
   - Review NATS logs

3. **Agent Issues**
   - Check agent logs
   - Verify agent configuration
   - Review agent dependencies

### Logs
- Check `logs/` directory for detailed logs
- Use appropriate log level for debugging
- Monitor error rates and patterns

## Contributing
1. Create feature branch
2. Make changes
3. Add tests
4. Update documentation
5. Create pull request

## License
[Your License] 