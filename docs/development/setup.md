# Development Environment Setup Guide

## Prerequisites

### System Requirements
- Linux/Unix-based system (Ubuntu 20.04+ recommended)
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space
- Git 2.25+
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.10+
- Node.js 18+
- npm 8+

### Required Tools
1. **Git**
   ```bash
   # Install Git
   sudo apt update
   sudo apt install git

   # Configure Git
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

2. **Docker**
   ```bash
   # Install Docker
   sudo apt update
   sudo apt install docker.io docker-compose

   # Add user to docker group
   sudo usermod -aG docker $USER

   # Start Docker service
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

3. **Python**
   ```bash
   # Install Python 3.10
   sudo apt update
   sudo apt install python3.10 python3.10-venv python3-pip

   # Verify installation
   python3 --version
   pip3 --version
   ```

4. **Node.js**
   ```bash
   # Install Node.js 18
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt install -y nodejs

   # Verify installation
   node --version
   npm --version
   ```

## Project Setup

### 1. Clone Repository
```bash
# Clone the repository
git clone https://github.com/your-org/opmas.git
cd opmas

# Set up git hooks
cp .git-hooks/* .git/hooks/
chmod +x .git/hooks/*
```

### 2. Environment Setup

#### Management API
```bash
# Create and activate virtual environment
cd management_api
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Set up environment variables
cp example.env .env
# Edit .env with your configuration
```

#### UI
The UI component is built with React and TypeScript. To set up the development environment:

1. Navigate to the UI directory:
   ```bash
   cd ui
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The UI will be available at http://localhost:3000.

### 3. Database Setup
```bash
# Start PostgreSQL container
docker-compose up -d postgres

# Wait for database to be ready
sleep 10

# Run migrations
cd management_api
alembic upgrade head
```

### 4. Start Development Services
```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

## Development Tools

### IDE Setup

#### VS Code
1. Install recommended extensions:
   - Python
   - Pylance
   - ESLint
   - Prettier
   - Docker
   - GitLens

2. Configure settings:
   ```json
   {
     "editor.formatOnSave": true,
     "python.linting.enabled": true,
     "python.formatting.provider": "black",
     "editor.codeActionsOnSave": {
       "source.fixAll.eslint": true
     }
   }
   ```

### Debugging Tools

#### Backend
1. **Python Debugger**
   ```python
   # Add to code
   import pdb; pdb.set_trace()
   ```

2. **Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

#### Frontend
1. **React DevTools**
   - Install browser extension
   - Enable in development mode

2. **Redux DevTools**
   - Install browser extension
   - Configure store

### Testing Tools

#### Backend
```bash
# Run tests
cd management_api
pytest

# Run with coverage
pytest --cov=src
```

#### Frontend
```bash
# Run tests
cd ui
npm test

# Run with coverage
npm test -- --coverage
```

## Common Issues

### Docker Issues
1. **Permission Denied**
   ```bash
   # Fix Docker permissions
   sudo chmod 666 /var/run/docker.sock
   ```

2. **Container Won't Start**
   ```bash
   # Check logs
   docker-compose logs

   # Restart containers
   docker-compose down
   docker-compose up -d
   ```

### Database Issues
1. **Connection Refused**
   ```bash
   # Check PostgreSQL status
   docker exec opmas-postgres-1 pg_isready

   # Reset database
   docker-compose down -v
   docker-compose up -d
   ```

2. **Migration Errors**
   ```bash
   # Reset migrations
   cd management_api
   alembic downgrade base
   alembic upgrade head
   ```

### Frontend Issues
1. **Build Errors**
   ```bash
   # Clear cache
   cd ui
   rm -rf node_modules/.cache
   npm install
   ```

2. **TypeScript Errors**
   ```bash
   # Clear TypeScript cache
   rm -rf node_modules/.cache/typescript
   ```

## Maintenance

### Regular Updates
1. **Dependencies**
   ```bash
   # Backend
   cd management_api
   pip list --outdated
   pip install -U -r requirements.txt

   # Frontend
   cd ui
   npm outdated
   npm update
   ```

2. **Docker Images**
   ```bash
   # Update images
   docker-compose pull
   docker-compose build --no-cache
   ```

### Backup
1. **Database**
   ```bash
   # Create backup
   docker exec opmas-postgres-1 pg_dump -U opmas opmas_mgmt > backup.sql

   # Restore backup
   cat backup.sql | docker exec -i opmas-postgres-1 psql -U opmas opmas_mgmt
   ```

2. **Configuration**
   ```bash
   # Backup env files
   cp management_api/.env management_api/.env.backup
   cp ui/.env ui/.env.backup
   ```

## Getting Help

### Documentation
- [Recovery Guide](recovery-guide.md)
- [Troubleshooting Guide](troubleshooting.md)
- [Development Workflow](workflow.md)

### Support
- Team Slack channel
- GitHub Issues
- Email support
