"""Move rating from recipes to diary_entries

Revision ID: 0003
Revises: 0002
Create Date: 2025-11-09 13:15:00.000000

Changes:
- Add rating column to diary_entries (INTEGER)
- Migrate existing ratings from recipes to diary_entries (where recipe_id matches)
- Keep recipes.rating column as deprecated (for backward compatibility)
- Future: recipes.rating can be dropped in a later migration

Migration Strategy:
- For each diary_entry that has a recipe_id, copy the recipe's rating
- New diary entries will have rating=NULL until user sets it
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
    Add rating to diary_entries and migrate existing ratings
    """
    # Step 1: Add rating column to diary_entries
    op.add_column('diary_entries',
        sa.Column('rating', sa.Integer(), nullable=True)
    )

    # Step 2: Migrate existing ratings from recipes to diary_entries
    # For each diary_entry with a recipe_id, copy the recipe's rating
    op.execute("""
        UPDATE diary_entries de
        SET rating = r.rating
        FROM recipes r
        WHERE de.recipe_id = r.id
          AND r.rating IS NOT NULL
    """)

    # Note: We're keeping recipes.rating for now (deprecated)
    # It can be dropped in a future migration after confirming app works correctly


def downgrade() -> None:
    """
    Remove rating from diary_entries

    Note: This downgrade will LOSE per-diary-entry ratings!
    Only use this if you need to rollback immediately after upgrade.
    """
    op.drop_column('diary_entries', 'rating')
