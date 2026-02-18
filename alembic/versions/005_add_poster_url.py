"""Add poster_url to movies and tv_shows

Revision ID: 005
Revises: 004
Create Date: 2026-02-18

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('movies', sa.Column('poster_url', sa.String(500), nullable=True))
    op.add_column('tv_shows', sa.Column('poster_url', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('tv_shows', 'poster_url')
    op.drop_column('movies', 'poster_url')
