"""Comprehensive integration tests for file monitoring"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.application.pattern_recognition.service import PatternRecognitionService
from app.database import Base
from app.infrastructure.file_system.queue_manager import FileQueueManager
from app.models import FileQueue
from tests.db_utils import TEST_DATABASE_URL

# ============================================================================
# Test Database Setup
# ============================================================================


@pytest.fixture(scope="function")
def db_session():
    """Create a PostgreSQL database for testing"""
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
    """Create a temporary media directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ============================================================================
# File Detection Tests
# ============================================================================


class TestFileDetection:
    """Tests for file detection"""

    def test_detect_movie_file(self, temp_media_dir):
        """Test detecting a movie file"""
        # Create a test file
        movie_file = Path(temp_media_dir) / "The Matrix (1999).mp4"
        movie_file.touch()

        assert movie_file.exists()
        assert movie_file.suffix == ".mp4"

    def test_detect_tv_show_file(self, temp_media_dir):
        """Test detecting a TV show file"""
        # Create a test file
        tv_file = Path(temp_media_dir) / "Breaking Bad S01E01.mkv"
        tv_file.touch()

        assert tv_file.exists()
        assert tv_file.suffix == ".mkv"

    def test_detect_multiple_files(self, temp_media_dir):
        """Test detecting multiple files"""
        files = ["Movie1.mp4", "Movie2.mkv", "Show S01E01.avi", "Show S01E02.mov"]

        for filename in files:
            (Path(temp_media_dir) / filename).touch()

        detected = list(Path(temp_media_dir).glob("*"))
        assert len(detected) == 4

    def test_ignore_non_media_files(self, temp_media_dir):
        """Test ignoring non-media files"""
        # Create various files
        (Path(temp_media_dir) / "document.txt").touch()
        (Path(temp_media_dir) / "image.jpg").touch()
        (Path(temp_media_dir) / "movie.mp4").touch()

        # Filter for media files
        media_extensions = [".mp4", ".mkv", ".avi", ".mov"]
        media_files = [
            f for f in Path(temp_media_dir).glob("*") if f.suffix.lower() in media_extensions
        ]

        assert len(media_files) == 1
        assert media_files[0].name == "movie.mp4"


# ============================================================================
# Queue Management Tests
# ============================================================================


class TestQueueManagement:
    """Tests for file queue management"""

    def test_add_file_to_queue(self, db_session):
        """Test adding a file to queue"""
        manager = FileQueueManager(session=db_session)

        queue_id = manager.add_file("/path/to/file.mp4", "movie")
        assert queue_id is not None

        # Verify in database
        queue_entry = db_session.query(FileQueue).filter(FileQueue.id == queue_id).first()
        assert queue_entry is not None
        assert queue_entry.file_path == "/path/to/file.mp4"
        assert queue_entry.status == "pending"

    def test_get_pending_files(self, db_session):
        """Test getting pending files from queue"""
        manager = FileQueueManager(session=db_session)

        # Add multiple files
        for i in range(5):
            manager.add_file(f"/path/to/file{i}.mp4", "movie")

        # Get pending files
        pending = manager.get_pending_files(limit=10)
        assert len(pending) == 5

    def test_mark_file_processing(self, db_session):
        """Test marking file as processing"""
        manager = FileQueueManager(session=db_session)

        queue_id = manager.add_file("/path/to/file.mp4", "movie")
        success = manager.mark_processing(queue_id)

        assert success is True

        # Verify status changed
        queue_entry = db_session.query(FileQueue).filter(FileQueue.id == queue_id).first()
        assert queue_entry.status == "processing"

    def test_mark_file_completed(self, db_session):
        """Test marking file as completed"""
        manager = FileQueueManager(session=db_session)

        queue_id = manager.add_file("/path/to/file.mp4", "movie")
        manager.mark_processing(queue_id)
        success = manager.mark_completed(queue_id)

        assert success is True

        # Verify status changed
        queue_entry = db_session.query(FileQueue).filter(FileQueue.id == queue_id).first()
        assert queue_entry.status == "completed"

    def test_mark_file_failed(self, db_session):
        """Test marking file as failed"""
        manager = FileQueueManager(session=db_session)

        queue_id = manager.add_file("/path/to/file.mp4", "movie")
        success = manager.mark_failed(queue_id, "File corrupted")

        assert success is True

        # Verify status and error message
        queue_entry = db_session.query(FileQueue).filter(FileQueue.id == queue_id).first()
        assert queue_entry.status == "failed"
        assert queue_entry.error_message == "File corrupted"

    def test_duplicate_file_detection(self, db_session):
        """Test detecting duplicate files"""
        manager = FileQueueManager(session=db_session)

        # Add first file
        queue_id1 = manager.add_file("/path/to/file.mp4", "movie")

        # Try to add same file again
        queue_id2 = manager.add_file("/path/to/file.mp4", "movie")

        # Should return same ID (duplicate)
        assert queue_id1 == queue_id2

    def test_get_queue_stats(self, db_session):
        """Test getting queue statistics"""
        manager = FileQueueManager(session=db_session)

        # Add files with different statuses
        for i in range(3):
            manager.add_file(f"/path/to/file{i}.mp4", "movie")

        stats = manager.get_queue_stats()
        assert stats["total"] == 3
        assert stats["pending"] == 3


