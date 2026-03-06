"""Add plex_connections and plex_sync_records tables

Revision ID: 012
Revises: 011
Create Date: 2026-03-06
"""

import sqlalchemy as sa

from alembic import op

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plex_connections",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("server_url", sa.String(500), nullable=False),
        sa.Column("token", sa.String(500), nullable=False),
        sa.Column("movie_library_id", sa.String(20), nullable=True),
        sa.Column("tv_library_id", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("last_connected_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_plex_connections_id", "plex_connections", ["id"])

    plexitemtype = sa.Enum("movie", "tv_show", "episode", name="plexitemtype")
    plexsyncstatus = sa.Enum("pending", "synced", "failed", "not_found", name="plexsyncstatus")

    op.create_table(
        "plex_sync_records",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "connection_id",
            sa.Integer(),
            sa.ForeignKey("plex_connections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_type", plexitemtype, nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("plex_rating_key", sa.String(50), nullable=True),
        sa.Column("last_matched_at", sa.DateTime(), nullable=True),
        sa.Column("last_pulled_at", sa.DateTime(), nullable=True),
        sa.Column("watch_count", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("last_watched_at", sa.DateTime(), nullable=True),
        sa.Column("is_watched", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        sa.Column(
            "sync_status",
            plexsyncstatus,
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    op.create_index("ix_plex_sync_records_id", "plex_sync_records", ["id"])
    op.create_index("idx_plex_sync_item", "plex_sync_records", ["item_type", "item_id"])
    op.create_index("idx_plex_sync_connection", "plex_sync_records", ["connection_id"])
    op.create_index("idx_plex_sync_status", "plex_sync_records", ["sync_status"])


def downgrade() -> None:
    op.drop_index("idx_plex_sync_status", table_name="plex_sync_records")
    op.drop_index("idx_plex_sync_connection", table_name="plex_sync_records")
    op.drop_index("idx_plex_sync_item", table_name="plex_sync_records")
    op.drop_index("ix_plex_sync_records_id", table_name="plex_sync_records")
    op.drop_table("plex_sync_records")
    op.drop_index("ix_plex_connections_id", table_name="plex_connections")
    op.drop_table("plex_connections")
    sa.Enum(name="plexsyncstatus").drop(op.get_bind())
    sa.Enum(name="plexitemtype").drop(op.get_bind())
