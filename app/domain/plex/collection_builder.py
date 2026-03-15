"""Resolve builder configs to lists of Plex rating keys using local DB state."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.domain.movies.models import Movie
from app.domain.plex.models import PlexSyncRecord, PlexSyncStatus
from app.domain.tv_shows.models import TVShow

logger = logging.getLogger(__name__)


@dataclass
class ResolvedItem:
    plex_rating_key: str
    item_type: str  # "movie" or "tv_show"
    item_id: int


class BuilderResolver:
    """Resolve builder configs to ResolvedItem lists from local DB state."""

    def __init__(self, db: Session, connection_id: int):
        self._db = db
        self._connection_id = connection_id

    def resolve_static_items(self, config: Dict[str, Any]) -> List[ResolvedItem]:
        results: List[ResolvedItem] = []
        for entry in config.get("items", []):
            tmdb_id = str(entry["tmdb_id"])
            item_type = entry.get("item_type", "movie")
            resolved = self._resolve_single(tmdb_id=tmdb_id, item_type=item_type)
            if resolved:
                results.append(resolved)
        return results

    def resolve_tmdb_collection(self, config: Dict[str, Any]) -> List[ResolvedItem]:
        collection_id = int(config["tmdb_collection_id"])
        movies = self._db.query(Movie).filter(Movie.tmdb_collection_id == collection_id).all()
        results: List[ResolvedItem] = []
        for movie in movies:
            record = self._get_synced_record(item_type="movie", item_id=movie.id)
            if record and record.plex_rating_key:
                results.append(
                    ResolvedItem(
                        plex_rating_key=record.plex_rating_key,
                        item_type="movie",
                        item_id=movie.id,
                    )
                )
        return results

    def resolve_genre(self, config: Dict[str, Any]) -> List[ResolvedItem]:
        """Return synced movies and TV shows matching the given genre."""
        genre = config["genre"]
        results: List[ResolvedItem] = []
        results.extend(self._resolve_genre_for_model(genre, Movie, "movie"))
        results.extend(self._resolve_genre_for_model(genre, TVShow, "tv_show"))
        return results

    def resolve_decade(self, config: Dict[str, Any]) -> List[ResolvedItem]:
        """Return synced movies from the given decade (e.g. decade=2000 means 2000-2009)."""
        decade = int(config["decade"])
        movies = self._db.query(Movie).filter(Movie.year >= decade, Movie.year < decade + 10).all()
        results: List[ResolvedItem] = []
        for movie in movies:
            record = self._get_synced_record(item_type="movie", item_id=movie.id)
            if record and record.plex_rating_key:
                results.append(
                    ResolvedItem(
                        plex_rating_key=record.plex_rating_key,
                        item_type="movie",
                        item_id=movie.id,
                    )
                )
        return results

    def _resolve_genre_for_model(
        self, genre: str, model: type, item_type: str
    ) -> List[ResolvedItem]:
        items = self._db.query(model).filter(model.genres.isnot(None)).all()
        results: List[ResolvedItem] = []
        for item in items:
            try:
                genres = json.loads(item.genres or "[]")
            except (ValueError, TypeError):
                continue
            if genre not in genres:
                continue
            record = self._get_synced_record(item_type=item_type, item_id=item.id)
            if record and record.plex_rating_key:
                results.append(
                    ResolvedItem(
                        plex_rating_key=record.plex_rating_key,
                        item_type=item_type,
                        item_id=item.id,
                    )
                )
        return results

    def _resolve_single(self, tmdb_id: str, item_type: str) -> Optional[ResolvedItem]:
        item_id = self._find_item_id(tmdb_id=tmdb_id, item_type=item_type)
        if item_id is None:
            logger.debug("Builder: no %s found for tmdb_id=%s", item_type, tmdb_id)
            return None
        record = self._get_synced_record(item_type=item_type, item_id=item_id)
        if not record or not record.plex_rating_key:
            logger.debug("Builder: no synced record for %s id=%s", item_type, item_id)
            return None
        return ResolvedItem(
            plex_rating_key=record.plex_rating_key,
            item_type=item_type,
            item_id=item_id,
        )

    def _find_item_id(self, tmdb_id: str, item_type: str) -> Optional[int]:
        if item_type == "movie":
            movie = self._db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
            return movie.id if movie else None
        if item_type == "tv_show":
            show = self._db.query(TVShow).filter(TVShow.tmdb_id == tmdb_id).first()
            return show.id if show else None
        return None

    def _get_synced_record(self, item_type: str, item_id: int) -> Optional[PlexSyncRecord]:
        return (
            self._db.query(PlexSyncRecord)
            .filter(
                PlexSyncRecord.item_type == item_type,
                PlexSyncRecord.item_id == item_id,
                PlexSyncRecord.connection_id == self._connection_id,
                PlexSyncRecord.sync_status == PlexSyncStatus.SYNCED,
            )
            .first()
        )
