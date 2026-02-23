"""Unit tests for CacheService"""

import pytest
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models import APICache
from app.services_impl import CacheService


# Create test database
TEST_DATABASE_URL = "sqlite:///./test_cache.db"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


class TestCacheServiceKeyGeneration:
    """Test cache key generation"""

    def test_generate_cache_key_basic(self):
        """Test basic cache key generation"""
        key = CacheService.generate_cache_key("tmdb", "search", {"title": "Inception"})
        assert key == "tmdb:search:title=Inception"

    def test_generate_cache_key_multiple_params(self):
        """Test cache key generation with multiple parameters"""
        key = CacheService.generate_cache_key(
            "tmdb", "search", {"title": "Inception", "year": 2010}
        )
        # Parameters should be sorted
        assert "title=Inception" in key
        assert "year=2010" in key
        assert key.startswith("tmdb:search:")

    def test_generate_cache_key_generic(self):
        """Test cache key generation for generic type"""
        key = CacheService.generate_cache_key("generic", "series", {"tmdb_id": "1396"})
        assert key == "generic:series:tmdb_id=1396"


class TestCacheServiceSetGet:
    """Test cache set and get operations"""

    def test_set_and_get_cache(self, db):
        """Test setting and retrieving cache"""
        cache_key = "test:key:1"
        test_data = {"title": "Test Movie", "year": 2020}

        # Set cache
        result = CacheService.set_cache(db, cache_key, test_data, api_type="tmdb", ttl_seconds=3600)
        assert result is True

        # Get cache
        retrieved = CacheService.get_cache(db, cache_key)
        assert retrieved == test_data

    def test_get_nonexistent_cache(self, db):
        """Test getting non-existent cache returns None"""
        result = CacheService.get_cache(db, "nonexistent:key")
        assert result is None

    def test_get_expired_cache(self, db):
        """Test that expired cache is not returned"""
        cache_key = "test:expired:key"
        test_data = {"title": "Expired Movie"}

        # Set cache with negative TTL (already expired)
        cache_entry = APICache(
            api_type="tmdb",
            query_key=cache_key,
            response_data=json.dumps(test_data),
            expires_at=datetime.utcnow() - timedelta(seconds=1),
        )
        db.add(cache_entry)
        db.commit()

        # Should not retrieve expired cache
        result = CacheService.get_cache(db, cache_key)
        assert result is None

    def test_set_cache_updates_existing(self, db):
        """Test that set_cache updates existing entries"""
        cache_key = "test:update:key"
        old_data = {"title": "Old Title"}
        new_data = {"title": "New Title"}

        # Set initial cache
        CacheService.set_cache(db, cache_key, old_data, api_type="tmdb")

        # Update cache
        CacheService.set_cache(db, cache_key, new_data, api_type="tmdb")

        # Verify update
        retrieved = CacheService.get_cache(db, cache_key)
        assert retrieved == new_data

        # Verify only one entry exists
        count = db.query(APICache).filter(APICache.query_key == cache_key).count()
        assert count == 1


class TestCacheServiceDelete:
    """Test cache deletion operations"""

    def test_delete_cache(self, db):
        """Test deleting a cache entry"""
        cache_key = "test:delete:key"
        test_data = {"title": "Delete Me"}

        # Set cache
        CacheService.set_cache(db, cache_key, test_data, api_type="tmdb")

        # Verify it exists
        assert CacheService.get_cache(db, cache_key) is not None

        # Delete cache
        result = CacheService.delete_cache(db, cache_key)
        assert result is True

        # Verify it's deleted
        assert CacheService.get_cache(db, cache_key) is None

    def test_delete_nonexistent_cache(self, db):
        """Test deleting non-existent cache returns False"""
        result = CacheService.delete_cache(db, "nonexistent:key")
        assert result is False

    def test_bulk_delete_cache(self, db):
        """Test bulk deletion of cache entries"""
        keys = ["test:bulk:1", "test:bulk:2", "test:bulk:3"]
        test_data = {"title": "Test"}

        # Set multiple cache entries
        for key in keys:
            CacheService.set_cache(db, key, test_data, api_type="tmdb")

        # Verify all exist
        for key in keys:
            assert CacheService.get_cache(db, key) is not None

        # Bulk delete
        deleted_count = CacheService.bulk_delete_cache(db, keys)
        assert deleted_count == 3

        # Verify all are deleted
        for key in keys:
            assert CacheService.get_cache(db, key) is None


class TestCacheServiceExpiration:
    """Test cache expiration handling"""

    def test_clear_expired_cache(self, db):
        """Test clearing expired cache entries"""
        # Create expired entry
        expired_key = "test:expired:1"
        expired_data = {"title": "Expired"}
        expired_entry = APICache(
            api_type="tmdb",
            query_key=expired_key,
            response_data=json.dumps(expired_data),
            expires_at=datetime.utcnow() - timedelta(seconds=1),
        )
        db.add(expired_entry)

        # Create active entry
        active_key = "test:active:1"
        active_data = {"title": "Active"}
        CacheService.set_cache(db, active_key, active_data, api_type="tmdb", ttl_seconds=3600)

        db.commit()

        # Clear expired
        deleted_count = CacheService.clear_expired_cache(db)
        assert deleted_count == 1

        # Verify expired is gone
        assert CacheService.get_cache(db, expired_key) is None

        # Verify active still exists
        assert CacheService.get_cache(db, active_key) is not None


