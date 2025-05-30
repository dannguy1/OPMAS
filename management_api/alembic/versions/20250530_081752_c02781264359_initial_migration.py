"""Initial migration for OPMAS database schema."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c02781264359"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create tables
    op.create_table(
        "playbooks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("agent_type", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, default=True),
        sa.Column("steps", postgresql.JSONB(), nullable=False),
        sa.Column("playbook_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("last_executed", sa.DateTime(), nullable=True),
        sa.Column("execution_count", sa.Integer(), nullable=False, default=0),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table("playbooks")
