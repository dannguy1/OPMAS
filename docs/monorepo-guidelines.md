# OPMAS Monorepo Guidelines

This document outlines the development practices and guidelines for working with the OPMAS monorepo.

## Table of Contents
1. [Project Structure](#project-structure)
2. [Development Workflow](#development-workflow)
3. [Code Quality Standards](#code-quality-standards)
4. [Testing Strategy](#testing-strategy)
5. [Documentation Requirements](#documentation-requirements)
6. [Component Development](#component-development)
7. [CI/CD Practices](#cicd-practices)

## Project Structure

### Root Level Organization
```
OPMAS/
├── .github/                    # GitHub workflows and templates
├── docs/                       # Project-wide documentation
├── scripts/                    # Shared build/deployment scripts
├── core/                       # Core automation engine
├── management_api/            # Management API service
├── ui/                        # Frontend interface (if exists)
├── .gitignore                 # Root level gitignore
├── README.md                  # Project overview
├── docker-compose.yml         # Development environment setup
└── pyproject.toml            # Root level Python project config
```

### Component Structure
Each component (core, management_api, ui) should follow this structure:
```
component/
├── src/                       # Source code
├── tests/                     # Unit and integration tests
├── docs/                      # Component-specific documentation
├── config/                    # Configuration files
├── scripts/                   # Component-specific scripts
├── requirements.txt           # Runtime dependencies
├── requirements-dev.txt       # Development dependencies
├── setup.py                   # Package configuration
├── Dockerfile                 # Container definition
└── README.md                  # Component documentation
```

## Development Workflow

### Environment Setup
1. Use Python 3.10+ for all Python components
2. Create and use virtual environments for development
3. Install development dependencies from root `requirements-dev.txt`
4. Use pre-commit hooks for code quality checks

### Git Workflow
1. Branch naming convention: `feature/`, `bugfix/`, `hotfix/`, `release/`
2. Commit message format:
   ```
   type(scope): description

   [optional body]
   [optional footer]
   ```
   Types: feat, fix, docs, style, refactor, test, chore
3. Create pull requests for all changes
4. Require at least one review before merging
5. Keep branches up to date with main

### Code Quality Standards

#### Python Code
- Follow PEP 8 style guide
- Use type hints for all function parameters and return values
- Write docstrings for all public functions/classes
- Maximum line length: 88 characters (Black standard)
- Use absolute imports

#### Testing Requirements
- Unit test coverage: minimum 80%
- Integration tests for component interactions
- End-to-end tests for critical paths
- Mock external dependencies in tests

#### Documentation
- Keep README.md up to date
- Document all public APIs
- Include usage examples
- Document configuration options

## Component Development

### Core Component
- Focus on automation engine functionality
- Maintain separation of concerns
- Use dependency injection for flexibility
- Implement proper error handling and logging

### Management API
- Follow REST API best practices
- Implement proper authentication and authorization
- Use OpenAPI/Swagger for API documentation
- Implement rate limiting and request validation

### Frontend (if applicable)
- Follow component-based architecture
- Implement responsive design
- Use TypeScript for type safety
- Follow accessibility guidelines

## CI/CD Practices

### Continuous Integration
- Run tests on every pull request
- Enforce code quality checks
- Generate and publish documentation
- Build and test Docker images

### Continuous Deployment
- Use semantic versioning
- Implement automated releases
- Deploy to staging environment
- Implement rollback procedures

### Monitoring and Logging
- Implement structured logging
- Use centralized logging solution
- Monitor application metrics
- Set up alerting for critical issues

## Best Practices

### Security
- Never commit sensitive data
- Use environment variables for secrets
- Implement proper input validation
- Follow security best practices for each component

### Performance
- Optimize database queries
- Implement caching where appropriate
- Monitor resource usage
- Profile and optimize critical paths

### Maintainability
- Keep components loosely coupled
- Document architectural decisions
- Regular dependency updates
- Code review checklist

## Getting Started

1. Clone the repository
2. Set up development environment:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate

   # Install development dependencies
   pip install -r requirements-dev.txt

   # Install pre-commit hooks
   pre-commit install
   ```

3. Build components:
   ```bash
   ./scripts/build.sh
   ```

4. Run tests:
   ```bash
   pytest
   ```

## Additional Resources

- [Python Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
