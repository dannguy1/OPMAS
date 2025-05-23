# OPMAS Development Setup Guide

## Overview

This document provides detailed instructions for setting up the OPMAS development environment, including required tools, configuration, and development workflow.

## 1. Prerequisites

### 1.1 Required Software
- **Operating System:**
  - Linux (Ubuntu 20.04+ or Debian 11+)
  - macOS (10.15+)
  - Windows 10/11 with WSL2

- **Core Tools:**
  - Git 2.30+
  - Docker 20.10+
  - Docker Compose 2.0+
  - Python 3.9+
  - Node.js 16+
  - npm 8+

- **Development Tools:**
  - VS Code or preferred IDE
  - Postman or Insomnia
  - pgAdmin or DBeaver
  - Git LFS

### 1.2 System Requirements
- **Hardware:**
  - CPU: 4+ cores
  - RAM: 8GB minimum (16GB recommended)
  - Storage: 20GB+ free space
  - Network: Stable internet connection

- **Development Environment:**
  - Local development database
  - NATS message broker
  - Redis for caching
  - Local SSL certificates

## 2. Initial Setup

### 2.1 Repository Setup
```bash
# Clone the repository
git clone https://github.com/your-org/OPMAS.git
cd OPMAS

# Initialize Git LFS
git lfs install

# Create development branch
git checkout -b dev/your-name
```

### 2.2 Environment Configuration
```bash
# Create environment files
cp .env.example .env.development
cp .env.example .env.test

# Configure development environment
nano .env.development
```

Required environment variables:
```ini
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=opmas_dev
DB_USER=opmas
DB_PASSWORD=your_password

# NATS
NATS_URL=nats://localhost:4222

# API
API_PORT=8000
API_HOST=localhost

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

## 3. Development Environment

### 3.1 Docker Setup
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: opmas_dev
      POSTGRES_USER: opmas
      POSTGRES_PASSWORD: your_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  nats:
    image: nats:latest
    ports:
      - "4222:4222"

  redis:
    image: redis:6
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 3.2 Python Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 3.3 Node.js Environment
```bash
# Install dependencies
cd ui
npm install

# Install development dependencies
npm install --save-dev @types/react @types/node
```

## 4. Development Workflow

### 4.1 Starting the Environment
```bash
# Start Docker services
docker-compose -f docker-compose.dev.yml up -d

# Start backend services
cd core
python manage.py runserver

# Start frontend development server
cd ui
npm run dev
```

### 4.2 Development Process
1. **Code Changes:**
   - Create feature branch
   - Make changes
   - Run tests
   - Submit PR

2. **Testing:**
   ```bash
   # Run backend tests
   pytest

   # Run frontend tests
   npm test

   # Run linting
   flake8
   npm run lint
   ```

3. **Database Migrations:**
   ```bash
   # Create migration
   python manage.py makemigrations

   # Apply migration
   python manage.py migrate
   ```

### 4.3 Debugging
- **Backend Debugging:**
  - VS Code launch configuration
  - Debug logging
  - Database inspection

- **Frontend Debugging:**
  - React Developer Tools
  - Redux DevTools
  - Network inspection

## 5. Development Guidelines

### 5.1 Code Style
- **Python:**
  - PEP 8 compliance
  - Black for formatting
  - isort for imports
  - flake8 for linting

- **JavaScript/TypeScript:**
  - ESLint configuration
  - Prettier formatting
  - TypeScript strict mode
  - React best practices

### 5.2 Git Workflow
- **Branch Naming:**
  - feature/feature-name
  - bugfix/bug-description
  - hotfix/issue-description

- **Commit Messages:**
  ```
  type(scope): description

  [optional body]

  [optional footer]
  ```

### 5.3 Documentation
- **Code Documentation:**
  - Docstring format
  - Type hints
  - Component documentation
  - API documentation

- **Commit Documentation:**
  - PR templates
  - Issue templates
  - Changelog updates

## 6. Testing

### 6.1 Unit Testing
```bash
# Backend tests
pytest tests/unit

# Frontend tests
npm run test:unit
```

### 6.2 Integration Testing
```bash
# Backend integration tests
pytest tests/integration

# Frontend integration tests
npm run test:integration
```

### 6.3 End-to-End Testing
```bash
# Run E2E tests
npm run test:e2e
```

## 7. Troubleshooting

### 7.1 Common Issues
- **Database Connection:**
  - Check PostgreSQL service
  - Verify credentials
  - Check port availability

- **NATS Connection:**
  - Verify NATS service
  - Check port availability
  - Review connection settings

- **Frontend Issues:**
  - Clear npm cache
  - Rebuild node_modules
  - Check API connectivity

### 7.2 Development Tools
- **Database Management:**
  - pgAdmin setup
  - Database backup/restore
  - Query optimization

- **API Testing:**
  - Postman collections
  - API documentation
  - Request/response examples

## 8. Performance Optimization

### 8.1 Development Performance
- **Backend:**
  - Debug mode settings
  - Query optimization
  - Caching strategy

- **Frontend:**
  - Development build optimization
  - Hot module replacement
  - Bundle analysis

### 8.2 Resource Management
- **Memory Usage:**
  - Container limits
  - Process monitoring
  - Resource cleanup

- **Disk Space:**
  - Docker cleanup
  - Log rotation
  - Cache management

## Related Documents

- [OPMAS-DS.md](../specifications/OPMAS-DS.md): Main design specification
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md): System architecture overview
- [DEPLOYMENT.md](DEPLOYMENT.md): Deployment procedures and strategies
- [API_DOCUMENTATION.md](../api/API_DOCUMENTATION.md): API reference 