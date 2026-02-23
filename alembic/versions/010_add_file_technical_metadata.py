"""Add technical metadata columns to file_items

Revision ID: 010
Revises: 009
Create Date: 2026-02-23
"""
import sqlalchemy as sa
from alembic import op

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('file_items', sa.Column('duration_seconds', sa.Integer(), nullable=True))
    op.add_column('file_items', sa.Column('video_codec', sa.String(20), nullable=True))
    op.add_column('file_items', sa.Column('video_width', sa.Integer(), nullable=True))
    op.add_column('file_items', sa.Column('video_height', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('file_items', 'video_height')
    op.drop_column('file_items', 'video_width')
    op.drop_column('file_items', 'video_codec')
    op.drop_column('file_items', 'duration_seconds')
