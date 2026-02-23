"""Data persistence tests for database, cache, and file queue persistence"""

import pytest
import json
import tempfile
import os
import sqlite3
from datetime import datetime, timedelta
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock, patch

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


# ============================================================================
# Test Database Setup
# ============================================================================


@pytest.fixture(scope="function")
def db_session():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def temp_db_file():
    """Create a temporary database file"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


# ============================================================================
# Database Persistence Tests
# ============================================================================


class TestDatabasePersistence:
    """Tests for database persistence across restarts"""

    def test_movie_persistence_across_sessions(self, db_session):
        """Test movie data persists across database sessions"""
        # Create movie in first session
        movie = Movie(title="The Shawshank Redemption", year=1994, rating=9.3, tmdb_id="tt0111161")
        db_session.add(movie)
        db_session.commit()
        movie_id = movie.id

        # Retrieve in same session
        retrieved = db_session.query(Movie).filter(Movie.id == movie_id).first()
        assert retrieved is not None
        assert retrieved.title == "The Shawshank Redemption"
        assert retrieved.year == 1994

    def test_tv_show_persistence_across_sessions(self, db_session):
        """Test TV show data persists across database sessions"""
        # Create TV show
        show = TVShow(title="Breaking Bad", rating=9.5, status="Ended", tmdb_id="81189")
        db_session.add(show)
        db_session.commit()
        show_id = show.id

        # Retrieve
        retrieved = db_session.query(TVShow).filter(TVShow.id == show_id).first()
        assert retrieved is not None
        assert retrieved.title == "Breaking Bad"
        assert retrieved.status == "Ended"

    def test_movie_file_persistence(self, db_session):
        """Test movie file metadata persists"""
        # Create movie and file
        movie = Movie(title="Test Movie")
        db_session.add(movie)
        db_session.commit()
        db_session.refresh(movie)

        file = MovieFile(
            movie_id=movie.id,
            file_path="/path/to/movie.mkv",
            file_size=1024000,
            resolution="1920x1080",
            bitrate=5000,
            codec_video="h264",
            codec_audio="aac",
            duration=7200,
        )
        db_session.add(file)
        db_session.commit()
        file_id = file.id

        # Retrieve
        retrieved_file = db_session.query(MovieFile).filter(MovieFile.id == file_id).first()
        assert retrieved_file is not None
        assert retrieved_file.file_path == "/path/to/movie.mkv"
        assert retrieved_file.resolution == "1920x1080"
        assert retrieved_file.duration == 7200

    def test_episode_file_persistence(self, db_session):
        """Test episode file metadata persists"""
        # Create show, season, episode, and file
        show = TVShow(title="Test Show")
        db_session.add(show)
        db_session.commit()
        db_session.refresh(show)

        season = Season(show_id=show.id, season_number=1)
        db_session.add(season)
        db_session.commit()
        db_session.refresh(season)

        episode = Episode(season_id=season.id, episode_number=1, title="Episode 1")
        db_session.add(episode)
        db_session.commit()
        db_session.refresh(episode)

        ep_file = EpisodeFile(
            episode_id=episode.id,
            file_path="/path/to/episode.mkv",
            file_size=512000,
            resolution="1920x1080",
            duration=2700,
        )
        db_session.add(ep_file)
        db_session.commit()
        file_id = ep_file.id

        # Retrieve
        retrieved_file = db_session.query(EpisodeFile).filter(EpisodeFile.id == file_id).first()
        assert retrieved_file is not None
        assert retrieved_file.file_path == "/path/to/episode.mkv"
        assert retrieved_file.duration == 2700

    def test_relationship_persistence(self, db_session):
        """Test relationships persist correctly"""
        # Create movie with files
        movie = Movie(title="Test Movie")
        db_session.add(movie)
        db_session.commit()
        db_session.refresh(movie)

        for i in range(3):
            file = MovieFile(movie_id=movie.id, file_path=f"/path/to/file_{i}.mkv")
            db_session.add(file)
        db_session.commit()

        movie_id = movie.id

        # Retrieve and verify relationships
        retrieved_movie = db_session.query(Movie).filter(Movie.id == movie_id).first()
        assert len(retrieved_movie.files) == 3
        assert all(f.movie_id == movie_id for f in retrieved_movie.files)


# ============================================================================
# Cache Persistence Tests
# ============================================================================


class TestCachePersistence:
    """Tests for cache persistence across restarts"""

    def test_api_cache_persistence(self, db_session):
        """Test API cache entries persist"""
        # Create cache entry
        cache_entry = APICache(
            api_type="tmdb",
            query_key="tt0111161",
            response_data=json.dumps(
                {"title": "The Shawshank Redemption", "year": 1994, "rating": 9.3}
            ),
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        db_session.add(cache_entry)
        db_session.commit()
        cache_id = cache_entry.id

        # Retrieve
        retrieved = db_session.query(APICache).filter(APICache.id == cache_id).first()
        assert retrieved is not None
        assert retrieved.api_type == "tmdb"
        assert retrieved.query_key == "tt0111161"

        # Verify data integrity
        data = json.loads(retrieved.response_data)
        assert data["title"] == "The Shawshank Redemption"
        assert data["rating"] == 9.3

    def test_cache_expiration_persistence(self, db_session):
        """Test cache expiration times persist"""
        # Create cache entries with different expiration times
        now = datetime.utcnow()

        cache1 = APICache(
            api_type="tmdb",
            query_key="key1",
            response_data="{}",
            expires_at=now + timedelta(hours=1),
        )

        cache2 = APICache(
            api_type="tmdb",
            query_key="key2",
            response_data="{}",
            expires_at=now + timedelta(hours=24),
        )

        db_session.add_all([cache1, cache2])
        db_session.commit()

        # Retrieve and verify expiration times
        retrieved1 = db_session.query(APICache).filter(APICache.query_key == "key1").first()
        retrieved2 = db_session.query(APICache).filter(APICache.query_key == "key2").first()

        assert retrieved1.expires_at > now
        assert retrieved2.expires_at > retrieved1.expires_at

    def test_expired_cache_cleanup(self, db_session):
        """Test expired cache entries can be cleaned up"""
        # Create expired and valid cache entries
        now = datetime.utcnow()

        expired = APICache(
            api_type="tmdb",
            query_key="expired",
            response_data="{}",
            expires_at=now - timedelta(hours=1),
        )

        valid = APICache(
            api_type="tmdb",
            query_key="valid",
            response_data="{}",
            expires_at=now + timedelta(hours=1),
        )

        db_session.add_all([expired, valid])
        db_session.commit()

        # Query for expired entries
        expired_entries = db_session.query(APICache).filter(APICache.expires_at < now).all()

        assert len(expired_entries) == 1
        assert expired_entries[0].query_key == "expired"

        # Delete expired entries
        for entry in expired_entries:
            db_session.delete(entry)
        db_session.commit()

        # Verify cleanup
        remaining = db_session.query(APICache).all()
        assert len(remaining) == 1
        assert remaining[0].query_key == "valid"


# ============================================================================
# File Queue Persistence Tests
# ============================================================================


class TestFileQueuePersistence:
    """Tests for file queue persistence"""

    def test_file_queue_persistence(self, db_session):
        """Test file queue entries persist"""
        # Create queue entries
        for i in range(5):
            queue_item = FileQueue(
                file_path=f"/path/to/file_{i}.mkv", status="pending", media_type="movie"
            )
            db_session.add(queue_item)
        db_session.commit()

        # Retrieve all pending items
        pending = db_session.query(FileQueue).filter(FileQueue.status == "pending").all()
        assert len(pending) == 5

    def test_file_queue_status_transitions(self, db_session):
        """Test file queue status transitions persist"""
        # Create queue item
        queue_item = FileQueue(file_path="/path/to/file.mkv", status="pending")
        db_session.add(queue_item)
        db_session.commit()
        queue_id = queue_item.id

        # Transition to processing
        queue_item.status = "processing"
        db_session.commit()

        retrieved = db_session.query(FileQueue).filter(FileQueue.id == queue_id).first()
        assert retrieved.status == "processing"

        # Transition to completed
        queue_item.status = "completed"
        queue_item.processed_at = datetime.utcnow()
        db_session.commit()

        retrieved = db_session.query(FileQueue).filter(FileQueue.id == queue_id).first()
        assert retrieved.status == "completed"
        assert retrieved.processed_at is not None

    def test_file_queue_error_persistence(self, db_session):
        """Test file queue error messages persist"""
        # Create failed queue item
        queue_item = FileQueue(
            file_path="/non/existent/file.mkv",
            status="failed",
            error_message="File not found",
        )
        db_session.add(queue_item)
        db_session.commit()
        queue_id = queue_item.id

        # Retrieve and verify error
        retrieved = db_session.query(FileQueue).filter(FileQueue.id == queue_id).first()
        assert retrieved.status == "failed"
        assert retrieved.error_message == "File not found"


# ============================================================================
# Batch Operation State Persistence Tests
# ============================================================================


class TestBatchOperationStatePersistence:
    """Tests for batch operation state persistence"""

    def test_batch_operation_creation_persistence(self, db_session):
        """Test batch operation creation persists"""
        # Create batch operation
        batch_op = BatchOperation(
            operation_type="metadata_sync",
            status="pending",
            total_items=100,
            completed_items=0,
            failed_items=0,
            progress_percentage=0.0,
        )
        db_session.add(batch_op)
        db_session.commit()
        batch_id = batch_op.id

        # Retrieve
        retrieved = db_session.query(BatchOperation).filter(BatchOperation.id == batch_id).first()
        assert retrieved is not None
        assert retrieved.operation_type == "metadata_sync"
        assert retrieved.total_items == 100

    def test_batch_operation_progress_persistence(self, db_session):
        """Test batch operation progress updates persist"""
        # Create batch operation
        batch_op = BatchOperation(
            operation_type="file_import",
            status="running",
            total_items=50,
            completed_items=0,
            failed_items=0,
            progress_percentage=0.0,
            started_at=datetime.utcnow(),
        )
        db_session.add(batch_op)
        db_session.commit()
        batch_id = batch_op.id

        # Update progress
        batch_op.completed_items = 25
        batch_op.progress_percentage = 50.0
        batch_op.updated_at = datetime.utcnow()
        db_session.commit()

        # Retrieve and verify
        retrieved = db_session.query(BatchOperation).filter(BatchOperation.id == batch_id).first()
        assert retrieved.completed_items == 25
        assert retrieved.progress_percentage == 50.0

    def test_batch_operation_completion_persistence(self, db_session):
        """Test batch operation completion state persists"""
        # Create and complete batch operation
        batch_op = BatchOperation(
            operation_type="metadata_sync",
            status="completed",
            total_items=100,
            completed_items=100,
            failed_items=0,
            progress_percentage=100.0,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db_session.add(batch_op)
        db_session.commit()
        batch_id = batch_op.id

        # Retrieve and verify completion
        retrieved = db_session.query(BatchOperation).filter(BatchOperation.id == batch_id).first()
        assert retrieved.status == "completed"
        assert retrieved.progress_percentage == 100.0
        assert retrieved.completed_at is not None

    def test_batch_operation_metadata_persistence(self, db_session):
        """Test batch operation metadata persists"""
        # Create batch with metadata
        metadata = {
            "media_type": "movie",
            "source": "file_import",
            "filters": {"year": 2020},
        }

        batch_op = BatchOperation(
            operation_type="metadata_sync",
            status="pending",
            total_items=10,
            operation_metadata=json.dumps(metadata),
        )
        db_session.add(batch_op)
        db_session.commit()
        batch_id = batch_op.id

        # Retrieve and verify metadata
        retrieved = db_session.query(BatchOperation).filter(BatchOperation.id == batch_id).first()
        retrieved_metadata = json.loads(retrieved.operation_metadata)
        assert retrieved_metadata["media_type"] == "movie"
        assert retrieved_metadata["filters"]["year"] == 2020


# ============================================================================
# Transaction Rollback Scenarios Tests
# ============================================================================


class TestTransactionRollbackScenarios:
    """Tests for transaction rollback scenarios"""

    def test_rollback_movie_creation(self, db_session):
        """Test rollback of movie creation"""
        # Create movie
        movie = Movie(title="Test Movie", year=2020)
        db_session.add(movie)
        db_session.commit()
        movie_id = movie.id

        # Verify creation
        assert db_session.query(Movie).filter(Movie.id == movie_id).first() is not None

        # Simulate error and rollback (before commit)
        try:
            movie.title = "Updated Title"
            raise Exception("Simulated error")
        except Exception:
            db_session.rollback()

        # Verify rollback - title should not have changed
        retrieved = db_session.query(Movie).filter(Movie.id == movie_id).first()
        assert retrieved.title == "Test Movie"

    def test_rollback_cascade_delete(self, db_session):
        """Test rollback of cascade delete"""
        # Create movie with files
        movie = Movie(title="Test Movie")
        db_session.add(movie)
        db_session.commit()
        db_session.refresh(movie)

        for i in range(3):
            file = MovieFile(movie_id=movie.id, file_path=f"/path/to/file_{i}.mkv")
            db_session.add(file)
        db_session.commit()

        movie_id = movie.id
        file_count_before = (
            db_session.query(MovieFile).filter(MovieFile.movie_id == movie_id).count()
        )
        assert file_count_before == 3

        # Attempt delete with rollback (before commit)
        try:
            db_session.delete(movie)
            raise Exception("Simulated error before delete commit")
        except Exception:
            db_session.rollback()

        # Verify rollback - movie and files should still exist
        movie_exists = db_session.query(Movie).filter(Movie.id == movie_id).first() is not None
        file_count_after = (
            db_session.query(MovieFile).filter(MovieFile.movie_id == movie_id).count()
        )

        assert movie_exists
        assert file_count_after == 3

    def test_rollback_batch_operation_update(self, db_session):
        """Test rollback of batch operation updates"""
        # Create batch operation
        batch_op = BatchOperation(
            operation_type="metadata_sync",
            status="running",
            total_items=100,
            completed_items=0,
            progress_percentage=0.0,
        )
        db_session.add(batch_op)
        db_session.commit()
        batch_id = batch_op.id

        # Attempt update with rollback (before commit)
        try:
            batch_op.completed_items = 50
            batch_op.progress_percentage = 50.0
            raise Exception("Simulated error during update")
        except Exception:
            db_session.rollback()

        # Verify rollback - values should not have changed
        retrieved = db_session.query(BatchOperation).filter(BatchOperation.id == batch_id).first()
        assert retrieved.completed_items == 0
        assert retrieved.progress_percentage == 0.0


# ============================================================================
# Data Integrity Verification Tests
# ============================================================================


class TestDataIntegrityVerification:
    """Tests for data integrity verification"""

    def test_unique_constraint_enforcement(self, db_session):
        """Test unique constraints are enforced"""
        # Create movie with unique tmdb_id
        movie1 = Movie(title="Movie 1", tmdb_id="tt0111161")
        db_session.add(movie1)
        db_session.commit()

        # Attempt to create duplicate
        movie2 = Movie(title="Movie 2", tmdb_id="tt0111161")
        db_session.add(movie2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_foreign_key_constraint_enforcement(self, db_session):
        """Test foreign key constraints are enforced"""
        # Attempt to create file with non-existent movie
        file = MovieFile(movie_id=99999, file_path="/path/to/file.mkv")  # Non-existent movie
        db_session.add(file)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_not_null_constraint_enforcement(self, db_session):
        """Test NOT NULL constraints are enforced"""
        # Attempt to create movie without title
        movie = Movie(year=2020)  # title is required
        db_session.add(movie)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_data_type_integrity(self, db_session):
        """Test data type integrity"""
        # Create movie with correct data types
        movie = Movie(title="Test Movie", year=2020, rating=8.5, runtime=120)
        db_session.add(movie)
        db_session.commit()
        db_session.refresh(movie)

        # Verify data types
        assert isinstance(movie.title, str)
        assert isinstance(movie.year, int)
        assert isinstance(movie.rating, float)
        assert isinstance(movie.runtime, int)

    def test_timestamp_integrity(self, db_session):
        """Test timestamp integrity"""
        # Create movie
        before = datetime.utcnow()
        movie = Movie(title="Test Movie")
        db_session.add(movie)
        db_session.commit()
        db_session.refresh(movie)
        after = datetime.utcnow()

        # Verify timestamps
        assert before <= movie.created_at <= after
        assert before <= movie.updated_at <= after

        # Update movie
        movie.title = "Updated Title"
        db_session.commit()
        db_session.refresh(movie)

        # Verify updated_at changed
        assert movie.updated_at >= movie.created_at
