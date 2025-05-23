import asyncio
import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from opmas.api.log_ingestion import SyslogMessage, SyslogServer
from opmas.core.config import SyslogConfig, NATSConfig

@pytest.fixture
def valid_syslog_message():
    """Create a valid syslog message."""
    return '<134>2024-03-20T10:15:30Z router1 hostapd 1234: wlan0: STA authenticated'

@pytest.fixture
def invalid_syslog_message():
    """Create an invalid syslog message."""
    return 'Invalid syslog message format'

def test_syslog_message_parse_valid(valid_syslog_message):
    """Test parsing a valid syslog message."""
    msg = SyslogMessage(valid_syslog_message, "192.168.1.1")
    assert msg.parse() is True
    assert msg.priority == 134
    assert msg.timestamp == "2024-03-20T10:15:30Z"
    assert msg.hostname == "router1"
    assert msg.process == "hostapd"
    assert msg.pid == "1234"
    assert msg.message == "wlan0: STA authenticated"

def test_syslog_message_parse_invalid(invalid_syslog_message):
    """Test parsing an invalid syslog message."""
    msg = SyslogMessage(invalid_syslog_message, "192.168.1.1")
    assert msg.parse() is False
    assert msg.parsed is False

def test_syslog_message_to_dict(valid_syslog_message):
    """Test converting syslog message to dictionary."""
    msg = SyslogMessage(valid_syslog_message, "192.168.1.1")
    msg.parse()
    event = msg.to_dict()
    
    assert "event_id" in event
    assert "arrival_ts_utc" in event
    assert event["source_ip"] == "192.168.1.1"
    assert event["original_ts"] == "2024-03-20T10:15:30Z"
    assert event["hostname"] == "router1"
    assert event["process_name"] == "hostapd"
    assert event["pid"] == "1234"
    assert event["message"] == "wlan0: STA authenticated"
    assert event["priority"] == 134
    assert event["facility"] == 16
    assert event["severity"] == 6

@pytest.mark.asyncio
async def test_syslog_server_start_stop():
    """Test starting and stopping the syslog server."""
    config = SyslogConfig(host="127.0.0.1", port=0)  # Use port 0 for testing
    nats_config = NATSConfig(url="nats://localhost:4222")
    
    with patch('nats.NATS') as mock_nats:
        # Mock NATS client
        mock_nats_client = AsyncMock()
        mock_nats.return_value = mock_nats_client
        mock_nats_client.is_connected = True
        
        # Create and start server
        server = SyslogServer(config)
        server_task = asyncio.create_task(server.start())
        
        # Wait for server to start
        await asyncio.sleep(0.1)
        
        # Stop server
        await server.stop()
        server_task.cancel()
        
        # Verify NATS connection
        mock_nats_client.connect.assert_called_once()
        mock_nats_client.close.assert_called_once()

@pytest.mark.asyncio
async def test_syslog_server_process_message():
    """Test processing a syslog message."""
    config = SyslogConfig(host="127.0.0.1", port=0)
    nats_config = NATSConfig(url="nats://localhost:4222")
    
    with patch('nats.NATS') as mock_nats:
        # Mock NATS client
        mock_nats_client = AsyncMock()
        mock_nats.return_value = mock_nats_client
        mock_nats_client.is_connected = True
        
        # Create server
        server = SyslogServer(config)
        server.nats_client = mock_nats_client
        
        # Process test message
        test_message = '<134>2024-03-20T10:15:30Z router1 hostapd 1234: wlan0: STA authenticated'
        await server.process_message(test_message, "192.168.1.1")
        
        # Verify NATS publish
        mock_nats_client.publish.assert_called_once()
        args = mock_nats_client.publish.call_args
        assert args[0][0] == "logs.parsed.raw"
        
        # Verify published message
        published_data = json.loads(args[0][1].decode())
        assert published_data["hostname"] == "router1"
        assert published_data["process_name"] == "hostapd"
        assert published_data["message"] == "wlan0: STA authenticated" 