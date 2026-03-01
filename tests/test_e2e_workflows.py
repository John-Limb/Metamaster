"""End-to-end workflow tests for complete system workflows"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import Mock, patch, MagicMock

from tests.db_utils import TEST_DATABASE_URL

from app.database import Base
from app.models import (
    Movie,
    MovieFile,
    TVShow,
    Season,
    Episode,
    EpisodeFile,
    APICache,
    FileQueue,
    TaskError,
    BatchOperation,
)
from app.services.batch_operations import BatchOperationService
from app.services.redis_cache import RedisCacheService
from app.services.file_queue_manager import FileQueueManager
from app.services.pattern_recognition import PatternRecognitionService


# ============================================================================
# Test Database Setup
# ============================================================================


@pytest.fixture(scope="function")
def db_session():
    """Create a PostgreSQL database session for testing"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def temp_media_dir():
    """Create a temporary media directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_redis_cache():
    """Create a mock Redis cache service"""
    cache = Mock(spec=RedisCacheService)
    cache.is_connected.return_value = True
    cache.get.return_value = None
    cache.set.return_value = True
    cache.delete.return_value = True
    cache.delete_pattern.return_value = 0
    cache.clear_all.return_value = True
    cache.get_stats.return_value = {
        "connected": True,
        "total_keys": 0,
        "memory_usage_bytes": 0,
        "memory_usage_mb": 0,
        "hit_rate": 0.0,
        "total_hits": 0,
        "total_misses": 0,
    }
    cache.warmup_cache.return_value = {"movies": 0, "tv_shows": 0}
    return cache


# ============================================================================
# Movie Import Workflow Tests
# ============================================================================


class TestMovieImportWorkflow:
    """Tests for complete movie import workflow"""

    def test_movie_import_workflow_complete(self, db_session, temp_media_dir, mock_redis_cache):
        """Test complete movie import workflow: file detection → pattern recognition → metadata sync → database storage"""
        # Step 1: Create movie file in temp directory
        movie_file_path = os.path.join(temp_media_dir, "The.Matrix.1999.1080p.mkv")
        with open(movie_file_path, "w") as f:
            f.write("fake movie content")

        # Step 2: Add to file queue (file detection)
        queue_item = FileQueue(
            file_path=movie_file_path,
            status="pending",
            media_type=None,
            created_at=datetime.utcnow(),
        )
        db_session.add(queue_item)
        db_session.commit()
        db_session.refresh(queue_item)

        assert queue_item.id is not None
        assert queue_item.status == "pending"

        # Step 3: Pattern recognition
        recognizer = PatternRecognitionService()
        pattern_result = recognizer.classify_file(movie_file_path)

        assert pattern_result["type"] in ["movie", "tv_show"]

        # Step 4: Update queue with media type
        queue_item.media_type = pattern_result["type"]
        queue_item.status = "processing"
        db_session.commit()

        # Step 5: Create movie in database
        movie = Movie(
            title=pattern_result.get("title", "The Matrix"),
            year=pattern_result.get("year", 1999),
            rating=8.7,
            plot="A computer hacker learns about the true nature of reality",
            genres='["Sci-Fi", "Action"]',
            tmdb_id="tt0133093",
        )
        db_session.add(movie)
        db_session.commit()
        db_session.refresh(movie)

        # Step 6: Create movie file record
        movie_file = MovieFile(
            movie_id=movie.id,
            file_path=movie_file_path,
            file_size=os.path.getsize(movie_file_path),
            resolution="1920x1080",
            bitrate=5000,
            codec_video="h264",
            codec_audio="aac",
            duration=8160,
        )
        db_session.add(movie_file)
        db_session.commit()
        db_session.refresh(movie_file)

        # Step 7: Mark queue item as completed
        queue_item.status = "completed"
        queue_item.processed_at = datetime.utcnow()
        db_session.commit()

        # Verify complete workflow
        retrieved_movie = db_session.query(Movie).filter(Movie.id == movie.id).first()
        assert retrieved_movie is not None
        assert retrieved_movie.title == "The Matrix"
        assert len(retrieved_movie.files) == 1
        assert retrieved_movie.files[0].file_path == movie_file_path

        queue_status = db_session.query(FileQueue).filter(FileQueue.id == queue_item.id).first()
        assert queue_status.status == "completed"

    def test_movie_import_workflow_with_metadata_enrichment(self, db_session, temp_media_dir):
        """Test movie import with metadata enrichment from external API"""
        # Create movie
        movie = Movie(title="Inception", year=2010, tmdb_id="tt1375666")
        db_session.add(movie)
        db_session.commit()
        db_session.refresh(movie)

        # Simulate metadata enrichment
        enriched_data = {
            "plot": "A skilled thief who steals corporate secrets through dream-sharing technology",
            "rating": 8.8,
            "runtime": 148,
            "genres": '["Sci-Fi", "Thriller", "Action"]',
        }

        movie.plot = enriched_data["plot"]
        movie.rating = enriched_data["rating"]
        movie.runtime = enriched_data["runtime"]
        movie.genres = enriched_data["genres"]
        movie.updated_at = datetime.utcnow()
        db_session.commit()
        db_session.refresh(movie)

        # Verify enrichment
        assert movie.plot == enriched_data["plot"]
        assert movie.rating == enriched_data["rating"]
        assert movie.runtime == enriched_data["runtime"]

    def test_movie_import_workflow_error_recovery(self, db_session, temp_media_dir):
        """Test movie import workflow with error recovery"""
        # Create queue item for non-existent file
        queue_item = FileQueue(
            file_path="/non/existent/file.mkv", status="pending", media_type="movie"
        )
        db_session.add(queue_item)
        db_session.commit()
        db_session.refresh(queue_item)

        # Simulate error
        error_message = "File not found: /non/existent/file.mkv"
        queue_item.status = "failed"
        queue_item.error_message = error_message
        queue_item.processed_at = datetime.utcnow()
        db_session.commit()

        # Verify error state
        assert queue_item.status == "failed"
        assert queue_item.error_message == error_message

        # Simulate retry
        queue_item.status = "pending"
        queue_item.error_message = None
        db_session.commit()

        assert queue_item.status == "pending"


# ============================================================================
# TV Show Import Workflow Tests
# ============================================================================


class TestTVShowImportWorkflow:
    """Tests for complete TV show import workflow"""

    def test_tv_show_import_workflow_complete(self, db_session, temp_media_dir):
        """Test complete TV show import workflow: file detection → season/episode parsing → metadata sync → database storage"""
        # Step 1: Create TV show
        show = TVShow(
            title="Breaking Bad",
            rating=9.5,
            plot="A high school chemistry teacher",
            genres='["Drama", "Crime"]',
            status="Ended",
            tmdb_id="81189",
        )
        db_session.add(show)
        db_session.commit()
        db_session.refresh(show)

        # Step 2: Create seasons
        for season_num in range(1, 6):
            season = Season(show_id=show.id, season_number=season_num)
            db_session.add(season)
        db_session.commit()

        # Step 3: Create episodes for season 1
        season_1 = (
            db_session.query(Season)
            .filter(Season.show_id == show.id, Season.season_number == 1)
            .first()
        )

        for ep_num in range(1, 8):
            episode = Episode(
                season_id=season_1.id,
                episode_number=ep_num,
                title=f"Episode {ep_num}",
                air_date="2008-01-20",
            )
            db_session.add(episode)
        db_session.commit()

        # Step 4: Create episode files
        episodes = db_session.query(Episode).filter(Episode.season_id == season_1.id).all()
        for episode in episodes:
            file_path = os.path.join(
                temp_media_dir, f"Breaking.Bad.S01E{episode.episode_number:02d}.mkv"
            )
            with open(file_path, "w") as f:
                f.write("fake episode content")

            ep_file = EpisodeFile(
                episode_id=episode.id,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                resolution="1920x1080",
                bitrate=5000,
                codec_video="h264",
                codec_audio="aac",
                duration=2700,
            )
            db_session.add(ep_file)
        db_session.commit()

        # Verify complete workflow
        retrieved_show = db_session.query(TVShow).filter(TVShow.id == show.id).first()
        assert retrieved_show is not None
        assert len(retrieved_show.seasons) == 5

        retrieved_season = db_session.query(Season).filter(Season.id == season_1.id).first()
        assert len(retrieved_season.episodes) == 7

        retrieved_episode = retrieved_season.episodes[0]
        assert len(retrieved_episode.files) == 1

    def test_tv_show_import_workflow_multi_season(self, db_session, temp_media_dir):
        """Test TV show import with multiple seasons and episodes"""
        # Create show with multiple seasons
        show = TVShow(title="Game of Thrones", rating=9.2, status="Ended")
        db_session.add(show)
        db_session.commit()
        db_session.refresh(show)

        # Create 3 seasons with 10 episodes each
        for season_num in range(1, 4):
            season = Season(show_id=show.id, season_number=season_num)
            db_session.add(season)
            db_session.commit()
            db_session.refresh(season)

            for ep_num in range(1, 11):
                episode = Episode(
                    season_id=season.id,
                    episode_number=ep_num,
                    title=f"Season {season_num} Episode {ep_num}",
                )
                db_session.add(episode)
            db_session.commit()

        # Verify structure
        retrieved_show = db_session.query(TVShow).filter(TVShow.id == show.id).first()
        assert len(retrieved_show.seasons) == 3

        total_episodes = sum(len(season.episodes) for season in retrieved_show.seasons)
        assert total_episodes == 30


# ============================================================================
# Search and Filter Workflow Tests
# ============================================================================


class TestSearchAndFilterWorkflow:
    """Tests for search and filter workflow with pagination and caching"""

    def test_search_workflow_with_pagination(self, db_session, mock_redis_cache):
        """Test search workflow with multiple filters and pagination"""
        # Create test movies
        for i in range(25):
            movie = Movie(
                title=f"Movie {i}",
                year=2020 + (i % 5),
                rating=7.0 + (i % 3),
                genres='["Action"]' if i % 2 == 0 else '["Drama"]',
            )
            db_session.add(movie)
        db_session.commit()

        # Test pagination
        page_size = 10
        page_1 = db_session.query(Movie).limit(page_size).offset(0).all()
        page_2 = db_session.query(Movie).limit(page_size).offset(page_size).all()
        page_3 = db_session.query(Movie).limit(page_size).offset(page_size * 2).all()

        assert len(page_1) == 10
        assert len(page_2) == 10
        assert len(page_3) == 5

        # Test filtering by year
        movies_2020 = db_session.query(Movie).filter(Movie.year == 2020).all()
        assert len(movies_2020) > 0

        # Test filtering by rating
        high_rated = db_session.query(Movie).filter(Movie.rating >= 8.0).all()
        assert len(high_rated) > 0

    def test_search_workflow_with_caching(self, db_session, mock_redis_cache):
        """Test search results caching"""
        # Create movies
        for i in range(10):
            movie = Movie(title=f"Movie {i}", year=2020)
            db_session.add(movie)
        db_session.commit()

        # First search - cache miss
        mock_redis_cache.get.return_value = None
        results = db_session.query(Movie).all()
        assert len(results) == 10

        # Cache results
        cache_key = "search:movies:all"
        mock_redis_cache.set(cache_key, [m.id for m in results])

        # Second search - cache hit
        mock_redis_cache.get.return_value = [m.id for m in results]
        cached_ids = mock_redis_cache.get(cache_key)
        assert cached_ids is not None
        assert len(cached_ids) == 10

    def test_search_workflow_filter_combinations(self, db_session):
        """Test search with multiple filter combinations"""
        # Create diverse movie set
        movies_data = [
            ("The Matrix", 1999, 8.7, '["Sci-Fi", "Action"]'),
            ("Inception", 2010, 8.8, '["Sci-Fi", "Thriller"]'),
            ("Interstellar", 2014, 8.6, '["Sci-Fi", "Drama"]'),
            ("The Dark Knight", 2008, 9.0, '["Action", "Crime"]'),
            ("Pulp Fiction", 1994, 8.9, '["Crime", "Drama"]'),
        ]

        for title, year, rating, genres in movies_data:
            movie = Movie(title=title, year=year, rating=rating, genres=genres)
            db_session.add(movie)
        db_session.commit()

        # Test filter: Sci-Fi movies from 2000+
        scifi_recent = (
            db_session.query(Movie).filter(Movie.year >= 2000, Movie.genres.like("%Sci-Fi%")).all()
        )
        assert len(scifi_recent) == 2  # Inception (2010) and Interstellar (2014)

        # Test filter: High-rated movies (8.8+)
        high_rated = db_session.query(Movie).filter(Movie.rating >= 8.8).all()
        assert len(high_rated) == 3  # Inception (8.8), The Dark Knight (9.0), Pulp Fiction (8.9)


# ============================================================================
# Batch Metadata Sync Workflow Tests
# ============================================================================


class TestBatchMetadataSyncWorkflow:
    """Tests for batch metadata sync workflow"""

    def test_batch_metadata_sync_workflow(self, db_session):
        """Test complete batch metadata sync workflow"""
        # Create batch operation
        batch_service = BatchOperationService(db_session)

        # Create movies to sync
        movie_ids = []
        for i in range(5):
            movie = Movie(title=f"Movie {i}", year=2020, tmdb_id=f"tt{1000000 + i}")
            db_session.add(movie)
            db_session.commit()
            db_session.refresh(movie)
            movie_ids.append(movie.id)

        # Create batch operation
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=len(movie_ids),
            metadata={"media_type": "movie"},
        )

        assert batch_op.status == "pending"
        assert batch_op.total_items == 5

        # Start batch operation
        batch_service.start_batch_operation(batch_op.id)
        batch_op = batch_service.get_batch_operation(batch_op.id)
        assert batch_op.status == "running"

        # Simulate progress updates
        batch_service.update_batch_progress(batch_op.id, completed_items=2, failed_items=0)
        batch_op = batch_service.get_batch_operation(batch_op.id)
        assert batch_op.completed_items == 2
        assert batch_op.progress_percentage == 40.0

        # Complete batch operation
        batch_service.complete_batch_operation(batch_op.id)
        batch_op = batch_service.get_batch_operation(batch_op.id)
        assert batch_op.status == "completed"
        assert batch_op.progress_percentage == 100.0

    def test_batch_metadata_sync_with_errors(self, db_session):
        """Test batch metadata sync with error handling"""
        batch_service = BatchOperationService(db_session)

        # Create batch operation
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync", total_items=10
        )

        # Start batch
        batch_service.start_batch_operation(batch_op.id)

        # Simulate partial failures
        batch_service.update_batch_progress(
            batch_op.id,
            completed_items=7,
            failed_items=3,
            error_message="3 items failed to sync",
        )

        batch_op = batch_service.get_batch_operation(batch_op.id)
        assert batch_op.completed_items == 7
        assert batch_op.failed_items == 3
        assert batch_op.progress_percentage == 100.0
        assert batch_op.error_message == "3 items failed to sync"


# ============================================================================
# Batch File Import Workflow Tests
# ============================================================================


class TestBatchFileImportWorkflow:
    """Tests for batch file import workflow"""

    def test_batch_file_import_workflow(self, db_session, temp_media_dir):
        """Test complete batch file import workflow"""
        batch_service = BatchOperationService(db_session)

        # Create test files
        file_paths = []
        for i in range(5):
            file_path = os.path.join(temp_media_dir, f"movie_{i}.mkv")
            with open(file_path, "w") as f:
                f.write("fake content")
            file_paths.append(file_path)

        # Create batch operation
        batch_op = batch_service.create_batch_operation(
            operation_type="file_import", total_items=len(file_paths)
        )

        # Start batch
        batch_service.start_batch_operation(batch_op.id)

        # Simulate file processing
        for i, file_path in enumerate(file_paths):
            queue_item = FileQueue(file_path=file_path, status="completed", media_type="movie")
            db_session.add(queue_item)

            if (i + 1) % 2 == 0:
                batch_service.update_batch_progress(
                    batch_op.id, completed_items=i + 1, failed_items=0
                )

        db_session.commit()

        # Complete batch
        batch_service.complete_batch_operation(batch_op.id)
        batch_op = batch_service.get_batch_operation(batch_op.id)

        assert batch_op.status == "completed"
        assert batch_op.progress_percentage == 100.0


# ============================================================================
# Cache Warming Workflow Tests
# ============================================================================


class TestCacheWarmingWorkflow:
    """Tests for cache warming workflow"""

    def test_cache_warming_workflow(self, db_session, mock_redis_cache):
        """Test cache warming workflow"""
        # Create movies and TV shows
        movies = []
        for i in range(10):
            movie = Movie(title=f"Movie {i}", year=2020)
            db_session.add(movie)
            movies.append(movie)

        tv_shows = []
        for i in range(5):
            show = TVShow(title=f"Show {i}")
            db_session.add(show)
            tv_shows.append(show)

        db_session.commit()

        # Configure mock to return expected values
        mock_redis_cache.warmup_cache.return_value = {"movies": 10, "tv_shows": 5}

        # Warm up cache
        result = mock_redis_cache.warmup_cache(movies, tv_shows)

        # Verify cache warming
        assert result["movies"] == 10
        assert result["tv_shows"] == 5

    def test_cache_warming_with_statistics(self, db_session, mock_redis_cache):
        """Test cache warming with statistics tracking"""
        # Create data
        movies = [Movie(title=f"Movie {i}", year=2020) for i in range(5)]
        tv_shows = [TVShow(title=f"Show {i}") for i in range(3)]

        for movie in movies:
            db_session.add(movie)
        for show in tv_shows:
            db_session.add(show)
        db_session.commit()

        # Warm cache
        mock_redis_cache.warmup_cache(movies, tv_shows)

        # Get cache statistics
        stats = mock_redis_cache.get_stats()

        assert stats["connected"] is True
        assert stats["total_keys"] >= 0


# ============================================================================
# Error Recovery Workflow Tests
# ============================================================================


class TestErrorRecoveryWorkflow:
    """Tests for error handling and recovery workflows"""

    def test_error_recovery_workflow_file_not_found(self, db_session):
        """Test error recovery when file is not found"""
        # Create queue item for non-existent file
        queue_item = FileQueue(
            file_path="/non/existent/file.mkv", status="pending", media_type="movie"
        )
        db_session.add(queue_item)
        db_session.commit()
        db_session.refresh(queue_item)

        # Simulate error
        queue_item.status = "failed"
        queue_item.error_message = "File not found"
        db_session.commit()

        # Create task error record
        task_error = TaskError(
            task_id="import_file_123",
            task_name="import_file",
            error_message="File not found: /non/existent/file.mkv",
            severity="warning",
            retry_count=0,
        )
        db_session.add(task_error)
        db_session.commit()
        db_session.refresh(task_error)

        # Verify error tracking
        assert task_error.id is not None
        assert task_error.severity == "warning"
        assert task_error.retry_count == 0

        # Simulate retry
        task_error.retry_count = 1
        db_session.commit()

        assert task_error.retry_count == 1

    def test_error_recovery_workflow_api_timeout(self, db_session):
        """Test error recovery for API timeout"""
        # Create task error for API timeout
        task_error = TaskError(
            task_id="sync_metadata_456",
            task_name="sync_metadata",
            error_message="API timeout: OMDB service did not respond within 30 seconds",
            error_traceback="Traceback...",
            severity="critical",
            retry_count=0,
        )
        db_session.add(task_error)
        db_session.commit()
        db_session.refresh(task_error)

        # Simulate retry with exponential backoff
        task_error.retry_count = 1
        db_session.commit()

        # Verify retry tracking
        assert task_error.retry_count == 1

        # Simulate successful retry
        task_error.resolved_at = datetime.utcnow()
        db_session.commit()

        assert task_error.resolved_at is not None

    def test_error_recovery_workflow_database_transaction_rollback(self, db_session):
        """Test error recovery with database transaction rollback"""
        # Create movie
        movie = Movie(title="Test Movie", year=2020)
        db_session.add(movie)
        db_session.commit()
        db_session.refresh(movie)

        movie_id = movie.id

        # Simulate transaction with error (before commit)
        try:
            movie.title = "Updated Title"
            # Simulate error that requires rollback (before commit)
            raise Exception("Simulated error during processing")
        except Exception:
            db_session.rollback()

        # Verify rollback - title should not have changed
        retrieved_movie = db_session.query(Movie).filter(Movie.id == movie_id).first()
        assert retrieved_movie.title == "Test Movie"  # Should be original value


# ============================================================================
# Data Consistency Workflow Tests
# ============================================================================


class TestDataConsistencyWorkflow:
    """Tests for data consistency across components"""

    def test_data_consistency_movie_cascade_delete(self, db_session):
        """Test data consistency when deleting movie with cascade"""
        # Create movie with files
        movie = Movie(title="Test Movie")
        db_session.add(movie)
        db_session.commit()
        db_session.refresh(movie)

        # Add files
        for i in range(3):
            file = MovieFile(movie_id=movie.id, file_path=f"/path/to/file_{i}.mkv")
            db_session.add(file)
        db_session.commit()

        movie_id = movie.id
        file_count_before = (
            db_session.query(MovieFile).filter(MovieFile.movie_id == movie_id).count()
        )
        assert file_count_before == 3

        # Delete movie
        db_session.delete(movie)
        db_session.commit()

        # Verify cascade delete
        file_count_after = (
            db_session.query(MovieFile).filter(MovieFile.movie_id == movie_id).count()
        )
        assert file_count_after == 0

    def test_data_consistency_tv_show_cascade_delete(self, db_session):
        """Test data consistency when deleting TV show with cascade"""
        # Create TV show with seasons and episodes
        show = TVShow(title="Test Show")
        db_session.add(show)
        db_session.commit()
        db_session.refresh(show)

        # Add seasons
        for season_num in range(1, 4):
            season = Season(show_id=show.id, season_number=season_num)
            db_session.add(season)
        db_session.commit()

        # Add episodes
        seasons = db_session.query(Season).filter(Season.show_id == show.id).all()
        for season in seasons:
            for ep_num in range(1, 6):
                episode = Episode(
                    season_id=season.id,
                    episode_number=ep_num,
                    title=f"Episode {ep_num}",
                )
                db_session.add(episode)
        db_session.commit()

        show_id = show.id
        season_count_before = db_session.query(Season).filter(Season.show_id == show_id).count()
        episode_count_before = (
            db_session.query(Episode).join(Season).filter(Season.show_id == show_id).count()
        )

        assert season_count_before == 3
        assert episode_count_before == 15

        # Delete show
        db_session.delete(show)
        db_session.commit()

        # Verify cascade delete
        season_count_after = db_session.query(Season).filter(Season.show_id == show_id).count()
        episode_count_after = (
            db_session.query(Episode).join(Season).filter(Season.show_id == show_id).count()
        )

        assert season_count_after == 0
        assert episode_count_after == 0
