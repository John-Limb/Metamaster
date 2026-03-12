"""Add mismatch support to plex_sync_records

Revision ID: 013
Revises: 012
Create Date: 2026-03-11
"""

import sqlalchemy as sa

from alembic import op

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE plexsyncstatus ADD VALUE IF NOT EXISTS 'mismatch'")
    op.add_column(
        "plex_sync_records",
        sa.Column("plex_tmdb_id", sa.String(50), nullable=True),
    )


def downgrade() -> None:
    op.execute("UPDATE plex_sync_records SET sync_status = 'failed' WHERE sync_status = 'mismatch'")
    op.drop_column("plex_sync_records", "plex_tmdb_id")
    # Note: PostgreSQL cannot remove enum values; 'mismatch' is left in place.
