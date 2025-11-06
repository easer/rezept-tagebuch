"""Add user_id to diary_entries

Revision ID: 20251106_0700_002
Revises: 20251104_2100_001
Create Date: 2025-11-06 07:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251106_0700_002'
down_revision = '20251104_2100_001'
branch_labels = None
depends_on = None


def upgrade():
    # Add user_id column to diary_entries table
    with op.batch_alter_table('diary_entries') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_diary_user', 'users', ['user_id'], ['id'])


def downgrade():
    # Remove user_id column from diary_entries table
    with op.batch_alter_table('diary_entries') as batch_op:
        batch_op.drop_constraint('fk_diary_user', type_='foreignkey')
        batch_op.drop_column('user_id')
