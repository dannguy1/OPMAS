"""Update playbook model.

Revision ID: 20250530_001019
Revises: 20250529_233000
Create Date: 2025-05-30 00:10:19.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20250530_001019"
down_revision: Union[str, None] = "20250529_233000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Drop existing foreign key constraints
    op.drop_constraint("playbooks_agent_id_fkey", "playbooks", type_="foreignkey")

    # Drop existing columns
    op.drop_column("playbooks", "agent_id")
    op.drop_column("playbooks", "version")
    op.drop_column("playbooks", "is_active")

    # Add new columns
    op.add_column("playbooks", sa.Column("agent_type", sa.String(50), nullable=False))
    op.add_column("playbooks", sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("playbooks", sa.Column("extra_metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column("playbooks", sa.Column("last_executed", sa.DateTime(), nullable=True))
    op.add_column("playbooks", sa.Column("execution_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("playbooks", sa.Column("owner_id", postgresql.UUID(), nullable=True))

    # Add new foreign key constraint
    op.create_foreign_key("playbooks_owner_id_fkey", "playbooks", "users", ["owner_id"], ["id"], ondelete="SET NULL")

    # Make description nullable
    op.alter_column("playbooks", "description", existing_type=sa.String(1000), nullable=True)


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop new foreign key constraint
    op.drop_constraint("playbooks_owner_id_fkey", "playbooks", type_="foreignkey")

    # Drop new columns
    op.drop_column("playbooks", "owner_id")
    op.drop_column("playbooks", "execution_count")
    op.drop_column("playbooks", "last_executed")
    op.drop_column("playbooks", "extra_metadata")
    op.drop_column("playbooks", "enabled")
    op.drop_column("playbooks", "agent_type")

    # Add back old columns
    op.add_column("playbooks", sa.Column("agent_id", postgresql.UUID(), nullable=False))
    op.add_column("playbooks", sa.Column("version", sa.String(50), nullable=False))
    op.add_column("playbooks", sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))

    # Add back old foreign key constraint
    op.create_foreign_key("playbooks_agent_id_fkey", "playbooks", "agents", ["agent_id"], ["id"], ondelete="CASCADE")

    # Make description non-nullable
    op.alter_column("playbooks", "description", existing_type=sa.String(1000), nullable=False)
