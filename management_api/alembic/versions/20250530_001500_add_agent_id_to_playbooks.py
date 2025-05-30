"""Add agent_id to playbooks.

Revision ID: 20250530_001500
Revises: 20250530_001019
Create Date: 2025-05-30 00:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20250530_001500"
down_revision: Union[str, None] = "20250530_001019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Add agent_id column to playbooks table
    op.add_column("playbooks", sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_playbooks_agent_id_agents", "playbooks", "agents", ["agent_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Remove agent_id column from playbooks table
    op.drop_constraint("fk_playbooks_agent_id_agents", "playbooks", type_="foreignkey")
    op.drop_column("playbooks", "agent_id")
