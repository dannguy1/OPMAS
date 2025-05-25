"""Log ingestion service."""

import json
import logging
import re
from datetime import datetime
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

    async def _get_or_create_source(
        self, identifier: Optional[str], ip_address: Optional[str]
    ) -> LogSource:
        """Get or create a log source.

        Args:
            identifier: Source identifier
            ip_address: Source IP address

        Returns:
            LogSource: Log source instance
        """
        # Try to find existing source
        if identifier:
            stmt = select(LogSource).where(LogSource.identifier == identifier)
            result = await self.db.execute(stmt)
            source = result.scalar_one_or_none()
            if source:
                return source

        # Create new source
        source_create = LogSourceCreate(
            identifier=identifier,
            ip_address=ip_address,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
        )

        source = LogSource(**source_create.dict())
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

    async def get_statistics(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get log ingestion statistics.

        Args:
            start_time: Optional start time for statistics
            end_time: Optional end time for statistics

        Returns:
            Dict[str, Any]: Statistics
        """
        # Build base query
        query = select(LogEntry)

        # Apply time filters
        if start_time:
            query = query.where(LogEntry.timestamp >= start_time)
        if end_time:
            query = query.where(LogEntry.timestamp <= end_time)

        # Get total logs
        total_stmt = select(func.count(LogEntry.id)).select_from(query.subquery())
        total_result = await self.db.execute(total_stmt)
        total_logs = total_result.scalar_one()

        # Get source statistics
        source_stmt = (
            select(LogSource.identifier, func.count(LogEntry.id).label("count"))
            .join(LogEntry)
            .group_by(LogSource.identifier)
        )

        source_result = await self.db.execute(source_stmt)
        source_stats = {row.identifier: row.count for row in source_result}

        return {
            "total_logs": total_logs,
            "source_stats": source_stats,
            "time_range": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None,
            },
        }
