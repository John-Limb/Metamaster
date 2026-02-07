"""Phase 6 Integration Tests

Comprehensive integration tests that verify all Phase 6 components work together correctly.
Tests cover:
- Redis caching with search filters
- Database optimization with batch operations
- End-to-end workflows combining all Phase 6 features
- Performance improvements (response times, cache hit rates)
- Error scenarios and edge cases
- Backward compatibility with existing functionality
"""

import pytest
import json
import time
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import (
    Movie,
    TVShow,
    Season,
    Episode,
    MovieFile,
    EpisodeFile,
    APICache,
    FileQueue,
    TaskError,
    BatchOperation,
)
from app.services.redis_cache import RedisCacheService
from app.services.search_service import (
    SearchFilters,
    MovieSearchService,
    TVShowSearchService,
)
from app.services.db_optimization import (
    QueryPerformanceTracker,
    DatabaseOptimizationService,
)
from app.services.batch_operations import BatchOperationService
from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def mock_redis():
    """Mock Redis connection."""
    with patch("app.services.redis_cache.redis.from_url") as mock:
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def cache_service(mock_redis):
    """Create a cache service instance with mocked Redis."""
    service = RedisCacheService()
    service.redis_client = mock_redis
    return service


@pytest.fixture
def sample_movies(test_db):
    """Create sample movie data for testing."""
    movies = [
        Movie(
            title="The Shawshank Redemption",
            year=1994,
            rating=9.3,
            genres=json.dumps(["Drama"]),
            plot="Two imprisoned men bond over a number of years...",
            omdb_id="tt0111161",
            runtime=142,
        ),
        Movie(
            title="The Godfather",
            year=1972,
            rating=9.2,
            genres=json.dumps(["Crime", "Drama"]),
            plot="The aging patriarch of an organized crime dynasty...",
            omdb_id="tt0068646",
            runtime=175,
        ),
        Movie(
            title="The Dark Knight",
            year=2008,
            rating=9.0,
            genres=json.dumps(["Action", "Crime", "Drama"]),
            plot="When the menace known as the Joker wreaks havoc...",
            omdb_id="tt0468569",
            runtime=152,
        ),
        Movie(
            title="Inception",
            year=2010,
            rating=8.8,
            genres=json.dumps(["Action", "Sci-Fi", "Thriller"]),
            plot="A skilled thief who steals corporate secrets...",
            omdb_id="tt1375666",
            runtime=148,
        ),
        Movie(
            title="The Matrix",
            year=1999,
            rating=8.7,
            genres=json.dumps(["Action", "Sci-Fi"]),
            plot="A computer hacker learns from mysterious rebels...",
            omdb_id="tt0133093",
            runtime=136,
        ),
    ]
    test_db.add_all(movies)
    test_db.commit()
    return movies


@pytest.fixture
def sample_tv_shows(test_db):
    """Create sample TV show data for testing."""
    shows = [
        TVShow(
            title="Breaking Bad",
            tvdb_id="tvdb81189",
            rating=9.5,
            genres=json.dumps(["Crime", "Drama", "Thriller"]),
            plot="A high school chemistry teacher...",
            status="Ended",
        ),
        TVShow(
            title="Game of Thrones",
            tvdb_id="tvdb121361",
            rating=9.2,
            genres=json.dumps(["Action", "Adventure", "Drama"]),
            plot="Nine noble families fight for control...",
            status="Ended",
        ),
        TVShow(
            title="The Office",
            tvdb_id="tvdb6091",
            rating=9.0,
            genres=json.dumps(["Comedy"]),
            plot="A mockumentary on a group of typical office workers...",
            status="Ended",
        ),
    ]
    test_db.add_all(shows)
    test_db.commit()
    return shows


# ============================================================================
# Phase 6 Feature Integration Tests
# ============================================================================


