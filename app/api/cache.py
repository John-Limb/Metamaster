"""Cache management API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    CacheStatsResponse,
    PaginatedCacheResponse,
    CacheOperationResponse,
    CacheEntryResponse,
)
from app.services import CacheService
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
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cache statistics"
        )


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
        raise HTTPException(
            status_code=500,
            detail="Failed to delete expired cache entries"
        )


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
                detail=f"Invalid cache type. Must be one of: {', '.join(valid_types)}"
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
        raise HTTPException(
            status_code=500,
            detail="Failed to invalidate cache entries"
        )


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
                detail=f"Invalid cache type. Must be one of: {', '.join(valid_types)}"
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
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cache entries"
        )
