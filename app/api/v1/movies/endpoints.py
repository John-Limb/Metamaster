"""Movie API endpoints"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel as PydanticBase
from sqlalchemy.orm import Session

from app.api.utils import pagination_metadata, resolve_pagination
from app.application.search.service import MovieSearchService, SearchFilters
from app.core.config import MOVIE_DIR
from app.core.database import get_db
from app.domain.files.service import FileService
from app.domain.movies.models import Movie as MovieModel
from app.domain.movies.scanner import (
    create_movies_from_files,
    probe_movie_file,
    probe_unscanned_movies,
)
from app.domain.plex.models import PlexSyncRecord as _PlexSyncRecord
from app.infrastructure.cache.redis_cache import get_cache_service
from app.schemas import (
    MetadataSyncResponse,
    MovieCreate,
    MovieResponse,
    MovieUpdate,
    PaginatedMovieResponse,
    PaginatedMovieResponseWithFilters,
)
from app.services_impl import MovieService, TMDBService
from app.tasks.enrichment import enrich_movie_external

logger = logging.getLogger(__name__)


def _get_movie_watch_status(db: Session, movie_id: int) -> bool:
    """Return True if a watched PlexSyncRecord exists for this movie."""
    record = (
        db.query(_PlexSyncRecord)
        .filter(
            _PlexSyncRecord.item_type == "movie",
            _PlexSyncRecord.item_id == movie_id,
            _PlexSyncRecord.is_watched.is_(True),
        )
        .first()
    )
    return record is not None


router = APIRouter(prefix="/movies", tags=["Movies"])


_ENRICHMENT_STATUS_GROUPS = {
    "indexed": ["fully_enriched"],
    "pending": ["local_only", "pending_local", "pending_external"],
    "failed": ["external_failed", "not_found"],
}


@router.get("/enrichment-stats")
async def get_enrichment_stats(db: Session = Depends(get_db)):
    """Return movie counts grouped by enrichment status (indexed / pending / failed)."""
    from sqlalchemy import func

    rows = (
        db.query(MovieModel.enrichment_status, func.count(MovieModel.id))
        .group_by(MovieModel.enrichment_status)
        .all()
    )
    counts: dict = dict(rows)

    indexed = counts.get("fully_enriched", 0)
    pending = sum(counts.get(s, 0) for s in ["local_only", "pending_local", "pending_external"])
    failed = sum(counts.get(s, 0) for s in ["external_failed", "not_found"])
    total = sum(counts.values())

    return {"total": total, "indexed": indexed, "pending": pending, "failed": failed}


def _build_applied_filters(
    genre: str,
    min_rating: float,
    max_rating: float,
    year: int,
    status: str,
) -> dict:
    """Build the applied_filters dict from the non-None filter parameters."""
    applied: dict = {}
    if genre:
        applied["genre"] = genre
    if min_rating is not None:
        applied["min_rating"] = min_rating
    if max_rating is not None:
        applied["max_rating"] = max_rating
    if year is not None:
        applied["year"] = year
    if status:
        applied["status"] = status
    return applied


@router.get("", response_model=PaginatedMovieResponseWithFilters)
async def list_movies(
    genre: str = Query(None, description="Filter by genre (case-insensitive)"),
    min_rating: float = Query(None, ge=0, le=10, description="Minimum rating (0-10)"),
    max_rating: float = Query(None, ge=0, le=10, description="Maximum rating (0-10)"),
    year: int = Query(None, ge=1800, le=2100, description="Release year"),
    sort_by: str = Query("title", description="Sort by: title, rating, year, date_added"),
    status: str = Query(None, description="Enrichment group: indexed, pending, or failed"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    skip: int = Query(0, ge=0, description="Offset from start"),
    page: int = Query(None, ge=1, description="Alternative page number"),
    page_size: int = Query(None, ge=1, le=100, description="Alternative page size"),
    db: Session = Depends(get_db),
):
    """
    List movies with advanced filtering and sorting.

    - **genre**: Filter by genre (case-insensitive, optional)
    - **min_rating**: Minimum rating 0-10 (optional)
    - **max_rating**: Maximum rating 0-10 (optional)
    - **year**: Release year (optional)
    - **sort_by**: Sort field - title, rating, year, date_added (default: title)
    - **limit**: Number of items per page (1-100, default: 10)
    - **skip**: Offset from start (default: 0)
    """
    cache_service = get_cache_service()

    normalized_limit, normalized_skip, current_page = resolve_pagination(
        limit=limit,
        skip=skip,
        page=page,
        page_size=page_size,
    )

    # Validate enrichment status group
    if status and status not in _ENRICHMENT_STATUS_GROUPS:
        raise HTTPException(
            status_code=400, detail="status must be one of: indexed, pending, failed"
        )
    enrichment_statuses = _ENRICHMENT_STATUS_GROUPS.get(status) if status else None

    # Build cache key including all filter parameters
    cache_key = (
        f"{cache_service.MOVIE_LIST_PREFIX}"
        f"genre={genre}:min_rating={min_rating}:max_rating={max_rating}:"
        f"year={year}:sort_by={sort_by}:status={status}"
        f":limit={normalized_limit}:skip={normalized_skip}"
    )

    # Try to get from cache
    cached_result = cache_service.get(cache_key)
    if cached_result:
        logger.debug("Returning cached movie list with filters")
        return cached_result

    # Create search filters
    filters = SearchFilters(
        genre=genre,
        min_rating=min_rating,
        max_rating=max_rating,
        year=year,
        sort_by=sort_by,
        skip=normalized_skip,
        limit=normalized_limit,
        enrichment_statuses=enrichment_statuses,
    )

    # Validate filters
    is_valid, error_msg = filters.validate()
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Perform search
    movies, total = MovieSearchService.search(db, filters)

    movie_items = []
    for m in movies:
        m_dict = MovieResponse.model_validate(m).model_dump()
        m_dict["is_watched"] = _get_movie_watch_status(db, int(m.id))
        movie_items.append(m_dict)

    applied_filters = _build_applied_filters(genre, min_rating, max_rating, year, status)

    result = {
        "items": movie_items,
        "total": total,
        "limit": normalized_limit,
        "offset": normalized_skip,
        "page": current_page,
        "pageSize": normalized_limit,
        "totalPages": (total + normalized_limit - 1) // normalized_limit,
        "filters": {
            "applied_filters": applied_filters,
            "sort_by": sort_by,
            "total_results": total,
        },
    }

    # Cache the result
    cache_service.set(cache_key, result, ttl=cache_service.LIST_TTL)

    return result


@router.get("/search", response_model=PaginatedMovieResponse)
async def search_movies(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset from start"),
    page: int = Query(None, ge=1, description="Alternative page number"),
    page_size: int = Query(None, ge=1, le=100, description="Alternative page size"),
    db: Session = Depends(get_db),
):
    """
    Search movies by title.

    - **q**: Search query (required)
    - **limit**: Number of items per page (1-100, default: 10)
    - **offset**: Offset from start (default: 0)
    """
    normalized_limit, normalized_offset, current_page = resolve_pagination(
        limit=limit,
        skip=offset,
        page=page,
        page_size=page_size,
    )

    movies, total = MovieService.search_movies(
        db, query=q, limit=normalized_limit, offset=normalized_offset
    )
    metadata = pagination_metadata(total=total, limit=normalized_limit, skip=normalized_offset)
    metadata.update({"page": current_page})
    return {"items": movies, "total": total, **metadata}


@router.get("/popular", response_model=PaginatedMovieResponse)
async def popular_movies(
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    skip: int = Query(0, ge=0, description="Offset from start"),
    page: int = Query(None, ge=1, description="Alternative page number"),
    page_size: int = Query(None, ge=1, le=100, description="Alternative page size"),
    db: Session = Depends(get_db),
):
    normalized_limit, normalized_skip, current_page = resolve_pagination(
        limit=limit,
        skip=skip,
        page=page,
        page_size=page_size,
    )

    movies, total = MovieService.get_popular_movies(
        db, limit=normalized_limit, offset=normalized_skip
    )

    metadata = pagination_metadata(total=total, limit=normalized_limit, skip=normalized_skip)
    metadata.update({"page": current_page})
    return {"items": movies, "total": total, **metadata}


@router.get("/top-rated", response_model=PaginatedMovieResponse)
async def top_rated_movies(
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    skip: int = Query(0, ge=0, description="Offset from start"),
    page: int = Query(None, ge=1, description="Alternative page number"),
    page_size: int = Query(None, ge=1, le=100, description="Alternative page size"),
    db: Session = Depends(get_db),
):
    normalized_limit, normalized_skip, current_page = resolve_pagination(
        limit=limit,
        skip=skip,
        page=page,
        page_size=page_size,
    )

    movies, total = MovieService.get_top_rated_movies(
        db, limit=normalized_limit, offset=normalized_skip
    )

    metadata = pagination_metadata(total=total, limit=normalized_limit, skip=normalized_skip)
    metadata.update({"page": current_page})
    return {"items": movies, "total": total, **metadata}


@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(
    movie_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific movie by ID"""
    cache_service = get_cache_service()
    cache_key = f"{cache_service.MOVIE_PREFIX}{movie_id}"

    # Try to get from cache
    cached_movie = cache_service.get(cache_key)
    if cached_movie:
        logger.debug(f"Returning cached movie: {movie_id}")
        return cached_movie

    movie = MovieService.get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    movie_dict = MovieResponse.model_validate(movie).model_dump()
    movie_dict["is_watched"] = _get_movie_watch_status(db, movie_id)

    cache_service.set(cache_key, movie_dict, ttl=cache_service.MOVIE_TTL)

    return movie_dict


