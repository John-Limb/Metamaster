"""PlexSyncService — orchestrates metadata push and watch status pull"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Tuple

from sqlalchemy.orm import Session

from app.domain.plex.models import PlexItemType, PlexSyncRecord, PlexSyncStatus
from app.infrastructure.external_apis.plex.client import PlexClient

if TYPE_CHECKING:
    from app.infrastructure.external_apis.plex.schemas import PlexMediaItem

logger = logging.getLogger(__name__)


class PlexSyncService:
    def __init__(
        self,
        db: Session,
        client: PlexClient,
        movie_library_name: str,
        tv_library_name: str,
    ):
        self._db = db
        self._client = client
        self._movie_lib_name = movie_library_name
        self._tv_lib_name = tv_library_name

    def resolve_library_ids(self) -> Tuple[str, str]:
        """Resolve library names to Plex section IDs.

        Returns (movie_section_id, tv_section_id).
        Raises ValueError with available names if either name is not found.
        """
        sections = self._client.get_library_sections()
        by_title = {s.title: s.key for s in sections}
        available = ", ".join(by_title.keys())

        if self._movie_lib_name not in by_title:
            raise ValueError(
                f"Library '{self._movie_lib_name}' not found in Plex. "
                f"Available libraries: {available}"
            )
        if self._tv_lib_name not in by_title:
            raise ValueError(
                f"Library '{self._tv_lib_name}' not found in Plex. "
                f"Available libraries: {available}"
            )

        return by_title[self._movie_lib_name], by_title[self._tv_lib_name]

    def lock_match(
        self,
        section_id: str,
        item_type: PlexItemType,
        item_id: int,
        tmdb_id: str,
        connection_id: int,
        title: Optional[str] = None,
        year: Optional[int] = None,
    ) -> PlexSyncRecord:
        """Resolve TMDB ID to Plex ratingKey and upsert sync record.

        Two-step lookup:
        1. Search by our tmdb_id -> SYNCED
        2. Fallback title+year search -> MISMATCH (different tmdb_id) or NOT_FOUND
        """
        record = (
            self._db.query(PlexSyncRecord)
            .filter(
                PlexSyncRecord.item_type == item_type,
                PlexSyncRecord.item_id == item_id,
                PlexSyncRecord.connection_id == connection_id,
            )
            .first()
        )
        if record is None:
            record = PlexSyncRecord(
                connection_id=connection_id,
                item_type=item_type,
                item_id=item_id,
            )
            self._db.add(record)

        rating_key = self._client.find_rating_key_by_tmdb_id(section_id=section_id, tmdb_id=tmdb_id)
        if rating_key:
            record.plex_rating_key = rating_key  # type: ignore[assignment]
            record.plex_tmdb_id = None  # type: ignore[assignment]
            record.sync_status = PlexSyncStatus.SYNCED  # type: ignore[assignment]
            record.last_matched_at = datetime.utcnow()  # type: ignore[assignment]
            logger.info("Plex match locked: %s id=%s key=%s", item_type, item_id, rating_key)
            self._db.commit()
            return record

        if title:
            plex_item = self._client.find_by_title_year(
                section_id=section_id, title=title, year=year
            )
            if plex_item and plex_item.tmdb_id and plex_item.tmdb_id != tmdb_id:
                record.plex_rating_key = plex_item.rating_key  # type: ignore[assignment]
                record.plex_tmdb_id = plex_item.tmdb_id  # type: ignore[assignment]
                record.sync_status = PlexSyncStatus.MISMATCH  # type: ignore[assignment]
                record.last_matched_at = datetime.utcnow()  # type: ignore[assignment]
                logger.warning(
                    "Plex TMDB mismatch: %s id=%s ours=%s plex=%s",
                    item_type,
                    item_id,
                    tmdb_id,
                    plex_item.tmdb_id,
                )
                self._db.commit()
                return record

        record.sync_status = PlexSyncStatus.NOT_FOUND  # type: ignore[assignment]
        record.plex_rating_key = None  # type: ignore[assignment]
        record.plex_tmdb_id = None  # type: ignore[assignment]
        logger.warning("Plex match not found: %s id=%s tmdb_id=%s", item_type, item_id, tmdb_id)
        self._db.commit()
        return record

    def pull_watched_status(self, section_id: str, media_type: int, connection_id: int) -> None:
        """Pull watch status from Plex for all items in a section.

        Skips items with no tmdb_id. Never blocks on a single missing record.
        """
        items = self._client.get_all_items(section_id=section_id, media_type=media_type)
        logger.info("Plex pull: %d items from section %s", len(items), section_id)

        for item in items:
            if not item.tmdb_id:
                continue
            self._update_watch_record(item=item, connection_id=connection_id)

        self._db.commit()

    def _update_watch_record(self, item: PlexMediaItem, connection_id: int) -> None:
        record: Optional[PlexSyncRecord] = (
            self._db.query(PlexSyncRecord)
            .filter(
                PlexSyncRecord.plex_rating_key == item.rating_key,
                PlexSyncRecord.connection_id == connection_id,
            )
            .first()
        )
        if record is None:
            return

        record.watch_count = item.view_count  # type: ignore[assignment]
        record.is_watched = item.view_count > 0  # type: ignore[assignment]
        record.last_pulled_at = datetime.utcnow()  # type: ignore[assignment]
        if item.last_viewed_at:
            record.last_watched_at = datetime.utcfromtimestamp(  # type: ignore[assignment]
                item.last_viewed_at
            )
        logger.info(
            "Plex watch update: rating_key=%s views=%d",
            item.rating_key,
            item.view_count,
        )
