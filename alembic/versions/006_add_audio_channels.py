"""Add audio_channels to movie_files and episode_files

Revision ID: 006
Revises: 005
Create Date: 2026-02-19

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('movie_files', sa.Column('audio_channels', sa.Integer(), nullable=True))
    op.add_column('episode_files', sa.Column('audio_channels', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('episode_files', 'audio_channels')
    op.drop_column('movie_files', 'audio_channels')
