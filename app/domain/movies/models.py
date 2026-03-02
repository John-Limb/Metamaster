"""SQLAlchemy ORM models for Movie entities"""

from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    Index,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Movie(Base):
    """Movie entity"""

    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    year = Column(Integer)
    tmdb_id = Column(String(50), unique=True)
    plot = Column(Text)
    rating = Column(Float)
    runtime = Column(Integer)  # in minutes
    genres = Column(Text)  # JSON array stored as string
    poster_url = Column(String(500))  # URL to movie poster image
    enrichment_status = Column(
        SAEnum(
            "pending_local",
            "local_only",
            "pending_external",
            "fully_enriched",
            "external_failed",
            "not_found",
            name="enrichmentstatus",
        ),
        nullable=False,
        default="pending_local",
        server_default="pending_local",
    )
    detected_external_id = Column(String(50), nullable=True)
    manual_external_id = Column(String(50), nullable=True)
    enrichment_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    files = relationship("MovieFile", back_populates="movie", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_movies_title", "title"),
        Index("idx_movies_tmdb_id", "tmdb_id"),
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

    @property
    def audio_channels(self):
        f = self._primary_file
        if not f or not f.audio_channels:
            return None
        channels = f.audio_channels
        labels = {1: "Mono", 2: "Stereo", 6: "5.1", 8: "7.1"}
        return labels.get(channels, f"{channels}ch")


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
    audio_channels = Column(Integer)  # number of audio channels (2=stereo, 6=5.1, 8=7.1)
    duration = Column(Integer)  # in seconds
    last_modified = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    movie = relationship("Movie", back_populates="files")

    __table_args__ = (
        Index("idx_movie_files_movie_id", "movie_id"),
        Index("idx_movie_files_path", "file_path"),
    )
