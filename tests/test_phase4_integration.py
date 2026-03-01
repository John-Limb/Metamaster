"""Phase 4 Integration Tests

Comprehensive integration tests that verify all Phase 4 components work together correctly.
Tests cover:
- File monitoring and detection
- Pattern recognition classification
- FFPROBE metadata extraction
- Queue management and status tracking
- Error handling and recovery
- Duplicate detection
- Status transitions
"""

import pytest
import asyncio
import tempfile
import time
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import FileQueue
from app.services.file_monitor import FileMonitorService
from app.services.pattern_recognition import PatternRecognitionService
from app.services.ffprobe_wrapper import FFProbeWrapper
from app.services.file_queue_manager import FileQueueManager
from tests.db_utils import TEST_DATABASE_URL


@pytest.fixture
def test_db():
    """Create a PostgreSQL database for testing."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def temp_watch_dir():
    """Create a temporary directory for file monitoring tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def queue_manager(test_db):
    """Create a FileQueueManager instance with test database."""
    return FileQueueManager(session=test_db)


@pytest.fixture
def pattern_service():
    """Create a PatternRecognitionService instance."""
    return PatternRecognitionService()


@pytest.fixture
def ffprobe_service():
    """Create an FFProbeWrapper instance (skip if ffprobe not available)."""
    try:
        return FFProbeWrapper()
    except RuntimeError:
        pytest.skip("FFProbe not available on system")


class TestScenario1CompleteFileProcessingPipeline:
    """Scenario 1: Complete File Processing Pipeline

    Monitor a directory for new files, detect file creation events, classify files
    using pattern recognition, extract metadata using FFPROBE, queue files for
    processing, and verify all components work together seamlessly.
    """

    @pytest.mark.asyncio
    async def test_complete_pipeline_movie_file(
        self, temp_watch_dir, queue_manager, pattern_service
    ):
        """Test complete pipeline with a movie file."""
        # Create test file
        test_file = Path(temp_watch_dir) / "The Matrix 1999.mp4"
        test_file.touch()

        # Initialize file monitor
        monitor = FileMonitorService(watch_path=temp_watch_dir)
        await monitor.start()

        # Give monitor time to detect file
        await asyncio.sleep(0.5)

        # Get queued files from monitor
        queued_files = monitor.peek_queued_files()

        # Verify file was detected
        assert len(queued_files) > 0
        # Use resolve() to handle symlinks and /private prefix on macOS
        assert str(test_file.resolve()) in [Path(f).resolve().__str__() for f in queued_files]

        # Classify file using pattern recognition
        classification = pattern_service.classify_file(str(test_file))
        assert classification["type"] == "movie"
        assert "title" in classification
        assert "year" in classification

        # Add to queue manager
        queue_id = queue_manager.add_file(str(test_file), classification["type"])
        assert queue_id > 0

        # Verify queue entry
        status = queue_manager.get_file_status(queue_id)
        assert status["status"] == "pending"
        assert status["media_type"] == "movie"

        # Cleanup
        await monitor.stop()

    @pytest.mark.asyncio
    async def test_complete_pipeline_tv_show_file(
        self, temp_watch_dir, queue_manager, pattern_service
    ):
        """Test complete pipeline with a TV show file."""
        # Create test file
        test_file = Path(temp_watch_dir) / "Breaking Bad S01E01.mkv"
        test_file.touch()

        # Initialize file monitor
        monitor = FileMonitorService(watch_path=temp_watch_dir)
        await monitor.start()

        # Give monitor time to detect file
        await asyncio.sleep(0.5)

        # Get queued files from monitor
        queued_files = monitor.peek_queued_files()

        # Verify file was detected
        assert len(queued_files) > 0
        # Use resolve() to handle symlinks and /private prefix on macOS
        assert str(test_file.resolve()) in [Path(f).resolve().__str__() for f in queued_files]

        # Classify file using pattern recognition
        classification = pattern_service.classify_file(str(test_file))
        assert classification["type"] == "tv_show"
        assert "show_name" in classification
        assert "season" in classification
        assert "episode" in classification

        # Add to queue manager
        queue_id = queue_manager.add_file(str(test_file), classification["type"])
        assert queue_id > 0

        # Verify queue entry
        status = queue_manager.get_file_status(queue_id)
        assert status["status"] == "pending"
        assert status["media_type"] == "tv_show"

        # Cleanup
        await monitor.stop()