@router.post("", response_model=MovieResponse, status_code=201)
async def create_movie(
    movie_data: MovieCreate,
    db: Session = Depends(get_db),
):
    """Create a new movie"""
    movie = MovieService.create_movie(db, movie_data)

    # Invalidate movie list cache
    cache_service = get_cache_service()
    cache_service.delete_pattern(f"{cache_service.MOVIE_LIST_PREFIX}*")
    logger.debug("Invalidated movie list cache after create")

    return movie


@router.put("/{movie_id}", response_model=MovieResponse)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing movie"""
    movie = MovieService.update_movie(db, movie_id, movie_data)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Invalidate cache for this movie and movie lists
    cache_service = get_cache_service()
    cache_service.invalidate_movie(movie_id)
    logger.debug(f"Invalidated cache for movie {movie_id} after update")

    return movie


@router.delete("/{movie_id}", status_code=204)
async def delete_movie(
    movie_id: int,
    db: Session = Depends(get_db),
):
    """Delete a movie"""
    success = MovieService.delete_movie(db, movie_id)
    if not success:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Invalidate cache for this movie and movie lists
    cache_service = get_cache_service()
    cache_service.invalidate_movie(movie_id)
    logger.debug(f"Invalidated cache for movie {movie_id} after delete")

    return None


@router.post("/scan-directory")
async def scan_movie_directory(db: Session = Depends(get_db)):
    """Scan the movie directory for new files and create movie records with FFprobe analysis."""
    try:
        file_service = FileService(db)
        try:
            files_synced = file_service.sync_directory(MOVIE_DIR)
        except ValueError as e:
            logger.warning(f"Could not sync {MOVIE_DIR}: {e}")
            files_synced = 0

        movies_created = create_movies_from_files(db)
        pending = (
            db.query(MovieModel)
            .filter(MovieModel.enrichment_status.in_(["local_only", "external_failed"]))
            .all()
        )
        for m in pending:
            enrich_movie_external(m.id)
        movies_enriched = len(pending)
        files_scanned = probe_unscanned_movies(db)

        # Invalidate movie list cache
        cache_service = get_cache_service()
        cache_service.delete_pattern(f"{cache_service.MOVIE_LIST_PREFIX}*")

        return {
            "files_synced": files_synced,
            "movies_created": movies_created,
            "movies_enriched": movies_enriched,
            "files_scanned": files_scanned,
        }
    except Exception as e:
        logger.error(f"Error scanning movie directory: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An error occurred while scanning the movie directory"
        )


@router.post("/{movie_id}/scan", response_model=MovieResponse)
async def scan_movie(
    movie_id: int,
    db: Session = Depends(get_db),
):
    """Run FFprobe on the movie's file and return updated metadata."""
    try:
        movie = probe_movie_file(db, movie_id)

        # Invalidate cache for this movie
        cache_service = get_cache_service()
        cache_service.invalidate_movie(movie_id)

        return movie
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error scanning movie {movie_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while scanning")


def _apply_parsed_fields(movie: MovieModel, parsed_data: dict) -> list:
    """Apply parsed TMDB fields to the movie ORM object.

    Returns the list of field names that were changed.
    """
    updated_fields = []

    simple_fields = ["title", "plot", "year", "rating", "runtime", "genres"]
    for field in simple_fields:
        if field in parsed_data and parsed_data[field] != getattr(movie, field):
            setattr(movie, field, parsed_data[field])
            updated_fields.append(field)

    poster = parsed_data.get("poster")
    if poster and poster != movie.poster_url:
        movie.poster_url = poster
        updated_fields.append("poster_url")

    return updated_fields


@router.post("/{movie_id}/sync-metadata", response_model=MetadataSyncResponse)
async def sync_movie_metadata(
    movie_id: int,
    db: Session = Depends(get_db),
):
    """
    Fetch movie metadata from TMDB and update the movie record.

    This endpoint:
    1. Retrieves the movie from the database
    2. Fetches updated metadata from TMDB using the movie's TMDB ID
    3. Updates the movie record with new metadata
    4. Returns the updated movie information

    Parameters:
    - **movie_id**: ID of the movie to sync

    Returns:
    - **success**: Whether sync was successful
    - **message**: Operation message
    - **movie_id**: ID of the synced movie
    - **updated_fields**: List of fields that were updated
    - **metadata**: Updated metadata
    """
    try:
        # Get the movie
        movie = MovieService.get_movie_by_id(db, movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")

        # Check if movie has TMDB ID
        if not movie.tmdb_id:
            raise HTTPException(
                status_code=400,
                detail="Movie does not have a TMDB ID. Cannot sync metadata.",
            )

        logger.info(f"Syncing metadata for movie {movie_id} (TMDB ID: {movie.tmdb_id})")

        # Fetch metadata from TMDB
        tmdb_data = await TMDBService.get_movie_details(db, movie.tmdb_id)
        if not tmdb_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch metadata from TMDB. Please try again later.",
            )

        # Parse TMDB response
        parsed_data = TMDBService.parse_movie_details_response(tmdb_data)
        if not parsed_data:
            raise HTTPException(status_code=500, detail="Failed to parse TMDB response")

        # Update movie fields and track which changed
        updated_fields = _apply_parsed_fields(movie, parsed_data)

        # Commit changes
        db.commit()
        db.refresh(movie)

        # Invalidate cache for this movie and movie lists
        cache_service = get_cache_service()
        cache_service.invalidate_movie(movie_id)
        logger.debug(f"Invalidated cache for movie {movie_id} after metadata sync")

        logger.info(
            f"Successfully synced metadata for movie {movie_id}. "
            f"Updated fields: {', '.join(updated_fields) if updated_fields else 'none'}"
        )

        # Prepare response metadata
        response_metadata = {
            "title": movie.title,
            "plot": movie.plot,
            "year": movie.year,
            "rating": movie.rating,
            "runtime": movie.runtime,
            "genres": json.loads(movie.genres) if movie.genres else [],
            "tmdb_id": movie.tmdb_id,
            "poster_url": movie.poster_url,
        }

        return {
            "success": True,
            "message": f"Movie metadata synced successfully. Updated {len(updated_fields)} field(s).",  # noqa: E501
            "movie_id": movie_id,
            "show_id": None,
            "updated_fields": updated_fields,
            "metadata": response_metadata,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing metadata for movie {movie_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while syncing metadata")


class ExternalIdPayload(PydanticBase):
    external_id: str


@router.patch("/{movie_id}/external-id", response_model=MovieResponse)
async def set_movie_external_id(
    movie_id: int,
    payload: ExternalIdPayload,
    db: Session = Depends(get_db),
):
    """Set a manual TMDB ID and trigger enrichment immediately."""
    movie = MovieService.get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    movie.manual_external_id = payload.external_id
    movie.enrichment_status = "local_only"
    movie.enrichment_error = None
    db.commit()
    db.refresh(movie)
    enrich_movie_external(movie.id)
    cache_service = get_cache_service()
    cache_service.invalidate_movie(movie_id)
    return movie


@router.post("/{movie_id}/enrich", status_code=202)
async def trigger_movie_enrichment(
    movie_id: int,
    db: Session = Depends(get_db),
):
    """Manually trigger external enrichment for a movie."""
    movie = MovieService.get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    enrich_movie_external(movie.id)
    cache_service = get_cache_service()
    cache_service.invalidate_movie(movie_id)
    return {"message": "Enrichment triggered", "movie_id": movie_id}
