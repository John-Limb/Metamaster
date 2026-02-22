"""Backfill enrichment_status for existing movies and tv_shows

Revision ID: 008
Revises: 007
Create Date: 2026-02-21
"""
from alembic import op

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Movies with omdb_id are fully enriched
    op.execute("""
        UPDATE movies
        SET enrichment_status = 'fully_enriched'
        WHERE omdb_id IS NOT NULL AND enrichment_status = 'pending_local'
    """)
    # Movies without omdb_id are local_only
    op.execute("""
        UPDATE movies
        SET enrichment_status = 'local_only'
        WHERE omdb_id IS NULL AND enrichment_status = 'pending_local'
    """)
    # TV shows with tvdb_id are fully enriched
    op.execute("""
        UPDATE tv_shows
        SET enrichment_status = 'fully_enriched'
        WHERE tvdb_id IS NOT NULL AND enrichment_status = 'pending_local'
    """)
    # TV shows without tvdb_id are local_only
    op.execute("""
        UPDATE tv_shows
        SET enrichment_status = 'local_only'
        WHERE tvdb_id IS NULL AND enrichment_status = 'pending_local'
    """)


def downgrade() -> None:
    op.execute("UPDATE movies SET enrichment_status = 'pending_local'")
    op.execute("UPDATE tv_shows SET enrichment_status = 'pending_local'")