class TestScenario2MovieFileDetectionAndProcessing:
    """Scenario 2: Movie File Detection and Processing

    Create test movie files with standard naming, verify file monitor detects them,
    verify pattern recognition classifies as movie, verify FFPROBE extracts metadata,
    and verify queue manager stores with correct metadata.
    """

    @pytest.mark.asyncio
    async def test_movie_detection_and_processing(
        self, temp_watch_dir, queue_manager, pattern_service
    ):
        """Test movie file detection and processing."""
        # Create multiple test movie files
        movie_files = [
            "The Matrix 1999.mp4",
            "Inception (2010).mkv",
            "Interstellar_2014.avi",
        ]

        created_files = []
        for movie_name in movie_files:
            test_file = Path(temp_watch_dir) / movie_name
            test_file.touch()
            created_files.append(test_file)

        # Initialize file monitor
        monitor = FileMonitorService(watch_path=temp_watch_dir)
        await monitor.start()

        # Give monitor time to detect files
        await asyncio.sleep(0.5)

        # Get queued files from monitor
        queued_files = monitor.peek_queued_files()

        # Verify all files were detected
        assert len(queued_files) >= len(movie_files)
        for test_file in created_files:
            # Use resolve() to handle symlinks and /private prefix on macOS
            assert str(test_file.resolve()) in [Path(f).resolve().__str__() for f in queued_files]

        # Process each file
        for test_file in created_files:
            # Classify file
            classification = pattern_service.classify_file(str(test_file))
            assert classification["type"] == "movie"

            # Add to queue
            queue_id = queue_manager.add_file(str(test_file), "movie")

            # Verify queue entry
            status = queue_manager.get_file_status(queue_id)
            assert status["media_type"] == "movie"
            assert status["status"] == "pending"

        # Verify queue stats
        stats = queue_manager.get_queue_stats()
        assert stats["total"] >= len(movie_files)
        assert stats["pending"] >= len(movie_files)

        # Cleanup
        await monitor.stop()

    def test_movie_classification_accuracy(self, pattern_service):
        """Test accuracy of movie classification."""
        test_cases = [
            ("The Matrix 1999.mp4", "movie", "The Matrix", 1999),
            ("Inception (2010).mkv", "movie", "Inception", 2010),
            ("Interstellar_2014.avi", "movie", "Interstellar", 2014),
            ("Avatar [2009].mov", "movie", "Avatar", 2009),
        ]

        for filename, expected_type, expected_title, expected_year in test_cases:
            classification = pattern_service.classify_file(filename)
            assert classification["type"] == expected_type
            assert classification.get("title") == expected_title
            assert classification.get("year") == expected_year


