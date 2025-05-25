# Playbook Management API

## Overview
The Playbook Management API provides endpoints for managing playbooks and their executions in the OPMAS system. Playbooks are collections of steps that define automated workflows for handling various scenarios.

## Authentication
All endpoints require authentication using JWT tokens. Include the token in the Authorization header:
```
Authorization: Bearer <your_token>
```

## Endpoints

### List Playbooks
```http
GET /api/v1/playbooks
```

Query Parameters:
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum number of records to return (default: 100)
- `is_active` (boolean, optional): Filter by active status

Response:
```json
[
  {
    "id": 1,
    "name": "example-playbook",
    "description": "Example playbook description",
    "steps": [
      {
        "type": "command",
        "action": "example-action"
      }
    ],
    "version": "1.0.0",
    "is_active": true,
    "created_at": "2024-03-20T10:00:00Z",
    "updated_at": "2024-03-20T10:00:00Z"
  }
]
```

### Create Playbook
```http
POST /api/v1/playbooks
```

Request Body:
```json
{
  "name": "new-playbook",
  "description": "New playbook description",
  "steps": [
    {
      "type": "command",
      "action": "new-action"
    }
  ],
  "version": "1.0.0"
}
```

Response: Created playbook object

### Get Playbook
```http
GET /api/v1/playbooks/{playbook_id}
```

Response: Playbook object

### Update Playbook
```http
PUT /api/v1/playbooks/{playbook_id}
```

Request Body:
```json
{
  "name": "updated-playbook",
  "description": "Updated description",
  "steps": [
    {
      "type": "command",
      "action": "updated-action"
    }
  ],
  "version": "1.0.1",
  "is_active": true
}
```

Response: Updated playbook object

### Delete Playbook
```http
DELETE /api/v1/playbooks/{playbook_id}
```

Response:
```json
{
  "message": "Playbook deleted successfully"
}
```

### Get Playbook Status
```http
GET /api/v1/playbooks/{playbook_id}/status
```

Response:
```json
{
  "is_active": true,
  "updated_at": "2024-03-20T10:00:00Z"
}
```

### Update Playbook Status
```http
PUT /api/v1/playbooks/{playbook_id}/status
```

Request Body:
```json
{
  "is_active": false
}
```

Response: Updated status object

### Execute Playbook
```http
POST /api/v1/playbooks/{playbook_id}/execute
```

Response:
```json
{
  "id": 1,
  "playbook_id": 1,
  "status": "pending",
  "started_at": null,
  "completed_at": null,
  "results": null,
  "error_message": null,
  "created_at": "2024-03-20T10:00:00Z",
  "updated_at": "2024-03-20T10:00:00Z"
}
```

### List Playbook Executions
```http
GET /api/v1/playbooks/{playbook_id}/executions
```

Query Parameters:
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum number of records to return (default: 100)
- `status` (string, optional): Filter by execution status

Response: List of execution objects

### Get Execution
```http
GET /api/v1/playbooks/executions/{execution_id}
```

Response: Execution object

### Update Execution
```http
PUT /api/v1/playbooks/executions/{execution_id}
```

Request Body:
```json
{
  "status": "completed",
  "results": {
    "output": "Execution completed successfully"
  }
}
```

Response: Updated execution object

## Data Models

### Playbook
```json
{
  "id": "integer",
  "name": "string",
  "description": "string",
  "steps": [
    {
      "type": "string",
      "action": "string"
    }
  ],
  "version": "string",
  "is_active": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Playbook Execution
```json
{
  "id": "integer",
  "playbook_id": "integer",
  "status": "string",
  "started_at": "datetime",
  "completed_at": "datetime",
  "results": "object",
  "error_message": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid playbook name format"
}
```

### 404 Not Found
```json
{
  "detail": "Playbook not found"
}
```

### 409 Conflict
```json
{
  "detail": "Playbook with this name already exists"
}
```

## Validation Rules

1. Playbook Name:
   - Must match pattern: `^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]$`
   - Must be unique

2. Version:
   - Must match pattern: `^\d+\.\d+\.\d+$`
   - Example: "1.0.0"

3. Steps:
   - Must have at least one step
   - Each step must have:
     - `type` field
     - `action` field

4. Execution Status:
   - Must be one of: "pending", "running", "completed", "failed", "cancelled"
