# OPMAS Management API Overview

## API Structure
The OPMAS Management API follows RESTful principles and is organized into the following main sections:

### Base URL
```
/api/v1
```

### Authentication
All API endpoints require authentication using JWT tokens. Include the token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

### Response Format
All responses follow a standard format:
```json
{
    "status": "success" | "error",
    "data": <response_data>,
    "message": "Optional message",
    "errors": ["Optional error messages"]
}
```

## Core Endpoints

### Authentication
- `POST /api/v1/auth/token` - Get access token
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/users` - Create new user

### Device Management
- `GET /api/v1/devices` - List all devices
- `POST /api/v1/devices` - Create new device
- `GET /api/v1/devices/{id}` - Get device details
- `PUT /api/v1/devices/{id}` - Update device
- `DELETE /api/v1/devices/{id}` - Delete device

### Agent Management
- `GET /api/v1/agents` - List all agents
- `POST /api/v1/agents` - Create new agent
- `GET /api/v1/agents/{id}` - Get agent details
- `PUT /api/v1/agents/{id}` - Update agent
- `DELETE /api/v1/agents/{id}` - Delete agent

### Playbook Management
- `GET /api/v1/playbooks` - List all playbooks
- `POST /api/v1/playbooks` - Create new playbook
- `GET /api/v1/playbooks/{id}` - Get playbook details
- `PUT /api/v1/playbooks/{id}` - Update playbook
- `DELETE /api/v1/playbooks/{id}` - Delete playbook

### Rule Management
- `GET /api/v1/rules` - List all rules
- `POST /api/v1/rules` - Create new rule
- `GET /api/v1/rules/{id}` - Get rule details
- `PUT /api/v1/rules/{id}` - Update rule
- `DELETE /api/v1/rules/{id}` - Delete rule

### System Management
- `GET /api/v1/system/health` - Check system health
- `GET /api/v1/system/metrics` - Get system metrics
- `GET /api/v1/system/config` - Get system configuration
- `PUT /api/v1/system/config` - Update system configuration

## Error Handling

### HTTP Status Codes
- `200 OK` - Request successful
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Error Response Format
```json
{
    "status": "error",
    "detail": "Error message",
    "code": "ERROR_CODE"
}
```

## Rate Limiting
- Default: 60 requests per minute per IP
- Headers:
  - `X-RateLimit-Limit`: Maximum requests per minute
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time until limit resets

## Security
- All endpoints require HTTPS
- JWT-based authentication
- Rate limiting
- Input validation
- CORS configuration
- Security headers

## Pagination
List endpoints support pagination using query parameters:
- `skip`: Number of records to skip
- `limit`: Maximum number of records to return

Example:
```
GET /api/v1/devices?skip=0&limit=10
```

## Filtering and Sorting
List endpoints support filtering and sorting:
- `filter`: Filter criteria
- `sort`: Sort field and direction

Example:
```
GET /api/v1/devices?filter=status:active&sort=name:asc
```

## Versioning
- Current version: v1
- Version included in URL path
- Backward compatibility maintained
- Breaking changes require new version

## API Documentation
- Interactive documentation available at `/docs`
- OpenAPI specification at `/openapi.json`
- ReDoc documentation at `/redoc`

## Best Practices
1. Always use HTTPS
2. Include proper error handling
3. Validate input data
4. Use appropriate HTTP methods
5. Follow RESTful principles
6. Implement proper authentication
7. Use rate limiting
8. Monitor API usage

## Example Usage

### Authentication
```bash
# Get access token
curl -X POST "https://api.example.com/api/v1/auth/token" \
     -H "Content-Type: application/json" \
     -d '{"username": "user", "password": "pass"}'

# Use token
curl "https://api.example.com/api/v1/devices" \
     -H "Authorization: Bearer <token>"
```

### Device Management
```bash
# Create device
curl -X POST "https://api.example.com/api/v1/devices" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
           "hostname": "device1",
           "ip_address": "192.168.1.1",
           "device_type": "router"
         }'

# List devices
curl "https://api.example.com/api/v1/devices" \
     -H "Authorization: Bearer <token>"
```

## Support
For API support:
1. Check the [Troubleshooting Guide](../maintenance/troubleshooting.md)
2. Review the [FAQ](../maintenance/faq.md)
3. Open an issue in the project repository
4. Contact the development team