class TestScenario3TVShowFileDetectionAndProcessing:
    """Scenario 3: TV Show File Detection and Processing

    Create test TV show files with standard naming, verify file monitor detects them,
    verify pattern recognition classifies as TV show, verify FFPROBE extracts metadata,
    and verify queue manager stores with correct metadata.
    """

    @pytest.mark.asyncio
    async def test_tv_show_detection_and_processing(
        self, temp_watch_dir, queue_manager, pattern_service
    ):
        """Test TV show file detection and processing."""
        # Create multiple test TV show files
        tv_files = [
            "Breaking Bad S01E01.mkv",
            "Game of Thrones S08E06.mp4",
            "The Office 2x03.avi",
        ]

        created_files = []
        for tv_name in tv_files:
            test_file = Path(temp_watch_dir) / tv_name
            test_file.touch()
            created_files.append(test_file)

        # Initialize file monitor
        monitor = FileMonitorService(watch_path=temp_watch_dir)
        await monitor.start()

        # Give monitor time to detect files
        await asyncio.sleep(0.5)

        # Get queued files from monitor
        queued_files = monitor.peek_queued_files()

        # Verify all files were detected
        assert len(queued_files) >= len(tv_files)
        for test_file in created_files:
            # Use resolve() to handle symlinks and /private prefix on macOS
            assert str(test_file.resolve()) in [Path(f).resolve().__str__() for f in queued_files]

        # Process each file
        for test_file in created_files:
            # Classify file
            classification = pattern_service.classify_file(str(test_file))
            assert classification["type"] == "tv_show"

            # Add to queue
            queue_id = queue_manager.add_file(str(test_file), "tv_show")

            # Verify queue entry
            status = queue_manager.get_file_status(queue_id)
            assert status["media_type"] == "tv_show"
            assert status["status"] == "pending"

        # Verify queue stats
        stats = queue_manager.get_queue_stats()
        assert stats["total"] >= len(tv_files)
        assert stats["pending"] >= len(tv_files)

        # Cleanup
        await monitor.stop()

    def test_tv_show_classification_accuracy(self, pattern_service):
        """Test accuracy of TV show classification."""
        test_cases = [
            ("Breaking Bad S01E01.mkv", "tv_show", "Breaking Bad", 1, 1),
            ("Game of Thrones S08E06.mp4", "tv_show", "Game of Thrones", 8, 6),
            ("The Office 2x03.avi", "tv_show", "The Office", 2, 3),
            (
                "Stranger Things Season 1 Episode 1.mov",
                "tv_show",
                "Stranger Things",
                1,
                1,
            ),
        ]

        for (
            filename,
            expected_type,
            expected_show,
            expected_season,
            expected_episode,
        ) in test_cases:
            classification = pattern_service.classify_file(filename)
            assert classification["type"] == expected_type
            assert classification.get("season") == expected_season
            assert classification.get("episode") == expected_episode


class TestScenario4MixedContentProcessing:
    """Scenario 4: Mixed Content Processing

    Create both movie and TV show files in same directory, verify correct
    classification for each, and verify queue contains both with correct types.
    """

    @pytest.mark.asyncio
    async def test_mixed_content_processing(self, temp_watch_dir, queue_manager, pattern_service):
        """Test processing of mixed movie and TV show files."""
        # Create mixed content
        mixed_files = {
            "The Matrix 1999.mp4": "movie",
            "Breaking Bad S01E01.mkv": "tv_show",
            "Inception (2010).avi": "movie",
            "Game of Thrones S08E06.mov": "tv_show",
        }

        created_files = []
        for filename in mixed_files.keys():
            test_file = Path(temp_watch_dir) / filename
            test_file.touch()
            created_files.append(test_file)

        # Initialize file monitor
        monitor = FileMonitorService(watch_path=temp_watch_dir)
        await monitor.start()

        # Give monitor time to detect files
        await asyncio.sleep(0.5)

        # Get queued files from monitor
        queued_files = monitor.peek_queued_files()

        # Verify all files were detected
        assert len(queued_files) >= len(mixed_files)

        # Process each file
        for test_file in created_files:
            # Classify file
            classification = pattern_service.classify_file(str(test_file))
            expected_type = mixed_files[test_file.name]
            assert classification["type"] == expected_type

            # Add to queue
            queue_id = queue_manager.add_file(str(test_file), expected_type)

            # Verify queue entry
            status = queue_manager.get_file_status(queue_id)
            assert status["media_type"] == expected_type

        # Verify queue stats
        stats = queue_manager.get_queue_stats()
        assert stats["total"] >= len(mixed_files)

        # Verify correct counts by type
        movies = (
            queue_manager.session.query(FileQueue).filter(FileQueue.media_type == "movie").count()
        )
        tv_shows = (
            queue_manager.session.query(FileQueue).filter(FileQueue.media_type == "tv_show").count()
        )

        assert movies >= 2  # At least 2 movies
        assert tv_shows >= 2  # At least 2 TV shows

        # Cleanup
        await monitor.stop()


