# API Documentation

## Overview

The OPMAS Management API provides a RESTful interface for managing the system. This documentation covers the API endpoints, authentication, and usage examples.

## Base URL

- Development: `http://localhost:8000`
- Staging: `https://staging-api.opmas.example.com`
- Production: `https://api.opmas.example.com`

## Authentication

### JWT Authentication
```http
Authorization: Bearer <token>
```

### API Key Authentication
```http
X-API-Key: <api-key>
```

## API Endpoints

### Authentication

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "username": "string",
    "password": "string"
}
```

Response:
```json
{
    "access_token": "string",
    "token_type": "bearer",
    "expires_in": 3600
}
```

### Configurations

#### List Configurations
```http
GET /api/v1/config
```

Response:
```json
{
    "items": [
        {
            "id": "string",
            "name": "string",
            "value": "string",
            "created_at": "string",
            "updated_at": "string"
        }
    ],
    "total": 0,
    "skip": 0,
    "limit": 10
}
```

#### Create Configuration
```http
POST /api/v1/config
Content-Type: application/json

{
    "name": "string",
    "value": "string"
}
```

### Agents

#### List Agents
```http
GET /api/v1/agents
```

Response:
```json
{
    "items": [
        {
            "id": "string",
            "name": "string",
            "type": "string",
            "status": "string",
            "created_at": "string",
            "updated_at": "string"
        }
    ],
    "total": 0,
    "skip": 0,
    "limit": 10
}
```

### Rules

#### List Rules
```http
GET /api/v1/rules
```

Response:
```json
{
    "items": [
        {
            "id": "string",
            "name": "string",
            "condition": "string",
            "action": "string",
            "enabled": true,
            "created_at": "string",
            "updated_at": "string"
        }
    ],
    "total": 0,
    "skip": 0,
    "limit": 10
}
```

## Error Handling

### Error Response Format
```json
{
    "error": {
        "code": "string",
        "message": "string",
        "details": {}
    }
}
```

### Common Error Codes
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Rate Limiting

- 100 requests per minute per IP
- 1000 requests per hour per API key

## Pagination

### Query Parameters
- `skip`: Number of items to skip (default: 0)
- `limit`: Maximum number of items to return (default: 10, max: 100)

### Response Format
```json
{
    "items": [],
    "total": 0,
    "skip": 0,
    "limit": 10
}
```

## Versioning

### URL Versioning
- Current version: `v1`
- Example: `/api/v1/resource`

### Version Header
```http
Accept: application/vnd.opmas.v1+json
```

## Webhooks

### Configuration
```http
POST /api/v1/webhooks
Content-Type: application/json

{
    "url": "string",
    "events": ["string"],
    "secret": "string"
}
```

### Event Types
- `agent.status_change`
- `rule.triggered`
- `config.updated`

### Webhook Payload
```json
{
    "event": "string",
    "timestamp": "string",
    "data": {}
}
```

## SDK Examples

### Python
```python
import requests

def get_configurations():
    response = requests.get(
        "http://localhost:8000/api/v1/config",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()
```

### JavaScript
```javascript
async function getConfigurations() {
    const response = await fetch(
        "http://localhost:8000/api/v1/config",
        {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        }
    );
    return response.json();
}
```

## Best Practices

### Security
- Use HTTPS
- Implement rate limiting
- Validate input
- Sanitize output
- Use secure headers

### Performance
- Use pagination
- Implement caching
- Optimize queries
- Monitor response times

### Error Handling
- Use appropriate status codes
- Provide detailed error messages
- Log errors properly
- Handle timeouts

## Support

### Documentation
- [API Reference](../api/reference.md)
- [Authentication Guide](../api/auth.md)
- [Webhook Guide](../api/webhooks.md)

### Contact
- API Support: api-support@opmas.example.com
- Developer Portal: https://developers.opmas.example.com
