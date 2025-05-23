import asyncio
import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from opmas.parsers.log_parser import LogParser
from opmas.data_models import ParsedLogEvent

@pytest.fixture
def log_parser():
    """Create a LogParser instance for testing."""
    return LogParser()

@pytest.fixture
def wifi_log_event():
    """Create a Wi-Fi related log event."""
    return {
        "event_id": "test-event-1",
        "arrival_ts_utc": datetime.utcnow().isoformat(),
        "source_ip": "192.168.1.1",
        "original_ts": "2024-03-20T10:15:30Z",
        "hostname": "router1",
        "process_name": "hostapd",
        "pid": "1234",
        "message": "wlan0: STA aa:bb:cc:dd:ee:ff authenticated",
        "structured_fields": {}
    }

@pytest.fixture
def security_log_event():
    """Create a security related log event."""
    return {
        "event_id": "test-event-2",
        "arrival_ts_utc": datetime.utcnow().isoformat(),
        "source_ip": "192.168.1.1",
        "original_ts": "2024-03-20T10:15:31Z",
        "hostname": "router1",
        "process_name": "dropbear",
        "pid": "5678",
        "message": "Failed password for root from 192.168.1.50",
        "structured_fields": {}
    }

@pytest.fixture
def connectivity_log_event():
    """Create a connectivity related log event."""
    return {
        "event_id": "test-event-3",
        "arrival_ts_utc": datetime.utcnow().isoformat(),
        "source_ip": "192.168.1.1",
        "original_ts": "2024-03-20T10:15:32Z",
        "hostname": "router1",
        "process_name": "netifd",
        "pid": "9012",
        "message": "interface eth0 up",
        "structured_fields": {}
    }

@pytest.fixture
def health_log_event():
    """Create a health related log event."""
    return {
        "event_id": "test-event-4",
        "arrival_ts_utc": datetime.utcnow().isoformat(),
        "source_ip": "192.168.1.1",
        "original_ts": "2024-03-20T10:15:33Z",
        "hostname": "router1",
        "process_name": "kernel",
        "pid": None,
        "message": "Out of memory: Kill process 1234 (nginx) score 0 or sacrifice child",
        "structured_fields": {}
    }

def test_classify_wifi_log(log_parser, wifi_log_event):
    """Test classification of Wi-Fi related logs."""
    event = ParsedLogEvent.from_dict(wifi_log_event)
    domain = log_parser._classify_log(event)
    assert domain == 'wifi'

def test_classify_security_log(log_parser, security_log_event):
    """Test classification of security related logs."""
    event = ParsedLogEvent.from_dict(security_log_event)
    domain = log_parser._classify_log(event)
    assert domain == 'security'

def test_classify_connectivity_log(log_parser, connectivity_log_event):
    """Test classification of connectivity related logs."""
    event = ParsedLogEvent.from_dict(connectivity_log_event)
    domain = log_parser._classify_log(event)
    assert domain == 'connectivity'

def test_classify_health_log(log_parser, health_log_event):
    """Test classification of health related logs."""
    event = ParsedLogEvent.from_dict(health_log_event)
    domain = log_parser._classify_log(event)
    assert domain == 'health'

def test_enrich_wifi_log(log_parser, wifi_log_event):
    """Test enrichment of Wi-Fi related logs."""
    event = ParsedLogEvent.from_dict(wifi_log_event)
    event.log_source_type = 'wifi'
    log_parser._enrich_log(event)
    
    assert 'wifi_extracted' in event.structured_fields
    assert 'metadata' in event.structured_fields
    assert event.structured_fields['metadata']['source_type'] == 'syslog'

@pytest.mark.asyncio
async def test_process_log(log_parser, wifi_log_event):
    """Test processing of a log event."""
    event = await log_parser.process_log(wifi_log_event)
    assert event is not None
    assert event.log_source_type == 'wifi'
    assert 'wifi_extracted' in event.structured_fields

@pytest.mark.asyncio
async def test_handle_raw_log(log_parser, wifi_log_event):
    """Test handling of raw log messages."""
    # Mock NATS message
    mock_msg = MagicMock()
    mock_msg.data = json.dumps(wifi_log_event).encode()
    
    # Mock NATS client publish
    log_parser.nats_client.publish = AsyncMock()
    
    # Handle the message
    await log_parser._handle_raw_log(mock_msg)
    
    # Verify NATS publish was called with correct topic
    log_parser.nats_client.publish.assert_called_once()
    args = log_parser.nats_client.publish.call_args
    assert args[0][0] == "logs.wifi"

@pytest.mark.asyncio
async def test_start_stop(log_parser):
    """Test starting and stopping the log parser service."""
    # Mock NATS client methods
    log_parser.nats_client.connect = AsyncMock()
    log_parser.nats_client.subscribe = AsyncMock()
    log_parser.nats_client.close = AsyncMock()
    
    # Start service
    await log_parser.start()
    log_parser.nats_client.connect.assert_called_once()
    log_parser.nats_client.subscribe.assert_called_once()
    
    # Stop service
    await log_parser.stop()
    log_parser.nats_client.close.assert_called_once() 