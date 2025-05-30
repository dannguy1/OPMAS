"""Add assignee_id to actions.

Revision ID: 20250529_230000
Revises: 20250529_220000
Create Date: 2025-05-29 23:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20250529_230000"
down_revision: Union[str, None] = "20250529_220000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Add assignee_id column to actions table
    op.add_column("actions", sa.Column("assignee_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_actions_assignee_id_users", "actions", "users", ["assignee_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Remove assignee_id column from actions table
    op.drop_constraint("fk_actions_assignee_id_users", "actions", type_="foreignkey")
    op.drop_column("actions", "assignee_id")
