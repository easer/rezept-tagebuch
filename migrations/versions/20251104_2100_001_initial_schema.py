"""Initial schema - v2.1

Revision ID: 001
Revises:
Create Date: 2025-11-04 21:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema"""

    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('avatar_color', sa.Text(), nullable=True, server_default='#FFB6C1'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Recipes table
    op.create_table(
        'recipes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('image', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('duration', sa.Real(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_system', sa.Integer(), nullable=True, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # TODOs table
    op.create_table(
        'todos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='2'),
        sa.Column('completed', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Insert default user (Natalie)
    op.execute("""
        INSERT INTO users (id, name, email, avatar_color)
        VALUES (1, 'Natalie', 'natalie@seaser.local', '#FFB6C1')
    """)


def downgrade() -> None:
    """Drop all tables"""
    op.drop_table('todos')
    op.drop_table('recipes')
    op.drop_table('users')
