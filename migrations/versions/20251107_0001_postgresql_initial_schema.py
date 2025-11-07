"""PostgreSQL initial schema

Revision ID: 0001
Revises:
Create Date: 2025-11-07 00:00:00.000000

This is a fresh start for PostgreSQL migration.
The schema has already been applied via schema-postgres.sql.
This migration just marks the baseline.

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Schema is already created by schema-postgres.sql.
    This migration exists only to mark the baseline.

    If you run this on an empty database, it will create all tables.
    If you run this after applying schema-postgres.sql, it will do nothing (tables already exist).
    """
    # Check if tables already exist, if not create them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'users' not in existing_tables:
        # Create users table
        op.create_table('users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.Text(), nullable=False),
            sa.Column('name', sa.Text(), nullable=False),
            sa.Column('avatar_color', sa.Text(), server_default='#FFB6C1', nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email')
        )

    if 'recipes' not in existing_tables:
        # Create recipes table
        op.create_table('recipes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.Text(), nullable=False),
            sa.Column('image', sa.Text(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('duration', sa.Float(), nullable=True),
            sa.Column('rating', sa.Integer(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('is_system', sa.Boolean(), server_default='false', nullable=True),
            sa.Column('auto_imported', sa.Boolean(), server_default='false', nullable=True),
            sa.Column('imported_at', sa.Date(), nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_recipes_user_id', 'recipes', ['user_id'])
        op.create_index('idx_recipes_auto_imported', 'recipes', ['auto_imported'])

    if 'todos' not in existing_tables:
        # Create todos table
        op.create_table('todos',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('text', sa.Text(), nullable=False),
            sa.Column('priority', sa.Integer(), nullable=False),
            sa.Column('completed', sa.Boolean(), server_default='false', nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_todos_user_id', 'todos', ['user_id'])
        op.create_index('idx_todos_completed', 'todos', ['completed'])

    if 'diary_entries' not in existing_tables:
        # Create diary_entries table
        op.create_table('diary_entries',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('recipe_id', sa.Integer(), nullable=True),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('images', sa.Text(), nullable=True),
            sa.Column('dish_name', sa.Text(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_diary_entries_user_id', 'diary_entries', ['user_id'])
        op.create_index('idx_diary_entries_recipe_id', 'diary_entries', ['recipe_id'])
        op.create_index('idx_diary_entries_date', 'diary_entries', ['date'])


def downgrade() -> None:
    """Drop all tables"""
    op.drop_index('idx_diary_entries_date', 'diary_entries')
    op.drop_index('idx_diary_entries_recipe_id', 'diary_entries')
    op.drop_index('idx_diary_entries_user_id', 'diary_entries')
    op.drop_table('diary_entries')

    op.drop_index('idx_todos_completed', 'todos')
    op.drop_index('idx_todos_user_id', 'todos')
    op.drop_table('todos')

    op.drop_index('idx_recipes_auto_imported', 'recipes')
    op.drop_index('idx_recipes_user_id', 'recipes')
    op.drop_table('recipes')

    op.drop_table('users')
