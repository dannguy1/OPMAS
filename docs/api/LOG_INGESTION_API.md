# OPMAS Log Ingestion API Usage

This document describes how to send logs to the OPMAS system using its HTTP API endpoint.

## 1. Prerequisites

Before sending logs to the API, ensure the following components are running:

*   **The OPMAS Log API:** Start the API server using `uvicorn` from the OPMAS project root directory:
    ```bash
    uvicorn src.opmas.log_api:app --host 0.0.0.0 --port 8000
    ```
    *   Use `--reload` during development for automatic restarts on code changes.
    *   Replace `0.0.0.0` with `127.0.0.1` to restrict access to the local machine.
    *   Ensure the specified port (default `8000`) is available.

*   **NATS Server:** The NATS message queue must be running and accessible at the URL configured in `config/opmas_config.yaml` (default: `nats://localhost:4222`).

*   **Relevant OPMAS Agents:** Start any OPMAS agents (e.g., `WiFiAgent`, `OrchestratorAgent`, `ActionExecutorAgent`) that you expect to process the logs being sent. Run agents using the `python -m` flag to ensure correct module loading:
    ```bash
    # Example: Start WiFiAgent
    python3 -m src.opmas.agents.wifi_agent &> wifi_agent_run.log &

    # Example: Start Orchestrator
    python3 -m src.opmas.orchestrator &> orchestrator_run.log &

    # Add other agents as needed
    ```

## 2. API Endpoint Details

### 2.1 Log Ingestion Endpoint

*   **URL:** `http://<OPMAS_HOST_IP>:8000/api/v1/logs/ingest`
    *   Replace `<OPMAS_HOST_IP>` with the IP address or hostname where the OPMAS Log API (`uvicorn`) is running (use `localhost` if running on the same machine).
    *   The default port is `8000`.
*   **HTTP Method:** `POST`
*   **Required Headers:**
    *   `Content-Type: application/json`
    *   `Authorization: Bearer <JWT_TOKEN>` (Required for authenticated endpoints)

### 2.2 Status Endpoint

*   **URL:** `http://<OPMAS_HOST_IP>:8000/api/v1/logs/status`
*   **HTTP Method:** `GET`
*   **Required Headers:**
    *   `Authorization: Bearer <JWT_TOKEN>`
*   **Response:**
    ```json
    {
      "service_status": "running",
      "nats_connection": true,
      "processing_stats": {
        "total_logs": 1000,
        "first_log": "2024-03-20T10:00:00Z",
        "last_log": "2024-03-20T11:00:00Z"
      }
    }
    ```

### 2.3 Statistics Endpoint

*   **URL:** `http://<OPMAS_HOST_IP>:8000/api/v1/logs/stats`
*   **HTTP Method:** `GET`
*   **Query Parameters:**
    *   `start_time` (Optional): ISO 8601 timestamp for start of statistics period
    *   `end_time` (Optional): ISO 8601 timestamp for end of statistics period
*   **Required Headers:**
    *   `Authorization: Bearer <JWT_TOKEN>`
*   **Response:**
    ```json
    {
      "total_logs": 1000,
      "source_stats": [
        {
          "identifier": "source1",
          "count": 600
        },
        {
          "identifier": "source2",
          "count": 400
        }
      ],
      "time_range": {
        "start": "2024-03-20T10:00:00Z",
        "end": "2024-03-20T11:00:00Z"
      }
    }
    ```

## 3. Authentication

*   **JWT Token Required:** All API endpoints require a valid JWT token for authentication.
*   **Token Format:** `Bearer <JWT_TOKEN>`
*   **Token Acquisition:** Contact your system administrator to obtain a valid JWT token.
*   **Token Expiration:** Tokens expire after a configured period (default: 24 hours).
*   **Token Refresh:** Use the refresh token endpoint to obtain a new token before expiration.

## 4. Rate Limiting

*   **Default Limits:**
    *   100 requests per minute per IP address
    *   1000 requests per hour per IP address
*   **Rate Limit Headers:**
    *   `X-RateLimit-Limit`: Maximum requests allowed in the time window
    *   `X-RateLimit-Remaining`: Remaining requests in the current time window
    *   `X-RateLimit-Reset`: Time when the rate limit resets (Unix timestamp)
*   **Exceeding Limits:** Requests exceeding the rate limit will receive a `429 Too Many Requests` response.

## 5. Request Payload Structure

The API expects a JSON object in the request body:

```json
{
  "logs": [
    "raw log string 1",
    "raw log string 2",
    "<29>Apr 19 14:00:05 Hostname program[pid]: Syslog formatted line",
    "...",
    "raw log string N"
  ],
  "source_identifier": "OptionalSourceNameOrIP",
  "explicit_source_ip": "OptionalOriginalDeviceIP"
}
```

*   **`logs`** (Required, `List[str]`): A JSON array containing one or more raw log strings.
    *   The API attempts to parse lines matching the syslog format: `<PRI>Timestamp Hostname Program[PID]: Message`.
    *   Lines not matching are treated as generic raw messages.
    *   Maximum 1000 log entries per request.
*   **`source_identifier`** (Optional, `str`): A string identifying the log source (e.g., hostname, IP, application name). Used as a fallback hostname if one cannot be parsed from the log line.
*   **`explicit_source_ip`** (Optional, `str`): If provided, this IP address will be used as the `source_ip` in the `ParsedLogEvent` sent to NATS. Use this when the system sending logs to the API is a proxy or forwarder, and you want to preserve the IP of the *original* device that generated the log. If omitted or null, the IP address of the client calling the API will be used as the `source_ip`.

## 6. Expected Response (Success)

### 6.1 Log Ingestion Response

