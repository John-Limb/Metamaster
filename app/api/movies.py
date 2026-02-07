"""Movie API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    MovieCreate,
    MovieUpdate,
    MovieResponse,
    PaginatedMovieResponse,
    PaginatedMovieResponseWithFilters,
    MetadataSyncResponse,
)
from app.services_impl import MovieService, OMDBService
from app.services.redis_cache import get_cache_service
from app.services.search_service import SearchFilters, MovieSearchService
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("", response_model=PaginatedMovieResponseWithFilters)
async def list_movies(
    genre: str = Query(None, description="Filter by genre (case-insensitive)"),
    min_rating: float = Query(None, ge=0, le=10, description="Minimum rating (0-10)"),
    max_rating: float = Query(None, ge=0, le=10, description="Maximum rating (0-10)"),
    year: int = Query(None, ge=1800, le=2100, description="Release year"),
    sort_by: str = Query(
        "title", description="Sort by: title, rating, year, date_added"
    ),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    skip: int = Query(0, ge=0, description="Offset from start"),
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

    # Build cache key including all filter parameters
    cache_key = (
        f"{cache_service.MOVIE_LIST_PREFIX}"
        f"genre={genre}:min_rating={min_rating}:max_rating={max_rating}:"
        f"year={year}:sort_by={sort_by}:limit={limit}:skip={skip}"
    )

    # Try to get from cache
    cached_result = cache_service.get(cache_key)
    if cached_result:
        logger.debug(f"Returning cached movie list with filters")
        return cached_result

    # Create search filters
    filters = SearchFilters(
        genre=genre,
        min_rating=min_rating,
        max_rating=max_rating,
        year=year,
        sort_by=sort_by,
        skip=skip,
        limit=limit,
    )

    # Validate filters
    is_valid, error_msg = filters.validate()
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Perform search
    movies, total = MovieSearchService.search(db, filters)

    # Build applied filters dict
    applied_filters = {}
    if genre:
        applied_filters["genre"] = genre
    if min_rating is not None:
        applied_filters["min_rating"] = min_rating
    if max_rating is not None:
        applied_filters["max_rating"] = max_rating
    if year is not None:
        applied_filters["year"] = year

    result = {
        "items": movies,
        "total": total,
        "limit": limit,
        "offset": skip,
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
    db: Session = Depends(get_db),
):
    """
    Search movies by title.

    - **q**: Search query (required)
    - **limit**: Number of items per page (1-100, default: 10)
    - **offset**: Offset from start (default: 0)
    """
    movies, total = MovieService.search_movies(db, query=q, limit=limit, offset=offset)
    return {
        "items": movies,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


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

    # Cache the result
    cache_service.set(cache_key, movie, ttl=cache_service.MOVIE_TTL)

    return movie


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


@router.post("/{movie_id}/sync-metadata", response_model=MetadataSyncResponse)
async def sync_movie_metadata(
    movie_id: int,
    db: Session = Depends(get_db),
):
    """
    Fetch movie metadata from OMDB and update the movie record.

    This endpoint:
    1. Retrieves the movie from the database
    2. Fetches updated metadata from OMDB using the movie's OMDB ID
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

        # Check if movie has OMDB ID
        if not movie.omdb_id:
            raise HTTPException(
                status_code=400,
                detail="Movie does not have an OMDB ID. Cannot sync metadata.",
            )

        logger.info(f"Syncing metadata for movie {movie_id} (OMDB ID: {movie.omdb_id})")

        # Fetch metadata from OMDB
        omdb_data = await OMDBService.get_movie_details(db, movie.omdb_id)
        if not omdb_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch metadata from OMDB. Please try again later.",
            )

        # Parse OMDB response
        parsed_data = OMDBService.parse_omdb_response(omdb_data)
        if not parsed_data:
            raise HTTPException(status_code=500, detail="Failed to parse OMDB response")

        # Track which fields were updated
        updated_fields = []
        old_values = {}

        # Update movie fields
        if "title" in parsed_data and parsed_data["title"] != movie.title:
            old_values["title"] = movie.title
            movie.title = parsed_data["title"]
            updated_fields.append("title")

        if "plot" in parsed_data and parsed_data["plot"] != movie.plot:
            old_values["plot"] = movie.plot
            movie.plot = parsed_data["plot"]
            updated_fields.append("plot")

        if "year" in parsed_data and parsed_data["year"] != movie.year:
            old_values["year"] = movie.year
            movie.year = parsed_data["year"]
            updated_fields.append("year")

        if "rating" in parsed_data and parsed_data["rating"] != movie.rating:
            old_values["rating"] = movie.rating
            movie.rating = parsed_data["rating"]
            updated_fields.append("rating")

        if "runtime" in parsed_data and parsed_data["runtime"] != movie.runtime:
            old_values["runtime"] = movie.runtime
            movie.runtime = parsed_data["runtime"]
            updated_fields.append("runtime")

        if "genres" in parsed_data and parsed_data["genres"] != movie.genres:
            old_values["genres"] = movie.genres
            movie.genres = parsed_data["genres"]
            updated_fields.append("genres")

        # Commit changes
        db.commit()
        db.refresh(movie)

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
            "omdb_id": movie.omdb_id,
        }

        return {
            "success": True,
            "message": f"Movie metadata synced successfully. Updated {len(updated_fields)} field(s).",
            "movie_id": movie_id,
            "show_id": None,
            "updated_fields": updated_fields,
            "metadata": response_metadata,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing metadata for movie {movie_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An error occurred while syncing metadata"
        )