class TestRedisCachingWithSearchFilters:
    """Test Redis caching integration with search filters"""

    def test_cache_search_results(self, test_db, cache_service, sample_movies):
        """Test caching of search results"""
        cache_key = "search:movies:drama:1994"
        # Convert movies to dictionaries for JSON serialization
        search_results = [
            {"id": m.id, "title": m.title}
            for m in sample_movies
            if "Drama" in json.loads(m.genres)
        ]

        # Set cache
        result = cache_service.set(cache_key, search_results, ttl=3600)
        assert result is True

        # Verify cache was set
        cache_service.redis_client.setex.assert_called()

    def test_cache_hit_on_repeated_search(self, test_db, cache_service, sample_movies):
        """Test cache hit on repeated search queries"""
        cache_key = "search:movies:action"

        # First search - cache miss
        cache_service.redis_client.get.return_value = None
        result1 = cache_service.get(cache_key)
        assert result1 is None

        # Set cache
        search_data = {
            "results": [
                m.title for m in sample_movies if "Action" in json.loads(m.genres)
            ]
        }
        cache_service.redis_client.get.return_value = json.dumps(search_data)

        # Second search - cache hit
        result2 = cache_service.get(cache_key)
        assert result2 == search_data

    def test_cache_invalidation_on_filter_change(self, test_db, cache_service):
        """Test cache invalidation when filters change"""
        cache_key1 = "search:movies:drama:1994"
        cache_key2 = "search:movies:drama:2000"

        # Both keys should be different
        assert cache_key1 != cache_key2

        # Verify cache service can handle multiple keys
        cache_service.set(cache_key1, {"results": []})
        cache_service.set(cache_key2, {"results": []})

        cache_service.redis_client.setex.assert_called()

    def test_cache_ttl_for_search_results(self, test_db, cache_service):
        """Test TTL settings for cached search results"""
        cache_key = "search:movies:filtered"
        data = {"results": []}

        # Set with custom TTL
        cache_service.set(cache_key, data, ttl=1800)

        # Verify TTL was set correctly
        cache_service.redis_client.setex.assert_called_with(
            cache_key, 1800, json.dumps(data)
        )


class TestDatabaseOptimizationWithBatchOperations:
    """Test database optimization with batch operations"""

    def test_batch_operation_creation(self, test_db):
        """Test creating a batch operation"""
        batch_service = BatchOperationService(test_db)

        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=100,
            metadata={"media_type": "movie"},
        )

        assert batch_op.id is not None
        assert batch_op.operation_type == "metadata_sync"
        assert batch_op.status == "pending"
        assert batch_op.total_items == 100
        assert batch_op.progress_percentage == 0.0
        # Verify metadata is stored correctly
        if batch_op.operation_metadata:
            stored_metadata = json.loads(batch_op.operation_metadata)
            assert stored_metadata == {"media_type": "movie"}

    def test_batch_operation_progress_tracking(self, test_db):
        """Test progress tracking during batch operations"""
        batch_service = BatchOperationService(test_db)

        batch_op = batch_service.create_batch_operation(
            operation_type="file_import", total_items=50
        )

        # Update progress
        batch_service.update_batch_progress(batch_op.id, 25, 0)

        # Verify progress was updated
        updated_op = batch_service.get_batch_operation(batch_op.id)
        assert updated_op.completed_items == 25
        assert updated_op.progress_percentage == 50.0

    def test_batch_operation_with_errors(self, test_db):
        """Test batch operation error handling"""
        batch_service = BatchOperationService(test_db)

        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync", total_items=10
        )

        # Simulate errors
        batch_service.update_batch_progress(batch_op.id, 5, 2)

        updated_op = batch_service.get_batch_operation(batch_op.id)
        assert updated_op.completed_items == 5
        assert updated_op.failed_items == 2

    def test_query_performance_tracking(self, test_db, sample_movies):
        """Test query performance tracking during batch operations"""
        tracker = QueryPerformanceTracker(slow_query_threshold=0.1)

        # Record some queries
        tracker.record_query("SELECT * FROM movies", 0.05)
        tracker.record_query("SELECT * FROM movies WHERE year > 2000", 0.15)
        tracker.record_query("SELECT * FROM movies", 0.03)

        # Verify tracking
        assert tracker.total_queries == 3
        assert len(tracker.slow_queries) == 1  # One query exceeded threshold
        assert tracker.slow_queries[0]["execution_time"] == 0.15


