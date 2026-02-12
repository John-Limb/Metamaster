"""Cache management API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas import (
    CacheStatsResponse,
    PaginatedCacheResponse,
    CacheOperationResponse,
    CacheEntryResponse,
)
from app.services_impl import CacheService
from app.infrastructure.cache.redis_cache import get_cache_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["Cache Management"])


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    db: Session = Depends(get_db),
):
    """
    Get cache statistics including size, count, and breakdown by API type.

    Returns:
    - **total_entries**: Total number of cache entries
    - **active_entries**: Number of non-expired entries
    - **expired_entries**: Number of expired entries
    - **total_size_bytes**: Total cache size in bytes
    - **total_size_mb**: Total cache size in megabytes
    - **by_api_type**: Breakdown of entries by API type
    - **timestamp**: When statistics were generated
    """
    try:
        stats = CacheService.get_cache_stats(db)
        logger.info(f"Retrieved cache statistics: {stats['total_entries']} total entries")
        return stats
    except Exception as e:
        logger.error(f"Error retrieving cache statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache statistics")


@router.delete("/expired", response_model=CacheOperationResponse)
async def delete_expired_cache(
    db: Session = Depends(get_db),
):
    """
    Delete all expired cache entries.

    Returns:
    - **success**: Whether operation was successful
    - **message**: Operation message
    - **affected_entries**: Number of entries deleted
    """
    try:
        count = CacheService.clear_expired_cache(db)
        logger.info(f"Deleted {count} expired cache entries")
        return {
            "success": True,
            "message": f"Deleted {count} expired cache entries",
            "affected_entries": count,
        }
    except Exception as e:
        logger.error(f"Error deleting expired cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete expired cache entries")


@router.delete("/{cache_type}", response_model=CacheOperationResponse)
async def invalidate_cache_by_type(
    cache_type: str,
    db: Session = Depends(get_db),
):
    """
    Invalidate all cache entries for a specific API type.

    Parameters:
    - **cache_type**: API type to invalidate (e.g., 'omdb', 'tvdb')

    Returns:
    - **success**: Whether operation was successful
    - **message**: Operation message
    - **affected_entries**: Number of entries invalidated
    """
    try:
        # Validate cache type
        valid_types = ["omdb", "tvdb", "generic"]
        if cache_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid cache type. Must be one of: {', '.join(valid_types)}",
            )

        count = CacheService.invalidate_by_type(db, cache_type)
        logger.info(f"Invalidated {count} cache entries for type: {cache_type}")
        return {
            "success": True,
            "message": f"Invalidated {count} cache entries for type: {cache_type}",
            "affected_entries": count,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error invalidating cache by type {cache_type}: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate cache entries")


@router.get("/{cache_type}", response_model=PaginatedCacheResponse)
async def list_cache_by_type(
    cache_type: str,
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset from start"),
    db: Session = Depends(get_db),
):
    """
    List cache entries for a specific API type with pagination.

    Parameters:
    - **cache_type**: API type to list (e.g., 'omdb', 'tvdb')
    - **limit**: Number of items per page (1-100, default: 10)
    - **offset**: Offset from start (default: 0)

    Returns:
    - **items**: List of cache entries
    - **total**: Total number of entries for this type
    - **limit**: Items per page
    - **offset**: Offset from start
    """
    try:
        # Validate cache type
        valid_types = ["omdb", "tvdb", "generic"]
        if cache_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid cache type. Must be one of: {', '.join(valid_types)}",
            )

        entries, total = CacheService.get_cache_by_type(
            db, cache_type=cache_type, limit=limit, offset=offset
        )
        logger.info(f"Retrieved {len(entries)} cache entries for type: {cache_type}")
        return {
            "items": entries,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving cache entries for type {cache_type}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache entries")


@router.get("/redis/stats", response_model=dict)
async def get_redis_cache_stats():
    """
    Get Redis cache statistics including hit/miss rates and memory usage.

    Returns:
    - **connected**: Whether Redis is connected
    - **total_keys**: Total number of keys in cache
    - **memory_usage_bytes**: Memory usage in bytes
    - **memory_usage_mb**: Memory usage in megabytes
    - **hit_rate**: Cache hit rate percentage
    - **total_hits**: Total cache hits
    - **total_misses**: Total cache misses
    - **timestamp**: When statistics were generated
    """
    try:
        cache_service = get_cache_service()
        stats = cache_service.get_stats()
        logger.info(f"Retrieved Redis cache statistics")
        return stats
    except Exception as e:
        logger.error(f"Error retrieving Redis cache statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Redis cache statistics")


@router.delete("/redis/clear", response_model=CacheOperationResponse)
async def clear_redis_cache():
    """
    Clear all Redis cache.

    Returns:
    - **success**: Whether operation was successful
    - **message**: Operation message
    - **affected_entries**: Number of entries cleared (always 0 for Redis)
    """
    try:
        cache_service = get_cache_service()
        success = cache_service.clear_all()
        if success:
            logger.info("Cleared all Redis cache")
            return {
                "success": True,
                "message": "All Redis cache cleared successfully",
                "affected_entries": 0,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear Redis cache")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing Redis cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear Redis cache")


@router.post("/redis/warmup", response_model=dict)
async def warmup_redis_cache(
    db: Session = Depends(get_db),
):
    """
    Pre-populate Redis cache with frequently accessed data.

    Returns:
    - **success**: Whether operation was successful
    - **message**: Operation message
    - **movies_cached**: Number of movies cached
    - **tv_shows_cached**: Number of TV shows cached
    """
    try:
        from app.domain.movies.service import MovieService
        from app.domain.tv_shows.service import TVShowService

        cache_service = get_cache_service()

        # Get all movies and TV shows
        movies, _ = MovieService.get_all_movies(db, limit=1000, offset=0)
        shows, _ = TVShowService.get_all_tv_shows(db, limit=1000, offset=0)

        # Warmup cache
        result = cache_service.warmup_cache(movies, shows)

        logger.info(
            f"Cache warmup completed: {result['movies']} movies, {result['tv_shows']} TV shows"
        )
        return {
            "success": True,
            "message": "Cache warmup completed successfully",
            "movies_cached": result["movies"],
            "tv_shows_cached": result["tv_shows"],
        }
    except Exception as e:
        logger.error(f"Error during cache warmup: {e}")
        raise HTTPException(status_code=500, detail="Failed to warmup cache")


@router.get("/db-stats", response_model=dict)
async def get_database_stats(
    db: Session = Depends(get_db),
):
    """
    Get database connection pool statistics and performance metrics.

    Returns:
    - **timestamp**: When statistics were generated
    - **query_performance**: Query execution statistics
    - **slow_queries**: List of slow queries detected
    - **connection_pool**: Connection pool statistics
    - **index_recommendations**: Recommended indexes
    - **all_indexes**: All existing indexes
    """
    try:
        from app.core.database import get_engine
        from app.application.db_optimization.service import DatabaseOptimizationService

        engine = get_engine()
        report = DatabaseOptimizationService.get_optimization_report(db, engine)

        logger.info("Retrieved database statistics")
        return report
    except Exception as e:
        logger.error(f"Error retrieving database statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve database statistics")


@router.get("/slow-queries", response_model=dict)
async def get_slow_queries(
    limit: int = Query(10, ge=1, le=100, description="Number of slow queries to return"),
):
    """
    Get list of slow queries detected by the query performance tracker.

    Parameters:
    - **limit**: Number of slow queries to return (1-100, default: 10)

    Returns:
    - **slow_queries**: List of slow queries with execution times
    - **count**: Number of slow queries returned
    - **threshold**: Slow query threshold in seconds
    """
    try:
        from app.application.db_optimization.service import DatabaseOptimizationService

        tracker = DatabaseOptimizationService.get_query_tracker()
        slow_queries = tracker.get_slow_queries(limit=limit)

        logger.info(f"Retrieved {len(slow_queries)} slow queries")
        return {
            "slow_queries": slow_queries,
            "count": len(slow_queries),
            "threshold": tracker.slow_query_threshold,
        }
    except Exception as e:
        logger.error(f"Error retrieving slow queries: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve slow queries")
