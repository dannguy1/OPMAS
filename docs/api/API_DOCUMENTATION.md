# OPMAS API Documentation

## Overview

This document provides comprehensive documentation for the OPMAS API ecosystem, including versioning strategy, deprecation policies, and general API guidelines. For specific API endpoint documentation, refer to the respective API guides.

## 1. API Architecture

### 1.1 API Components
- **Log Ingestion API**: Handles log ingestion and processing
  - See [Log Ingestion API Guide](LOG_INGESTION_API.md)
- **Management API**: System configuration and monitoring
  - See [Management API Guide](#management-api)
- **Action API**: Command execution and control
- **Monitoring API**: System metrics and health checks

### 1.2 API Gateway
- **Authentication**: JWT-based authentication
- **Rate Limiting**: Per-endpoint and global limits
- **Request Validation**: Input validation and sanitization
- **Response Formatting**: Standardized response structure

## 2. API Versioning

### 2.1 Version Strategy
- **URL-based Versioning**: `/api/v1/...`
- **Header-based Versioning**: `Accept: application/vnd.opmas.v1+json`
- **Version Lifecycle**:
  - Current: v1
  - Supported: v1
  - Deprecated: None
  - Sunset: None

### 2.2 Version Policy
- Major versions: Breaking changes
- Minor versions: Backward-compatible features
- Patch versions: Backward-compatible fixes
- Version support period: 12 months after deprecation

## 3. API Standards

### 3.1 Request Format
```json
{
  "data": {
    // Request-specific data
  },
  "metadata": {
    "request_id": "uuid",
    "timestamp": "ISO-8601",
    "client_info": {
      "version": "string",
      "platform": "string"
    }
  }
}
```

### 3.2 Response Format
```json
{
  "data": {
    // Response-specific data
  },
  "metadata": {
    "request_id": "uuid",
    "timestamp": "ISO-8601",
    "version": "string"
  },
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

### 3.3 Error Codes
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **429**: Too Many Requests
- **500**: Internal Server Error

## 4. Authentication

### 4.1 JWT Authentication
- **Token Format**: `Bearer <token>`
- **Token Lifetime**: 24 hours
- **Refresh Token**: 30 days
- **Token Claims**:
  ```json
  {
    "sub": "user_id",
    "roles": ["role1", "role2"],
    "permissions": ["perm1", "perm2"],
    "exp": 1234567890,
    "iat": 1234567890
  }
  ```

### 4.2 API Keys
- **Format**: `X-API-Key: <key>`
- **Usage**: For service-to-service communication
- **Rotation**: Every 90 days
- **Scope**: Per-service or global

## 5. Rate Limiting

### 5.1 Global Limits
- **Requests per minute**: 1000
- **Requests per hour**: 10000
- **Concurrent connections**: 100

### 5.2 Per-Endpoint Limits
- **Log Ingestion**: 100/min, 1000/hour
- **Management API**: 60/min, 600/hour
- **Action API**: 30/min, 300/hour
- **Monitoring API**: 120/min, 1200/hour

## 6. Management API

### 6.1 Agent Management

#### Base URL
All agent endpoints are relative to `/api/v1/agents`

#### Endpoints

##### List Agents
```http
GET /api/v1/agents
```

List all agents with optional filtering and pagination.

###### Query Parameters

| Parameter   | Type    | Required | Description                                    |
|-------------|---------|----------|------------------------------------------------|
| skip        | integer | No       | Number of records to skip (default: 0)         |
| limit       | integer | No       | Number of records to return (default: 100)     |
| agent_type  | string  | No       | Filter by agent type                           |
| status      | string  | No       | Filter by status                               |

###### Response
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "agent-name",
      "agent_type": "wifi",
      "description": "Agent description",
      "configuration": {},
      "capabilities": {},
      "status": "active",
      "created_at": "2024-03-20T12:00:00Z",
      "updated_at": "2024-03-20T12:00:00Z",
      "last_heartbeat": "2024-03-20T12:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

##### Create Agent
```http
POST /api/v1/agents
```

Create a new agent.

###### Request Body
```json
{
  "name": "agent-name",
  "agent_type": "wifi",
  "description": "Agent description",
  "configuration": {},
  "capabilities": {}
}
```

###### Response
```json
{
  "id": "uuid",
  "name": "agent-name",
  "agent_type": "wifi",
  "description": "Agent description",
  "configuration": {},
  "capabilities": {},
  "status": "inactive",
  "created_at": "2024-03-20T12:00:00Z",
  "updated_at": "2024-03-20T12:00:00Z",
  "last_heartbeat": null
}
```

##### Get Agent
```http
GET /api/v1/agents/{agent_id}
```

Get agent details by ID.

###### Path Parameters

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| agent_id  | UUID   | Yes      | Agent ID    |

###### Response
```json
{
  "id": "uuid",
  "name": "agent-name",
  "agent_type": "wifi",
  "description": "Agent description",
  "configuration": {},
  "capabilities": {},
  "status": "active",
  "created_at": "2024-03-20T12:00:00Z",
  "updated_at": "2024-03-20T12:00:00Z",
  "last_heartbeat": "2024-03-20T12:00:00Z"
}
```

##### Update Agent
```http
PATCH /api/v1/agents/{agent_id}
```

Update agent details.

###### Path Parameters

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| agent_id  | UUID   | Yes      | Agent ID    |

###### Request Body
```json
{
  "name": "updated-name",
  "description": "Updated description",
  "configuration": {},
  "capabilities": {}
}
```

###### Response
```json
{
  "id": "uuid",
  "name": "updated-name",
  "agent_type": "wifi",
  "description": "Updated description",
  "configuration": {},
  "capabilities": {},
  "status": "active",
  "created_at": "2024-03-20T12:00:00Z",
  "updated_at": "2024-03-20T12:00:00Z",
  "last_heartbeat": "2024-03-20T12:00:00Z"
}
```

##### Delete Agent
```http
DELETE /api/v1/agents/{agent_id}
```

Delete an agent.

###### Path Parameters

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| agent_id  | UUID   | Yes      | Agent ID    |

###### Response
- Status: 204 No Content

##### Get Agent Status
```http
GET /api/v1/agents/{agent_id}/status
```

Get agent status and metrics.

###### Path Parameters

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| agent_id  | UUID   | Yes      | Agent ID    |

###### Response
```json
{
  "status": "active",
  "timestamp": "2024-03-20T12:00:00Z",
  "details": {
    "last_heartbeat": "2024-03-20T12:00:00Z"
  },
  "metrics": {
    "cpu": 0.5
  }
}
```

##### Update Agent Status
```http
POST /api/v1/agents/{agent_id}/status
```

Update agent status and metrics.

###### Path Parameters

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| agent_id  | UUID   | Yes      | Agent ID    |

###### Request Body
```json
{
  "status": "maintenance",
  "details": {
    "reason": "scheduled maintenance"
  },
  "metrics": {
    "cpu": 0.7
  }
}
```

###### Response
```json
{
  "status": "maintenance",
  "timestamp": "2024-03-20T12:00:00Z",
  "details": {
    "reason": "scheduled maintenance"
  },
  "metrics": {
    "cpu": 0.7
  }
}
```

##### Discover Agents
```http
GET /api/v1/agents/discover
```

Discover available agents in the system.

###### Response
```json
[
  {
    "id": "uuid",
    "name": "agent-name",
    "agent_type": "wifi",
    "status": "active",
    "last_heartbeat": "2024-03-20T12:00:00Z"
  }
]
```

#### Agent Status Values

| Status      | Description                                    |
|-------------|------------------------------------------------|
| active      | Agent is active and functioning normally       |
| inactive    | Agent is inactive or not yet activated         |
| maintenance | Agent is in maintenance mode                   |
| error       | Agent has encountered an error                 |

#### Error Responses

##### 400 Bad Request
```json
{
  "detail": "Agent creation failed: duplicate name"
}
```

##### 404 Not Found
```json
{
  "detail": "Agent not found"
}
```

##### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## 7. API Lifecycle

### 7.1 Development
- **Alpha**: Internal testing
- **Beta**: Limited external testing
- **Release Candidate**: Pre-release testing
- **General Availability**: Production release

### 7.2 Deprecation Process
1. **Announcement**: 6 months notice
2. **Documentation**: Update API docs
3. **Monitoring**: Track usage
4. **Sunset**: Remove deprecated endpoints

## 8. API Documentation

### 8.1 OpenAPI/Swagger
- **Location**: `/api/docs`
- **Version**: OpenAPI 3.0
- **Authentication**: Required for protected endpoints
- **Examples**: Included for all endpoints

### 8.2 API Guides
- [Log Ingestion API](LOG_INGESTION_API.md)
- Management API Guide (This document)
- Action API Guide (Coming Soon)
- Monitoring API Guide (Coming Soon)

## 9. Best Practices

### 9.1 Client Implementation
- Implement exponential backoff
- Handle rate limiting
- Cache responses when appropriate
- Use connection pooling
- Implement proper error handling

### 9.2 Security
- Use HTTPS only
- Implement proper token storage
- Rotate credentials regularly
- Monitor API usage
- Implement proper logging

## 10. Support

### 10.1 API Status
- **Status Page**: `/api/status`
- **Health Check**: `/api/health`
- **Version Info**: `/api/version`

### 10.2 Support Channels
- **Documentation**: `/api/docs`
- **Support Email**: api-support@opmas.org
- **Issue Tracking**: GitHub Issues
- **Slack Channel**: #opmas-api-support

## Related Documents

- [OPMAS-DS.md](../specifications/OPMAS-DS.md): Main design specification
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md): System architecture overview
- [LOG_INGESTION_API.md](LOG_INGESTION_API.md): Detailed documentation for the Log Ingestion API 