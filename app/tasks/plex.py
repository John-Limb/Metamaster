"""Celery tasks for Plex Media Server integration"""

import logging
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.domain.movies.models import Movie
from app.domain.plex.models import PlexItemType
from app.domain.plex.service import PlexSyncService
from app.domain.tv_shows.models import TVShow
from app.infrastructure.external_apis.plex.client import PlexClient
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

_ITEM_TYPE_MAP = {
    "movie": PlexItemType.MOVIE,
    "tv_show": PlexItemType.TV_SHOW,
    "episode": PlexItemType.EPISODE,
}


def _make_client() -> Optional[PlexClient]:
    """Return a configured PlexClient, or None if Plex is not configured."""
    if not settings.plex_server_url:
        logger.warning("Plex not configured (PLEX_SERVER_URL not set) — skipping")
        return None
    token = settings.plex_token or ""
    return PlexClient(server_url=settings.plex_server_url, token=token)


@celery_app.task(
    name="app.tasks.plex.refresh_plex_library",
    queue="external_api",
)
def refresh_plex_library(section_id: str) -> None:
    """Trigger a Plex library section rescan."""
    client = _make_client()
    if client is None:
        return None
    logger.info("Plex: refreshing library section %s", section_id)
    client.refresh_library_section(section_id=section_id)
    logger.info("Plex: library section %s refresh triggered", section_id)


def _get_title_year(db, item_type_str: str, item_id: int):
    """Return (title, year) for the given item, or (None, None) if not found."""
    if item_type_str == "movie":
        item = db.query(Movie).filter(Movie.id == item_id).first()
        return (item.title, item.year) if item else (None, None)
    if item_type_str == "tv_show":
        item = db.query(TVShow).filter(TVShow.id == item_id).first()
        return (item.title, None) if item else (None, None)
    return (None, None)


@celery_app.task(
    name="app.tasks.plex.lock_plex_match",
    queue="external_api",
)
def lock_plex_match(item_type_str: str, item_id: int, tmdb_id: str, connection_id: int) -> None:
    """Resolve TMDB ID to Plex ratingKey and lock the match."""
    client = _make_client()
    if client is None:
        return None

    db = next(get_db())
    try:
        svc = PlexSyncService(
            db=db,
            client=client,
            movie_library_name=settings.plex_library_movies,
            tv_library_name=settings.plex_library_tv,
        )
        movie_section_id, tv_section_id = svc.resolve_library_ids()
        item_type = _ITEM_TYPE_MAP[item_type_str]
        # Route to correct section: movies to movie library, TV/episodes to TV library
        section_id = movie_section_id if item_type == PlexItemType.MOVIE else tv_section_id
        title, year = _get_title_year(db, item_type_str, item_id)
        svc.lock_match(
            section_id=section_id,
            item_type=item_type,
            item_id=item_id,
            tmdb_id=tmdb_id,
            connection_id=connection_id,
            title=title,
            year=year,
        )
    finally:
        db.close()


@celery_app.task(
    name="app.tasks.plex.poll_plex_watched_status",
    queue="external_api",
)
def poll_plex_watched_status(connection_id: int) -> None:
    """Pull watch status from Plex for all movies and episodes."""
    client = _make_client()
    if client is None:
        return None

    db = next(get_db())
    try:
        svc = PlexSyncService(
            db=db,
            client=client,
            movie_library_name=settings.plex_library_movies,
            tv_library_name=settings.plex_library_tv,
        )
        movie_section_id, tv_section_id = svc.resolve_library_ids()
        logger.info("Plex: polling watched status for movies and TV")
        svc.pull_watched_status(
            section_id=movie_section_id, media_type=1, connection_id=connection_id
        )
        svc.pull_watched_status(section_id=tv_section_id, media_type=4, connection_id=connection_id)
        logger.info("Plex: watched status poll complete")
    finally:
        db.close()
