"""Celery tasks for Plex collections and playlists push/pull."""

import logging
from typing import Optional, Tuple

from app.core.database import get_db
from app.domain.plex.collection_builder import BuilderResolver
from app.domain.plex.collection_models import PlexCollection, PlexPlaylist
from app.domain.plex.collection_service import PlexCollectionService
from app.domain.plex.default_collection_manager import DefaultCollectionManager
from app.domain.plex.models import PlexConnection
from app.domain.plex.playlist_service import PlexPlaylistService
from app.domain.plex.service import get_or_cache_library_ids
from app.infrastructure.external_apis.plex.client import PlexClient
from app.infrastructure.external_apis.plex.collection_client import PlexCollectionClient
from app.infrastructure.external_apis.plex.playlist_client import PlexPlaylistClient
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _build_collection_svc(
    db, conn: PlexConnection
) -> Tuple[PlexCollectionService, PlexPlaylistService]:
    """Return (PlexCollectionService, PlexPlaylistService) for a connection."""
    plex_client = PlexClient(server_url=conn.server_url, token=conn.token)
    machine_id = plex_client.get_machine_identifier()
    cc = PlexCollectionClient(server_url=conn.server_url, token=conn.token, machine_id=machine_id)
    pc = PlexPlaylistClient(server_url=conn.server_url, token=conn.token, machine_id=machine_id)
    movie_section_id, tv_section_id = get_or_cache_library_ids(db, conn)
    resolver = BuilderResolver(db=db, connection_id=conn.id)
    coll_svc = PlexCollectionService(
        db=db,
        collection_client=cc,
        resolver=resolver,
        movie_section_id=movie_section_id,
        tv_section_id=tv_section_id,
    )
    playlist_svc = PlexPlaylistService(db=db, playlist_client=pc, resolver=resolver)
    return coll_svc, playlist_svc


def _get_connection(db, connection_id: int, task_name: str) -> Optional[PlexConnection]:
    """Query PlexConnection by id; log a warning and return None if not found."""
    conn = db.query(PlexConnection).filter(PlexConnection.id == connection_id).first()
    if conn is None:
        logger.warning("%s: connection_id=%s not found, skipping", task_name, connection_id)
    return conn


@celery_app.task(
    name="app.tasks.plex_collections.push_all_collections",
    queue="external_api",
)
def push_all_collections(connection_id: int) -> None:
    """Push all enabled collections for a connection to Plex."""
    db = next(get_db())
    try:
        conn = _get_connection(db, connection_id, "push_all_collections")
        if conn is None:
            return None
        coll_svc, _ = _build_collection_svc(db, conn)
        collections = (
            db.query(PlexCollection)
            .filter(
                PlexCollection.connection_id == connection_id,
                PlexCollection.enabled.is_(True),
            )
            .all()
        )
        logger.info("push_all_collections: pushing %d collections", len(collections))
        for c in collections:
            coll_svc.push_collection(c)
        logger.info("push_all_collections: done")
    finally:
        db.close()


@celery_app.task(
    name="app.tasks.plex_collections.pull_all_collections",
    queue="external_api",
)
def pull_all_collections(connection_id: int) -> None:
    """Pull all collections from Plex for a connection (unconditional)."""
    db = next(get_db())
    try:
        conn = _get_connection(db, connection_id, "pull_all_collections")
        if conn is None:
            return None
        coll_svc, _ = _build_collection_svc(db, conn)
        logger.info("pull_all_collections: pulling for connection_id=%s", connection_id)
        coll_svc.pull_collections(connection_id)
        logger.info("pull_all_collections: done")
    finally:
        db.close()


@celery_app.task(
    name="app.tasks.plex_collections.push_all_playlists",
    queue="external_api",
)
def push_all_playlists(connection_id: int) -> None:
    """Push all enabled playlists for a connection to Plex."""
    db = next(get_db())
    try:
        conn = _get_connection(db, connection_id, "push_all_playlists")
        if conn is None:
            return None
        _, playlist_svc = _build_collection_svc(db, conn)
        playlists = (
            db.query(PlexPlaylist)
            .filter(
                PlexPlaylist.connection_id == connection_id,
                PlexPlaylist.enabled.is_(True),
            )
            .all()
        )
        logger.info("push_all_playlists: pushing %d playlists", len(playlists))
        for p in playlists:
            playlist_svc.push_playlist(p)
        logger.info("push_all_playlists: done")
    finally:
        db.close()


@celery_app.task(
    name="app.tasks.plex_collections.pull_all_playlists",
    queue="external_api",
)
def pull_all_playlists(connection_id: int) -> None:
    """Pull all playlists from Plex for a connection (unconditional)."""
    db = next(get_db())
    try:
        conn = _get_connection(db, connection_id, "pull_all_playlists")
        if conn is None:
            return None
        _, playlist_svc = _build_collection_svc(db, conn)
        logger.info("pull_all_playlists: pulling for connection_id=%s", connection_id)
        playlist_svc.pull_playlists(connection_id)
        logger.info("pull_all_playlists: done")
    finally:
        db.close()


@celery_app.task(
    name="app.tasks.plex_collections.run_collection_discovery",
    queue="external_api",
)
def run_collection_discovery(connection_id: int) -> None:
    """Discover default collections from library metadata."""
    db = next(get_db())
    try:
        conn = db.query(PlexConnection).filter(PlexConnection.id == connection_id).first()
        if conn is None:
            logger.warning("run_collection_discovery: connection_id=%s not found", connection_id)
            return None
        manager = DefaultCollectionManager(db=db, connection_id=connection_id)
        manager.discover_franchises()
        manager.discover_genres()
        manager.discover_decades()
        logger.info("Plex: collection discovery complete for connection_id=%s", connection_id)
    finally:
        db.close()