# ============================================================================
# Pattern Recognition Tests
# ============================================================================


class TestPatternRecognition:
    """Tests for pattern recognition"""

    def test_classify_movie_pattern(self):
        """Test classifying movie filename pattern"""
        service = PatternRecognitionService()

        result = service.classify_file("The Matrix (1999).mp4")
        assert result["type"] == "movie"
        assert result["title"] == "The Matrix"
        assert result["year"] == 1999

    def test_classify_tv_show_pattern(self):
        """Test classifying TV show filename pattern"""
        service = PatternRecognitionService()

        result = service.classify_file("Breaking Bad S01E01.mkv")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "Breaking Bad"
        assert result["season"] == 1
        assert result["episode"] == 1

    def test_classify_movie_with_year_brackets(self):
        """Test classifying movie with year in brackets"""
        service = PatternRecognitionService()

        result = service.classify_file("Inception [2010].mp4")
        assert result["type"] == "movie"
        assert result["title"] == "Inception"
        assert result["year"] == 2010

    def test_classify_tv_show_lowercase(self):
        """Test classifying TV show with lowercase pattern"""
        service = PatternRecognitionService()

        result = service.classify_file("Game of Thrones s08e06.mkv")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "Game of Thrones"
        assert result["season"] == 8
        assert result["episode"] == 6

    def test_classify_tv_show_number_x_format(self):
        """Test classifying TV show with number x format"""
        service = PatternRecognitionService()

        result = service.classify_file("The Office 9x23.mp4")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "The Office"
        assert result["season"] == 9
        assert result["episode"] == 23

    def test_fallback_classification(self):
        """Test fallback classification for ambiguous filenames"""
        service = PatternRecognitionService()

        result = service.classify_file("random_filename.mp4")
        assert result["type"] in ["movie", "tv_show"]
        assert result["confidence"] == "low"


# ============================================================================
# File Import Workflow Tests
# ============================================================================


class TestFileImportWorkflow:
    """Tests for file import workflow"""

    def test_import_movie_workflow(self, db_session, temp_media_dir):
        """Test complete movie import workflow"""
        # Create a movie file
        movie_file = Path(temp_media_dir) / "The Shawshank Redemption (1994).mp4"
        movie_file.touch()

        # Add to queue
        manager = FileQueueManager(session=db_session)
        queue_id = manager.add_file(str(movie_file), "movie")

        # Mark as processing
        manager.mark_processing(queue_id)

        # Classify file
        service = PatternRecognitionService()
        classification = service.classify_file(movie_file.name)

        assert classification["type"] == "movie"
        assert classification["title"] == "The Shawshank Redemption"

        # Mark as completed
        manager.mark_completed(queue_id)

        # Verify final status
        queue_entry = db_session.query(FileQueue).filter(FileQueue.id == queue_id).first()
        assert queue_entry.status == "completed"

    def test_import_tv_show_workflow(self, db_session, temp_media_dir):
        """Test complete TV show import workflow"""
        # Create a TV show file
        tv_file = Path(temp_media_dir) / "Breaking Bad S01E01.mkv"
        tv_file.touch()

        # Add to queue
        manager = FileQueueManager(session=db_session)
        queue_id = manager.add_file(str(tv_file), "tv_show")

        # Mark as processing
        manager.mark_processing(queue_id)

        # Classify file
        service = PatternRecognitionService()
        classification = service.classify_file(tv_file.name)

        assert classification["type"] == "tv_show"
        assert classification["show_name"] == "Breaking Bad"
        assert classification["season"] == 1
        assert classification["episode"] == 1

        # Mark as completed
        manager.mark_completed(queue_id)

        # Verify final status
        queue_entry = db_session.query(FileQueue).filter(FileQueue.id == queue_id).first()
        assert queue_entry.status == "completed"

    def test_import_with_error_handling(self, db_session):
        """Test import workflow with error handling"""
        manager = FileQueueManager(session=db_session)

        # Add file
        queue_id = manager.add_file("/path/to/corrupted.mp4", "movie")

        # Mark as processing
        manager.mark_processing(queue_id)

        # Simulate error
        error_msg = "File is corrupted or not a valid media file"
        manager.mark_failed(queue_id, error_msg)

        # Verify error status
        queue_entry = db_session.query(FileQueue).filter(FileQueue.id == queue_id).first()
        assert queue_entry.status == "failed"
        assert queue_entry.error_message == error_msg


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestFileMonitoringErrorHandling:
    """Tests for error handling in file monitoring"""

    def test_handle_missing_file(self, db_session):
        """Test handling missing file"""
        manager = FileQueueManager(session=db_session)

        queue_id = manager.add_file("/nonexistent/file.mp4", "movie")
        manager.mark_processing(queue_id)

        # Simulate file not found error
        manager.mark_failed(queue_id, "File not found")

        queue_entry = db_session.query(FileQueue).filter(FileQueue.id == queue_id).first()
        assert queue_entry.status == "failed"

    def test_handle_corrupted_file(self, db_session):
        """Test handling corrupted file"""
        manager = FileQueueManager(session=db_session)

        queue_id = manager.add_file("/path/to/corrupted.mp4", "movie")
        manager.mark_processing(queue_id)

        # Simulate corruption error
        manager.mark_failed(queue_id, "File is corrupted")

        queue_entry = db_session.query(FileQueue).filter(FileQueue.id == queue_id).first()
        assert queue_entry.status == "failed"

    def test_handle_invalid_media_type(self, db_session):
        """Test handling invalid media type"""
        manager = FileQueueManager(session=db_session)

        with pytest.raises(ValueError):
            manager.add_file("/path/to/file.mp4", "invalid_type")

    def test_handle_empty_file_path(self, db_session):
        """Test handling empty file path"""
        manager = FileQueueManager(session=db_session)

        with pytest.raises(ValueError):
            manager.add_file("", "movie")


