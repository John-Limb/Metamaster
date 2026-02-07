"""Add database indexes for performance optimization

Revision ID: 002
Revises: 001
Create Date: 2026-02-07 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add indexes for frequently queried columns"""
    
    # Movies table indexes
    op.create_index('idx_movies_title', 'movies', ['title'])
    op.create_index('idx_movies_genres', 'movies', ['genres'])
    op.create_index('idx_movies_rating', 'movies', ['rating'])
    op.create_index('idx_movies_year', 'movies', ['year'])
    
    # Composite index for common movie filter combinations
    op.create_index('idx_movies_title_year', 'movies', ['title', 'year'])
    op.create_index('idx_movies_genres_rating', 'movies', ['genres', 'rating'])
    
    # TV Shows table indexes
    op.create_index('idx_tv_shows_title', 'tv_shows', ['title'])
    op.create_index('idx_tv_shows_genres', 'tv_shows', ['genres'])
    op.create_index('idx_tv_shows_rating', 'tv_shows', ['rating'])
    op.create_index('idx_tv_shows_status', 'tv_shows', ['status'])
    
    # Composite index for common TV show filter combinations
    op.create_index('idx_tv_shows_title_status', 'tv_shows', ['title', 'status'])
    op.create_index('idx_tv_shows_genres_rating', 'tv_shows', ['genres', 'rating'])
    
    # Movie Files table indexes
    op.create_index('idx_movie_files_movie_id', 'movie_files', ['movie_id'])
    op.create_index('idx_movie_files_file_path', 'movie_files', ['file_path'])
    
    # Seasons table indexes
    op.create_index('idx_seasons_show_id', 'seasons', ['show_id'])
    op.create_index('idx_seasons_show_season', 'seasons', ['show_id', 'season_number'])
    
    # Episodes table indexes
    op.create_index('idx_episodes_season_id', 'episodes', ['season_id'])
    op.create_index('idx_episodes_tvdb_id', 'episodes', ['tvdb_id'])
    
    # Episode Files table indexes
    op.create_index('idx_episode_files_episode_id', 'episode_files', ['episode_id'])
    op.create_index('idx_episode_files_file_path', 'episode_files', ['file_path'])
    
    # API Cache table indexes
    op.create_index('idx_api_cache_type_key', 'api_cache', ['api_type', 'query_key'])
    op.create_index('idx_api_cache_expires', 'api_cache', ['expires_at'])
    
    # File Queue table indexes
    op.create_index('idx_file_queue_status', 'file_queue', ['status'])
    op.create_index('idx_file_queue_created', 'file_queue', ['created_at'])
    op.create_index('idx_file_queue_status_created', 'file_queue', ['status', 'created_at'])
    
    # Task Errors table indexes
    op.create_index('idx_task_errors_task_id', 'task_errors', ['task_id'])
    op.create_index('idx_task_errors_created', 'task_errors', ['created_at'])
    op.create_index('idx_task_errors_severity', 'task_errors', ['severity'])
    op.create_index('idx_task_errors_severity_created', 'task_errors', ['severity', 'created_at'])


def downgrade() -> None:
    """Remove all added indexes"""
    
    # Task Errors table indexes
    op.drop_index('idx_task_errors_severity_created', table_name='task_errors')
    op.drop_index('idx_task_errors_severity', table_name='task_errors')
    op.drop_index('idx_task_errors_created', table_name='task_errors')
    op.drop_index('idx_task_errors_task_id', table_name='task_errors')
    
    # File Queue table indexes
    op.drop_index('idx_file_queue_status_created', table_name='file_queue')
    op.drop_index('idx_file_queue_created', table_name='file_queue')
    op.drop_index('idx_file_queue_status', table_name='file_queue')
    
    # API Cache table indexes
    op.drop_index('idx_api_cache_expires', table_name='api_cache')
    op.drop_index('idx_api_cache_type_key', table_name='api_cache')
    
    # Episode Files table indexes
    op.drop_index('idx_episode_files_file_path', table_name='episode_files')
    op.drop_index('idx_episode_files_episode_id', table_name='episode_files')
    
    # Episodes table indexes
    op.drop_index('idx_episodes_tvdb_id', table_name='episodes')
    op.drop_index('idx_episodes_season_id', table_name='episodes')
    
    # Seasons table indexes
    op.drop_index('idx_seasons_show_season', table_name='seasons')
    op.drop_index('idx_seasons_show_id', table_name='seasons')
    
    # Movie Files table indexes
    op.drop_index('idx_movie_files_file_path', table_name='movie_files')
    op.drop_index('idx_movie_files_movie_id', table_name='movie_files')
    
    # TV Shows table composite indexes
    op.drop_index('idx_tv_shows_genres_rating', table_name='tv_shows')
    op.drop_index('idx_tv_shows_title_status', table_name='tv_shows')
    
    # TV Shows table indexes
    op.drop_index('idx_tv_shows_status', table_name='tv_shows')
    op.drop_index('idx_tv_shows_rating', table_name='tv_shows')
    op.drop_index('idx_tv_shows_genres', table_name='tv_shows')
    op.drop_index('idx_tv_shows_title', table_name='tv_shows')
    
    # Movies table composite indexes
    op.drop_index('idx_movies_genres_rating', table_name='movies')
    op.drop_index('idx_movies_title_year', table_name='movies')
    
    # Movies table indexes
    op.drop_index('idx_movies_year', table_name='movies')
    op.drop_index('idx_movies_rating', table_name='movies')
    op.drop_index('idx_movies_genres', table_name='movies')
    op.drop_index('idx_movies_title', table_name='movies')
