# OPMAS Monorepo Setup Guide

## Overview
This guide outlines the steps to set up the OPMAS monorepo structure, which will contain all components (Management API, Core Services, UI, Agents) in a single repository. This approach allows for:
- Coordinated development across components
- Shared configuration and documentation
- Simplified dependency management
- Unified versioning and releases

## Prerequisites
- Git installed
- GitHub account/organization
- Access to the OPMAS project directory
- Docker Engine (version 20.10.0 or later)
- Docker Compose (version 2.0.0 or later)
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis
- NATS Server

## Clean Start
```bash
# Navigate to project root
cd /home/dannguyen/WNC/OPMAS

# Remove existing git repository if any
rm -rf .git

# Initialize new git repository
git init
```

## Repository Structure
```
opmas/
├── management_api/     # Management API service
├── core/              # Core backend services
├── ui/                # Web interface
├── agents/            # Security and monitoring agents
├── docs/             # Documentation
└── k8s/              # Kubernetes manifests
```

## Setup Steps

### 1. Create Root-Level Configuration Files

#### .gitignore
```bash
cat > .gitignore << 'EOL'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/
.env

# IDE
.idea/
.vscode/
*.swp
*.swo
.cursor/

# Logs
logs/
*.log

# Database
*.db

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/

# Distribution
dist/
build/

# Documentation
docs/_build/
site/

# Environment variables
.env
.env.*
!.env.example

# Kubernetes
k8s/secrets/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*
.npm
.yarn

# Build outputs
dist/
build/
out/
.next/
.nuxt/
.output/

# Misc
.DS_Store
Thumbs.db
*.bak
*.tmp
*.temp
EOL
```

#### LICENSE
```bash
cat > LICENSE << 'EOL'
MIT License

Copyright (c) 2024 OPMAS

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOL
```

#### README.md
```bash
cat > README.md << 'EOL'
# OPMAS (Open Platform Management and Security)

OPMAS is a comprehensive platform for managing and securing network infrastructure, providing centralized control, monitoring, and automation capabilities.

## Components

- **Management API** (`/management_api`): RESTful API for system management
- **Core Services** (`/core`): Core services for device management and security
- **UI** (`/ui`): Web interface for system administration
- **Agents** (`/agents`): Security and monitoring agents for network devices
- **Documentation** (`/docs`): System documentation and guides

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis
- NATS Server
- Docker & Docker Compose

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/your-org/opmas.git
cd opmas
```

2. Set up the Management API:
```bash
cd management_api
docker-compose up -d
```

3. Set up the UI:
```bash
cd ui
npm install
cp .env.example .env
```

4. Start the development environment:
```bash
docker-compose up -d
```

## Development Workflow

1. Create a new branch for your feature:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit them:
```bash
git add .
git commit -m "Description of your changes"
```

3. Push your changes:
```bash
git push origin feature/your-feature-name
```

4. Create a Pull Request

## Project Structure

```
opmas/
├── management_api/     # Management API service
├── core/              # Core backend services
├── ui/                # Web interface
├── agents/            # Security and monitoring agents
├── docs/             # Documentation
└── k8s/              # Kubernetes manifests
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Your Name - your.email@example.com

Project Link: [https://github.com/your-org/opmas](https://github.com/your-org/opmas)
EOL
```

### 2. Initial Commit
```bash
# Add all files
git add .

# Initial commit
git commit -m "Initial commit: OPMAS monorepo setup"
```

### 3. Create Development Branches
```bash
# Create and switch to core branch
git checkout -b feature/core

# Create and switch to ui branch
git checkout -b feature/ui

# Create and switch to api branch
git checkout -b feature/api

# Return to main branch
git checkout main
```

### 4. Set Up Remote Repository
```bash
# Add remote repository (replace with your actual GitHub repository URL)
git remote add origin https://github.com/your-org/opmas.git

# Push main branch
git push -u origin main

# Push development branches
git push -u origin feature/core
git push -u origin feature/ui
git push -u origin feature/api
```

## Monorepo Benefits
- **Unified Versioning**: All components are versioned together
- **Simplified Dependency Management**: Shared dependencies and configurations
- **Coordinated Development**: Easier to manage cross-component changes
- **Unified Documentation**: Centralized documentation and guides
- **Simplified CI/CD**: Single pipeline for all components
- **Easier Testing**: End-to-end testing across components

## Notes
1. Replace `your-org` in the repository URLs with your actual GitHub organization/username
2. Update the contact information in the README.md
3. Each component (core, ui, api) will be developed in its respective feature branch
4. The main branch will contain the stable, integrated version of all components
5. Consider using Git LFS for large files if needed

## Next Steps
1. Set up GitHub repository
2. Configure branch protection rules
3. Set up CI/CD pipeline
4. Begin component development in respective feature branches
