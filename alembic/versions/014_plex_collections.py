"""add plex collections and playlists

Revision ID: 014
Revises: 013
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PgENUM

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    builder_type_enum = sa.Enum(
        "tmdb_collection", "static_items", "genre", "decade", name="plexbuildertype"
    )
    builder_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "plex_collections",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "connection_id",
            sa.Integer,
            sa.ForeignKey("plex_connections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("sort_title", sa.String(500), nullable=True),
        sa.Column(
            "builder_type",
            PgENUM(
                "tmdb_collection",
                "static_items",
                "genre",
                "decade",
                name="plexbuildertype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("builder_config", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("plex_rating_key", sa.String(50), nullable=True),
        sa.Column("last_synced_at", sa.DateTime, nullable=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
    )
    op.create_index("idx_plex_collection_connection", "plex_collections", ["connection_id"])
    op.create_index("idx_plex_collection_key", "plex_collections", ["plex_rating_key"])

    op.create_table(
        "plex_collection_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "collection_id",
            sa.Integer,
            sa.ForeignKey("plex_collections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("plex_rating_key", sa.String(50), nullable=False),
        sa.Column("item_type", sa.String(20), nullable=False),
        sa.Column("item_id", sa.Integer, nullable=False),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
    )

    op.create_table(
        "plex_playlists",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "connection_id",
            sa.Integer,
            sa.ForeignKey("plex_connections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("builder_config", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("plex_rating_key", sa.String(50), nullable=True),
        sa.Column("last_synced_at", sa.DateTime, nullable=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="false"),
    )
    op.create_index("idx_plex_playlist_connection", "plex_playlists", ["connection_id"])
    op.create_index("idx_plex_playlist_key", "plex_playlists", ["plex_rating_key"])

    op.create_table(
        "plex_playlist_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "playlist_id",
            sa.Integer,
            sa.ForeignKey("plex_playlists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("plex_rating_key", sa.String(50), nullable=False),
        sa.Column("item_type", sa.String(20), nullable=False),
        sa.Column("item_id", sa.Integer, nullable=False),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
    )

    set_type_enum = sa.Enum("franchise", "genre", "decade", name="plexsettype")
    set_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "plex_collection_sets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "connection_id",
            sa.Integer,
            sa.ForeignKey("plex_connections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "set_type",
            PgENUM("franchise", "genre", "decade", name="plexsettype", create_type=False),
            nullable=False,
        ),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("last_run_at", sa.DateTime, nullable=True),
    )
    op.create_index("idx_plex_set_connection", "plex_collection_sets", ["connection_id"])


def downgrade() -> None:
    op.drop_table("plex_collection_sets")
    op.execute("DROP TYPE IF EXISTS plexsettype")
    op.drop_table("plex_playlist_items")
    op.drop_table("plex_playlists")
    op.drop_table("plex_collection_items")
    op.drop_table("plex_collections")
    op.execute("DROP TYPE IF EXISTS plexbuildertype")
