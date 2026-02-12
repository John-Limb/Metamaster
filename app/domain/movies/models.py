"""SQLAlchemy ORM models for Movie entities"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class Movie(Base):
    """Movie entity"""

    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    year = Column(Integer)
    omdb_id = Column(String(50), unique=True)
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
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
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
    movie = relationship("Movie", back_populates="files")

    __table_args__ = (
        Index("idx_movie_files_movie_id", "movie_id"),
        Index("idx_movie_files_path", "file_path"),
    )
