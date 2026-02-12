"""TV Show API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas import (
    TVShowCreate,
    TVShowUpdate,
    TVShowResponse,
    PaginatedTVShowResponse,
    PaginatedTVShowResponseWithFilters,
    PaginatedSeasonResponse,
    PaginatedEpisodeResponse,
    SeasonResponse,
    EpisodeResponse,
    MetadataSyncResponse,
)
from app.services_impl import TVShowService, TVDBService
from app.infrastructure.cache.redis_cache import get_cache_service
from app.application.search.service import SearchFilters, TVShowSearchService
from app.api.utils import pagination_metadata, resolve_pagination
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tv-shows", tags=["TV Shows"])


@router.get("", response_model=PaginatedTVShowResponseWithFilters)
async def list_tv_shows(
    genre: str = Query(None, description="Filter by genre (case-insensitive)"),
    min_rating: float = Query(None, ge=0, le=10, description="Minimum rating (0-10)"),
    max_rating: float = Query(None, ge=0, le=10, description="Maximum rating (0-10)"),
    sort_by: str = Query("title", description="Sort by: title, rating, date_added"),
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

    # Build cache key including all filter parameters
    cache_key = (
        f"{cache_service.TV_SHOW_LIST_PREFIX}"
        f"genre={genre}:min_rating={min_rating}:max_rating={max_rating}:"
        f"sort_by={sort_by}:limit={normalized_limit}:skip={normalized_skip}"
    )

    # Try to get from cache
    cached_result = cache_service.get(cache_key)
    if cached_result:
        logger.debug(f"Returning cached TV show list with filters")
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
            "tvdb_id": season.tvdb_id,
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

    return {
        "items": episodes,
        "total": total,
        **pagination_metadata(total=total, limit=normalized_limit, skip=normalized_offset),
        "page": current_page,
    }


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
    Fetch TV show metadata from TVDB and update the TV show record.

    This endpoint:
    1. Retrieves the TV show from the database
    2. Fetches updated metadata from TVDB using the show's TVDB ID
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

        # Check if show has TVDB ID
        if not show.tvdb_id:
            raise HTTPException(
                status_code=400,
                detail="TV show does not have a TVDB ID. Cannot sync metadata.",
            )

        logger.info(f"Syncing metadata for TV show {show_id} (TVDB ID: {show.tvdb_id})")

        # Fetch metadata from TVDB
        tvdb_data = await TVDBService.get_series_details(db, show.tvdb_id)
        if not tvdb_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch metadata from TVDB. Please try again later.",
            )

        # Parse TVDB response
        parsed_data = TVDBService.parse_tvdb_series_response(tvdb_data)
        if not parsed_data:
            raise HTTPException(status_code=500, detail="Failed to parse TVDB response")

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

        # Commit changes
        db.commit()
        db.refresh(show)

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
            "tvdb_id": show.tvdb_id,
        }

        return {
            "success": True,
            "message": f"TV show metadata synced successfully. Updated {len(updated_fields)} field(s).",
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
