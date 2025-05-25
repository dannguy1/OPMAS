"""Log ingestion service."""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from opmas_mgmt_api.core.exceptions import OPMASException
from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.models.logs import LogEntry, LogSource
from opmas_mgmt_api.schemas.logs import LogEntryCreate, LogSourceCreate
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class LogService:
    """Service for handling log ingestion and processing."""

    def __init__(self, db: AsyncSession, nats: NATSManager):
        """Initialize log service.

        Args:
            db: Database session
            nats: NATS manager
        """
        self.db = db
        self.nats = nats
        self.syslog_pattern = re.compile(
            r"<(\d+)>(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+([^:]+):\s+(.*)"
        )

    async def process_logs(
        self,
        logs: List[str],
        source_identifier: Optional[str] = None,
        source_ip: Optional[str] = None,
    ) -> int:
        """Process a batch of logs.

        Args:
            logs: List of log entries to process
            source_identifier: Optional identifier for the log source
            source_ip: Source IP address

        Returns:
            int: Number of successfully processed logs

        Raises:
            OPMASException: If processing fails
        """
        processed_count = 0

        try:
            # Get or create log source
            source = await self._get_or_create_source(source_identifier, source_ip)

            # Process each log
            for log_entry in logs:
                try:
                    # Parse log entry
                    parsed_log = self._parse_log(log_entry)

                    # Create log entry in database
                    log_entry_create = LogEntryCreate(
                        source_id=source.id,
                        timestamp=parsed_log["timestamp"],
                        level=parsed_log["level"],
                        facility=parsed_log["facility"],
                        message=parsed_log["message"],
                        raw_log=log_entry,
                    )

                    # Save to database
                    await self._save_log_entry(log_entry_create)

                    # Publish to NATS for further processing
                    await self._publish_log(parsed_log, source)

                    processed_count += 1

                except Exception as e:
                    logger.error(f"Failed to process log entry: {e}", exc_info=True)
                    continue

            return processed_count

        except Exception as e:
            logger.error(f"Log processing failed: {e}", exc_info=True)
            raise OPMASException(f"Failed to process logs: {str(e)}")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get log statistics."""
        try:
            # Get total logs count
            total_logs = await self.db.scalar(select(func.count()).select_from(LogEntry)) or 0

            # Get logs by severity in last 24 hours
            last_24h = datetime.utcnow() - timedelta(hours=24)
            severity_counts = await self.db.execute(
                select(LogEntry.level, func.count())
                .select_from(LogEntry)
                .where(LogEntry.timestamp >= last_24h)
                .group_by(LogEntry.level)
            )
            severity_stats = {row[0]: row[1] for row in severity_counts}

            return {
                "total_logs": total_logs,
                "last_24h": {
                    "error": severity_stats.get("error", 0),
                    "warning": severity_stats.get("warning", 0),
                    "info": severity_stats.get("info", 0),
                    "debug": severity_stats.get("debug", 0),
                },
            }
        except Exception as e:
            logger.error(f"Error getting log statistics: {e}")
            return {"total_logs": 0, "last_24h": {}}

    async def get_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent log entries."""
        try:
            # Query recent logs
            query = select(LogEntry).order_by(LogEntry.timestamp.desc()).limit(limit)
            result = await self.db.execute(query)
            logs = result.scalars().all()

            if not logs:
                return []

            return [
                {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat(),
                    "level": log.level,
                    "facility": log.facility,
                    "message": log.message,
                    "source": {
                        "id": log.source.id,
                        "identifier": log.source.identifier,
                        "ip_address": log.source.ip_address,
                    },
                }
                for log in logs
            ]
        except Exception as e:
            logger.error(f"Error getting recent logs: {e}")
            return []

    async def _get_or_create_source(
        self, identifier: Optional[str], ip_address: Optional[str]
    ) -> LogSource:
        """Get or create a log source.

        Args:
            identifier: Source identifier
            ip_address: Source IP address

        Returns:
            LogSource: Log source
        """
        if not identifier:
            identifier = "unknown"

        # Try to find existing source
        query = select(LogSource).where(LogSource.identifier == identifier)
        result = await self.db.execute(query)
        source = result.scalar_one_or_none()

        if not source:
            # Create new source
            source = LogSource(
                identifier=identifier,
                ip_address=ip_address,
                created_at=datetime.utcnow(),
            )
            self.db.add(source)
            await self.db.commit()
            await self.db.refresh(source)

        return source

    def _parse_log(self, log_entry: str) -> Dict[str, Any]:
        """Parse a log entry.

        Args:
            log_entry: Raw log entry

        Returns:
            Dict[str, Any]: Parsed log data

        Raises:
            ValueError: If log parsing fails
        """
        # Try syslog format first
        match = self.syslog_pattern.match(log_entry)
        if match:
            priority, timestamp, hostname, program, message = match.groups()
            facility = int(priority) // 8
            level = int(priority) % 8

            # Parse timestamp
            try:
                parsed_timestamp = datetime.strptime(
                    f"{datetime.now().year} {timestamp}", "%Y %b %d %H:%M:%S"
                )
            except ValueError:
                parsed_timestamp = datetime.utcnow()

            return {
                "timestamp": parsed_timestamp,
                "level": level,
                "facility": facility,
                "hostname": hostname,
                "program": program,
                "message": message,
            }

        # Fall back to raw text format
        return {
            "timestamp": datetime.utcnow(),
            "level": 6,  # INFO
            "facility": 1,  # user-level
            "hostname": None,
            "program": None,
            "message": log_entry,
        }

    async def _save_log_entry(self, log_entry: LogEntryCreate) -> LogEntry:
        """Save a log entry to the database.

        Args:
            log_entry: Log entry data

        Returns:
            LogEntry: Created log entry
        """
        db_log = LogEntry(**log_entry.dict())
        self.db.add(db_log)
        await self.db.commit()
        await self.db.refresh(db_log)
        return db_log

    async def _publish_log(self, log_data: Dict[str, Any], source: LogSource) -> None:
        """Publish log to NATS for further processing.

        Args:
            log_data: Parsed log data
            source: Log source
        """
        message = {
            "timestamp": log_data["timestamp"].isoformat(),
            "level": log_data["level"],
            "facility": log_data["facility"],
            "hostname": log_data["hostname"],
            "program": log_data["program"],
            "message": log_data["message"],
            "source": {
                "id": source.id,
                "identifier": source.identifier,
                "ip_address": source.ip_address,
            },
        }

        await self.nats.publish("logs.ingested", json.dumps(message))

    async def get_status(self) -> Dict[str, Any]:
        """Get log ingestion service status.

        Returns:
            Dict[str, Any]: Status information
        """
        # Get processing statistics
        stmt = select(
            func.count(LogEntry.id).label("total_logs"),
            func.min(LogEntry.timestamp).label("first_log"),
            func.max(LogEntry.timestamp).label("last_log"),
        )
        result = await self.db.execute(stmt)
        stats = result.first()

        return {
            "service_status": "running",
            "nats_connection": self.nats.is_connected(),
            "processing_stats": {
                "total_logs": stats.total_logs or 0,
                "first_log": stats.first_log.isoformat() if stats.first_log else None,
                "last_log": stats.last_log.isoformat() if stats.last_log else None,
            },
        }

    async def create_log(
        self, severity: str, message: str, source: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a new log entry."""
        try:
            log = LogEntry(
                severity=severity,
                message=message,
                source=source,
                details=details or {},
                timestamp=datetime.utcnow(),
            )
            self.db.add(log)
            await self.db.commit()

            # Publish log to NATS
            await self.nats.publish(
                "system.logs",
                {
                    "severity": severity,
                    "message": message,
                    "source": source,
                    "details": details,
                    "timestamp": log.timestamp.isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"Error creating log entry: {e}")
            raise