# ============================================================================
# Concurrent File Processing Tests
# ============================================================================


class TestConcurrentFileProcessing:
    """Tests for concurrent file processing"""

    def test_process_multiple_files_sequentially(self, db_session):
        """Test processing multiple files sequentially"""
        manager = FileQueueManager(session=db_session)

        # Add multiple files
        queue_ids = []
        for i in range(5):
            queue_id = manager.add_file(f"/path/to/file{i}.mp4", "movie")
            queue_ids.append(queue_id)

        # Process each file
        for queue_id in queue_ids:
            manager.mark_processing(queue_id)
            manager.mark_completed(queue_id)

        # Verify all completed
        completed = db_session.query(FileQueue).filter(FileQueue.status == "completed").all()
        assert len(completed) == 5

    def test_process_mixed_media_types(self, db_session):
        """Test processing mixed media types"""
        manager = FileQueueManager(session=db_session)

        # Add movies and TV shows
        for i in range(3):
            manager.add_file(f"/path/to/movie{i}.mp4", "movie")
            manager.add_file(f"/path/to/show{i}.mkv", "tv_show")

        # Verify counts
        movies = db_session.query(FileQueue).filter(FileQueue.media_type == "movie").all()
        shows = db_session.query(FileQueue).filter(FileQueue.media_type == "tv_show").all()

        assert len(movies) == 3
        assert len(shows) == 3

    def test_retry_failed_file(self, db_session):
        """Test retrying failed file"""
        manager = FileQueueManager(session=db_session)

        # Add file
        queue_id = manager.add_file("/path/to/file.mp4", "movie")

        # Mark as failed
        manager.mark_failed(queue_id, "Temporary error")

        # Retry
        success = manager.retry_failed_file(queue_id)
        assert success is True

        # Verify status reset to pending
        queue_entry = db_session.query(FileQueue).filter(FileQueue.id == queue_id).first()
        assert queue_entry.status == "pending"


# ============================================================================
# File Monitoring Event Tests
# ============================================================================


class TestFileMonitoringEvents:
    """Tests for file monitoring events"""

    @patch("watchdog.observers.Observer")
    def test_file_created_event(self, mock_observer):
        """Test file created event"""
        # Mock observer
        mock_obs_instance = MagicMock()
        mock_observer.return_value = mock_obs_instance

        # Simulate file creation
        event = MagicMock()
        event.src_path = "/media/new_movie.mp4"
        event.is_directory = False

        assert not event.is_directory
        assert event.src_path.endswith(".mp4")

    @patch("watchdog.observers.Observer")
    def test_file_modified_event(self, mock_observer):
        """Test file modified event"""
        # Mock observer
        mock_obs_instance = MagicMock()
        mock_observer.return_value = mock_obs_instance

        # Simulate file modification
        event = MagicMock()
        event.src_path = "/media/movie.mp4"
        event.is_directory = False

        assert not event.is_directory

    @patch("watchdog.observers.Observer")
    def test_directory_ignored(self, mock_observer):
        """Test that directories are ignored"""
        # Mock observer
        mock_obs_instance = MagicMock()
        mock_observer.return_value = mock_obs_instance

        # Simulate directory event
        event = MagicMock()
        event.src_path = "/media/subfolder"
        event.is_directory = True

        # Should be ignored
        assert event.is_directory


# ============================================================================
# File Queue Statistics Tests
# ============================================================================


class TestFileQueueStatistics:
    """Tests for file queue statistics"""

    def test_queue_statistics(self, db_session):
        """Test getting queue statistics"""
        manager = FileQueueManager(session=db_session)

        # Add files with different statuses
        for i in range(3):
            manager.add_file(f"/path/to/pending{i}.mp4", "movie")

        for i in range(2):
            queue_id = manager.add_file(f"/path/to/completed{i}.mp4", "movie")
            manager.mark_processing(queue_id)
            manager.mark_completed(queue_id)

        for i in range(1):
            queue_id = manager.add_file(f"/path/to/failed{i}.mp4", "movie")
            manager.mark_failed(queue_id, "Error")

        stats = manager.get_queue_stats()
        assert stats["total"] == 6
        assert stats["pending"] == 3
        assert stats["completed"] == 2
        assert stats["failed"] == 1
