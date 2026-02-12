"""SQLAlchemy ORM models for TV Show entities"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class TVShow(Base):
    """TV Show entity"""

    __tablename__ = "tv_shows"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    tvdb_id = Column(String(50), unique=True)
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
    show_id = Column(
        Integer,
        ForeignKey("tv_shows.id", ondelete="CASCADE"),
        nullable=False,
    )
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
    season_id = Column(
        Integer,
        ForeignKey("seasons.id", ondelete="CASCADE"),
        nullable=False,
    )
    episode_number = Column(Integer, nullable=False)
    tvdb_id = Column(String(50), unique=True)
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
    episode_id = Column(
        Integer,
        ForeignKey("episodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_path = Column(String(500), unique=True, nullable=False)
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
