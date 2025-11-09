"""Add rating to diary_entries

Revision ID: 0002
Revises: 0001
Create Date: 2025-11-09 14:00:00.000000

Changes:
- Add rating column to diary_entries (INTEGER)
- Migrate existing recipe ratings to diary entries
- For fresh installations: rating is already in 0001
- For existing PROD: adds rating column and migrates data

Note: recipes.rating stays for now (deprecated, will be removed in future migration)
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
    Add rating to diary_entries (idempotent) and migrate existing data
    """
    # Check if column already exists (fresh install from updated 0001)
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('diary_entries')]

    if 'rating' not in columns:
        # Add rating column to diary_entries
        op.add_column('diary_entries',
            sa.Column('rating', sa.Integer(), nullable=True)
        )

    # Migrate existing recipe ratings to diary entries
    # Copy rating from recipes to diary_entries where diary entry has a recipe
    op.execute("""
        UPDATE diary_entries
        SET rating = recipes.rating
        FROM recipes
        WHERE diary_entries.recipe_id = recipes.id
        AND recipes.rating IS NOT NULL
        AND diary_entries.rating IS NULL
    """)


def downgrade() -> None:
    """
    Remove rating from diary_entries
    """
    op.drop_column('diary_entries', 'rating')
