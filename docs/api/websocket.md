# WebSocket API Documentation

## Overview

The OPMAS Management API provides WebSocket endpoints for real-time updates on devices, agents, rules, and system metrics. All WebSocket connections require authentication using a JWT token.

## Authentication

To connect to any WebSocket endpoint, you must provide a valid JWT token as a query parameter:

```javascript
const token = 'your.jwt.token';
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/devices?token=${token}`);
```

## Available Endpoints

### Device Updates
- **Endpoint**: `/api/v1/ws/devices`
- **Purpose**: Real-time device status and event updates
- **Example**:
```javascript
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/devices?token=${token}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle device update
  console.log('Device update:', data);
};
```

### Agent Updates
- **Endpoint**: `/api/v1/ws/agents`
- **Purpose**: Real-time agent status and event updates
- **Example**:
```javascript
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/agents?token=${token}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle agent update
  console.log('Agent update:', data);
};
```

### Rule Updates
- **Endpoint**: `/api/v1/ws/rules`
- **Purpose**: Real-time rule execution updates
- **Example**:
```javascript
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/rules?token=${token}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle rule update
  console.log('Rule update:', data);
};
```

### System Updates
- **Endpoint**: `/api/v1/ws/system`
- **Purpose**: Real-time system metrics and events
- **Example**:
```javascript
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/system?token=${token}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle system update
  console.log('System update:', data);
};
```

## Message Format

All WebSocket messages follow this format:

```json
{
  "type": "event_type",
  "subject": "nats.subject",
  "data": {
    // Event-specific data
  }
}
```

### Event Types

1. **Device Events**:
   - `device.status_update`
   - `device.config_change`
   - `device.error`

2. **Agent Events**:
   - `agent.status_update`
   - `agent.task_complete`
   - `agent.error`

3. **Rule Events**:
   - `rule.execution_start`
   - `rule.execution_complete`
   - `rule.triggered`

4. **System Events**:
   - `system.metrics`
   - `system.alert`
   - `system.status`

## Error Handling

WebSocket connections may close with the following status codes:

- `4001`: Authentication failed (missing or invalid token)
- `1000`: Normal closure
- `1006`: Abnormal closure
- `1011`: Internal error

## Best Practices

1. **Reconnection Strategy**:
```javascript
function connectWebSocket() {
  const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/devices?token=${token}`);

  ws.onclose = (event) => {
    if (event.code === 4001) {
      // Authentication error - refresh token and reconnect
      refreshToken().then(newToken => {
        token = newToken;
        setTimeout(connectWebSocket, 1000);
      });
    } else {
      // Other errors - attempt to reconnect
      setTimeout(connectWebSocket, 1000);
    }
  };

  return ws;
}
```

2. **Heartbeat**:
```javascript
function setupHeartbeat(ws) {
  const interval = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }));
    }
  }, 30000);

  ws.onclose = () => clearInterval(interval);
}
```

3. **Error Handling**:
```javascript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  // Implement your error handling logic
};
```

## Security Considerations

1. Always use secure WebSocket connections (`wss://`) in production
2. Implement token refresh before expiration
3. Validate all received messages
4. Implement rate limiting for client messages
5. Monitor connection health and implement automatic reconnection

## Example Implementation

Here's a complete example of a WebSocket client:

```javascript
class OPMASWebSocket {
  constructor(endpoint, token) {
    this.endpoint = endpoint;
    this.token = token;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
  }

  connect() {
    this.ws = new WebSocket(`${this.endpoint}?token=${this.token}`);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.setupHeartbeat();
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onclose = (event) => {
      this.handleClose(event);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  setupHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }

  handleMessage(data) {
    switch (data.type) {
      case 'device.status_update':
        // Handle device status update
        break;
      case 'agent.status_update':
        // Handle agent status update
        break;
      // Add more event handlers
    }
  }

  handleClose(event) {
    clearInterval(this.heartbeatInterval);

    if (event.code === 4001) {
      // Authentication error - refresh token
      this.refreshToken().then(() => {
        this.connect();
      });
    } else if (this.reconnectAttempts < this.maxReconnectAttempts) {
      // Attempt to reconnect
      this.reconnectAttempts++;
      setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts);
    }
  }

  async refreshToken() {
    // Implement token refresh logic
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}
```

## Support

For issues or questions about the WebSocket API, please:
1. Check the [API Documentation](../api/README.md)
2. Review the [Troubleshooting Guide](../development/troubleshooting.md)
3. Contact the development team
