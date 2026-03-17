"""Add content_type to plex_collections

Revision ID: 016
Revises: 015
Create Date: 2026-03-16
"""

import sqlalchemy as sa

from alembic import op

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "plex_collections",
        sa.Column("content_type", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("plex_collections", "content_type")