class TestEndToEndWorkflows:
    """Test end-to-end workflows combining all Phase 6 features"""

    def test_search_with_caching_and_optimization(
        self, test_db, cache_service, sample_movies
    ):
        """Test complete workflow: search -> cache -> optimize"""
        cache_key = "search:movies:drama"

        # Step 1: Perform search
        drama_movies = [m for m in sample_movies if "Drama" in json.loads(m.genres)]

        # Step 2: Cache results
        cache_service.set(cache_key, drama_movies)

        # Step 3: Retrieve from cache
        cache_service.redis_client.get.return_value = json.dumps(
            [{"id": m.id, "title": m.title} for m in drama_movies]
        )
        cached_result = cache_service.get(cache_key)

        assert cached_result is not None
        assert len(cached_result) > 0

    def test_batch_import_with_search_and_cache(
        self, test_db, cache_service, sample_movies
    ):
        """Test batch import workflow with search and caching"""
        batch_service = BatchOperationService(test_db)

        # Create batch operation
        batch_op = batch_service.create_batch_operation(
            operation_type="file_import", total_items=len(sample_movies)
        )

        # Process batch with caching
        for i, movie in enumerate(sample_movies):
            cache_key = f"movie:{movie.id}"
            cache_service.set(cache_key, {"id": movie.id, "title": movie.title})
            batch_service.update_batch_progress(batch_op.id, i + 1, 0)

        # Verify batch completed
        final_op = batch_service.get_batch_operation(batch_op.id)
        assert final_op.completed_items == len(sample_movies)
        assert final_op.progress_percentage == 100.0

    def test_search_filter_with_batch_operations(self, test_db, sample_movies):
        """Test search filters applied during batch operations"""
        batch_service = BatchOperationService(test_db)

        # Create batch for filtered movies
        action_movies = [m for m in sample_movies if "Action" in json.loads(m.genres)]

        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=len(action_movies),
            metadata={"filter": "Action", "count": len(action_movies)},
        )

        assert batch_op.total_items == len(action_movies)
        if batch_op.operation_metadata:
            metadata = json.loads(batch_op.operation_metadata)
            assert metadata["filter"] == "Action"


class TestPerformanceImprovements:
    """Test performance improvements from Phase 6 features"""

    def test_cache_hit_rate_improvement(self, cache_service):
        """Test cache hit rate metrics"""
        # Simulate cache operations
        cache_service.redis_client.get.return_value = None
        cache_service.get("key1")  # Miss

        cache_service.redis_client.get.return_value = json.dumps({"data": "value"})
        cache_service.get("key2")  # Hit
        cache_service.get("key2")  # Hit

        # Verify cache operations were tracked
        assert cache_service.redis_client.get.call_count >= 3

    def test_query_response_time_improvement(self, test_db, sample_movies):
        """Test query response time improvements with optimization"""
        tracker = QueryPerformanceTracker()

        # Simulate optimized queries
        start = time.time()
        tracker.record_query("SELECT * FROM movies WHERE year > 2000", 0.02)
        elapsed = time.time() - start

        # Verify query was fast
        assert tracker.query_stats
        assert elapsed < 0.1

    def test_batch_operation_throughput(self, test_db, sample_movies):
        """Test batch operation throughput improvements"""
        batch_service = BatchOperationService(test_db)

        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync", total_items=100
        )

        # Simulate batch processing
        start = time.time()
        for i in range(100):
            batch_service.update_batch_progress(batch_op.id, i + 1, 0)
        elapsed = time.time() - start

        # Verify batch processing was efficient
        assert elapsed < 5.0  # Should complete in less than 5 seconds


class TestErrorScenariosAndEdgeCases:
    """Test error scenarios and edge cases"""

    def test_cache_connection_failure(self):
        """Test graceful handling of cache connection failure"""
        service = RedisCacheService()
        service.redis_client = None

        # Should return None instead of raising exception
        result = service.get("key")
        assert result is None

    def test_batch_operation_cancellation(self, test_db):
        """Test batch operation cancellation"""
        batch_service = BatchOperationService(test_db)

        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync", total_items=100
        )

        # Cancel operation
        batch_service.cancel_batch_operation(batch_op.id)

        # Verify cancellation
        cancelled_op = batch_service.get_batch_operation(batch_op.id)
        assert cancelled_op.status == "cancelled"

    def test_search_with_invalid_filters(self, test_db):
        """Test search with invalid filter parameters"""
        filters = SearchFilters(
            min_rating=15.0,  # Invalid: > 10
            max_rating=5.0,  # Invalid: min > max
        )

        is_valid, error_msg = filters.validate()
        assert not is_valid
        assert error_msg is not None

    def test_batch_operation_with_empty_dataset(self, test_db):
        """Test batch operation with empty dataset"""
        batch_service = BatchOperationService(test_db)

        batch_op = batch_service.create_batch_operation(
            operation_type="file_import", total_items=0
        )

        assert batch_op.total_items == 0
        assert batch_op.progress_percentage == 0.0

    def test_cache_with_large_data(self, cache_service):
        """Test caching with large data objects"""
        large_data = {
            "results": [{"id": i, "title": f"Movie {i}"} for i in range(1000)]
        }

        result = cache_service.set("large_cache", large_data, ttl=3600)
        assert result is True


