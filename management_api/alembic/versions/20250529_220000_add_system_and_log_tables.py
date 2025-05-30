"""Add system and log tables.

Revision ID: 20250529_220000
Revises: 20250528_041238_6fb0e22afd5e
Create Date: 2025-05-29 22:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20250529_220000"
down_revision: Union[str, None] = "20250528_041238_6fb0e22afd5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create system_events table
    op.create_table(
        "system_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("message", sa.String(1000), nullable=False),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    # Create system_configs table
    op.create_table(
        "system_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("components", postgresql.JSONB, nullable=False),
        sa.Column("security", postgresql.JSONB, nullable=False),
        sa.Column("logging", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Create log_sources table
    op.create_table(
        "log_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("identifier", sa.String(255), nullable=False),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Create log_entries table
    op.create_table(
        "log_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("level", sa.String(50), nullable=False),
        sa.Column("facility", sa.String(50), nullable=False),
        sa.Column("message", sa.String(1000), nullable=False),
        sa.Column("raw_log", sa.Text, nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["log_sources.id"], ondelete="CASCADE"),
    )

    # Create indexes
    op.create_index("ix_system_events_timestamp", "system_events", ["timestamp"])
    op.create_index("ix_system_configs_created_at", "system_configs", ["created_at"])
    op.create_index("ix_log_sources_identifier", "log_sources", ["identifier"])
    op.create_index("ix_log_entries_timestamp", "log_entries", ["timestamp"])
    op.create_index("ix_log_entries_level", "log_entries", ["level"])


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop indexes
    op.drop_index("ix_log_entries_level")
    op.drop_index("ix_log_entries_timestamp")
    op.drop_index("ix_log_sources_identifier")
    op.drop_index("ix_system_configs_created_at")
    op.drop_index("ix_system_events_timestamp")

    # Drop tables
    op.drop_table("log_entries")
    op.drop_table("log_sources")
    op.drop_table("system_configs")
    op.drop_table("system_events")
