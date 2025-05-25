"""Test log service."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from opmas_mgmt_api.core.exceptions import OPMASException
from opmas_mgmt_api.models.logs import LogEntry, LogSource
from opmas_mgmt_api.schemas.logs import LogEntryCreate, LogSourceCreate
from opmas_mgmt_api.services.logs import LogService
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


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
def log_service(mock_db, mock_nats):
    """Create log service instance."""
    return LogService(mock_db, mock_nats)


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
async def test_process_logs_success(log_service, sample_logs):
    """Test successful log processing."""
    # Mock database operations
    log_service._get_or_create_source = AsyncMock(return_value=sample_source)
    log_service._save_log_entry = AsyncMock()
    log_service._publish_log = AsyncMock()

    processed_count = await log_service.process_logs(
        logs=sample_logs, source_identifier="test-source", source_ip="192.168.1.1"
    )

    assert processed_count == 3
    assert log_service._get_or_create_source.call_count == 1
    assert log_service._save_log_entry.call_count == 3
    assert log_service._publish_log.call_count == 3


@pytest.mark.asyncio
async def test_process_logs_empty_batch(log_service):
    """Test processing empty log batch."""
    with pytest.raises(ValueError, match="At least one log entry is required"):
        await log_service.process_logs(logs=[])


@pytest.mark.asyncio
async def test_process_logs_large_batch(log_service):
    """Test processing log batch exceeding size limit."""
    large_batch = ["log entry"] * 1001

    with pytest.raises(ValueError, match="Maximum 1000 log entries per request"):
        await log_service.process_logs(logs=large_batch)


@pytest.mark.asyncio
async def test_process_logs_db_error(log_service, sample_logs):
    """Test log processing with database error."""
    log_service._get_or_create_source = AsyncMock(side_effect=IntegrityError(None, None, None))

    with pytest.raises(OPMASException, match="Failed to process logs"):
        await log_service.process_logs(logs=sample_logs)


@pytest.mark.asyncio
async def test_process_logs_nats_error(log_service, sample_logs):
    """Test log processing with NATS error."""
    log_service._get_or_create_source = AsyncMock(return_value=sample_source)
    log_service._save_log_entry = AsyncMock()
    log_service._publish_log = AsyncMock(side_effect=Exception("NATS error"))

    processed_count = await log_service.process_logs(logs=sample_logs)
    assert processed_count == 0


@pytest.mark.asyncio
async def test_get_or_create_source_new(log_service):
    """Test creating new log source."""
    # Mock database to return no existing source
    log_service.db.execute.return_value.scalar_one_or_none.return_value = None

    source = await log_service._get_or_create_source(
        identifier="new-source", ip_address="192.168.1.2"
    )

    assert source.identifier == "new-source"
    assert source.ip_address == "192.168.1.2"
    assert log_service.db.add.called
    assert log_service.db.commit.called
    assert log_service.db.refresh.called


@pytest.mark.asyncio
async def test_get_or_create_source_existing(log_service, sample_source):
    """Test getting existing log source."""
    # Mock database to return existing source
    log_service.db.execute.return_value.scalar_one_or_none.return_value = sample_source

    source = await log_service._get_or_create_source(
        identifier="test-source", ip_address="192.168.1.1"
    )

    assert source.id == sample_source.id
    assert source.identifier == sample_source.identifier
    assert not log_service.db.add.called
    assert not log_service.db.commit.called
    assert not log_service.db.refresh.called


def test_parse_log_syslog_format(log_service):
    """Test parsing syslog format log."""
    log_entry = "<34>Oct 11 22:14:15 mymachine su: 'su root' failed for lonvick on /dev/pts/8"

    parsed = log_service._parse_log(log_entry)

    assert parsed["level"] == 2  # 34 % 8
    assert parsed["facility"] == 4  # 34 // 8
    assert parsed["hostname"] == "mymachine"
    assert parsed["program"] == "su"
    assert "failed for lonvick" in parsed["message"]


def test_parse_log_raw_format(log_service):
    """Test parsing raw format log."""
    log_entry = "This is a raw log message"

    parsed = log_service._parse_log(log_entry)

    assert parsed["level"] == 6  # INFO
    assert parsed["facility"] == 1  # user-level
    assert parsed["hostname"] is None
    assert parsed["program"] is None
    assert parsed["message"] == log_entry


@pytest.mark.asyncio
async def test_save_log_entry(log_service):
    """Test saving log entry."""
    log_entry = LogEntryCreate(
        source_id=1,
        timestamp=datetime.utcnow(),
        level=6,
        facility=1,
        message="Test message",
        raw_log="Raw test message",
    )

    saved_entry = await log_service._save_log_entry(log_entry)

    assert log_service.db.add.called
    assert log_service.db.commit.called
    assert log_service.db.refresh.called
    assert saved_entry.source_id == log_entry.source_id
    assert saved_entry.message == log_entry.message


@pytest.mark.asyncio
async def test_publish_log(log_service, sample_source):
    """Test publishing log to NATS."""
    log_data = {
        "timestamp": datetime.utcnow(),
        "level": 6,
        "facility": 1,
        "hostname": "test-host",
        "program": "test-program",
        "message": "Test message",
    }

    await log_service._publish_log(log_data, sample_source)

    assert log_service.nats.publish.called
    call_args = log_service.nats.publish.call_args
    assert call_args[0][0] == "logs.ingested"
    published_data = eval(call_args[0][1])  # Convert JSON string back to dict
    assert published_data["level"] == log_data["level"]
    assert published_data["message"] == log_data["message"]
    assert published_data["source"]["id"] == sample_source.id


@pytest.mark.asyncio
async def test_get_status(log_service):
    """Test getting service status."""
    # Mock database query results
    mock_result = MagicMock()
    mock_result.total_logs = 100
    mock_result.first_log = datetime.utcnow() - timedelta(days=1)
    mock_result.last_log = datetime.utcnow()
    log_service.db.execute.return_value.first.return_value = mock_result

    status = await log_service.get_status()

    assert status["service_status"] == "running"
    assert status["nats_connection"] is True
    assert "processing_stats" in status
    assert status["processing_stats"]["total_logs"] == 100


@pytest.mark.asyncio
async def test_get_statistics(log_service):
    """Test getting log statistics."""
    # Mock database query results
    mock_total = MagicMock()
    mock_total.scalar_one.return_value = 100
    log_service.db.execute.return_value.scalar_one.return_value = 100

    mock_source_stats = [
        MagicMock(identifier="source1", count=60),
        MagicMock(identifier="source2", count=40),
    ]
    log_service.db.execute.return_value = mock_source_stats

    start_time = datetime.utcnow() - timedelta(days=1)
    end_time = datetime.utcnow()

    stats = await log_service.get_statistics(start_time, end_time)

    assert stats["total_logs"] == 100
    assert "source_stats" in stats
    assert "time_range" in stats
    assert stats["time_range"]["start"] == start_time.isoformat()
    assert stats["time_range"]["end"] == end_time.isoformat()


@pytest.mark.asyncio
async def test_get_statistics_no_time_range(log_service):
    """Test getting log statistics without time range."""
    # Mock database query results
    mock_total = MagicMock()
    mock_total.scalar_one.return_value = 100
    log_service.db.execute.return_value.scalar_one.return_value = 100

    mock_source_stats = [
        MagicMock(identifier="source1", count=60),
        MagicMock(identifier="source2", count=40),
    ]
    log_service.db.execute.return_value = mock_source_stats

    stats = await log_service.get_statistics()

    assert stats["total_logs"] == 100
    assert "source_stats" in stats
    assert "time_range" in stats
    assert stats["time_range"]["start"] is None
    assert stats["time_range"]["end"] is None
