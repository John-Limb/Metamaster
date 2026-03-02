"""Tests for Redis caching service"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.infrastructure.cache.redis_cache import RedisCacheService, get_cache_service
from app.models import Movie, TVShow


class TestRedisCacheService:
    """Test cases for RedisCacheService"""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client"""
        with patch("app.infrastructure.cache.redis_cache.redis.from_url") as mock:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def cache_service(self, mock_redis):
        """Create a cache service instance with mocked Redis"""
        service = RedisCacheService()
        service.redis_client = mock_redis
        return service

    def test_cache_service_initialization(self, mock_redis):
        """Test cache service initialization"""
        service = RedisCacheService()
        assert service.redis_client is not None
        mock_redis.ping.assert_called()

    def test_is_connected_true(self, cache_service):
        """Test is_connected returns True when Redis is available"""
        cache_service.redis_client.ping.return_value = True
        assert cache_service.is_connected() is True

    def test_is_connected_false(self, cache_service):
        """Test is_connected returns False when Redis is unavailable"""
        cache_service.redis_client.ping.side_effect = Exception("Connection failed")
        assert cache_service.is_connected() is False

    def test_is_connected_no_client(self):
        """Test is_connected returns False when no client"""
        service = RedisCacheService()
        service.redis_client = None
        assert service.is_connected() is False

    def test_get_cache_hit(self, cache_service):
        """Test getting a value from cache (cache hit)"""
        test_data = {"id": 1, "title": "Test Movie"}
        cache_service.redis_client.get.return_value = json.dumps(test_data)

        result = cache_service.get("movie:1")

        assert result == test_data
        cache_service.redis_client.get.assert_called_with("movie:1")
        cache_service.redis_client.incr.assert_called()

    def test_get_cache_miss(self, cache_service):
        """Test getting a value from cache (cache miss)"""
        cache_service.redis_client.get.return_value = None

        result = cache_service.get("movie:999")

        assert result is None
        cache_service.redis_client.get.assert_called_with("movie:999")

    def test_get_non_json_value(self, cache_service):
        """Test getting a non-JSON value from cache"""
        cache_service.redis_client.get.return_value = "simple_string"

        result = cache_service.get("key:1")

        assert result == "simple_string"

    def test_get_redis_disconnected(self, cache_service):
        """Test get returns None when Redis is disconnected"""
        cache_service.redis_client = None

        result = cache_service.get("movie:1")

        assert result is None

    def test_set_cache(self, cache_service):
        """Test setting a value in cache"""
        test_data = {"id": 1, "title": "Test Movie"}

        result = cache_service.set("movie:1", test_data, ttl=3600)

        assert result is True
        cache_service.redis_client.setex.assert_called_with("movie:1", 3600, json.dumps(test_data))

    def test_set_cache_default_ttl(self, cache_service):
        """Test setting a value with default TTL"""
        test_data = {"id": 1, "title": "Test Movie"}

        result = cache_service.set("movie:1", test_data)

        assert result is True
        cache_service.redis_client.setex.assert_called_with(
            "movie:1", cache_service.DEFAULT_TTL, json.dumps(test_data)
        )

    def test_set_cache_redis_disconnected(self, cache_service):
        """Test set returns False when Redis is disconnected"""
        cache_service.redis_client = None

        result = cache_service.set("movie:1", {"id": 1})

        assert result is False

    def test_set_cache_error(self, cache_service):
        """Test set returns False on Redis error"""
        cache_service.redis_client.setex.side_effect = Exception("Redis error")

        result = cache_service.set("movie:1", {"id": 1})

        assert result is False

    def test_delete_cache(self, cache_service):
        """Test deleting a key from cache"""
        cache_service.redis_client.delete.return_value = 1

        result = cache_service.delete("movie:1")

        assert result is True
        cache_service.redis_client.delete.assert_called_with("movie:1")

    def test_delete_cache_not_found(self, cache_service):
        """Test deleting a non-existent key"""
        cache_service.redis_client.delete.return_value = 0

        result = cache_service.delete("movie:999")

        assert result is False

    def test_delete_pattern(self, cache_service):
        """Test deleting keys matching a pattern"""
        cache_service.redis_client.keys.return_value = ["movie:1", "movie:2", "movie:3"]
        cache_service.redis_client.delete.return_value = 3

        result = cache_service.delete_pattern("movie:*")

        assert result == 3
        cache_service.redis_client.keys.assert_called_with("movie:*")
        cache_service.redis_client.delete.assert_called_with("movie:1", "movie:2", "movie:3")

    def test_delete_pattern_no_keys(self, cache_service):
        """Test deleting pattern with no matching keys"""
        cache_service.redis_client.keys.return_value = []

        result = cache_service.delete_pattern("movie:*")

        assert result == 0
        cache_service.redis_client.delete.assert_not_called()

    def test_clear_all(self, cache_service):
        """Test clearing all cache"""
        result = cache_service.clear_all()

        assert result is True
        cache_service.redis_client.flushdb.assert_called()

    def test_clear_all_error(self, cache_service):
        """Test clear_all returns False on error"""
        cache_service.redis_client.flushdb.side_effect = Exception("Redis error")

        result = cache_service.clear_all()

        assert result is False

    def test_get_stats(self, cache_service):
        """Test getting cache statistics"""
        cache_service.redis_client.info.return_value = {
            "used_memory": 1024000,
        }
        cache_service.redis_client.keys.return_value = ["key1", "key2", "key3"]
        cache_service.redis_client.get.return_value = "10"

        stats = cache_service.get_stats()

        assert stats["connected"] is True
        assert stats["total_keys"] == 3
        assert stats["memory_usage_bytes"] == 1024000
        assert stats["memory_usage_mb"] == pytest.approx(0.976, rel=0.01)
        assert "timestamp" in stats

    def test_get_stats_disconnected(self, cache_service):
        """Test get_stats returns default values when disconnected"""
        cache_service.redis_client = None

        stats = cache_service.get_stats()

        assert stats["connected"] is False
        assert stats["total_keys"] == 0
        assert stats["memory_usage_bytes"] == 0

    def test_invalidate_movie(self, cache_service):
        """Test invalidating cache for a specific movie"""
        cache_service.redis_client.delete.return_value = 1
        cache_service.redis_client.keys.return_value = ["movies:list:10:0"]

        cache_service.invalidate_movie(1)

        # Should delete the movie key and movie list patterns
        assert cache_service.redis_client.delete.called
        assert cache_service.redis_client.keys.called

    def test_invalidate_tv_show(self, cache_service):
        """Test invalidating cache for a specific TV show"""
        cache_service.redis_client.delete.return_value = 1
        cache_service.redis_client.keys.return_value = ["tvshows:list:10:0"]

        cache_service.invalidate_tv_show(1)

        # Should delete the TV show key and TV show list patterns
        assert cache_service.redis_client.delete.called
        assert cache_service.redis_client.keys.called

    def test_invalidate_all_movies(self, cache_service):
        """Test invalidating all movie cache"""
        cache_service.redis_client.keys.return_value = ["movie:1", "movie:2"]
        cache_service.redis_client.delete.return_value = 2

        cache_service.invalidate_all_movies()

        assert cache_service.redis_client.keys.called
        assert cache_service.redis_client.delete.called

    def test_invalidate_all_tv_shows(self, cache_service):
        """Test invalidating all TV show cache"""
        cache_service.redis_client.keys.return_value = ["tvshow:1", "tvshow:2"]
        cache_service.redis_client.delete.return_value = 2

        cache_service.invalidate_all_tv_shows()

        assert cache_service.redis_client.keys.called
        assert cache_service.redis_client.delete.called

    def test_warmup_cache(self, cache_service):
        """Test cache warmup with movies and TV shows"""
        # Create mock objects
        mock_movie = Mock(spec=Movie)
        mock_movie.id = 1
        mock_movie.title = "Test Movie"
        mock_movie.plot = "Test plot"
        mock_movie.year = 2023
        mock_movie.rating = 8.5
        mock_movie.runtime = 120
        mock_movie.genres = '["Action", "Drama"]'
        mock_movie.tmdb_id = "tt1234567"

        mock_show = Mock(spec=TVShow)
        mock_show.id = 1
        mock_show.title = "Test Show"
        mock_show.plot = "Test plot"
        mock_show.rating = 8.0
        mock_show.status = "Ongoing"
        mock_show.genres = '["Drama"]'
        mock_show.tmdb_id = "123456"

        cache_service.redis_client.setex.return_value = True

        result = cache_service.warmup_cache([mock_movie], [mock_show])

        assert result["movies"] == 1
        assert result["tv_shows"] == 1
        assert cache_service.redis_client.setex.call_count == 2

    def test_warmup_cache_empty(self, cache_service):
        """Test cache warmup with empty lists"""
        result = cache_service.warmup_cache([], [])

        assert result["movies"] == 0
        assert result["tv_shows"] == 0

    def test_warmup_cache_error(self, cache_service):
        """Test cache warmup handles errors gracefully"""
        cache_service.redis_client.setex.side_effect = Exception("Redis error")

        mock_movie = Mock(spec=Movie)
        mock_movie.id = 1

        result = cache_service.warmup_cache([mock_movie], [])

        assert result["movies"] == 0
        assert result["tv_shows"] == 0

    def test_track_hit(self, cache_service):
        """Test tracking cache hits"""
        cache_service._track_hit("movie:1")

        cache_service.redis_client.incr.assert_called()

    def test_track_miss(self, cache_service):
        """Test tracking cache misses"""
        cache_service._track_miss("movie:1")

        cache_service.redis_client.incr.assert_called()

    def test_get_stat(self, cache_service):
        """Test getting a statistic value"""
        cache_service.redis_client.get.return_value = "42"

        result = cache_service._get_stat("total_hits")

        assert result == 42

    def test_get_stat_default(self, cache_service):
        """Test getting a statistic with default value"""
        cache_service.redis_client.get.return_value = None

        result = cache_service._get_stat("total_hits", default=0)

        assert result == 0

    def test_cache_key_prefixes(self):
        """Test cache key prefix constants"""
        assert RedisCacheService.MOVIE_PREFIX == "movie:"
        assert RedisCacheService.MOVIE_LIST_PREFIX == "movies:list:"
        assert RedisCacheService.TV_SHOW_PREFIX == "tvshow:"
        assert RedisCacheService.TV_SHOW_LIST_PREFIX == "tvshows:list:"

    def test_cache_ttl_constants(self):
        """Test cache TTL constants"""
        assert RedisCacheService.DEFAULT_TTL == 3600
        assert RedisCacheService.MOVIE_TTL == 86400
        assert RedisCacheService.TV_SHOW_TTL == 86400
        assert RedisCacheService.LIST_TTL == 1800


