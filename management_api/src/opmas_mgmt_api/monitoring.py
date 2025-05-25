import time

from fastapi import Request
from fastapi.responses import Response
from prometheus_client import REGISTRY, Counter, Gauge, Histogram
from prometheus_client.openmetrics.exposition import generate_latest

# Request metrics
http_requests_total = Counter(
    "http_requests_total", "Total number of HTTP requests", ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds", "HTTP request duration in seconds", ["method", "endpoint"]
)

# Playbook metrics
playbook_execution_total = Counter(
    "playbook_execution_total", "Total number of playbook executions", ["playbook_id", "status"]
)

playbook_execution_duration_seconds = Histogram(
    "playbook_execution_duration_seconds", "Playbook execution duration in seconds", ["playbook_id"]
)

active_playbooks = Gauge("active_playbooks", "Number of active playbooks")

# Database metrics
db_operation_duration_seconds = Histogram(
    "db_operation_duration_seconds", "Database operation duration in seconds", ["operation"]
)


async def metrics_middleware(request: Request, call_next):
    start_time = time.time()

    # Process the request
    response = await call_next(request)

    # Record metrics
    duration = time.time() - start_time
    http_requests_total.labels(
        method=request.method, endpoint=request.url.path, status=response.status_code
    ).inc()

    http_request_duration_seconds.labels(method=request.method, endpoint=request.url.path).observe(
        duration
    )

    return response


async def metrics_endpoint():
    return Response(generate_latest(REGISTRY), media_type="text/plain")


def record_playbook_execution(playbook_id: int, status: str, duration: float):
    playbook_execution_total.labels(playbook_id=playbook_id, status=status).inc()

    playbook_execution_duration_seconds.labels(playbook_id=playbook_id).observe(duration)


def update_active_playbooks(count: int):
    active_playbooks.set(count)


def record_db_operation(operation: str, duration: float):
    db_operation_duration_seconds.labels(operation=operation).observe(duration)
