"""Comprehensive unit tests for Pydantic schemas and validation"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas import (
    MovieCreate,
    MovieUpdate,
    MovieResponse,
    TVShowCreate,
    TVShowUpdate,
    TVShowResponse,
    SeasonResponse,
    EpisodeResponse,
    PaginatedMovieResponse,
    PaginatedTVShowResponse,
    PaginatedSeasonResponse,
    PaginatedEpisodeResponse,
    CacheStatsResponse,
    CacheEntryResponse,
    PaginatedCacheResponse,
    CacheOperationResponse,
    MetadataSyncResponse,
    TaskStatusResponse,
    TaskRetryResponse,
    TaskListItemResponse,
    TaskListResponse,
    TaskCancelResponse,
    TaskErrorResponse,
    PaginatedTaskErrorResponse,
    SearchFiltersRequest,
)


# ============================================================================
# Movie Schema Tests
# ============================================================================


class TestMovieCreateSchema:
    """Tests for MovieCreate schema"""

    def test_valid_movie_create(self):
        """Test valid movie creation"""
        movie = MovieCreate(
            title="The Matrix",
            plot="A computer hacker learns about the true nature of reality",
            year=1999,
            rating=8.7,
            runtime=136,
            genres='["Sci-Fi", "Action"]',
            tmdb_id="tt0133093",
        )
        assert movie.title == "The Matrix"
        assert movie.year == 1999
        assert movie.rating == 8.7

    def test_movie_create_minimal(self):
        """Test movie creation with minimal fields"""
        movie = MovieCreate(title="Test Movie")
        assert movie.title == "Test Movie"
        assert movie.year is None
        assert movie.rating is None

    def test_movie_create_empty_title(self):
        """Test movie creation with empty title"""
        with pytest.raises(ValidationError):
            MovieCreate(title="")

    def test_movie_create_invalid_year(self):
        """Test movie creation with invalid year"""
        with pytest.raises(ValidationError):
            MovieCreate(title="Test", year=1500)

    def test_movie_create_invalid_rating(self):
        """Test movie creation with invalid rating"""
        with pytest.raises(ValidationError):
            MovieCreate(title="Test", rating=15)

    def test_movie_create_negative_runtime(self):
        """Test movie creation with negative runtime"""
        with pytest.raises(ValidationError):
            MovieCreate(title="Test", runtime=-10)

    def test_movie_create_title_too_long(self):
        """Test movie creation with title exceeding max length"""
        with pytest.raises(ValidationError):
            MovieCreate(title="x" * 300)


class TestMovieUpdateSchema:
    """Tests for MovieUpdate schema"""

    def test_valid_movie_update(self):
        """Test valid movie update"""
        update = MovieUpdate(title="Updated Title", rating=9.0, runtime=140)
        assert update.title == "Updated Title"
        assert update.rating == 9.0

    def test_movie_update_partial(self):
        """Test partial movie update"""
        update = MovieUpdate(rating=8.5)
        assert update.rating == 8.5
        assert update.title is None

    def test_movie_update_empty(self):
        """Test empty movie update"""
        update = MovieUpdate()
        assert update.title is None
        assert update.rating is None


class TestMovieResponseSchema:
    """Tests for MovieResponse schema"""

    def test_valid_movie_response(self):
        """Test valid movie response"""
        now = datetime.utcnow()
        response = MovieResponse(
            id=1,
            title="The Matrix",
            year=1999,
            rating=8.7,
            created_at=now,
            updated_at=now,
        )
        assert response.id == 1
        assert response.title == "The Matrix"

    def test_movie_response_from_attributes(self):
        """Test movie response from ORM attributes"""

        class MockMovie:
            id = 1
            title = "Test"
            year = 2020
            rating = 8.0
            plot = "Test plot"
            runtime = 120
            genres = '["Drama"]'
            tmdb_id = "tt123"
            created_at = datetime.utcnow()
            updated_at = datetime.utcnow()

        response = MovieResponse.model_validate(MockMovie())
        assert response.id == 1
        assert response.title == "Test"


# ============================================================================
# TV Show Schema Tests
# ============================================================================


class TestTVShowCreateSchema:
    """Tests for TVShowCreate schema"""

    def test_valid_tv_show_create(self):
        """Test valid TV show creation"""
        show = TVShowCreate(
            title="Breaking Bad",
            plot="A chemistry teacher turns to cooking meth",
            rating=9.5,
            genres='["Drama", "Crime"]',
            status="Ended",
            tmdb_id="81189",
        )
        assert show.title == "Breaking Bad"
        assert show.rating == 9.5

    def test_tv_show_create_minimal(self):
        """Test TV show creation with minimal fields"""
        show = TVShowCreate(title="Test Show")
        assert show.title == "Test Show"
        assert show.rating is None

    def test_tv_show_create_empty_title(self):
        """Test TV show creation with empty title"""
        with pytest.raises(ValidationError):
            TVShowCreate(title="")

    def test_tv_show_create_invalid_rating(self):
        """Test TV show creation with invalid rating"""
        with pytest.raises(ValidationError):
            TVShowCreate(title="Test", rating=11)


class TestTVShowUpdateSchema:
    """Tests for TVShowUpdate schema"""

    def test_valid_tv_show_update(self):
        """Test valid TV show update"""
        update = TVShowUpdate(title="Updated Show", status="Continuing")
        assert update.title == "Updated Show"
        assert update.status == "Continuing"

    def test_tv_show_update_partial(self):
        """Test partial TV show update"""
        update = TVShowUpdate(rating=9.0)
        assert update.rating == 9.0
        assert update.title is None


class TestTVShowResponseSchema:
    """Tests for TVShowResponse schema"""

    def test_valid_tv_show_response(self):
        """Test valid TV show response"""
        now = datetime.utcnow()
        response = TVShowResponse(
            id=1,
            title="Breaking Bad",
            rating=9.5,
            status="Ended",
            created_at=now,
            updated_at=now,
        )
        assert response.id == 1
        assert response.title == "Breaking Bad"


# ============================================================================
# Season and Episode Schema Tests
# ============================================================================


class TestSeasonResponseSchema:
    """Tests for SeasonResponse schema"""

    def test_valid_season_response(self):
        """Test valid season response"""
        now = datetime.utcnow()
        response = SeasonResponse(
            id=1, season_number=1, tmdb_id="123456", episode_count=10, created_at=now
        )
        assert response.id == 1
        assert response.season_number == 1


class TestEpisodeResponseSchema:
    """Tests for EpisodeResponse schema"""

    def test_valid_episode_response(self):
        """Test valid episode response"""
        now = datetime.utcnow()
        response = EpisodeResponse(
            id=1,
            episode_number=1,
            title="Pilot",
            plot="The beginning",
            air_date="2008-01-20",
            rating=8.5,
            tmdb_id="123456",
            created_at=now,
            updated_at=now,
        )
        assert response.id == 1
        assert response.episode_number == 1
        assert response.title == "Pilot"


# ============================================================================
# Pagination Schema Tests
# ============================================================================


class TestPaginatedMovieResponseSchema:
    """Tests for PaginatedMovieResponse schema"""

    def test_valid_paginated_response(self):
        """Test valid paginated movie response"""
        now = datetime.utcnow()
        response = PaginatedMovieResponse(
            items=[MovieResponse(id=1, title="Movie 1", created_at=now, updated_at=now)],
            total=100,
            limit=10,
            offset=0,
        )
        assert len(response.items) == 1
        assert response.total == 100
        assert response.limit == 10

    def test_paginated_response_empty_items(self):
        """Test paginated response with empty items"""
        response = PaginatedMovieResponse(items=[], total=0, limit=10, offset=0)
        assert len(response.items) == 0
        assert response.total == 0


class TestPaginatedTVShowResponseSchema:
    """Tests for PaginatedTVShowResponse schema"""

    def test_valid_paginated_tv_show_response(self):
        """Test valid paginated TV show response"""
        now = datetime.utcnow()
        response = PaginatedTVShowResponse(
            items=[TVShowResponse(id=1, title="Show 1", created_at=now, updated_at=now)],
            total=50,
            limit=10,
            offset=0,
        )
        assert len(response.items) == 1
        assert response.total == 50


# ============================================================================
# Cache Schema Tests
# ============================================================================


class TestCacheStatsResponseSchema:
    """Tests for CacheStatsResponse schema"""

    def test_valid_cache_stats(self):
        """Test valid cache statistics response"""
        response = CacheStatsResponse(
            total_entries=150,
            active_entries=120,
            expired_entries=30,
            total_size_bytes=5242880,
            total_size_mb=5.0,
            by_api_type={"tmdb": 80},
            timestamp="2026-02-07T12:00:00Z",
        )
        assert response.total_entries == 150
        assert response.active_entries == 120
        assert response.total_size_mb == 5.0


class TestCacheOperationResponseSchema:
    """Tests for CacheOperationResponse schema"""

    def test_valid_cache_operation_response(self):
        """Test valid cache operation response"""
        response = CacheOperationResponse(
            success=True, message="Cache cleared successfully", affected_entries=25
        )
        assert response.success is True
        assert response.affected_entries == 25


class TestMetadataSyncResponseSchema:
    """Tests for MetadataSyncResponse schema"""

    def test_valid_metadata_sync_response(self):
        """Test valid metadata sync response"""
        response = MetadataSyncResponse(
            success=True,
            message="Metadata synced",
            movie_id=1,
            updated_fields=["rating", "plot"],
            metadata={"rating": 8.5, "plot": "Test"},
        )
        assert response.success is True
        assert response.movie_id == 1
        assert len(response.updated_fields) == 2


# ============================================================================
# Task Monitoring Schema Tests
# ============================================================================


class TestTaskStatusResponseSchema:
    """Tests for TaskStatusResponse schema"""

    def test_valid_task_status_response(self):
        """Test valid task status response"""
        now = datetime.utcnow()
        response = TaskStatusResponse(
            task_id="abc123",
            status="success",
            result={"processed": 42},
            created_at=now,
            updated_at=now,
        )
        assert response.task_id == "abc123"
        assert response.status == "success"

    def test_task_status_response_with_error(self):
        """Test task status response with error"""
        now = datetime.utcnow()
        response = TaskStatusResponse(
            task_id="abc123",
            status="failure",
            error="Task failed",
            created_at=now,
            updated_at=now,
        )
        assert response.status == "failure"
        assert response.error == "Task failed"


class TestTaskRetryResponseSchema:
    """Tests for TaskRetryResponse schema"""

    def test_valid_task_retry_response(self):
        """Test valid task retry response"""
        response = TaskRetryResponse(
            success=True,
            message="Task retry initiated",
            original_task_id="abc123",
            new_task_id="xyz789",
        )
        assert response.success is True
        assert response.original_task_id == "abc123"


class TestTaskListResponseSchema:
    """Tests for TaskListResponse schema"""

    def test_valid_task_list_response(self):
        """Test valid task list response"""
        now = datetime.utcnow()
        response = TaskListResponse(
            items=[
                TaskListItemResponse(
                    task_id="abc123", status="success", created_at=now, updated_at=now
                )
            ],
            total=100,
            limit=50,
            offset=0,
        )
        assert len(response.items) == 1
        assert response.total == 100


class TestTaskCancelResponseSchema:
    """Tests for TaskCancelResponse schema"""

    def test_valid_task_cancel_response(self):
        """Test valid task cancel response"""
        response = TaskCancelResponse(success=True, message="Task cancelled", task_id="abc123")
        assert response.success is True
        assert response.task_id == "abc123"


# ============================================================================
# Task Error Schema Tests
# ============================================================================


class TestTaskErrorResponseSchema:
    """Tests for TaskErrorResponse schema"""

    def test_valid_task_error_response(self):
        """Test valid task error response"""
        now = datetime.utcnow()
        response = TaskErrorResponse(
            id=1,
            task_id="abc123",
            task_name="app.tasks.analyze_file",
            error_message="File not found",
            error_traceback="Traceback...",
            severity="critical",
            retry_count=3,
            created_at=now,
            resolved_at=None,
        )
        assert response.id == 1
        assert response.severity == "critical"
        assert response.retry_count == 3

    def test_task_error_response_resolved(self):
        """Test task error response with resolution"""
        now = datetime.utcnow()
        response = TaskErrorResponse(
            id=1,
            task_id="abc123",
            task_name="app.tasks.analyze_file",
            error_message="File not found",
            severity="critical",
            retry_count=0,
            created_at=now,
            resolved_at=now,
        )
        assert response.resolved_at is not None


class TestPaginatedTaskErrorResponseSchema:
    """Tests for PaginatedTaskErrorResponse schema"""

    def test_valid_paginated_task_error_response(self):
        """Test valid paginated task error response"""
        now = datetime.utcnow()
        response = PaginatedTaskErrorResponse(
            items=[
                TaskErrorResponse(
                    id=1,
                    task_id="abc123",
                    task_name="app.tasks.analyze_file",
                    error_message="Error",
                    severity="critical",
                    retry_count=0,
                    created_at=now,
                )
            ],
            total=10,
            limit=50,
            offset=0,
        )
        assert len(response.items) == 1
        assert response.total == 10


# ============================================================================
# Search Filter Schema Tests
# ============================================================================


class TestSearchFiltersRequestSchema:
    """Tests for SearchFiltersRequest schema"""

    def test_valid_search_filters(self):
        """Test valid search filters"""
        filters = SearchFiltersRequest(
            genre="Drama",
            min_rating=7.0,
            max_rating=10.0,
            year=2020,
            sort_by="rating",
            skip=0,
            limit=20,
        )
        assert filters.genre == "Drama"
        assert filters.min_rating == 7.0
        assert filters.limit == 20

    def test_search_filters_defaults(self):
        """Test search filters with defaults"""
        filters = SearchFiltersRequest()
        assert filters.sort_by == "title"
        assert filters.skip == 0
        assert filters.limit == 10

    def test_search_filters_invalid_rating(self):
        """Test search filters with invalid rating"""
        with pytest.raises(ValidationError):
            SearchFiltersRequest(min_rating=15)

    def test_search_filters_invalid_limit(self):
        """Test search filters with invalid limit"""
        with pytest.raises(ValidationError):
            SearchFiltersRequest(limit=0)

    def test_search_filters_invalid_skip(self):
        """Test search filters with negative skip"""
        with pytest.raises(ValidationError):
            SearchFiltersRequest(skip=-1)

    def test_search_filters_limit_max(self):
        """Test search filters with limit exceeding max"""
        with pytest.raises(ValidationError):
            SearchFiltersRequest(limit=200)


# ============================================================================
# Edge Cases and Boundary Tests
# ============================================================================


class TestSchemaEdgeCases:
    """Tests for schema edge cases and boundary conditions"""

    def test_movie_create_year_boundary_min(self):
        """Test movie with minimum valid year"""
        movie = MovieCreate(title="Test", year=1800)
        assert movie.year == 1800

    def test_movie_create_year_boundary_max(self):
        """Test movie with maximum valid year"""
        movie = MovieCreate(title="Test", year=2100)
        assert movie.year == 2100

    def test_movie_create_rating_boundary_min(self):
        """Test movie with minimum rating"""
        movie = MovieCreate(title="Test", rating=0.0)
        assert movie.rating == 0.0

    def test_movie_create_rating_boundary_max(self):
        """Test movie with maximum rating"""
        movie = MovieCreate(title="Test", rating=10.0)
        assert movie.rating == 10.0

    def test_tv_show_create_title_max_length(self):
        """Test TV show with maximum title length"""
        show = TVShowCreate(title="x" * 255)
        assert len(show.title) == 255

    def test_search_filters_limit_boundary_min(self):
        """Test search filters with minimum limit"""
        filters = SearchFiltersRequest(limit=1)
        assert filters.limit == 1

    def test_search_filters_limit_boundary_max(self):
        """Test search filters with maximum limit"""
        filters = SearchFiltersRequest(limit=100)
        assert filters.limit == 100

    def test_paginated_response_large_offset(self):
        """Test paginated response with large offset"""
        response = PaginatedMovieResponse(items=[], total=1000, limit=10, offset=990)
        assert response.offset == 990
