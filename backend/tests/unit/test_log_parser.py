from datetime import datetime

import pytest

from opmas.core.parser import LogParser, ParsedLogEntry


def test_parse_wifi_log():
    """Test parsing of a WiFi authentication log entry."""
    parser = LogParser()
    log_entry = "Apr 18 15:02:17 OpenWRT-Router1 hostapd: wlan0: STA authenticated"

    result = parser.parse(log_entry)

    assert isinstance(result, ParsedLogEntry)
    assert result.event_type == "wifi"
    assert result.device_hostname == "OpenWRT-Router1"
    assert result.process_name == "hostapd"
    assert result.interface == "wlan0"
    assert result.event == "STA authenticated"
    assert isinstance(result.timestamp, datetime)


def test_parse_system_log():
    """Test parsing of a system log entry."""
    parser = LogParser()
    log_entry = (
        "Apr 18 15:02:17 OpenWRT-Router1 kernel: [12345.678] CPU temperature above threshold"
    )

    result = parser.parse(log_entry)

    assert isinstance(result, ParsedLogEntry)
    assert result.event_type == "system"
    assert result.device_hostname == "OpenWRT-Router1"
    assert result.process_name == "kernel"
    assert result.event == "CPU temperature above threshold"
    assert isinstance(result.timestamp, datetime)


def test_parse_network_log():
    """Test parsing of a network log entry."""
    parser = LogParser()
    log_entry = "Apr 18 15:02:17 OpenWRT-Router1 dnsmasq: DHCPACK(eth0) 192.168.1.100"

    result = parser.parse(log_entry)

    assert isinstance(result, ParsedLogEntry)
    assert result.event_type == "network"
    assert result.device_hostname == "OpenWRT-Router1"
    assert result.process_name == "dnsmasq"
    assert result.event == "DHCPACK(eth0) 192.168.1.100"
    assert isinstance(result.timestamp, datetime)


def test_parse_invalid_log():
    """Test parsing of an invalid log entry."""
    parser = LogParser()
    log_entry = "Invalid log format"

    with pytest.raises(ValueError):
        parser.parse(log_entry)


def test_parse_log_with_metadata():
    """Test parsing of a log entry with additional metadata."""
    parser = LogParser()
    log_entry = "Apr 18 15:02:17 OpenWRT-Router1 hostapd: wlan0: STA authenticated"
    metadata = {"source": "syslog", "facility": "daemon"}

    result = parser.parse(log_entry, metadata=metadata)

    assert isinstance(result, ParsedLogEntry)
    assert result.metadata["source"] == "syslog"
    assert result.metadata["facility"] == "daemon"


def test_parse_multiple_logs():
    """Test parsing of multiple log entries."""
    parser = LogParser()
    log_entries = [
        "Apr 18 15:02:17 OpenWRT-Router1 hostapd: wlan0: STA authenticated",
        "Apr 18 15:02:18 OpenWRT-Router1 kernel: [12345.678] CPU temperature above threshold",
        "Apr 18 15:02:19 OpenWRT-Router1 dnsmasq: DHCPACK(eth0) 192.168.1.100",
    ]

    results = [parser.parse(entry) for entry in log_entries]

    assert len(results) == 3
    assert results[0].event_type == "wifi"
    assert results[1].event_type == "system"
    assert results[2].event_type == "network"
