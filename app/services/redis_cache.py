"""Redis caching service for application data"""

import redis
import json
import logging
from typing import Optional, Any, Dict
from datetime import datetime, timedelta, timezone
from app.config import settings

logger = logging.getLogger(__name__)


class RedisCacheService:
    """Service for managing Redis cache operations"""

    # Cache key prefixes
    MOVIE_PREFIX = "movie:"
    MOVIE_LIST_PREFIX = "movies:list:"
    TV_SHOW_PREFIX = "tvshow:"
    TV_SHOW_LIST_PREFIX = "tvshows:list:"
    STATS_PREFIX = "cache:stats:"
    
    # Default TTLs (in seconds)
    DEFAULT_TTL = 3600  # 1 hour
    MOVIE_TTL = 86400  # 24 hours
    TV_SHOW_TTL = 86400  # 24 hours
    LIST_TTL = 1800  # 30 minutes

    def __init__(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if not self.is_connected():
            logger.warning("Redis not connected, skipping cache get")
            return None

        try:
            value = self.redis_client.get(key)
            if value:
                # Track cache hit
                self._track_hit(key)
                logger.debug(f"Cache hit for key: {key}")
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            else:
                # Track cache miss
                self._track_miss(key)
                logger.debug(f"Cache miss for key: {key}")
                return None
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in cache
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (uses DEFAULT_TTL if not specified)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            logger.warning("Redis not connected, skipping cache set")
            return False

        try:
            if ttl is None:
                ttl = self.DEFAULT_TTL

            # Serialize value to JSON
            serialized_value = json.dumps(value)
            
            # Set with expiration
            self.redis_client.setex(key, ttl, serialized_value)
            logger.debug(f"Cache set for key: {key} with TTL: {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a key from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False otherwise
        """
        if not self.is_connected():
            logger.warning("Redis not connected, skipping cache delete")
            return False

        try:
            result = self.redis_client.delete(key)
            logger.debug(f"Cache deleted for key: {key}")
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern
        
        Args:
            pattern: Key pattern (e.g., "movie:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.is_connected():
            logger.warning("Redis not connected, skipping pattern delete")
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Deleted {deleted} cache keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Error deleting cache pattern {pattern}: {e}")
            return 0

    def clear_all(self) -> bool:
        """
        Clear all cache
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            logger.warning("Redis not connected, skipping cache clear")
            return False

        try:
            self.redis_client.flushdb()
            logger.info("All cache cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing all cache: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.is_connected():
            return {
                "connected": False,
                "total_keys": 0,
                "memory_usage_bytes": 0,
                "memory_usage_mb": 0,
                "hit_rate": 0.0,
                "total_hits": 0,
                "total_misses": 0,
            }

        try:
            info = self.redis_client.info()
            keys = self.redis_client.keys("*")
            
            total_hits = self._get_stat("total_hits", 0)
            total_misses = self._get_stat("total_misses", 0)
            total_requests = total_hits + total_misses
            hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0

            return {
                "connected": True,
                "total_keys": len(keys),
                "memory_usage_bytes": info.get("used_memory", 0),
                "memory_usage_mb": info.get("used_memory", 0) / (1024 * 1024),
                "hit_rate": round(hit_rate, 2),
                "total_hits": total_hits,
                "total_misses": total_misses,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "connected": False,
                "total_keys": 0,
                "memory_usage_bytes": 0,
                "memory_usage_mb": 0,
                "hit_rate": 0.0,
                "total_hits": 0,
                "total_misses": 0,
            }

    def _track_hit(self, key: str) -> None:
        """Track cache hit"""
        try:
            self.redis_client.incr(f"{self.STATS_PREFIX}total_hits")
        except Exception as e:
            logger.debug(f"Error tracking cache hit: {e}")

    def _track_miss(self, key: str) -> None:
        """Track cache miss"""
        try:
            self.redis_client.incr(f"{self.STATS_PREFIX}total_misses")
        except Exception as e:
            logger.debug(f"Error tracking cache miss: {e}")

    def _get_stat(self, stat_name: str, default: int = 0) -> int:
        """Get a statistic value"""
        try:
            value = self.redis_client.get(f"{self.STATS_PREFIX}{stat_name}")
            return int(value) if value else default
        except Exception:
            return default

    def invalidate_movie(self, movie_id: int) -> None:
        """Invalidate cache for a specific movie"""
        key = f"{self.MOVIE_PREFIX}{movie_id}"
        self.delete(key)
        # Also invalidate movie lists
        self.delete_pattern(f"{self.MOVIE_LIST_PREFIX}*")
        logger.info(f"Invalidated cache for movie {movie_id}")

    def invalidate_tv_show(self, show_id: int) -> None:
        """Invalidate cache for a specific TV show"""
        key = f"{self.TV_SHOW_PREFIX}{show_id}"
        self.delete(key)
        # Also invalidate TV show lists
        self.delete_pattern(f"{self.TV_SHOW_LIST_PREFIX}*")
        logger.info(f"Invalidated cache for TV show {show_id}")

    def invalidate_all_movies(self) -> None:
        """Invalidate all movie cache"""
        self.delete_pattern(f"{self.MOVIE_PREFIX}*")
        self.delete_pattern(f"{self.MOVIE_LIST_PREFIX}*")
        logger.info("Invalidated all movie cache")

    def invalidate_all_tv_shows(self) -> None:
        """Invalidate all TV show cache"""
        self.delete_pattern(f"{self.TV_SHOW_PREFIX}*")
        self.delete_pattern(f"{self.TV_SHOW_LIST_PREFIX}*")
        logger.info("Invalidated all TV show cache")

    def warmup_cache(self, movies: list, tv_shows: list) -> Dict[str, int]:
        """
        Pre-populate cache with frequently accessed data
        
        Args:
            movies: List of movie objects to cache
            tv_shows: List of TV show objects to cache
            
        Returns:
            Dictionary with count of cached items
        """
        if not self.is_connected():
            logger.warning("Redis not connected, skipping cache warmup")
            return {"movies": 0, "tv_shows": 0}

        try:
            movie_count = 0
            tv_show_count = 0

            # Cache movies
            for movie in movies:
                key = f"{self.MOVIE_PREFIX}{movie.id}"
                movie_dict = {
                    "id": movie.id,
                    "title": movie.title,
                    "plot": movie.plot,
                    "year": movie.year,
                    "rating": movie.rating,
                    "runtime": movie.runtime,
                    "genres": movie.genres,
                    "omdb_id": movie.omdb_id,
                }
                if self.set(key, movie_dict, ttl=self.MOVIE_TTL):
                    movie_count += 1

            # Cache TV shows
            for show in tv_shows:
                key = f"{self.TV_SHOW_PREFIX}{show.id}"
                show_dict = {
                    "id": show.id,
                    "title": show.title,
                    "plot": show.plot,
                    "rating": show.rating,
                    "status": show.status,
                    "genres": show.genres,
                    "tvdb_id": show.tvdb_id,
                }
                if self.set(key, show_dict, ttl=self.TV_SHOW_TTL):
                    tv_show_count += 1

            logger.info(f"Cache warmup completed: {movie_count} movies, {tv_show_count} TV shows")
            return {"movies": movie_count, "tv_shows": tv_show_count}
        except Exception as e:
            logger.error(f"Error during cache warmup: {e}")
            return {"movies": 0, "tv_shows": 0}


# Global cache service instance
_cache_service: Optional[RedisCacheService] = None


def get_cache_service() -> RedisCacheService:
    """Get or create the global cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = RedisCacheService()
    return _cache_service