class TestCacheServiceGlobal:
    """Test cases for global cache service instance"""

    def test_get_cache_service_singleton(self):
        """Test get_cache_service returns singleton instance"""
        with patch("app.infrastructure.cache.redis_cache.redis.from_url"):
            service1 = get_cache_service()
            service2 = get_cache_service()

            assert service1 is service2

    def test_get_cache_service_creates_instance(self):
        """Test get_cache_service creates instance on first call"""
        with patch("app.infrastructure.cache.redis_cache.redis.from_url"):
            service = get_cache_service()

            assert service is not None
            assert isinstance(service, RedisCacheService)


class TestCacheIntegration:
    """Integration tests for cache operations"""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client"""
        with patch("app.infrastructure.cache.redis_cache.redis.from_url") as mock:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def cache_service(self, mock_redis):
        """Create a cache service instance"""
        service = RedisCacheService()
        service.redis_client = mock_redis
        return service

    def test_cache_workflow_movie(self, cache_service):
        """Test complete cache workflow for a movie"""
        movie_data = {"id": 1, "title": "Test Movie", "year": 2023}

        # Set cache
        cache_service.redis_client.setex.return_value = True
        set_result = cache_service.set("movie:1", movie_data, ttl=86400)
        assert set_result is True

        # Get cache
        cache_service.redis_client.get.return_value = json.dumps(movie_data)
        get_result = cache_service.get("movie:1")
        assert get_result == movie_data

        # Delete cache
        cache_service.redis_client.delete.return_value = 1
        delete_result = cache_service.delete("movie:1")
        assert delete_result is True

    def test_cache_workflow_list(self, cache_service):
        """Test complete cache workflow for a list"""
        list_data = {
            "items": [{"id": 1, "title": "Movie 1"}],
            "total": 1,
            "limit": 10,
            "offset": 0,
        }

        # Set cache
        cache_service.redis_client.setex.return_value = True
        set_result = cache_service.set("movies:list:10:0", list_data, ttl=1800)
        assert set_result is True

        # Get cache
        cache_service.redis_client.get.return_value = json.dumps(list_data)
        get_result = cache_service.get("movies:list:10:0")
        assert get_result == list_data

    def test_cache_invalidation_workflow(self, cache_service):
        """Test cache invalidation workflow"""
        cache_service.redis_client.keys.return_value = [
            "movie:1",
            "movies:list:10:0",
            "movies:list:10:10",
        ]
        cache_service.redis_client.delete.return_value = 3

        # Invalidate movie
        cache_service.invalidate_movie(1)

        # Verify delete was called
        assert cache_service.redis_client.delete.called
