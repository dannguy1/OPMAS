# Development Environment Setup

This guide provides instructions for setting up a development environment for the OPMAS project.

## Prerequisites

- Python 3.10 or higher
- Git
- Docker and Docker Compose
- Make (optional, for using Makefile commands)

## Initial Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/opmas.git
   cd opmas
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Component Setup

### Core Component

1. Navigate to core directory:
   ```bash
   cd core
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Initialize database:
   ```bash
   python scripts/init_db.py
   ```

### Management API

1. Navigate to management_api directory:
   ```bash
   cd management_api
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp example.env .env
   # Edit .env with your configuration
   ```

## Development Tools

### Code Quality

- Black: Code formatting
  ```bash
  black .
  ```

- isort: Import sorting
  ```bash
  isort .
  ```

- flake8: Code linting
  ```bash
  flake8
  ```

- mypy: Type checking
  ```bash
  mypy .
  ```

### Testing

Run tests for all components:
```bash
pytest
```

Run tests for specific component:
```bash
pytest core/tests/
# or
pytest management_api/tests/
```

### Docker Development

1. Build development images:
   ```bash
   docker-compose build
   ```

2. Start development environment:
   ```bash
   docker-compose up -d
   ```

3. View logs:
   ```bash
   docker-compose logs -f
   ```

## IDE Setup

### VS Code

1. Install recommended extensions:
   - Python
   - Pylance
   - Python Test Explorer
   - Docker
   - GitLens

2. Configure settings:
   ```json
   {
     "python.linting.enabled": true,
     "python.linting.flake8Enabled": true,
     "python.formatting.provider": "black",
     "editor.formatOnSave": true,
     "editor.codeActionsOnSave": {
       "source.organizeImports": true
     }
   }
   ```

### PyCharm

1. Configure Python interpreter:
   - Use the virtual environment created in the setup

2. Enable code quality tools:
   - Enable Black
   - Enable isort
   - Enable mypy

## Common Tasks

### Adding Dependencies

1. Add to requirements.txt:
   ```bash
   pip freeze > requirements.txt
   ```

2. Add to requirements-dev.txt for development dependencies:
   ```bash
   pip freeze > requirements-dev.txt
   ```

### Running Components

1. Core service:
   ```bash
   cd core
   ./start_opmas.sh
   ```

2. Management API:
   ```bash
   cd management_api
   python run.py
   ```

### Database Management

1. Initialize database:
   ```bash
   python scripts/init_db.py
   ```

2. Run migrations:
   ```bash
   alembic upgrade head
   ```

## Troubleshooting

### Common Issues

1. **Virtual Environment Issues**
   - Solution: Delete venv directory and recreate
   ```bash
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements-dev.txt
   ```

2. **Database Connection Issues**
   - Check PostgreSQL is running
   - Verify connection settings in .env
   - Check network connectivity

3. **Docker Issues**
   - Check Docker daemon is running
   - Verify ports are not in use
   - Check Docker Compose configuration

### Getting Help

- Check component-specific documentation
- Review logs in `logs/` directory
- Check GitHub issues
- Contact development team 