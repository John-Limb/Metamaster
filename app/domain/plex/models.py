"""SQLAlchemy ORM models for Plex integration"""

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class PlexSyncStatus(str, enum.Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    NOT_FOUND = "not_found"
    MISMATCH = "mismatch"


class PlexItemType(str, enum.Enum):
    MOVIE = "movie"
    TV_SHOW = "tv_show"
    EPISODE = "episode"


class PlexConnection(Base):
    """Plex server connection configuration"""

    __tablename__ = "plex_connections"

    id = Column(Integer, primary_key=True, index=True)
    server_url = Column(String(500), nullable=False)
    token = Column(String(500), nullable=False)
    movie_library_id = Column(String(20), nullable=True)
    tv_library_id = Column(String(20), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_connected_at = Column(DateTime, nullable=True)

    sync_records = relationship(
        "PlexSyncRecord", back_populates="connection", cascade="all, delete-orphan"
    )


class PlexSyncRecord(Base):
    """Sync state and watch history for a single MetaMaster item"""

    __tablename__ = "plex_sync_records"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(
        Integer, ForeignKey("plex_connections.id", ondelete="CASCADE"), nullable=False
    )
    item_type: Any = Column(
        SAEnum("movie", "tv_show", "episode", name="plexitemtype"),
        nullable=False,
    )
    item_id = Column(Integer, nullable=False)
    plex_rating_key = Column(String(50), nullable=True)
    plex_tmdb_id = Column(String(50), nullable=True)
    last_matched_at = Column(DateTime, nullable=True)
    last_pulled_at = Column(DateTime, nullable=True)
    watch_count = Column(Integer, default=0)
    last_watched_at = Column(DateTime, nullable=True)
    is_watched = Column(Boolean, default=False)
    sync_status: Any = Column(
        SAEnum("pending", "synced", "failed", "not_found", "mismatch", name="plexsyncstatus"),
        nullable=False,
        default="pending",
    )
    last_error = Column(Text, nullable=True)

    connection = relationship("PlexConnection", back_populates="sync_records")

    __table_args__ = (
        Index("idx_plex_sync_item", "item_type", "item_id"),
        Index("idx_plex_sync_connection", "connection_id"),
        Index("idx_plex_sync_status", "sync_status"),
    )
