# OPMAS Management API Design Specification (OPMAS-Management-API-DS)

## 1. Introduction

This document outlines the design for the Management API component of OPMAS. The Management API serves as the intermediary between the Frontend UI and the core OPMAS system, providing a secure RESTful interface for configuration management, system control, and data access.

## 2. Goals

* Provide a secure, RESTful API for the Frontend UI
* Enable centralized configuration management
* Support system monitoring and control
* Ensure data integrity and security
* Facilitate future extensibility

## 3. Technology Stack

* **Framework:** FastAPI
* **Database:** PostgreSQL with SQLAlchemy ORM
* **Authentication:** JWT
* **Documentation:** OpenAPI/Swagger
* **Testing:** Pytest
* **Containerization:** Docker

## 4. API Structure

### 4.1. Base URL and Versioning

* Base URL: `/api/v1`
* Version prefix in URL
* Content-Type: `application/json`
* Response format: JSON

### 4.2. Endpoint Categories

#### 4.2.1. System Status (`/api/v1/status`)

* `GET /status`: Get system component status
* `GET /status/components`: Get detailed component status
* `GET /status/health`: Get system health check

#### 4.2.2. System Control (`/api/v1/control`)

* `POST /control/start`: Start OPMAS system
* `POST /control/stop`: Stop OPMAS system
* `POST /control/restart`: Restart OPMAS system

#### 4.2.3. Configuration Management

* **Core Configuration**
  * `GET /config/core`: Get core configuration
  * `PUT /config/core`: Update core configuration

* **Agent Management**
  * `GET /config/agents`: List all agents
  * `POST /config/agents`: Create new agent
  * `GET /config/agents/{agent_id}`: Get agent details
  * `PUT /config/agents/{agent_id}`: Update agent
  * `DELETE /config/agents/{agent_id}`: Delete agent
  * `GET /config/agents/discover`: Discover available agents

* **Agent Rules**
  * `GET /config/agent-rules/{agent_id}`: Get agent rules
  * `POST /config/agent-rules/{agent_id}`: Create agent rule
  * `PUT /config/agent-rules/{agent_id}/{rule_id}`: Update rule
  * `DELETE /config/agent-rules/{agent_id}/{rule_id}`: Delete rule

* **Playbook Management**
  * `GET /config/playbooks`: List all playbooks
  * `POST /config/playbooks`: Create playbook
  * `GET /config/playbooks/{playbook_id}`: Get playbook
  * `PUT /config/playbooks/{playbook_id}`: Update playbook
  * `DELETE /config/playbooks/{playbook_id}`: Delete playbook

* **Playbook Steps**
  * `GET /config/playbook-steps/{playbook_id}`: Get steps
  * `POST /config/playbook-steps/{playbook_id}`: Add step
  * `PUT /config/playbook-steps/{playbook_id}/{step_id}`: Update step
  * `DELETE /config/playbook-steps/{playbook_id}/{step_id}`: Delete step

#### 4.2.4. Operational Data

* **Findings**
  * `GET /findings`: List findings
  * `GET /findings/{finding_id}`: Get finding details
  * `GET /findings/statistics`: Get findings statistics

* **Intended Actions**
  * `GET /intended-actions`: List intended actions
  * `GET /intended-actions/{action_id}`: Get action details
  * `GET /intended-actions/statistics`: Get action statistics

#### 4.2.5. Logs

* `GET /logs/{component}`: Get component logs
* `GET /logs/system`: Get system logs

## 5. Data Models

### 5.1. Request/Response Models

* Use Pydantic models for request/response validation
* Define clear schemas for all endpoints
* Include proper type hints and validation

### 5.2. Database Models

* SQLAlchemy models for database interaction
* Proper relationships and constraints
* Indexing for performance

## 6. Authentication & Authorization

### 6.1. Authentication

* JWT-based authentication
* Token refresh mechanism
* Secure password handling
* Session management

### 6.2. Authorization

* Role-based access control
* Permission management
* API key support for external integration

## 7. Error Handling

### 7.1. Error Responses

* Standardized error format
* HTTP status code usage
* Detailed error messages
* Error logging

### 7.2. Validation

* Input validation
* Business rule validation
* Database constraint handling

## 8. Performance

### 8.1. Optimization

* Database query optimization
* Response caching
* Connection pooling
* Pagination

### 8.2. Monitoring

* Request timing
* Resource usage
* Error rates
* Performance metrics

## 9. Security

### 9.1. API Security

* HTTPS enforcement
* CORS configuration
* Rate limiting
* Input sanitization

### 9.2. Data Security

* Data encryption
* Secure storage
* Audit logging
* Access control

## 10. Testing

### 10.1. Unit Tests

* Endpoint testing
* Model testing
* Service testing
* Utility testing

### 10.2. Integration Tests

* API flow testing
* Database integration
* Authentication testing
* Error handling

## 11. Documentation

### 11.1. API Documentation

* OpenAPI/Swagger documentation
* Endpoint descriptions
* Request/response examples
* Authentication details

### 11.2. Code Documentation

* Code comments
* Type hints
* Function documentation
* Architecture documentation

## 12. Deployment

### 12.1. Containerization

* Dockerfile configuration
* Environment variables
* Volume management
* Health checks

### 12.2. Configuration

* Environment-based config
* Secret management
* Logging configuration
* Database configuration

## 13. Monitoring & Logging

### 13.1. Logging

* Request logging
* Error logging
* Audit logging
* Performance logging

### 13.2. Monitoring

* Health checks
* Performance monitoring
* Error tracking
* Resource monitoring

## 14. Future Enhancements

* WebSocket support
* GraphQL API
* Advanced filtering
* Bulk operations
* API versioning strategy
* Enhanced security features 