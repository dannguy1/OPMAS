"""Test log ingestion endpoints."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from opmas_mgmt_api.core.exceptions import OPMASException
from opmas_mgmt_api.main import app
from opmas_mgmt_api.models.logs import LogEntry, LogSource
from opmas_mgmt_api.schemas.logs import LogEntryCreate, LogSourceCreate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

client = TestClient(app)


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_nats():
    """Create mock NATS manager."""
    nats = AsyncMock()
    nats.is_connected.return_value = True
    return nats


@pytest.fixture
def sample_logs():
    """Sample log entries for testing."""
    return [
        "<34>Oct 11 22:14:15 mymachine su: 'su root' failed for lonvick on /dev/pts/8",
        "<165>Oct 11 22:14:15 mymachine auth: Authentication failure",
        "This is a raw log message",
    ]


@pytest.fixture
def sample_source():
    """Sample log source for testing."""
    return LogSource(
        id=1,
        identifier="test-source",
        ip_address="192.168.1.1",
        first_seen=datetime.utcnow(),
        last_seen=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_ingest_logs_success(mock_db, mock_nats, sample_logs):
    """Test successful log ingestion."""
    # Mock database operations
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    # Mock NATS publish
    mock_nats.publish = AsyncMock()

    response = client.post(
        "/api/v1/logs/ingest",
        json={
            "logs": sample_logs,
            "source_identifier": "test-source",
            "explicit_source_ip": "192.168.1.1",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Successfully ingested 3 logs"
    assert data["log_count"] == 3
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_ingest_logs_empty_batch(mock_db, mock_nats):
    """Test log ingestion with empty batch."""
    response = client.post(
        "/api/v1/logs/ingest", json={"logs": [], "source_identifier": "test-source"}
    )

    assert response.status_code == 400
    assert "At least one log entry is required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_ingest_logs_large_batch(mock_db, mock_nats):
    """Test log ingestion with batch exceeding size limit."""
    large_batch = ["log entry"] * 1001

    response = client.post(
        "/api/v1/logs/ingest", json={"logs": large_batch, "source_identifier": "test-source"}
    )

    assert response.status_code == 400
    assert "Maximum 1000 log entries per request" in response.json()["detail"]


@pytest.mark.asyncio
async def test_ingest_logs_invalid_ip(mock_db, mock_nats, sample_logs):
    """Test log ingestion with invalid IP address."""
    response = client.post(
        "/api/v1/logs/ingest",
        json={
            "logs": sample_logs,
            "source_identifier": "test-source",
            "explicit_source_ip": "invalid-ip",
        },
    )

    assert response.status_code == 400
    assert "Invalid IP address format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_ingest_logs_db_error(mock_db, mock_nats, sample_logs):
    """Test log ingestion with database error."""
    mock_db.execute.side_effect = IntegrityError(None, None, None)

    response = client.post(
        "/api/v1/logs/ingest", json={"logs": sample_logs, "source_identifier": "test-source"}
    )

    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_ingest_logs_nats_error(mock_db, mock_nats, sample_logs):
    """Test log ingestion with NATS error."""
    mock_nats.publish.side_effect = Exception("NATS error")

    response = client.post(
        "/api/v1/logs/ingest", json={"logs": sample_logs, "source_identifier": "test-source"}
    )

    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_log_ingestion_status(mock_db, mock_nats):
    """Test getting log ingestion status."""
    # Mock database query results
    mock_result = MagicMock()
    mock_result.total_logs = 100
    mock_result.first_log = datetime.utcnow() - timedelta(days=1)
    mock_result.last_log = datetime.utcnow()
    mock_db.execute.return_value.first.return_value = mock_result

    response = client.get("/api/v1/logs/status")

    assert response.status_code == 200
    data = response.json()
    assert data["service_status"] == "running"
    assert data["nats_connection"] is True
    assert "processing_stats" in data
    assert data["processing_stats"]["total_logs"] == 100


@pytest.mark.asyncio
async def test_get_log_ingestion_stats(mock_db, mock_nats):
    """Test getting log ingestion statistics."""
    # Mock database query results
    mock_total = MagicMock()
    mock_total.scalar_one.return_value = 100
    mock_db.execute.return_value.scalar_one.return_value = 100

    mock_source_stats = [
        MagicMock(identifier="source1", count=60),
        MagicMock(identifier="source2", count=40),
    ]
    mock_db.execute.return_value = mock_source_stats

    start_time = datetime.utcnow() - timedelta(days=1)
    end_time = datetime.utcnow()

    response = client.get(
        f"/api/v1/logs/stats?start_time={start_time.isoformat()}&end_time={end_time.isoformat()}"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_logs"] == 100
    assert "source_stats" in data
    assert "time_range" in data
    assert data["time_range"]["start"] == start_time.isoformat()
    assert data["time_range"]["end"] == end_time.isoformat()


@pytest.mark.asyncio
async def test_get_log_ingestion_stats_no_time_range(mock_db, mock_nats):
    """Test getting log ingestion statistics without time range."""
    # Mock database query results
    mock_total = MagicMock()
    mock_total.scalar_one.return_value = 100
    mock_db.execute.return_value.scalar_one.return_value = 100

    mock_source_stats = [
        MagicMock(identifier="source1", count=60),
        MagicMock(identifier="source2", count=40),
    ]
    mock_db.execute.return_value = mock_source_stats

    response = client.get("/api/v1/logs/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["total_logs"] == 100
    assert "source_stats" in data
    assert "time_range" in data
    assert data["time_range"]["start"] is None
    assert data["time_range"]["end"] is None


@pytest.mark.asyncio
async def test_get_log_ingestion_stats_db_error(mock_db, mock_nats):
    """Test getting log ingestion statistics with database error."""
    mock_db.execute.side_effect = Exception("Database error")

    response = client.get("/api/v1/logs/stats")

    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_log_parsing_syslog_format(mock_db, mock_nats):
    """Test parsing of syslog format logs."""
    syslog_entry = "<34>Oct 11 22:14:15 mymachine su: 'su root' failed for lonvick on /dev/pts/8"

    response = client.post(
        "/api/v1/logs/ingest", json={"logs": [syslog_entry], "source_identifier": "test-source"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["log_count"] == 1


@pytest.mark.asyncio
async def test_log_parsing_raw_format(mock_db, mock_nats):
    """Test parsing of raw format logs."""
    raw_entry = "This is a raw log message"

    response = client.post(
        "/api/v1/logs/ingest", json={"logs": [raw_entry], "source_identifier": "test-source"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["log_count"] == 1


@pytest.mark.asyncio
async def test_log_source_creation(mock_db, mock_nats, sample_logs):
    """Test creation of new log source."""
    # Mock database to return no existing source
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    response = client.post(
        "/api/v1/logs/ingest",
        json={
            "logs": sample_logs,
            "source_identifier": "new-source",
            "explicit_source_ip": "192.168.1.2",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["log_count"] == 3


@pytest.mark.asyncio
async def test_log_source_reuse(mock_db, mock_nats, sample_logs, sample_source):
    """Test reuse of existing log source."""
    # Mock database to return existing source
    mock_db.execute.return_value.scalar_one_or_none.return_value = sample_source

    response = client.post(
        "/api/v1/logs/ingest", json={"logs": sample_logs, "source_identifier": "test-source"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["log_count"] == 3


@pytest.mark.asyncio
async def test_log_ingestion_with_client_ip(mock_db, mock_nats, sample_logs):
    """Test log ingestion using client IP when not explicitly provided."""
    response = client.post(
        "/api/v1/logs/ingest",
        json={"logs": sample_logs, "source_identifier": "test-source"},
        headers={"X-Forwarded-For": "192.168.1.3"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["log_count"] == 3
