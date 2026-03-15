"""Discovers default collections from library metadata."""

import json
import logging
from typing import List

from sqlalchemy.orm import Session

from app.domain.movies.models import Movie
from app.domain.plex.collection_models import BuilderType, PlexCollection
from app.domain.tv_shows.models import TVShow

logger = logging.getLogger(__name__)


class DefaultCollectionManager:
    def __init__(self, db: Session, connection_id: int):
        self._db = db
        self._connection_id = connection_id

    def discover_franchises(self) -> List[PlexCollection]:
        """Create one collection per TMDB franchise (tmdb_collection_id/name)."""
        rows = (
            self._db.query(Movie.tmdb_collection_id, Movie.tmdb_collection_name)
            .filter(Movie.tmdb_collection_id.isnot(None))
            .distinct()
            .all()
        )
        results = []
        for coll_id, coll_name in rows:
            coll = self._upsert_collection(
                name=coll_name or f"Collection {coll_id}",
                builder_type=BuilderType.TMDB_COLLECTION,
                builder_config={"tmdb_collection_id": coll_id},
            )
            results.append(coll)
        self._db.commit()
        return results

    def discover_genres(self) -> List[PlexCollection]:
        """Create one collection per distinct genre across movies and TV shows."""
        genres: set = set()
        for movie in self._db.query(Movie).filter(Movie.genres.isnot(None)).all():
            try:
                genres.update(json.loads(movie.genres))
            except (ValueError, TypeError):
                pass
        for show in self._db.query(TVShow).filter(TVShow.genres.isnot(None)).all():
            try:
                genres.update(json.loads(show.genres))
            except (ValueError, TypeError):
                pass

        results = []
        for genre in sorted(genres):
            coll = self._upsert_collection(
                name=f"{genre} Films",
                builder_type=BuilderType.GENRE,
                builder_config={"genre": genre},
            )
            results.append(coll)
        self._db.commit()
        return results

    def discover_decades(self) -> List[PlexCollection]:
        """Create one collection per decade found in movies."""
        movies = self._db.query(Movie).filter(Movie.year.isnot(None)).all()
        decades = {(m.year // 10) * 10 for m in movies}
        results = []
        for decade in sorted(decades):
            coll = self._upsert_collection(
                name=f"{decade}s",
                builder_type=BuilderType.DECADE,
                builder_config={"decade": decade},
            )
            results.append(coll)
        self._db.commit()
        return results

    def _upsert_collection(
        self, name: str, builder_type: BuilderType, builder_config: dict
    ) -> PlexCollection:
        existing = (
            self._db.query(PlexCollection)
            .filter(
                PlexCollection.connection_id == self._connection_id,
                PlexCollection.name == name,
            )
            .first()
        )
        if existing is not None:
            return existing
        coll = PlexCollection(
            connection_id=self._connection_id,
            name=name,
            builder_type=builder_type,
            builder_config=builder_config,
            enabled=False,
            is_default=True,
        )
        self._db.add(coll)
        self._db.flush()
        logger.info(
            "Plex: seeded default collection '%s' type=%s",
            name,
            builder_type.value,
        )
        return coll
