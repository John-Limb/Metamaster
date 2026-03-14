"""Add tmdb_collection_id and tmdb_collection_name to movies

Revision ID: 015
Revises: 014
Create Date: 2026-03-14
"""

import sqlalchemy as sa

from alembic import op

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("movies", sa.Column("tmdb_collection_id", sa.Integer(), nullable=True))
    op.add_column("movies", sa.Column("tmdb_collection_name", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("movies", "tmdb_collection_name")
    op.drop_column("movies", "tmdb_collection_id")
