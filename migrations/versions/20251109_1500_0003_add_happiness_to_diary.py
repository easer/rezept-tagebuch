"""Add happiness rating to diary_entries

Revision ID: 0003
Revises: 0002
Create Date: 2025-11-09 15:00:00.000000

Changes:
- Add happiness column to diary_entries (INTEGER, 1-10)
- Represents "Glücksfaktor" - how happy was the meal experience
- Optional field (NULL allowed)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add happiness rating to diary_entries
    """
    op.add_column('diary_entries',
        sa.Column('happiness', sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    """
    Remove happiness from diary_entries
    """
    op.drop_column('diary_entries', 'happiness')
