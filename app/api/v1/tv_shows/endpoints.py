"""TV Show API endpoints"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel as PydanticBase
from sqlalchemy.orm import Session

from app.api.utils import pagination_metadata, resolve_pagination
from app.application.search.service import SearchFilters, TVShowSearchService
from app.core.config import TV_DIR
from app.core.database import get_db
from app.domain.files.service import FileService
from app.domain.tv_shows.models import TVShow as TVShowModel
from app.domain.tv_shows.scanner import (
    create_tv_shows_from_files,
    probe_unscanned_episodes,
)
from app.infrastructure.cache.redis_cache import get_cache_service
from app.schemas import (
    MetadataSyncResponse,
    PaginatedEpisodeResponse,
    PaginatedSeasonResponse,
    PaginatedTVShowResponseWithFilters,
    TVShowCreate,
    TVShowResponse,
    TVShowUpdate,
)
from app.services_impl import TMDBService, TVShowService
from app.tasks.enrichment import enrich_tv_show_external

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tv-shows", tags=["TV Shows"])

_ENRICHMENT_STATUS_GROUPS = {
    "indexed": ["fully_enriched"],
    "pending": ["local_only", "pending_local", "pending_external"],
    "failed": ["external_failed", "not_found"],
}


def _resolution_to_quality(resolution: Optional[str]) -> Optional[str]:
    """Convert a resolution string like '1920x1080' to a quality label like '1080p'."""
    if not resolution:
        return None
    try:
        height = int(resolution.split("x")[1])
    except (IndexError, ValueError):
        return None
    if height >= 2160:
        return "4K"
    if height >= 1080:
        return "1080p"
    if height >= 720:
        return "720p"
    if height >= 576:
        return "576p"
    if height >= 480:
        return "480p"
    return f"{height}p"


@router.get("/enrichment-stats")
async def get_tv_show_enrichment_stats(db: Session = Depends(get_db)):
    """Return TV show counts grouped by enrichment status (indexed / pending / failed)."""
    from sqlalchemy import func

    rows = (
        db.query(TVShowModel.enrichment_status, func.count(TVShowModel.id))
        .group_by(TVShowModel.enrichment_status)
        .all()
    )
    counts: dict = dict(rows)

    indexed = counts.get("fully_enriched", 0)
    pending = sum(counts.get(s, 0) for s in ["local_only", "pending_local", "pending_external"])
    failed = sum(counts.get(s, 0) for s in ["external_failed", "not_found"])
    total = sum(counts.values())

    return {"total": total, "indexed": indexed, "pending": pending, "failed": failed}


@router.get("", response_model=PaginatedTVShowResponseWithFilters)
async def list_tv_shows(
    genre: str = Query(None, description="Filter by genre (case-insensitive)"),
    min_rating: float = Query(None, ge=0, le=10, description="Minimum rating (0-10)"),
    max_rating: float = Query(None, ge=0, le=10, description="Maximum rating (0-10)"),
    sort_by: str = Query("title", description="Sort by: title, rating, date_added"),
    status: str = Query(None, description="Enrichment group: indexed, pending, or failed"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    skip: int = Query(0, ge=0, description="Offset from start"),
    page: int = Query(None, ge=1, description="Alternative page number"),
    page_size: int = Query(None, ge=1, le=100, description="Alternative page size"),
    db: Session = Depends(get_db),
):
    """
    List TV shows with advanced filtering and sorting.

    - **genre**: Filter by genre (case-insensitive, optional)
    - **min_rating**: Minimum rating 0-10 (optional)
    - **max_rating**: Maximum rating 0-10 (optional)
    - **sort_by**: Sort field - title, rating, date_added (default: title)
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
        f"{cache_service.TV_SHOW_LIST_PREFIX}"
        f"genre={genre}:min_rating={min_rating}:max_rating={max_rating}:"
        f"sort_by={sort_by}:status={status}:limit={normalized_limit}:skip={normalized_skip}"
    )

    # Try to get from cache
    cached_result = cache_service.get(cache_key)
    if cached_result:
        logger.debug("Returning cached TV show list with filters")
        return cached_result

    # Create search filters
    filters = SearchFilters(
        genre=genre,
        min_rating=min_rating,
        max_rating=max_rating,
        year=None,  # TV shows don't have year field
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
    shows, total = TVShowSearchService.search(db, filters)

    # Build applied filters dict
    applied_filters = {}
    if genre:
        applied_filters["genre"] = genre
    if min_rating is not None:
        applied_filters["min_rating"] = min_rating
    if max_rating is not None:
        applied_filters["max_rating"] = max_rating

    result = {
        "items": shows,
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


@router.get("/{show_id}", response_model=TVShowResponse)
async def get_tv_show(
    show_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific TV show by ID"""
    cache_service = get_cache_service()
    cache_key = f"{cache_service.TV_SHOW_PREFIX}{show_id}"

    # Try to get from cache
    cached_show = cache_service.get(cache_key)
    if cached_show:
        logger.debug(f"Returning cached TV show: {show_id}")
        return cached_show

    show = TVShowService.get_tv_show_by_id(db, show_id)
    if not show:
        raise HTTPException(status_code=404, detail="TV show not found")

    # Cache the result
    cache_service.set(cache_key, show, ttl=cache_service.TV_SHOW_TTL)

    return show


@router.get("/{show_id}/seasons", response_model=PaginatedSeasonResponse)
async def get_tv_show_seasons(
    show_id: int,
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset from start"),
    page: int = Query(None, ge=1, description="Alternative page number"),
    page_size: int = Query(None, ge=1, le=100, description="Alternative page size"),
    db: Session = Depends(get_db),
):
    """
    List all seasons for a TV show.

    - **show_id**: TV show ID
    - **limit**: Number of items per page (1-100, default: 10)
    - **offset**: Offset from start (default: 0)
    """
    normalized_limit, normalized_offset, current_page = resolve_pagination(
        limit=limit,
        skip=offset,
        page=page,
        page_size=page_size,
    )

    seasons, total = TVShowService.get_tv_show_seasons(
        db, show_id=show_id, limit=normalized_limit, offset=normalized_offset
    )
    if seasons is None:
        raise HTTPException(status_code=404, detail="TV show not found")

    # Add episode count to each season
    seasons_with_count = []
    for season in seasons:
        season_dict = {
            "id": season.id,
            "season_number": season.season_number,
            "tmdb_id": season.tmdb_id,
            "episode_count": len(season.episodes),
            "created_at": season.created_at,
        }
        seasons_with_count.append(season_dict)

    return {
        "items": seasons_with_count,
        "total": total,
        **pagination_metadata(total=total, limit=normalized_limit, skip=normalized_offset),
        "page": current_page,
    }


@router.get("/{show_id}/seasons/{season_id}/episodes", response_model=PaginatedEpisodeResponse)
async def get_season_episodes(
    show_id: int,
    season_id: int,
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset from start"),
    page: int = Query(None, ge=1, description="Alternative page number"),
    page_size: int = Query(None, ge=1, le=100, description="Alternative page size"),
    db: Session = Depends(get_db),
):
    """
    List all episodes for a season.

    - **show_id**: TV show ID
    - **season_id**: Season ID
    - **limit**: Number of items per page (1-100, default: 10)
    - **offset**: Offset from start (default: 0)
    """
    normalized_limit, normalized_offset, current_page = resolve_pagination(
        limit=limit,
        skip=offset,
        page=page,
        page_size=page_size,
    )

    episodes, total = TVShowService.get_season_episodes(
        db, show_id=show_id, season_id=season_id, limit=normalized_limit, offset=normalized_offset
    )
    if episodes is None:
        raise HTTPException(status_code=404, detail="TV show or season not found")

    # Build episode dicts with quality/runtime from first associated file
    episode_items = []
    for ep in episodes:
        first_file = ep.files[0] if ep.files else None
        quality = _resolution_to_quality(first_file.resolution if first_file else None)
        runtime_minutes = (
            round(first_file.duration / 60) if first_file and first_file.duration else None
        )
        episode_items.append(
            {
                "id": ep.id,
                "episode_number": ep.episode_number,
                "title": ep.title,
                "plot": ep.plot,
                "air_date": ep.air_date,
                "rating": ep.rating,
                "tmdb_id": ep.tmdb_id,
                "quality": quality,
                "runtime": runtime_minutes,
                "created_at": ep.created_at,
                "updated_at": ep.updated_at,
            }
        )

    return {
        "items": episode_items,
        "total": total,
        **pagination_metadata(total=total, limit=normalized_limit, skip=normalized_offset),
        "page": current_page,
    }


@router.post("/scan-directory")
async def scan_tv_directory(db: Session = Depends(get_db)):
    """Scan the TV directory for new files and create show/season/episode records with FFprobe analysis."""  # noqa: E501
    try:
        file_service = FileService(db)
        try:
            files_synced = file_service.sync_directory(TV_DIR)
        except ValueError as e:
            logger.warning(f"Could not sync {TV_DIR}: {e}")
            files_synced = 0

        shows_created = create_tv_shows_from_files(db)
        pending_shows = (
            db.query(TVShowModel)
            .filter(TVShowModel.enrichment_status.in_(["local_only", "external_failed"]))
            .all()
        )
        for s in pending_shows:
            enrich_tv_show_external(s.id)
        shows_enriched = len(pending_shows)
        files_scanned = probe_unscanned_episodes(db)

        # Invalidate TV show list cache
        cache_service = get_cache_service()
        cache_service.delete_pattern(f"{cache_service.TV_SHOW_LIST_PREFIX}*")

        return {
            "files_synced": files_synced,
            "shows_created": shows_created,
            "shows_enriched": shows_enriched,
            "files_scanned": files_scanned,
        }
    except Exception as e:
        logger.error(f"Error scanning TV directory: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An error occurred while scanning the TV directory"
        )


@router.post("", response_model=TVShowResponse, status_code=201)
async def create_tv_show(
    show_data: TVShowCreate,
    db: Session = Depends(get_db),
):
    """Create a new TV show"""
    show = TVShowService.create_tv_show(db, show_data)

    # Invalidate TV show list cache
    cache_service = get_cache_service()
    cache_service.delete_pattern(f"{cache_service.TV_SHOW_LIST_PREFIX}*")
    logger.debug("Invalidated TV show list cache after create")

    return show


@router.put("/{show_id}", response_model=TVShowResponse)
async def update_tv_show(
    show_id: int,
    show_data: TVShowUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing TV show"""
    show = TVShowService.update_tv_show(db, show_id, show_data)
    if not show:
        raise HTTPException(status_code=404, detail="TV show not found")

    # Invalidate cache for this TV show and TV show lists
    cache_service = get_cache_service()
    cache_service.invalidate_tv_show(show_id)
    logger.debug(f"Invalidated cache for TV show {show_id} after update")

    return show


@router.delete("/{show_id}", status_code=204)
async def delete_tv_show(
    show_id: int,
    db: Session = Depends(get_db),
):
    """Delete a TV show"""
    success = TVShowService.delete_tv_show(db, show_id)
    if not success:
        raise HTTPException(status_code=404, detail="TV show not found")

    # Invalidate cache for this TV show and TV show lists
    cache_service = get_cache_service()
    cache_service.invalidate_tv_show(show_id)
    logger.debug(f"Invalidated cache for TV show {show_id} after delete")

    return None


@router.post("/{show_id}/sync-metadata", response_model=MetadataSyncResponse)
async def sync_tv_show_metadata(
    show_id: int,
    db: Session = Depends(get_db),
):
    """
    Fetch TV show metadata from TMDB and update the TV show record.

    This endpoint:
    1. Retrieves the TV show from the database
    2. Fetches updated metadata from TMDB using the show's TMDB ID
    3. Updates the TV show record with new metadata
    4. Returns the updated TV show information

    Parameters:
    - **show_id**: ID of the TV show to sync

    Returns:
    - **success**: Whether sync was successful
    - **message**: Operation message
    - **show_id**: ID of the synced TV show
    - **updated_fields**: List of fields that were updated
    - **metadata**: Updated metadata
    """
    try:
        # Get the TV show
        show = TVShowService.get_tv_show_by_id(db, show_id)
        if not show:
            raise HTTPException(status_code=404, detail="TV show not found")

        # Check if show has TMDB ID
        if not show.tmdb_id:
            raise HTTPException(
                status_code=400,
                detail="TV show does not have a TMDB ID. Cannot sync metadata.",
            )

        logger.info(f"Syncing metadata for TV show {show_id} (TMDB ID: {show.tmdb_id})")

        # Fetch metadata from TMDB
        tmdb_data = await TMDBService.get_series_details(db, show.tmdb_id)
        if not tmdb_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch metadata from TMDB. Please try again later.",
            )

        # Parse TMDB response
        parsed_data = TMDBService.parse_series_response(tmdb_data)
        if not parsed_data:
            raise HTTPException(status_code=500, detail="Failed to parse TMDB response")

        # Track which fields were updated
        updated_fields = []
        old_values = {}

        # Update TV show fields
        if "title" in parsed_data and parsed_data["title"] != show.title:
            old_values["title"] = show.title
            show.title = parsed_data["title"]
            updated_fields.append("title")

        if "plot" in parsed_data and parsed_data["plot"] != show.plot:
            old_values["plot"] = show.plot
            show.plot = parsed_data["plot"]
            updated_fields.append("plot")

        if "rating" in parsed_data and parsed_data["rating"] != show.rating:
            old_values["rating"] = show.rating
            show.rating = parsed_data["rating"]
            updated_fields.append("rating")

        if "status" in parsed_data and parsed_data["status"] != show.status:
            old_values["status"] = show.status
            show.status = parsed_data["status"]
            updated_fields.append("status")

        if "genres" in parsed_data and parsed_data["genres"] != show.genres:
            old_values["genres"] = show.genres
            show.genres = parsed_data["genres"]
            updated_fields.append("genres")

        poster = parsed_data.get("poster")
        if poster and poster != show.poster_url:
            old_values["poster_url"] = show.poster_url
            show.poster_url = poster
            updated_fields.append("poster_url")

        # Commit changes
        db.commit()
        db.refresh(show)

        # Invalidate cache for this TV show and TV show lists
        cache_service = get_cache_service()
        cache_service.invalidate_tv_show(show_id)
        logger.debug(f"Invalidated cache for TV show {show_id} after metadata sync")

        logger.info(
            f"Successfully synced metadata for TV show {show_id}. "
            f"Updated fields: {', '.join(updated_fields) if updated_fields else 'none'}"
        )

        # Prepare response metadata
        response_metadata = {
            "title": show.title,
            "plot": show.plot,
            "rating": show.rating,
            "status": show.status,
            "genres": json.loads(show.genres) if show.genres else [],
            "tmdb_id": show.tmdb_id,
            "poster_url": show.poster_url,
        }

        return {
            "success": True,
            "message": f"TV show metadata synced successfully. Updated {len(updated_fields)} field(s).",  # noqa: E501
            "movie_id": None,
            "show_id": show_id,
            "updated_fields": updated_fields,
            "metadata": response_metadata,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing metadata for TV show {show_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while syncing metadata")


class ExternalIdPayload(PydanticBase):
    external_id: str


@router.patch("/{show_id}/external-id", response_model=TVShowResponse)
async def set_tvshow_external_id(
    show_id: int,
    payload: ExternalIdPayload,
    db: Session = Depends(get_db),
):
    """Set a manual TMDB ID and trigger enrichment immediately."""
    show = TVShowService.get_tv_show_by_id(db, show_id)
    if not show:
        raise HTTPException(status_code=404, detail="TV show not found")
    show.manual_external_id = payload.external_id
    show.enrichment_status = "local_only"
    show.enrichment_error = None
    db.commit()
    db.refresh(show)
    enrich_tv_show_external(show.id)
    cache_service = get_cache_service()
    cache_service.invalidate_tv_show(show_id)
    return show


@router.post("/{show_id}/enrich", status_code=202)
async def trigger_tvshow_enrichment(
    show_id: int,
    db: Session = Depends(get_db),
):
    """Manually trigger external enrichment for a TV show."""
    show = TVShowService.get_tv_show_by_id(db, show_id)
    if not show:
        raise HTTPException(status_code=404, detail="TV show not found")
    enrich_tv_show_external(show.id)
    cache_service = get_cache_service()
    cache_service.invalidate_tv_show(show_id)
    return {"message": "Enrichment triggered", "show_id": show_id}
