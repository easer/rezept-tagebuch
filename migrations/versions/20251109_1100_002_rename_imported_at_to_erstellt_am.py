"""Rename imported_at to erstellt_am with timestamp default

Revision ID: 0002
Revises: 0001
Create Date: 2025-11-09 11:00:00.000000

Changes:
- Rename column imported_at → erstellt_am
- Change type from DATE to TIMESTAMP
- Set default to CURRENT_TIMESTAMP for all new recipes
- Backfill existing NULL values with created_at

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Rename imported_at to erstellt_am and change type to TIMESTAMP
    """
    # Step 1: Add new column erstellt_am with TIMESTAMP type
    op.add_column('recipes',
        sa.Column('erstellt_am', sa.TIMESTAMP(),
                  server_default=sa.text('CURRENT_TIMESTAMP'),
                  nullable=True)
    )

    # Step 2: Copy data from imported_at to erstellt_am (convert DATE to TIMESTAMP)
    op.execute("""
        UPDATE recipes
        SET erstellt_am = COALESCE(
            imported_at::timestamp,
            created_at
        )
    """)

    # Step 3: Drop old column imported_at
    op.drop_column('recipes', 'imported_at')


def downgrade() -> None:
    """
    Revert erstellt_am back to imported_at (DATE type)
    """
    # Step 1: Add back imported_at column
    op.add_column('recipes',
        sa.Column('imported_at', sa.DATE(), nullable=True)
    )

    # Step 2: Copy data back (TIMESTAMP to DATE, losing time component)
    op.execute("""
        UPDATE recipes
        SET imported_at = erstellt_am::date
        WHERE auto_imported = true
    """)

    # Step 3: Drop erstellt_am column
    op.drop_column('recipes', 'erstellt_am')