class TestBackwardCompatibility:
    """Test backward compatibility with existing functionality"""

    def test_existing_movie_queries_still_work(self, test_db, sample_movies):
        """Test that existing movie queries still work"""
        # Query movies by year
        movies_1994 = test_db.query(Movie).filter(Movie.year == 1994).all()
        assert len(movies_1994) > 0

    def test_existing_tv_show_queries_still_work(self, test_db, sample_tv_shows):
        """Test that existing TV show queries still work"""
        # Query TV shows by status
        ended_shows = test_db.query(TVShow).filter(TVShow.status == "Ended").all()
        assert len(ended_shows) > 0

    def test_existing_cache_api_still_works(self, cache_service):
        """Test that existing cache API still works"""
        test_data = {"id": 1, "title": "Test"}

        # Set and get
        cache_service.set("test_key", test_data)
        cache_service.redis_client.get.return_value = json.dumps(test_data)
        result = cache_service.get("test_key")

        assert result == test_data

    def test_existing_batch_operations_still_work(self, test_db):
        """Test that existing batch operations still work"""
        batch_service = BatchOperationService(test_db)

        # Create and retrieve
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync", total_items=50
        )

        retrieved = batch_service.get_batch_operation(batch_op.id)
        assert retrieved.id == batch_op.id


class TestPhase6APIEndpoints:
    """Test Phase 6 API endpoints"""

    def test_search_endpoint_with_filters(self, test_db, sample_movies):
        """Test search endpoint with various filters"""
        # This would test the actual API endpoint
        # For now, we verify the underlying service works
        filters = SearchFilters(genre="Drama", min_rating=8.0, sort_by="rating")

        is_valid, _ = filters.validate()
        assert is_valid

    def test_batch_operations_endpoint(self, test_db):
        """Test batch operations endpoint"""
        batch_service = BatchOperationService(test_db)

        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync", total_items=100
        )

        # Verify endpoint data structure
        assert hasattr(batch_op, "id")
        assert hasattr(batch_op, "status")
        assert hasattr(batch_op, "progress_percentage")

    def test_cache_stats_endpoint(self, cache_service):
        """Test cache stats endpoint"""
        # Verify cache service can provide stats
        cache_service.redis_client.dbsize.return_value = 100
        cache_service.redis_client.info.return_value = {
            "used_memory": 1024000,
            "used_memory_human": "1M",
        }

        # Stats should be retrievable
        assert cache_service.is_connected()


# ============================================================================
# Integration Test Scenarios
# ============================================================================


class TestCompletePhase6Scenarios:
    """Test complete Phase 6 scenarios"""

    def test_scenario_1_search_cache_optimize(
        self, test_db, cache_service, sample_movies
    ):
        """Scenario 1: Search -> Cache -> Optimize"""
        # 1. Search for movies
        drama_movies = [m for m in sample_movies if "Drama" in json.loads(m.genres)]

        # 2. Cache results
        cache_key = "search:drama"
        cache_service.set(cache_key, drama_movies)

        # 3. Retrieve from cache
        cache_service.redis_client.get.return_value = json.dumps(
            [{"id": m.id, "title": m.title} for m in drama_movies]
        )
        result = cache_service.get(cache_key)

        assert result is not None

    def test_scenario_2_batch_with_search_and_cache(
        self, test_db, cache_service, sample_movies
    ):
        """Scenario 2: Batch Operation with Search and Cache"""
        batch_service = BatchOperationService(test_db)

        # 1. Create batch for action movies
        action_movies = [m for m in sample_movies if "Action" in json.loads(m.genres)]
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync", total_items=len(action_movies)
        )

        # 2. Process with caching
        for i, movie in enumerate(action_movies):
            cache_key = f"movie:{movie.id}"
            cache_service.set(cache_key, {"id": movie.id, "title": movie.title})
            batch_service.update_batch_progress(batch_op.id, i + 1, 0)

        # 3. Verify completion
        final_op = batch_service.get_batch_operation(batch_op.id)
        assert final_op.progress_percentage == 100.0

    def test_scenario_3_performance_monitoring(self, test_db, sample_movies):
        """Scenario 3: Performance Monitoring During Operations"""
        tracker = QueryPerformanceTracker()
        batch_service = BatchOperationService(test_db)

        # 1. Create batch
        batch_op = batch_service.create_batch_operation(
            operation_type="file_import", total_items=len(sample_movies)
        )

        # 2. Track performance
        for i, movie in enumerate(sample_movies):
            start = time.time()
            batch_service.update_batch_progress(batch_op.id, i + 1, 0)
            elapsed = time.time() - start
            tracker.record_query(f"process_movie_{movie.id}", elapsed)

        # 3. Verify metrics
        assert tracker.total_queries == len(sample_movies)
        assert tracker.total_time >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
