"""remove agent owner_id

Revision ID: 6fb0e22afd5e
Revises: 
Create Date: 2025-05-28 04:12:38.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6fb0e22afd5e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the foreign key constraint first
    op.drop_constraint('agents_owner_id_fkey', 'agents', type_='foreignkey')
    
    # Drop the owner_id column
    op.drop_column('agents', 'owner_id')


def downgrade() -> None:
    # Add the owner_id column back
    op.add_column('agents', sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False))
    
    # Add the foreign key constraint back
    op.create_foreign_key(
        'agents_owner_id_fkey',
        'agents',
        'users',
        ['owner_id'],
        ['id']
    )