If the API receives the request successfully, it processes the logs and returns:

*   **Status Code:** `200 OK`
*   **Response Body:**
    ```json
    {
      "message": "Successfully ingested N logs",
      "log_count": N,
      "timestamp": "2024-03-20T10:00:00Z"
    }
    ```
    *_(Where `N` is the number of log lines processed.)*

### 6.2 Status Response

*   **Status Code:** `200 OK`
*   **Response Body:** See section 2.2 for response format.

### 6.3 Statistics Response

*   **Status Code:** `200 OK`
*   **Response Body:** See section 2.3 for response format.

## 7. Error Responses

The API may return the following error responses:

*   **400 Bad Request:**
    ```json
    {
      "error": "Invalid request format",
      "details": "Missing required field: logs"
    }
    ```
    or
    ```json
    {
      "error": "Invalid request format",
      "details": "Maximum 1000 log entries per request"
    }
    ```
    or
    ```json
    {
      "error": "Invalid request format",
      "details": "Invalid IP address format"
    }
    ```
*   **401 Unauthorized:**
    ```json
    {
      "error": "Authentication required",
      "details": "Missing or invalid JWT token"
    }
    ```
*   **403 Forbidden:**
    ```json
    {
      "error": "Permission denied",
      "details": "Insufficient permissions to access this endpoint"
    }
    ```
*   **429 Too Many Requests:**
    ```json
    {
      "error": "Rate limit exceeded",
      "details": "Too many requests from this IP address"
    }
    ```
*   **500 Internal Server Error:**
    ```json
    {
      "error": "Internal server error",
      "details": "An unexpected error occurred while processing your request"
    }
    ```

## 8. Examples

### Example 1: Using `curl`

```bash
# Note: For multi-line JSON with curl's -d, ensure proper shell escaping
# or use @filename syntax to read data from a file.
# Example including explicit_source_ip:
curl -X POST "http://localhost:8000/api/v1/logs/ingest" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
-d '{
  "logs": [
    "<29>Apr 19 15:10:05 TestDevice wpa_supplicant[1501]: wlan0: CTRL-EVENT-AUTH-REJECT sa=aa:bb:cc:11:22:44 reason=1 status_code=1",
    "Some random application log message without syslog format",
    "<86>Apr 19 15:10:10 OtherDevice dropbear[2105]: Bad password attempt for '''root''' from 192.168.1.100:12345"
  ],
  "source_identifier": "LogForwarderSystem",
  "explicit_source_ip": "10.0.0.55"
}'

# Get log ingestion status
curl -X GET "http://localhost:8000/api/v1/logs/status" \
-H "Authorization: Bearer <YOUR_JWT_TOKEN>"

# Get log statistics for the last hour
curl -X GET "http://localhost:8000/api/v1/logs/stats?start_time=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)&end_time=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
-H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

### Example 2: Using Python (`requests` library)

*(Install the library first: `pip install requests`)*

```python
import requests
import json
from datetime import datetime, timedelta

api_url = "http://localhost:8000/api/v1/logs" # Replace localhost if needed
jwt_token = "<YOUR_JWT_TOKEN>" # Replace with your actual JWT token

# Headers for all requests
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {jwt_token}"
}

# Example 1: Send logs
log_payload = {
    "logs": [
        "<29>Apr 19 15:10:05 TestDevice wpa_supplicant[1501]: wlan0: CTRL-EVENT-AUTH-REJECT sa=aa:bb:cc:11:22:44 reason=1 status_code=1",
        "Some random application log message without syslog format",
        "<86>Apr 19 15:10:10 OtherDevice dropbear[2105]: Bad password attempt for 'root' from 192.168.1.100:12345"
    ],
    "source_identifier": "MyPythonScript",
    "explicit_source_ip": "10.0.0.55"
}

try:
    # Send logs
    response = requests.post(f"{api_url}/ingest", headers=headers, json=log_payload, timeout=10)
    response.raise_for_status()
    print(f"Log Ingestion Response: {response.json()}")

    # Get status
    response = requests.get(f"{api_url}/status", headers=headers)
    response.raise_for_status()
    print(f"Status Response: {response.json()}")

    # Get statistics for the last hour
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    params = {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    response = requests.get(f"{api_url}/stats", headers=headers, params=params)
    response.raise_for_status()
    print(f"Statistics Response: {response.json()}")

except requests.exceptions.RequestException as e:
    print(f"Error making API request: {e}")
except json.JSONDecodeError:
    print(f"Error decoding API response: {response.text}")
```

## 9. Important Notes

*   **Log Processing:** Logs are processed synchronously and stored in the database before being published to NATS. The API response indicates successful processing of all logs.
*   **Error Handling:** If NATS is unavailable or other errors occur during processing, they will be logged by the API server and may result in a 500 error response.
*   **Log Format:** The API primarily attempts to parse the specific syslog format identified. Enhance `src/opmas/parsing_utils.py` to support additional structured formats if needed.
*   **Source IP Precedence:** If `explicit_source_ip` is provided in the request, it will override the IP address of the client making the API call when populating the `source_ip` field in the published NATS message.
*   **Authentication:** Always include a valid JWT token in the Authorization header. Token expiration and refresh should be handled by the client.
*   **Rate Limiting:** Monitor the rate limit headers to avoid exceeding the allowed request limits. Implement appropriate backoff strategies when rate limits are encountered.
*   **Statistics Time Range:** When querying statistics, ensure the time range is reasonable. Very large time ranges may result in slower response times.
*   **Status Monitoring:** Use the status endpoint to monitor the health of the log ingestion service and its connection to NATS.
*   **Source Tracking:** The API maintains statistics about log sources, including the number of logs received from each source and when they were first and last seen.
 