"""Bi-directional sync service for Plex playlists."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.domain.plex.collection_builder import BuilderResolver, ResolvedItem
from app.domain.plex.collection_models import PlexPlaylist, PlexPlaylistItem
from app.infrastructure.external_apis.plex.playlist_client import PlexPlaylistClient

logger = logging.getLogger(__name__)


class PlexPlaylistService:
    def __init__(
        self,
        db: Session,
        playlist_client: PlexPlaylistClient,
        resolver: BuilderResolver,
    ):
        self._db = db
        self._pc = playlist_client
        self._resolver = resolver

    def push_playlist(self, playlist: PlexPlaylist) -> None:
        items = self._resolver.resolve_static_items(playlist.builder_config)
        target_keys = {i.plex_rating_key for i in items}

        if not playlist.plex_rating_key:
            key = self._pc.create_playlist(
                title=playlist.name,
                rating_keys=[i.plex_rating_key for i in items],
            )
            playlist.plex_rating_key = key
        else:
            self._reconcile(playlist.plex_rating_key, target_keys)
            self._pc.update_playlist_metadata(
                playlist_key=playlist.plex_rating_key,
                title=playlist.name,
                description=playlist.description,
            )

        self._upsert_item_records(playlist, items)
        playlist.last_synced_at = datetime.utcnow()
        self._db.commit()
        logger.info(
            "Plex: pushed playlist '%s' key=%s",
            playlist.name,
            playlist.plex_rating_key,
        )

    def pull_playlists(self, connection_id: int) -> None:
        """Import all Plex playlists into the DB. Pull is always unconditional."""
        for raw in self._pc.get_playlists():
            self._upsert_pulled_playlist(raw, connection_id)
        self._db.commit()

    def _reconcile(self, playlist_key: str, target_keys: set) -> None:
        current_keys = set(self._pc.get_playlist_item_keys(playlist_key))
        for key in target_keys - current_keys:
            self._pc.add_item_to_playlist(playlist_key=playlist_key, rating_key=key)
        for key in current_keys - target_keys:
            self._pc.remove_item_from_playlist(playlist_key=playlist_key, item_key=key)

    def _upsert_item_records(self, playlist: PlexPlaylist, items: List[ResolvedItem]) -> None:
        self._db.query(PlexPlaylistItem).filter(
            PlexPlaylistItem.playlist_id == playlist.id
        ).delete()
        for pos, item in enumerate(items):
            self._db.add(
                PlexPlaylistItem(
                    playlist_id=playlist.id,
                    plex_rating_key=item.plex_rating_key,
                    item_type=item.item_type,
                    item_id=item.item_id,
                    position=pos,
                )
            )

    def _upsert_pulled_playlist(self, raw: dict, connection_id: int) -> None:
        plex_key = raw["ratingKey"]
        existing = (
            self._db.query(PlexPlaylist).filter(PlexPlaylist.plex_rating_key == plex_key).first()
        )
        if existing is None:
            existing = PlexPlaylist(
                connection_id=connection_id,
                builder_config={"items": []},
                plex_rating_key=plex_key,
                enabled=False,
            )
            self._db.add(existing)
        existing.name = raw.get("title", plex_key)
        existing.description = raw.get("summary")
        existing.last_synced_at = datetime.utcnow()
