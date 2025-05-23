# Development Setup Guide

## Prerequisites

### System Requirements
- Python 3.8 or higher
- PostgreSQL 14 or higher
- Redis
- NATS Server
- Git
- Docker (optional)
- Docker Compose (optional)

### Development Tools
- VS Code or preferred IDE
- Postman or similar API testing tool
- pgAdmin or similar database management tool

## Environment Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/opmas.git
cd opmas/management_api
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install production dependencies
pip install -r requirements.txt
```

### 4. Environment Variables
Create a `.env` file in the project root:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/opmas
TEST_DATABASE_URL=postgresql://user:password@localhost:5432/opmas_test

# Authentication
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# API Settings
API_HOST=0.0.0.0
API_PORT=8001
API_WORKERS=4
API_RELOAD=true

# Security
CORS_ORIGINS=["http://localhost:3000"]
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60

# Redis
REDIS_URL=redis://localhost:6379/0

# NATS
NATS_URL=nats://localhost:4222

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### 5. Database Setup
```bash
# Create database
createdb opmas
createdb opmas_test

# Run migrations
alembic upgrade head
```

### 6. Development Services
Using Docker Compose (recommended):
```bash
# Start development services
docker-compose -f docker-compose.dev.yml up -d
```

Or start services manually:
```bash
# Start PostgreSQL
pg_ctl -D /path/to/data start

# Start Redis
redis-server

# Start NATS
nats-server
```

## Development Workflow

### 1. Code Structure
```
management_api/
├── src/
│   └── opmas_mgmt_api/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── auth/
│       ├── models/
│       ├── schemas/
│       ├── routers/
│       └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/
├── alembic/
└── scripts/
```

### 2. Running the Application
```bash
# Development mode
uvicorn opmas_mgmt_api.main:app --reload --port 8001

# Production mode
uvicorn opmas_mgmt_api.main:app --workers 4 --port 8001
```

### 3. Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_auth.py

# Run with coverage
pytest --cov=opmas_mgmt_api

# Run specific test
pytest tests/unit/test_auth.py::test_login
```

### 4. Code Quality
```bash
# Run linter
flake8

# Run type checker
mypy .

# Run formatter
black .

# Run all checks
./scripts/check.sh
```

### 5. Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Development Tools

### 1. VS Code Extensions
- Python
- Pylance
- Python Test Explorer
- Docker
- GitLens
- REST Client

### 2. VS Code Settings
```json
{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.nosetestsEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ]
}
```

### 3. Git Hooks
Install pre-commit hooks:
```bash
pre-commit install
```

## Troubleshooting

### Common Issues

1. Database Connection
```bash
# Check PostgreSQL status
pg_ctl status

# Check connection
psql -h localhost -U user -d opmas
```

2. Redis Connection
```bash
# Check Redis status
redis-cli ping

# Monitor Redis
redis-cli monitor
```

3. NATS Connection
```bash
# Check NATS status
nats-server -v

# Test connection
nats-pub test "Hello World"
```

### Debugging

1. Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. Use Debugger
```python
import pdb; pdb.set_trace()
```

3. Check Logs
```bash
# View application logs
tail -f logs/app.log

# View error logs
tail -f logs/error.log
```

## Additional Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)

### Tools
- [Postman](https://www.postman.com/)
- [pgAdmin](https://www.pgadmin.org/)
- [Redis Commander](https://github.com/joeferner/redis-commander)
- [NATS CLI](https://github.com/nats-io/natscli)

### Support
For development support:
1. Check the [Troubleshooting Guide](../maintenance/troubleshooting.md)
2. Review the [FAQ](../maintenance/faq.md)
3. Open an issue in the project repository
4. Contact the development team 