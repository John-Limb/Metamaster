"""SQLAlchemy ORM models for Movie entities"""

from datetime import datetime
from sqlalchemy import BigInteger, Column, Integer, String, Text, Float, DateTime, ForeignKey, Index
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
    poster_url = Column(String(500))  # URL to movie poster image
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    files = relationship("MovieFile", back_populates="movie", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_movies_title", "title"),
        Index("idx_movies_omdb_id", "omdb_id"),
        Index("idx_movies_year", "year"),
    )

    @property
    def _primary_file(self):
        """Return the first associated MovieFile, if any."""
        return self.files[0] if self.files else None

    @property
    def quality(self):
        f = self._primary_file
        if not f or not f.resolution:
            return None
        # Derive label from resolution string e.g. "1920x1080" -> "1080p"
        try:
            _, h = f.resolution.split("x")
            height = int(h)
            if height >= 2160:
                return "4K"
            elif height >= 1440:
                return "1440p"
            elif height >= 1080:
                return "1080p"
            elif height >= 720:
                return "720p"
            elif height >= 480:
                return "480p"
            return f"{height}p"
        except (ValueError, AttributeError):
            return None

    @property
    def resolution(self):
        f = self._primary_file
        return f.resolution if f else None

    @property
    def codec_video(self):
        f = self._primary_file
        return f.codec_video if f else None

    @property
    def codec_audio(self):
        f = self._primary_file
        return f.codec_audio if f else None

    @property
    def file_duration(self):
        f = self._primary_file
        return f.duration if f else None

    @property
    def file_size(self):
        f = self._primary_file
        return f.file_size if f else None


class MovieFile(Base):
    """Movie file metadata"""

    __tablename__ = "movie_files"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(500), unique=True, nullable=False)
    file_size = Column(BigInteger)  # in bytes
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