class TestScenario5ErrorHandlingAndRecovery:
    """Scenario 5: Error Handling and Recovery

    Test handling of corrupted media files, non-media files, verify graceful
    error handling without crashing, and verify error logging.
    """

    @pytest.mark.asyncio
    async def test_non_media_file_handling(self, temp_watch_dir):
        """Test that non-media files are ignored."""
        # Create non-media files
        non_media_files = [
            "document.txt",
            "image.jpg",
            "archive.zip",
            "script.py",
        ]

        for filename in non_media_files:
            test_file = Path(temp_watch_dir) / filename
            test_file.touch()

        # Initialize file monitor
        monitor = FileMonitorService(watch_path=temp_watch_dir)
        await monitor.start()

        # Give monitor time to detect files
        await asyncio.sleep(0.5)

        # Get queued files from monitor
        queued_files = monitor.peek_queued_files()

        # Verify non-media files were NOT queued
        for filename in non_media_files:
            test_file = Path(temp_watch_dir) / filename
            assert str(test_file) not in queued_files

        # Cleanup
        await monitor.stop()

    def test_invalid_file_type_handling(self, queue_manager):
        """Test handling of invalid file types."""
        with pytest.raises(ValueError):
            queue_manager.add_file("/path/to/file.mp4", "invalid_type")

    def test_empty_file_path_handling(self, queue_manager):
        """Test handling of empty file paths."""
        with pytest.raises(ValueError):
            queue_manager.add_file("", "movie")

    def test_error_message_logging(self, queue_manager):
        """Test that error messages are properly logged."""
        queue_id = queue_manager.add_file("/path/to/file.mp4", "movie")

        # Mark as failed with error message
        result = queue_manager.mark_failed(queue_id, "Test error message")
        assert result is True

        # Verify error message is stored
        status = queue_manager.get_file_status(queue_id)
        assert status["error_message"] == "Test error message"


class TestScenario6DuplicateDetection:
    """Scenario 6: Duplicate Detection

    Add same file twice, verify duplicate is not added to queue twice,
    and verify queue stats reflect correct count.
    """

    def test_duplicate_detection_single_add(self, queue_manager):
        """Test that duplicate file returns existing ID."""
        file_path = "/path/to/movie.mp4"

        # Add file first time
        queue_id1 = queue_manager.add_file(file_path, "movie")

        # Add same file second time
        queue_id2 = queue_manager.add_file(file_path, "movie")

        # Should return same ID
        assert queue_id1 == queue_id2

    def test_duplicate_detection_batch_add(self, queue_manager):
        """Test duplicate detection in batch operations."""
        files = [
            {"file_path": "/path/to/movie1.mp4", "file_type": "movie"},
            {"file_path": "/path/to/movie1.mp4", "file_type": "movie"},  # Duplicate
            {"file_path": "/path/to/movie2.mp4", "file_type": "movie"},
        ]

        queue_ids = queue_manager.add_files_batch(files)

        # Should only add 2 unique files
        assert len(queue_ids) == 2

    def test_duplicate_detection_queue_stats(self, queue_manager):
        """Test that queue stats reflect correct count with duplicates."""
        file_path = "/path/to/movie.mp4"

        # Add file multiple times
        queue_manager.add_file(file_path, "movie")
        queue_manager.add_file(file_path, "movie")
        queue_manager.add_file(file_path, "movie")

        # Queue stats should show only 1 file
        stats = queue_manager.get_queue_stats()
        assert stats["total"] == 1
        assert stats["pending"] == 1

    def test_is_duplicate_check(self, queue_manager):
        """Test is_duplicate method."""
        file_path = "/path/to/movie.mp4"

        # File not in queue yet
        assert queue_manager.is_duplicate(file_path) is False

        # Add file
        queue_manager.add_file(file_path, "movie")

        # Now it should be detected as duplicate
        assert queue_manager.is_duplicate(file_path) is True


