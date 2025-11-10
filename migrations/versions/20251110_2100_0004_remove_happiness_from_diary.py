"""Remove happiness from diary_entries

Revision ID: 0004
Revises: 0003
Create Date: 2025-11-10 21:00:00.000000

Changes:
- Remove happiness column from diary_entries
- Feature rollback: Glücksfaktor not needed
"""
from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove happiness from diary_entries"""
    op.drop_column('diary_entries', 'happiness')


def downgrade() -> None:
    """Restore happiness to diary_entries"""
    op.add_column('diary_entries',
        sa.Column('happiness', sa.Integer(), nullable=True)
    )