class TestCacheServiceInvalidation:
    """Test cache invalidation operations"""

    def test_invalidate_by_type(self, db):
        """Test invalidating cache by API type"""
        # Create OMDB cache entries
        CacheService.set_cache(db, "tmdb:key:1", {"data": "omdb1"}, api_type="tmdb")
        CacheService.set_cache(db, "tmdb:key:2", {"data": "omdb2"}, api_type="tmdb")

        # Create TVDB cache entries
        CacheService.set_cache(db, "generic:key:1", {"data": "tvdb1"}, api_type="generic")

        # Invalidate OMDB
        deleted_count = CacheService.invalidate_by_type(db, "tmdb")
        assert deleted_count == 2

        # Verify OMDB entries are gone
        assert CacheService.get_cache(db, "tmdb:key:1") is None
        assert CacheService.get_cache(db, "tmdb:key:2") is None

        # Verify TVDB entry still exists
        assert CacheService.get_cache(db, "generic:key:1") is not None

    def test_invalidate_by_pattern(self, db):
        """Test invalidating cache by key pattern"""
        # Create cache entries with different patterns
        CacheService.set_cache(db, "tmdb:search:inception", {"data": "1"}, api_type="tmdb")
        CacheService.set_cache(db, "tmdb:search:matrix", {"data": "2"}, api_type="tmdb")
        CacheService.set_cache(db, "tmdb:details:tt0111161", {"data": "3"}, api_type="tmdb")

        # Invalidate search pattern
        deleted_count = CacheService.invalidate_by_pattern(db, "tmdb:search:*")
        assert deleted_count == 2

        # Verify search entries are gone
        assert CacheService.get_cache(db, "tmdb:search:inception") is None
        assert CacheService.get_cache(db, "tmdb:search:matrix") is None

        # Verify details entry still exists
        assert CacheService.get_cache(db, "tmdb:details:tt0111161") is not None


class TestCacheServiceStatistics:
    """Test cache statistics tracking"""

    def test_get_cache_stats_empty(self, db):
        """Test cache stats with empty cache"""
        stats = CacheService.get_cache_stats(db)

        assert stats["total_entries"] == 0
        assert stats["active_entries"] == 0
        assert stats["expired_entries"] == 0
        assert stats["total_size_bytes"] == 0
        assert stats["by_api_type"] == {}

    def test_get_cache_stats_with_entries(self, db):
        """Test cache stats with multiple entries"""
        # Create entries
        CacheService.set_cache(db, "tmdb:key:1", {"data": "test1"}, api_type="tmdb")
        CacheService.set_cache(db, "tmdb:key:2", {"data": "test2"}, api_type="tmdb")
        CacheService.set_cache(db, "generic:key:1", {"data": "test3"}, api_type="generic")

        stats = CacheService.get_cache_stats(db)

        assert stats["total_entries"] == 3
        assert stats["active_entries"] == 3
        assert stats["expired_entries"] == 0
        assert stats["by_api_type"]["tmdb"] == 2
        assert stats["by_api_type"]["generic"] == 1
        assert stats["total_size_bytes"] > 0

    def test_get_cache_stats_with_expired(self, db):
        """Test cache stats includes expired entries"""
        # Create active entry
        CacheService.set_cache(db, "tmdb:key:1", {"data": "active"}, api_type="tmdb")

        # Create expired entry
        expired_entry = APICache(
            api_type="tmdb",
            query_key="tmdb:key:2",
            response_data=json.dumps({"data": "expired"}),
            expires_at=datetime.utcnow() - timedelta(seconds=1),
        )
        db.add(expired_entry)
        db.commit()

        stats = CacheService.get_cache_stats(db)

        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 1
        assert stats["expired_entries"] == 1


class TestCacheServiceBulkOperations:
    """Test bulk cache operations"""

    def test_clear_all_cache(self, db):
        """Test clearing all cache entries"""
        # Create multiple entries
        for i in range(5):
            CacheService.set_cache(db, f"test:key:{i}", {"data": f"test{i}"}, api_type="tmdb")

        # Verify entries exist
        stats = CacheService.get_cache_stats(db)
        assert stats["total_entries"] == 5

        # Clear all
        deleted_count = CacheService.clear_all_cache(db)
        assert deleted_count == 5

        # Verify all are deleted
        stats = CacheService.get_cache_stats(db)
        assert stats["total_entries"] == 0

    def test_get_cache_by_type(self, db):
        """Test retrieving cache entries by type"""
        # Create OMDB entries
        for i in range(3):
            CacheService.set_cache(db, f"tmdb:key:{i}", {"data": f"omdb{i}"}, api_type="tmdb")

        # Create TVDB entries
        for i in range(2):
            CacheService.set_cache(db, f"generic:key:{i}", {"data": f"tvdb{i}"}, api_type="generic")

        # Get OMDB entries
        entries, total = CacheService.get_cache_by_type(db, "tmdb")
        assert total == 3
        assert len(entries) == 3

        # Get TVDB entries
        entries, total = CacheService.get_cache_by_type(db, "generic")
        assert total == 2
        assert len(entries) == 2

    def test_get_cache_by_type_pagination(self, db):
        """Test pagination when retrieving cache by type"""
        # Create 10 entries
        for i in range(10):
            CacheService.set_cache(db, f"tmdb:key:{i}", {"data": f"omdb{i}"}, api_type="tmdb")

        # Get first page
        entries, total = CacheService.get_cache_by_type(db, "tmdb", limit=5, offset=0)
        assert total == 10
        assert len(entries) == 5

        # Get second page
        entries, total = CacheService.get_cache_by_type(db, "tmdb", limit=5, offset=5)
        assert total == 10
        assert len(entries) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
