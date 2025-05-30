"""Add agent columns.

Revision ID: 20250529_233000
Revises: 20250529_230000
Create Date: 2025-05-29 23:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20250529_233000"
down_revision: Union[str, None] = "20250529_230000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Add agent_metadata and capabilities columns to agents table
    op.add_column("agents", sa.Column("agent_metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column("agents", sa.Column("capabilities", postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column("agents", sa.Column("enabled", sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade database schema."""
    # Remove agent_metadata and capabilities columns from agents table
    op.drop_column("agents", "agent_metadata")
    op.drop_column("agents", "capabilities")
    op.drop_column("agents", "enabled")
