"""Celery tasks for external metadata enrichment (TMDB)."""

import logging

import httpx

from app.core.database import SessionLocal
from app.domain.movies.models import Movie
from app.domain.tv_shows.models import TVShow
from app.services_impl import TMDBService
from app.tasks.async_helpers import run_async
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

RETRYABLE_STATUSES = ("local_only", "external_failed")


def enrich_movie_external(movie_id: int) -> None:
    """Fetch TMDB metadata for a single movie. Sets enrichment_status accordingly.

    ID resolution priority: manual_external_id > detected_external_id > title search.
    """
    db = SessionLocal()
    try:
        movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if not movie:
            logger.warning(f"Movie {movie_id} not found for enrichment")
            return

        existing_ids = {
            row[0] for row in db.query(Movie.tmdb_id).filter(Movie.tmdb_id.isnot(None)).all()
        }

        try:
            movie.enrichment_status = "pending_external"
            db.commit()

            external_id = movie.manual_external_id or movie.detected_external_id

            if external_id:
                raw = run_async(TMDBService.get_movie_details(db, external_id))
            else:
                raw = run_async(TMDBService.search_movie(db, movie.title, movie.year))
                if raw:
                    parsed_search = TMDBService.parse_movie_search_response(raw)
                    results = (parsed_search or {}).get("search_results", [])
                    external_id = results[0].get("tmdb_id") if results else None
                    if not external_id:
                        movie.enrichment_status = "not_found"
                        movie.enrichment_error = "No match found in TMDB"
                        db.commit()
                        return
                    raw = run_async(TMDBService.get_movie_details(db, external_id))
                else:
                    movie.enrichment_status = "not_found"
                    movie.enrichment_error = "No match found in TMDB"
                    db.commit()
                    return

            if not raw:
                movie.enrichment_status = "not_found"
                movie.enrichment_error = "TMDB returned no data for this ID"
                db.commit()
                return

            detail = TMDBService.parse_movie_details_response(raw)
            if not detail:
                movie.enrichment_status = "not_found"
                movie.enrichment_error = "Could not parse TMDB response"
                db.commit()
                return

            tmdb_id = detail.get("tmdb_id") or external_id
            if tmdb_id and tmdb_id not in existing_ids:
                movie.tmdb_id = tmdb_id
            movie.plot = detail.get("plot", movie.plot)
            movie.rating = detail.get("rating", movie.rating)
            movie.runtime = detail.get("runtime", movie.runtime)
            movie.genres = detail.get("genres", movie.genres)
            poster = detail.get("poster")
            if poster:
                movie.poster_url = poster
            movie.enrichment_status = "fully_enriched"
            movie.enrichment_error = None
            db.commit()
            logger.info(f"Enriched movie {movie_id} ({movie.title}) successfully")

        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            movie.enrichment_status = "external_failed"
            movie.enrichment_error = f"API unreachable: {exc}"
            db.commit()
            logger.warning(f"External API unavailable for movie {movie_id}: {exc}")
        except Exception as exc:
            movie.enrichment_status = "external_failed"
            movie.enrichment_error = str(exc)
            db.commit()
            logger.error(f"Unexpected error enriching movie {movie_id}: {exc}", exc_info=True)
    finally:
        db.close()


def enrich_tv_show_external(show_id: int) -> None:
    """Fetch TMDB metadata for a single TV show. Sets enrichment_status accordingly."""
    db = SessionLocal()
    try:
        show = db.query(TVShow).filter(TVShow.id == show_id).first()
        if not show:
            logger.warning(f"TVShow {show_id} not found for enrichment")
            return

        external_id = show.manual_external_id or show.detected_external_id

        try:
            show.enrichment_status = "pending_external"
            db.commit()

            if external_id:
                raw = run_async(TMDBService.get_series_details(db, external_id))
            else:
                raw = run_async(TMDBService.search_show(db, show.title))
                if raw:
                    parsed = TMDBService.parse_series_search_response(raw)
                    results = (parsed or {}).get("search_results", [])
                    external_id = results[0].get("tmdb_id") if results else None
                    if not external_id:
                        show.enrichment_status = "not_found"
                        show.enrichment_error = "No match found in TMDB"
                        db.commit()
                        return
                    raw = run_async(TMDBService.get_series_details(db, external_id))
                else:
                    show.enrichment_status = "not_found"
                    show.enrichment_error = "No match found in TMDB"
                    db.commit()
                    return

            if not raw:
                show.enrichment_status = "not_found"
                show.enrichment_error = "TMDB returned no data for this ID"
                db.commit()
                return

            detail = TMDBService.parse_series_response(raw) if raw else None
            if not detail:
                show.enrichment_status = "not_found"
                show.enrichment_error = "Could not parse TMDB response"
                db.commit()
                return

            tmdb_id = detail.get("tmdb_id") or external_id
            if tmdb_id:
                show.tmdb_id = tmdb_id
            show.plot = detail.get("plot", show.plot)
            show.rating = detail.get("rating", show.rating)
            show.genres = detail.get("genres", show.genres)
            show.status = detail.get("status", show.status)
            poster = detail.get("poster")
            if poster:
                show.poster_url = poster
            show.enrichment_status = "fully_enriched"
            show.enrichment_error = None
            db.commit()
            logger.info(f"Enriched TV show {show_id} ({show.title}) successfully")

        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            show.enrichment_status = "external_failed"
            show.enrichment_error = f"API unreachable: {exc}"
            db.commit()
            logger.warning(f"External API unavailable for TV show {show_id}: {exc}")
        except Exception as exc:
            show.enrichment_status = "external_failed"
            show.enrichment_error = str(exc)
            db.commit()
            logger.error(f"Unexpected error enriching TV show {show_id}: {exc}", exc_info=True)
    finally:
        db.close()


@celery_app.task(name="app.tasks.retry_failed_enrichment", bind=True, max_retries=0)
def retry_failed_enrichment(self):
    """Periodic task: re-attempt external enrichment for local_only and external_failed items."""
    db = SessionLocal()
    try:
        movies = db.query(Movie).filter(Movie.enrichment_status.in_(RETRYABLE_STATUSES)).all()
        tv_shows = db.query(TVShow).filter(TVShow.enrichment_status.in_(RETRYABLE_STATUSES)).all()
        movie_ids = [m.id for m in movies]
        show_ids = [s.id for s in tv_shows]
    finally:
        db.close()

    logger.info(
        f"retry_failed_enrichment: {len(movie_ids)} movies, {len(show_ids)} TV shows to retry"
    )

    for movie_id in movie_ids:
        enrich_movie_external(movie_id)

    for show_id in show_ids:
        enrich_tv_show_external(show_id)
