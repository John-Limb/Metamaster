"""Bi-directional sync service for Plex collections."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.domain.plex.collection_builder import BuilderResolver, ResolvedItem
from app.domain.plex.collection_models import BuilderType, PlexCollection, PlexCollectionItem
from app.infrastructure.external_apis.plex.collection_client import PlexCollectionClient

logger = logging.getLogger(__name__)


class PlexCollectionService:
    def __init__(
        self,
        db: Session,
        collection_client: PlexCollectionClient,
        resolver: BuilderResolver,
        movie_section_id: str,
        tv_section_id: str,
    ):
        self._db = db
        self._cc = collection_client
        self._resolver = resolver
        self._movie_section = movie_section_id
        self._tv_section = tv_section_id

    def push_collection(self, collection: PlexCollection) -> None:
        """Push a single collection definition to Plex, reconciling items."""
        target_items = self._resolve(collection)
        target_keys = {item.plex_rating_key for item in target_items}

        if not collection.plex_rating_key:
            self._create_and_set_key(collection, target_items)
        else:
            self._reconcile_items(collection.plex_rating_key, target_keys)
            self._cc.update_collection_metadata(
                collection_key=collection.plex_rating_key,
                title=collection.name,
                description=collection.description,
                sort_title=collection.sort_title,
            )

        self._upsert_item_records(collection, target_items)
        collection.last_synced_at = datetime.utcnow()
        self._db.commit()
        logger.info(
            "Plex: pushed collection '%s' key=%s",
            collection.name,
            collection.plex_rating_key,
        )

    def pull_collections(self, connection_id: int) -> None:
        """Import all Plex-managed collections into the DB."""
        for section_id in (self._movie_section, self._tv_section):
            for raw in self._cc.get_collections(section_id=section_id):
                self._upsert_pulled_collection(raw, connection_id, section_id)
        self._db.commit()
        logger.info("Plex: pull collections complete")

    def _resolve(self, collection: PlexCollection) -> List[ResolvedItem]:
        config = collection.builder_config
        if collection.builder_type == BuilderType.TMDB_COLLECTION:
            return self._resolver.resolve_tmdb_collection(config)
        if collection.builder_type == BuilderType.GENRE:
            return self._resolver.resolve_genre(config)
        if collection.builder_type == BuilderType.DECADE:
            return self._resolver.resolve_decade(config)
        return self._resolver.resolve_static_items(config)

    def _create_and_set_key(self, collection: PlexCollection, items: List[ResolvedItem]) -> None:
        rating_keys = [i.plex_rating_key for i in items]
        key = self._cc.create_collection(
            section_id=self._movie_section,
            title=collection.name,
            rating_keys=rating_keys,
        )
        collection.plex_rating_key = key

    def _reconcile_items(self, collection_key: str, target_keys: set) -> None:
        current_keys = set(self._cc.get_collection_item_keys(collection_key))
        for key in target_keys - current_keys:
            self._cc.add_item_to_collection(collection_key=collection_key, rating_key=key)
        for key in current_keys - target_keys:
            self._cc.remove_item_from_collection(collection_key=collection_key, item_key=key)

    def _upsert_item_records(self, collection: PlexCollection, items: List[ResolvedItem]) -> None:
        self._db.query(PlexCollectionItem).filter(
            PlexCollectionItem.collection_id == collection.id
        ).delete()
        for pos, item in enumerate(items):
            self._db.add(
                PlexCollectionItem(
                    collection_id=collection.id,
                    plex_rating_key=item.plex_rating_key,
                    item_type=item.item_type,
                    item_id=item.item_id,
                    position=pos,
                )
            )

    def _upsert_pulled_collection(self, raw: dict, connection_id: int, section_id: str) -> None:
        plex_key = raw["ratingKey"]
        existing = (
            self._db.query(PlexCollection)
            .filter(PlexCollection.plex_rating_key == plex_key)
            .first()
        )
        if existing is None:
            existing = PlexCollection(
                connection_id=connection_id,
                builder_type=BuilderType.STATIC_ITEMS,
                builder_config={"items": []},
                plex_rating_key=plex_key,
                enabled=False,
                is_default=False,
            )
            self._db.add(existing)

        existing.name = raw.get("title", plex_key)
        existing.description = raw.get("summary")
        existing.last_synced_at = datetime.utcnow()

        item_keys = self._cc.get_collection_item_keys(plex_key)
        self._db.query(PlexCollectionItem).filter(
            PlexCollectionItem.collection_id == existing.id
        ).delete()
        for pos, rk in enumerate(item_keys):
            self._db.add(
                PlexCollectionItem(
                    collection_id=existing.id,
                    plex_rating_key=rk,
                    item_type="movie",
                    item_id=0,
                    position=pos,
                )
            )