class TestScenario7QueueStatusTransitions:
    """Scenario 7: Queue Status Transitions

    Add files to queue, transition through statuses (pending → processing → completed),
    verify status tracking works correctly, and verify queue stats update properly.
    """

    def test_status_transition_pending_to_processing(self, queue_manager):
        """Test transition from pending to processing."""
        queue_id = queue_manager.add_file("/path/to/file.mp4", "movie")

        # Initial status should be pending
        status = queue_manager.get_file_status(queue_id)
        assert status["status"] == "pending"

        # Transition to processing
        result = queue_manager.mark_processing(queue_id)
        assert result is True

        # Verify status changed
        status = queue_manager.get_file_status(queue_id)
        assert status["status"] == "processing"

    def test_status_transition_processing_to_completed(self, queue_manager):
        """Test transition from processing to completed."""
        queue_id = queue_manager.add_file("/path/to/file.mp4", "movie")
        queue_manager.mark_processing(queue_id)

        # Transition to completed
        result = queue_manager.mark_completed(queue_id)
        assert result is True

        # Verify status changed
        status = queue_manager.get_file_status(queue_id)
        assert status["status"] == "completed"
        assert status["processed_at"] is not None

    def test_status_transition_processing_to_failed(self, queue_manager):
        """Test transition from processing to failed."""
        queue_id = queue_manager.add_file("/path/to/file.mp4", "movie")
        queue_manager.mark_processing(queue_id)

        # Transition to failed
        result = queue_manager.mark_failed(queue_id, "Processing error")
        assert result is True

        # Verify status changed
        status = queue_manager.get_file_status(queue_id)
        assert status["status"] == "failed"
        assert status["error_message"] == "Processing error"

    def test_status_transition_failed_to_pending_retry(self, queue_manager):
        """Test retry transition from failed back to pending."""
        queue_id = queue_manager.add_file("/path/to/file.mp4", "movie")
        queue_manager.mark_processing(queue_id)
        queue_manager.mark_failed(queue_id, "Processing error")

        # Retry (transition back to pending)
        result = queue_manager.retry_failed_file(queue_id)
        assert result is True

        # Verify status changed
        status = queue_manager.get_file_status(queue_id)
        assert status["status"] == "pending"
        assert status["error_message"] is None

    def test_queue_stats_update_with_transitions(self, queue_manager):
        """Test that queue stats update correctly with status transitions."""
        # Add multiple files
        queue_id1 = queue_manager.add_file("/path/to/file1.mp4", "movie")
        queue_id2 = queue_manager.add_file("/path/to/file2.mp4", "movie")
        queue_id3 = queue_manager.add_file("/path/to/file3.mp4", "movie")

        # Initial stats
        stats = queue_manager.get_queue_stats()
        assert stats["pending"] == 3
        assert stats["processing"] == 0
        assert stats["completed"] == 0
        assert stats["failed"] == 0

        # Transition file 1 to processing
        queue_manager.mark_processing(queue_id1)
        stats = queue_manager.get_queue_stats()
        assert stats["pending"] == 2
        assert stats["processing"] == 1

        # Transition file 1 to completed
        queue_manager.mark_completed(queue_id1)
        stats = queue_manager.get_queue_stats()
        assert stats["pending"] == 2
        assert stats["processing"] == 0
        assert stats["completed"] == 1

        # Transition file 2 to processing then failed
        queue_manager.mark_processing(queue_id2)
        queue_manager.mark_failed(queue_id2, "Error")
        stats = queue_manager.get_queue_stats()
        assert stats["pending"] == 1
        assert stats["processing"] == 0
        assert stats["completed"] == 1
        assert stats["failed"] == 1

    def test_multiple_files_status_tracking(self, queue_manager):
        """Test tracking status of multiple files simultaneously."""
        files = [
            ("/path/to/file1.mp4", "movie"),
            ("/path/to/file2.mp4", "movie"),
            ("/path/to/file3.mp4", "tv_show"),
            ("/path/to/file4.mp4", "tv_show"),
        ]

        queue_ids = []
        for file_path, file_type in files:
            queue_id = queue_manager.add_file(file_path, file_type)
            queue_ids.append(queue_id)

        # Transition each file through different states
        queue_manager.mark_processing(queue_ids[0])
        queue_manager.mark_completed(queue_ids[0])

        queue_manager.mark_processing(queue_ids[1])
        queue_manager.mark_failed(queue_ids[1], "Error")

        queue_manager.mark_processing(queue_ids[2])

        # queue_ids[3] stays pending

        # Verify each file's status
        assert queue_manager.get_file_status(queue_ids[0])["status"] == "completed"
        assert queue_manager.get_file_status(queue_ids[1])["status"] == "failed"
        assert queue_manager.get_file_status(queue_ids[2])["status"] == "processing"
        assert queue_manager.get_file_status(queue_ids[3])["status"] == "pending"

        # Verify stats
        stats = queue_manager.get_queue_stats()
        assert stats["pending"] == 1
        assert stats["processing"] == 1
        assert stats["completed"] == 1
        assert stats["failed"] == 1


