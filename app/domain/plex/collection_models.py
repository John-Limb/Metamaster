"""ORM models for Plex collections and playlists."""

import enum
from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class BuilderType(str, enum.Enum):
    TMDB_COLLECTION = "tmdb_collection"
    STATIC_ITEMS = "static_items"
    GENRE = "genre"
    DECADE = "decade"


class SetType(str, enum.Enum):
    FRANCHISE = "franchise"
    GENRE = "genre"
    DECADE = "decade"


class PlexCollection(Base):
    __tablename__ = "plex_collections"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(
        Integer, ForeignKey("plex_connections.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    sort_title = Column(String(500), nullable=True)
    builder_type: Any = Column(
        SAEnum("tmdb_collection", "static_items", "genre", "decade", name="plexbuildertype"),
        nullable=False,
    )
    builder_config = Column(JSON, nullable=False, default=dict)
    plex_rating_key = Column(String(50), nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    enabled = Column(Boolean, nullable=False, default=False, server_default="false")
    is_default = Column(Boolean, nullable=False, default=False, server_default="false")

    items = relationship(
        "PlexCollectionItem", back_populates="collection", cascade="all, delete-orphan"
    )
    __table_args__ = (
        Index("idx_plex_collection_connection", "connection_id"),
        Index("idx_plex_collection_key", "plex_rating_key"),
    )


class PlexCollectionItem(Base):
    __tablename__ = "plex_collection_items"

    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(
        Integer, ForeignKey("plex_collections.id", ondelete="CASCADE"), nullable=False
    )
    plex_rating_key = Column(String(50), nullable=False)
    item_type = Column(String(20), nullable=False)
    item_id = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False, default=0)

    collection = relationship("PlexCollection", back_populates="items")


class PlexPlaylist(Base):
    __tablename__ = "plex_playlists"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(
        Integer, ForeignKey("plex_connections.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    builder_config = Column(JSON, nullable=False, default=dict)
    plex_rating_key = Column(String(50), nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    enabled = Column(Boolean, nullable=False, default=False, server_default="false")

    items = relationship(
        "PlexPlaylistItem", back_populates="playlist", cascade="all, delete-orphan"
    )
    __table_args__ = (
        Index("idx_plex_playlist_connection", "connection_id"),
        Index("idx_plex_playlist_key", "plex_rating_key"),
    )


class PlexPlaylistItem(Base):
    __tablename__ = "plex_playlist_items"

    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(
        Integer, ForeignKey("plex_playlists.id", ondelete="CASCADE"), nullable=False
    )
    plex_rating_key = Column(String(50), nullable=False)
    item_type = Column(String(20), nullable=False)
    item_id = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False, default=0)

    playlist = relationship("PlexPlaylist", back_populates="items")


class PlexCollectionSet(Base):
    """One row per auto-generation category; seeded at startup."""

    __tablename__ = "plex_collection_sets"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(
        Integer, ForeignKey("plex_connections.id", ondelete="CASCADE"), nullable=False
    )
    set_type: Any = Column(
        SAEnum("franchise", "genre", "decade", name="plexsettype"),
        nullable=False,
    )
    enabled = Column(Boolean, nullable=False, default=False, server_default="false")
    last_run_at = Column(DateTime, nullable=True)

    __table_args__ = (Index("idx_plex_set_connection", "connection_id"),)
