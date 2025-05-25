import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict, Optional, Tuple

import nats
from nats.aio.client import Client as NATS

from ..core.config import ConfigManager, NATSConfig, SyslogConfig
from ..core.logging import LogManager

logger = LogManager().get_logger(__name__)


class SyslogMessage:
    """Parse and validate syslog messages."""

    # RFC5424 syslog format pattern
    SYSLOG_PATTERN = r"<(\d+)>(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:?\d{2}|Z)) (\S+) (\S+) (\S+): (.+)"

    def __init__(self, raw_message: str, source_ip: str):
        self.raw_message = raw_message
        self.source_ip = source_ip
        self.priority = None
        self.timestamp = None
        self.hostname = None
        self.process = None
        self.pid = None
        self.message = None
        self.parsed = False

    def parse(self) -> bool:
        """Parse the syslog message."""
        match = re.match(self.SYSLOG_PATTERN, self.raw_message)
        if not match:
            return False

        self.priority = int(match.group(1))
        self.timestamp = match.group(2)
        self.hostname = match.group(3)
        self.process = match.group(4)
        self.pid = match.group(5)
        self.message = match.group(6)
        self.parsed = True
        return True

    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        if not self.parsed:
            return {}

        return {
            "event_id": str(uuid.uuid4()),
            "arrival_ts_utc": datetime.utcnow().isoformat(),
            "source_ip": self.source_ip,
            "original_ts": self.timestamp,
            "hostname": self.hostname,
            "process_name": self.process,
            "pid": self.pid,
            "message": self.message,
            "priority": self.priority,
            "facility": self.priority >> 3,
            "severity": self.priority & 0x07,
        }


class SyslogServer:
    """Handle syslog message reception and processing."""

    def __init__(self, config: Optional[SyslogConfig] = None):
        self.config = config or ConfigManager().get_config().syslog
        self.nats_config = ConfigManager().get_config().nats
        self.nats_client: Optional[NATS] = None
        self.server = None
        self.logger = logger

    async def start(self):
        """Start the syslog server and NATS connection."""
        # Connect to NATS
        self.nats_client = nats.NATS()
        await self.nats_client.connect(
            self.nats_config.url,
            max_reconnect_attempts=self.nats_config.max_reconnects,
            reconnect_time_wait=self.nats_config.reconnect_time_wait,
        )

        # Start syslog server
        self.server = await asyncio.start_server(
            self.handle_connection, self.config.host, self.config.port
        )

        self.logger.info(f"Syslog server started on {self.config.host}:{self.config.port}")

        async with self.server:
            await self.server.serve_forever()

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming syslog connection."""
        try:
            addr = writer.get_extra_info("peername")
            source_ip = addr[0]

            while True:
                data = await reader.read(self.config.buffer_size)
                if not data:
                    break

                message = data.decode().strip()
                await self.process_message(message, source_ip)

        except Exception as e:
            self.logger.error(f"Error handling connection from {source_ip}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def process_message(self, message: str, source_ip: str):
        """Process and forward a syslog message."""
        try:
            # Parse message
            syslog_msg = SyslogMessage(message, source_ip)
            if not syslog_msg.parse():
                self.logger.warning(f"Failed to parse syslog message: {message}")
                return

            # Convert to dictionary
            event = syslog_msg.to_dict()

            # Publish to NATS
            if self.nats_client and self.nats_client.is_connected:
                await self.nats_client.publish("logs.parsed.raw", json.dumps(event).encode())
                self.logger.debug(f"Published log event: {event['event_id']}")
            else:
                self.logger.error("NATS client not connected")

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    async def stop(self):
        """Stop the syslog server and NATS connection."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        if self.nats_client:
            await self.nats_client.close()

        self.logger.info("Syslog server stopped")


async def main():
    """Main entry point for the syslog server."""
    server = SyslogServer()
    try:
        await server.start()
    except KeyboardInterrupt:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
