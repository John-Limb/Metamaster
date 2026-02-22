"""Migrate from TVDB/OMDB IDs to TMDB IDs

Replaces tvdb_id columns on tv_shows/seasons/episodes with tmdb_id,
and replaces omdb_id on movies with tmdb_id. Resets enrichment_status
to 'local_only' for previously enriched records so they are re-enriched
with TMDB data.

Revision ID: 009
Revises: 008
Create Date: 2026-02-22
"""
import sqlalchemy as sa
from alembic import op

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- tv_shows: rename tvdb_id -> tmdb_id ---
    op.add_column('tv_shows', sa.Column('tmdb_id', sa.String(50), nullable=True))
    op.create_unique_constraint('uq_tv_shows_tmdb_id', 'tv_shows', ['tmdb_id'])
    op.create_index('idx_tv_shows_tmdb_id', 'tv_shows', ['tmdb_id'])
    op.drop_index('idx_tv_shows_tvdb_id', table_name='tv_shows')
    op.drop_constraint('tv_shows_tvdb_id_key', 'tv_shows', type_='unique')
    op.drop_column('tv_shows', 'tvdb_id')

    # --- seasons: rename tvdb_id -> tmdb_id ---
    op.add_column('seasons', sa.Column('tmdb_id', sa.String(50), nullable=True))
    op.drop_column('seasons', 'tvdb_id')

    # --- episodes: rename tvdb_id -> tmdb_id ---
    op.add_column('episodes', sa.Column('tmdb_id', sa.String(50), nullable=True))
    op.create_unique_constraint('uq_episodes_tmdb_id', 'episodes', ['tmdb_id'])
    op.create_index('idx_episodes_tmdb_id', 'episodes', ['tmdb_id'])
    op.drop_index('idx_episodes_tvdb_id', table_name='episodes')
    op.drop_constraint('episodes_tvdb_id_key', 'episodes', type_='unique')
    op.drop_column('episodes', 'tvdb_id')

    # --- movies: rename omdb_id -> tmdb_id ---
    op.add_column('movies', sa.Column('tmdb_id', sa.String(50), nullable=True))
    op.create_unique_constraint('uq_movies_tmdb_id', 'movies', ['tmdb_id'])
    op.create_index('idx_movies_tmdb_id', 'movies', ['tmdb_id'])
    op.drop_index('idx_movies_omdb_id', table_name='movies')
    op.drop_constraint('movies_omdb_id_key', 'movies', type_='unique')
    op.drop_column('movies', 'omdb_id')

    # Reset previously-enriched records so they get re-enriched via TMDB
    op.execute("""
        UPDATE tv_shows
        SET enrichment_status = 'local_only'
        WHERE enrichment_status = 'fully_enriched'
    """)
    op.execute("""
        UPDATE movies
        SET enrichment_status = 'local_only'
        WHERE enrichment_status = 'fully_enriched'
    """)


def downgrade() -> None:
    # --- movies: rename tmdb_id -> omdb_id ---
    op.add_column('movies', sa.Column('omdb_id', sa.String(50), nullable=True))
    op.create_unique_constraint('movies_omdb_id_key', 'movies', ['omdb_id'])
    op.create_index('idx_movies_omdb_id', 'movies', ['omdb_id'])
    op.drop_index('idx_movies_tmdb_id', table_name='movies')
    op.drop_constraint('uq_movies_tmdb_id', 'movies', type_='unique')
    op.drop_column('movies', 'tmdb_id')

    # --- episodes: rename tmdb_id -> tvdb_id ---
    op.add_column('episodes', sa.Column('tvdb_id', sa.String(50), nullable=True))
    op.create_unique_constraint('episodes_tvdb_id_key', 'episodes', ['tvdb_id'])
    op.create_index('idx_episodes_tvdb_id', 'episodes', ['tvdb_id'])
    op.drop_index('idx_episodes_tmdb_id', table_name='episodes')
    op.drop_constraint('uq_episodes_tmdb_id', 'episodes', type_='unique')
    op.drop_column('episodes', 'tmdb_id')

    # --- seasons: rename tmdb_id -> tvdb_id ---
    op.add_column('seasons', sa.Column('tvdb_id', sa.String(50), nullable=True))
    op.drop_column('seasons', 'tmdb_id')

    # --- tv_shows: rename tmdb_id -> tvdb_id ---
    op.add_column('tv_shows', sa.Column('tvdb_id', sa.String(50), nullable=True))
    op.create_unique_constraint('tv_shows_tvdb_id_key', 'tv_shows', ['tvdb_id'])
    op.create_index('idx_tv_shows_tvdb_id', 'tv_shows', ['tvdb_id'])
    op.drop_index('idx_tv_shows_tmdb_id', table_name='tv_shows')
    op.drop_constraint('uq_tv_shows_tmdb_id', 'tv_shows', type_='unique')
    op.drop_column('tv_shows', 'tmdb_id')