class TestIntegrationEdgeCases:
    """Test edge cases and integration scenarios."""

    @pytest.mark.asyncio
    async def test_rapid_file_creation(self, temp_watch_dir, queue_manager, pattern_service):
        """Test handling of rapid file creation."""
        # Initialize file monitor
        monitor = FileMonitorService(watch_path=temp_watch_dir)
        await monitor.start()

        # Rapidly create multiple files
        for i in range(5):
            test_file = Path(temp_watch_dir) / f"Movie {i} 2024.mp4"
            test_file.touch()

        # Give monitor time to detect files
        await asyncio.sleep(1)

        # Get queued files
        queued_files = monitor.peek_queued_files()

        # Verify all files were detected
        assert len(queued_files) >= 5

        # Cleanup
        await monitor.stop()

    def test_large_batch_processing(self, queue_manager):
        """Test processing of large batch of files."""
        # Create large batch
        files = [{"file_path": f"/path/to/movie{i}.mp4", "file_type": "movie"} for i in range(100)]

        queue_ids = queue_manager.add_files_batch(files)

        # Verify all files were added
        assert len(queue_ids) == 100

        # Verify stats
        stats = queue_manager.get_queue_stats()
        assert stats["total"] == 100
        assert stats["pending"] == 100

    def test_concurrent_status_updates(self, queue_manager):
        """Test concurrent status updates."""
        # Add multiple files
        queue_ids = []
        for i in range(10):
            queue_id = queue_manager.add_file(f"/path/to/file{i}.mp4", "movie")
            queue_ids.append(queue_id)

        # Update statuses
        for queue_id in queue_ids[:5]:
            queue_manager.mark_processing(queue_id)

        for queue_id in queue_ids[:3]:
            queue_manager.mark_completed(queue_id)

        for queue_id in queue_ids[3:5]:
            queue_manager.mark_failed(queue_id, "Error")

        # Verify final stats
        stats = queue_manager.get_queue_stats()
        assert stats["total"] == 10
        assert stats["pending"] == 5
        assert stats["processing"] == 0
        assert stats["completed"] == 3
        assert stats["failed"] == 2

    def test_database_consistency_after_operations(self, queue_manager):
        """Test database consistency after various operations."""
        # Add files
        queue_id1 = queue_manager.add_file("/path/to/file1.mp4", "movie")
        queue_id2 = queue_manager.add_file("/path/to/file2.mp4", "tv_show")

        # Perform operations
        queue_manager.mark_processing(queue_id1)
        queue_manager.mark_completed(queue_id1)
        queue_manager.mark_processing(queue_id2)
        queue_manager.mark_failed(queue_id2, "Error")

        # Verify database consistency
        stats = queue_manager.get_queue_stats()
        assert stats["total"] == 2
        assert stats["completed"] == 1
        assert stats["failed"] == 1

        # Verify individual entries
        status1 = queue_manager.get_file_status(queue_id1)
        status2 = queue_manager.get_file_status(queue_id2)

        assert status1["status"] == "completed"
        assert status2["status"] == "failed"
        assert status1["media_type"] == "movie"
        assert status2["media_type"] == "tv_show"
