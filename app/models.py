"""SQLAlchemy ORM models for database entities"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class Movie(Base):
    """Movie entity"""
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    year = Column(Integer, index=True)
    omdb_id = Column(String(50), unique=True, index=True)
    plot = Column(Text)
    rating = Column(Float)
    runtime = Column(Integer)  # in minutes
    genres = Column(Text)  # JSON array stored as string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    files = relationship("MovieFile", back_populates="movie", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_movies_title", "title"),
        Index("idx_movies_omdb_id", "omdb_id"),
        Index("idx_movies_year", "year"),
    )


class MovieFile(Base):
    """Movie file metadata"""
    __tablename__ = "movie_files"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(500), unique=True, nullable=False, index=True)
    file_size = Column(Integer)  # in bytes
    resolution = Column(String(20))  # e.g., "1920x1080"
    bitrate = Column(Integer)  # in kbps
    codec_video = Column(String(50))
    codec_audio = Column(String(50))
    duration = Column(Integer)  # in seconds
    last_modified = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    movie = relationship("Movie", back_populates="files")

    __table_args__ = (
        Index("idx_movie_files_movie_id", "movie_id"),
        Index("idx_movie_files_path", "file_path"),
    )


class TVShow(Base):
    """TV Show entity"""
    __tablename__ = "tv_shows"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    tvdb_id = Column(String(50), unique=True, index=True)
    plot = Column(Text)
    rating = Column(Float)
    genres = Column(Text)  # JSON array stored as string
    status = Column(String(50))  # "Continuing" or "Ended"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    seasons = relationship("Season", back_populates="show", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_tv_shows_title", "title"),
        Index("idx_tv_shows_tvdb_id", "tvdb_id"),
    )


class Season(Base):
    """TV Show season"""
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True, index=True)
    show_id = Column(Integer, ForeignKey("tv_shows.id", ondelete="CASCADE"), nullable=False, index=True)
    season_number = Column(Integer, nullable=False)
    tvdb_id = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    show = relationship("TVShow", back_populates="seasons")
    episodes = relationship("Episode", back_populates="season", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_seasons_show_id", "show_id"),
        Index("idx_seasons_show_season", "show_id", "season_number"),
    )


class Episode(Base):
    """TV Show episode"""
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, index=True)
    season_id = Column(Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False, index=True)
    episode_number = Column(Integer, nullable=False)
    tvdb_id = Column(String(50), unique=True, index=True)
    title = Column(String(255))
    plot = Column(Text)
    air_date = Column(String(10))  # YYYY-MM-DD format
    rating = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    season = relationship("Season", back_populates="episodes")
    files = relationship("EpisodeFile", back_populates="episode", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_episodes_season_id", "season_id"),
        Index("idx_episodes_tvdb_id", "tvdb_id"),
    )


class EpisodeFile(Base):
    """Episode file metadata"""
    __tablename__ = "episode_files"

    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(500), unique=True, nullable=False, index=True)
    file_size = Column(Integer)  # in bytes
    resolution = Column(String(20))  # e.g., "1920x1080"
    bitrate = Column(Integer)  # in kbps
    codec_video = Column(String(50))
    codec_audio = Column(String(50))
    duration = Column(Integer)  # in seconds
    last_modified = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    episode = relationship("Episode", back_populates="files")

    __table_args__ = (
        Index("idx_episode_files_episode_id", "episode_id"),
        Index("idx_episode_files_path", "file_path"),
    )


class APICache(Base):
    """API response cache"""
    __tablename__ = "api_cache"

    id = Column(Integer, primary_key=True, index=True)
    api_type = Column(String(20), nullable=False)  # "omdb" or "tvdb"
    query_key = Column(String(255), nullable=False)
    response_data = Column(Text, nullable=False)  # JSON response
    expires_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_api_cache_type_key", "api_type", "query_key"),
        Index("idx_api_cache_expires", "expires_at"),
    )


class FileQueue(Base):
     """File processing queue"""
     __tablename__ = "file_queue"

     id = Column(Integer, primary_key=True, index=True)
     file_path = Column(String(500), unique=True, nullable=False)
     status = Column(String(20), default="pending", index=True)  # pending, processing, completed, failed
     media_type = Column(String(20))  # "movie" or "tv_show"
     error_message = Column(Text)
     created_at = Column(DateTime, default=datetime.utcnow, index=True)
     processed_at = Column(DateTime)

     __table_args__ = (
         Index("idx_file_queue_status", "status"),
         Index("idx_file_queue_created", "created_at"),
     )


class TaskError(Base):
     """Task error tracking and audit trail"""
     __tablename__ = "task_errors"

     id = Column(Integer, primary_key=True, index=True)
     task_id = Column(String(255), nullable=False, index=True)
     task_name = Column(String(255), nullable=False)
     error_message = Column(Text, nullable=False)
     error_traceback = Column(Text)
     severity = Column(String(20), nullable=False, index=True)  # critical, warning, info
     retry_count = Column(Integer, default=0)
     created_at = Column(DateTime, default=datetime.utcnow, index=True)
     resolved_at = Column(DateTime, nullable=True)

     __table_args__ = (
         Index("idx_task_errors_task_id", "task_id"),
         Index("idx_task_errors_created", "created_at"),
         Index("idx_task_errors_severity", "severity"),
     )
