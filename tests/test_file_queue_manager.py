"""Unit tests for FileQueueManager

Comprehensive test coverage for file queue management including:
- Adding single and multiple files to queue
- Duplicate detection
- Status transitions
- Retry logic
- Queue statistics
- Batch operations
- Error handling
- Edge cases
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import FileQueue
from app.services.file_queue_manager import FileQueueManager


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def manager(test_db):
    """Create a FileQueueManager instance with test database."""
    return FileQueueManager(session=test_db)


class TestAddFile:
    """Tests for adding single files to queue."""

    def test_add_file_success(self, manager):
        """Test successfully adding a file to queue."""
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        assert isinstance(queue_id, int)
        assert queue_id > 0

    def test_add_file_returns_existing_id_for_duplicate(self, manager):
        """Test that adding duplicate file returns existing queue ID."""
        queue_id1 = manager.add_file("/path/to/movie.mp4", "movie")
        queue_id2 = manager.add_file("/path/to/movie.mp4", "movie")
        assert queue_id1 == queue_id2

    def test_add_file_with_tv_show_type(self, manager):
        """Test adding a TV show file."""
        queue_id = manager.add_file("/path/to/episode.mkv", "tv_show")
        assert isinstance(queue_id, int)
        status = manager.get_file_status(queue_id)
        assert status["media_type"] == "tv_show"

    def test_add_file_empty_path_raises_error(self, manager):
        """Test that empty file path raises ValueError."""
        with pytest.raises(ValueError, match="file_path cannot be empty"):
            manager.add_file("", "movie")

    def test_add_file_whitespace_path_raises_error(self, manager):
        """Test that whitespace-only file path raises ValueError."""
        with pytest.raises(ValueError, match="file_path cannot be empty"):
            manager.add_file("   ", "movie")

    def test_add_file_invalid_type_raises_error(self, manager):
        """Test that invalid file type raises ValueError."""
        with pytest.raises(ValueError, match="file_type must be"):
            manager.add_file("/path/to/file.mp4", "invalid_type")

    def test_add_file_with_metadata(self, manager):
        """Test adding file with metadata (reserved for future use)."""
        metadata = {"resolution": "1080p", "codec": "h264"}
        queue_id = manager.add_file("/path/to/movie.mp4", "movie", metadata=metadata)
        assert isinstance(queue_id, int)

    def test_add_file_creates_pending_status(self, manager):
        """Test that newly added file has pending status."""
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        status = manager.get_file_status(queue_id)
        assert status["status"] == "pending"

    def test_add_file_sets_created_at(self, manager):
        """Test that created_at timestamp is set."""
        before = datetime.utcnow()
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        after = datetime.utcnow()
        status = manager.get_file_status(queue_id)
        assert before <= status["created_at"] <= after


class TestAddFilesBatch:
    """Tests for batch adding files to queue."""

    def test_add_files_batch_success(self, manager):
        """Test successfully adding multiple files in batch."""
        files = [
            {"file_path": "/path/to/movie1.mp4", "file_type": "movie"},
            {"file_path": "/path/to/movie2.mkv", "file_type": "movie"},
            {"file_path": "/path/to/episode1.avi", "file_type": "tv_show"},
        ]
        queue_ids = manager.add_files_batch(files)
        assert len(queue_ids) == 3
        assert all(isinstance(qid, int) for qid in queue_ids)

    def test_add_files_batch_empty_list_raises_error(self, manager):
        """Test that empty files list raises ValueError."""
        with pytest.raises(ValueError, match="files list cannot be empty"):
            manager.add_files_batch([])

    def test_add_files_batch_skips_invalid_entries(self, manager):
        """Test that batch operation skips invalid entries."""
        files = [
            {"file_path": "/path/to/movie1.mp4", "file_type": "movie"},
            {"file_path": "", "file_type": "movie"},  # Invalid: empty path
            {
                "file_path": "/path/to/episode1.avi",
                "file_type": "invalid",
            },  # Invalid: type
            {"file_path": "/path/to/movie2.mkv", "file_type": "movie"},
        ]
        queue_ids = manager.add_files_batch(files)
        assert len(queue_ids) == 2  # Only valid entries

    def test_add_files_batch_handles_duplicates(self, manager):
        """Test that batch operation handles duplicates within batch."""
        files = [
            {"file_path": "/path/to/movie1.mp4", "file_type": "movie"},
            {
                "file_path": "/path/to/movie1.mp4",
                "file_type": "movie",
            },  # Duplicate within batch
        ]
        queue_ids = manager.add_files_batch(files)
        # Only one entry should be added (duplicate within batch is skipped)
        assert len(queue_ids) == 1
        assert isinstance(queue_ids[0], int)

    def test_add_files_batch_with_metadata(self, manager):
        """Test batch adding files with metadata."""
        files = [
            {
                "file_path": "/path/to/movie1.mp4",
                "file_type": "movie",
                "metadata": {"resolution": "1080p"},
            },
            {
                "file_path": "/path/to/movie2.mkv",
                "file_type": "movie",
                "metadata": {"resolution": "4k"},
            },
        ]
        queue_ids = manager.add_files_batch(files)
        assert len(queue_ids) == 2

    def test_add_files_batch_invalid_entry_type_skipped(self, manager):
        """Test that non-dict entry is skipped."""
        files = [
            {"file_path": "/path/to/movie1.mp4", "file_type": "movie"},
            "/path/to/movie2.mp4",  # Invalid: not a dict
        ]
        queue_ids = manager.add_files_batch(files)
        assert len(queue_ids) == 1  # Only valid entry


class TestDuplicateDetection:
    """Tests for duplicate detection functionality."""

    def test_is_duplicate_returns_true_for_existing_file(self, manager):
        """Test that is_duplicate returns True for existing file."""
        manager.add_file("/path/to/movie.mp4", "movie")
        assert manager.is_duplicate("/path/to/movie.mp4") is True

    def test_is_duplicate_returns_false_for_new_file(self, manager):
        """Test that is_duplicate returns False for new file."""
        assert manager.is_duplicate("/path/to/new_movie.mp4") is False

    def test_is_duplicate_empty_path_raises_error(self, manager):
        """Test that empty path raises ValueError."""
        with pytest.raises(ValueError, match="file_path cannot be empty"):
            manager.is_duplicate("")

    def test_is_duplicate_case_sensitive(self, manager):
        """Test that duplicate detection is case-sensitive."""
        manager.add_file("/path/to/movie.mp4", "movie")
        # Different case should not be detected as duplicate
        assert manager.is_duplicate("/path/to/MOVIE.mp4") is False


class TestStatusTransitions:
    """Tests for status transitions (pending → processing → completed/failed)."""

    def test_mark_processing_success(self, manager):
        """Test marking file as processing."""
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        result = manager.mark_processing(queue_id)
        assert result is True
        status = manager.get_file_status(queue_id)
        assert status["status"] == "processing"

    def test_mark_processing_nonexistent_file_returns_false(self, manager):
        """Test marking nonexistent file returns False."""
        result = manager.mark_processing(9999)
        assert result is False

    def test_mark_completed_success(self, manager):
        """Test marking file as completed."""
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        manager.mark_processing(queue_id)
        result = manager.mark_completed(queue_id)
        assert result is True
        status = manager.get_file_status(queue_id)
        assert status["status"] == "completed"
        assert status["processed_at"] is not None
        assert status["error_message"] is None

    def test_mark_completed_clears_error_message(self, manager):
        """Test that marking completed clears error message."""
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        manager.mark_failed(queue_id, "Some error")
        manager.mark_completed(queue_id)
        status = manager.get_file_status(queue_id)
        assert status["error_message"] is None

    def test_mark_completed_nonexistent_file_returns_false(self, manager):
        """Test marking nonexistent file as completed returns False."""
        result = manager.mark_completed(9999)
        assert result is False

    def test_mark_failed_success(self, manager):
        """Test marking file as failed."""
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        manager.mark_processing(queue_id)
        result = manager.mark_failed(queue_id, "Processing error")
        assert result is True
        status = manager.get_file_status(queue_id)
        assert status["status"] == "failed"
        assert status["error_message"] == "Processing error"
        assert status["processed_at"] is not None

    def test_mark_failed_empty_error_message_raises_error(self, manager):
        """Test that empty error message raises ValueError."""
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        with pytest.raises(ValueError, match="error_message cannot be empty"):
            manager.mark_failed(queue_id, "")

    def test_mark_failed_nonexistent_file_returns_false(self, manager):
        """Test marking nonexistent file as failed returns False."""
        result = manager.mark_failed(9999, "Error")
        assert result is False


class TestGetFileStatus:
    """Tests for getting file status."""

    def test_get_file_status_success(self, manager):
        """Test getting status of existing file."""
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        status = manager.get_file_status(queue_id)
        assert status["id"] == queue_id
        assert status["file_path"] == "/path/to/movie.mp4"
        assert status["media_type"] == "movie"
        assert status["status"] == "pending"

    def test_get_file_status_nonexistent_file_raises_error(self, manager):
        """Test getting status of nonexistent file raises RuntimeError."""
        with pytest.raises(RuntimeError, match="Queue entry not found"):
            manager.get_file_status(9999)

    def test_get_file_status_includes_all_fields(self, manager):
        """Test that status includes all required fields."""
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        status = manager.get_file_status(queue_id)
        required_fields = [
            "id",
            "file_path",
            "status",
            "media_type",
            "error_message",
            "created_at",
            "processed_at",
        ]
        for field in required_fields:
            assert field in status


class TestQueueStats:
    """Tests for queue statistics."""

    def test_get_queue_stats_empty_queue(self, manager):
        """Test queue stats for empty queue."""
        stats = manager.get_queue_stats()
        assert stats["total"] == 0
        assert stats["pending"] == 0
        assert stats["processing"] == 0
        assert stats["completed"] == 0
        assert stats["failed"] == 0

    def test_get_queue_stats_with_files(self, manager):
        """Test queue stats with various file statuses."""
        # Add pending files
        queue_id1 = manager.add_file("/path/to/movie1.mp4", "movie")
        queue_id2 = manager.add_file("/path/to/movie2.mp4", "movie")

        # Mark one as processing
        manager.mark_processing(queue_id1)

        # Add and complete another
        queue_id3 = manager.add_file("/path/to/movie3.mp4", "movie")
        manager.mark_processing(queue_id3)
        manager.mark_completed(queue_id3)

        # Add and fail another
        queue_id4 = manager.add_file("/path/to/movie4.mp4", "movie")
        manager.mark_processing(queue_id4)
        manager.mark_failed(queue_id4, "Error")

        stats = manager.get_queue_stats()
        assert stats["total"] == 4
        assert stats["pending"] == 1
        assert stats["processing"] == 1
        assert stats["completed"] == 1
        assert stats["failed"] == 1

    def test_get_queue_stats_includes_all_statuses(self, manager):
        """Test that stats includes all status types."""
        stats = manager.get_queue_stats()
        required_fields = ["total", "pending", "processing", "completed", "failed"]
        for field in required_fields:
            assert field in stats


class TestRetryLogic:
    """Tests for retry functionality."""

    def test_retry_failed_file_success(self, manager):
        """Test retrying a failed file."""
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        manager.mark_processing(queue_id)
        manager.mark_failed(queue_id, "Processing error")

        result = manager.retry_failed_file(queue_id)
        assert result is True

        status = manager.get_file_status(queue_id)
        assert status["status"] == "pending"
        assert status["error_message"] is None
        assert status["processed_at"] is None

    def test_retry_failed_file_nonexistent_returns_false(self, manager):
        """Test retrying nonexistent file returns False."""
        result = manager.retry_failed_file(9999)
        assert result is False

    def test_retry_failed_file_not_failed_returns_false(self, manager):
        """Test retrying non-failed file returns False."""
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        result = manager.retry_failed_file(queue_id)
        assert result is False

    def test_retry_failed_file_clears_error_message(self, manager):
        """Test that retry clears error message."""
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        manager.mark_processing(queue_id)
        manager.mark_failed(queue_id, "Error message")

        manager.retry_failed_file(queue_id)
        status = manager.get_file_status(queue_id)
        assert status["error_message"] is None


class TestGetPendingFiles:
    """Tests for getting pending files."""

    def test_get_pending_files_empty_queue(self, manager):
        """Test getting pending files from empty queue."""
        pending = manager.get_pending_files()
        assert pending == []

    def test_get_pending_files_returns_only_pending(self, manager):
        """Test that only pending files are returned."""
        queue_id1 = manager.add_file("/path/to/movie1.mp4", "movie")
        queue_id2 = manager.add_file("/path/to/movie2.mp4", "movie")
        queue_id3 = manager.add_file("/path/to/movie3.mp4", "movie")

        manager.mark_processing(queue_id1)
        manager.mark_completed(queue_id2)

        pending = manager.get_pending_files()
        assert len(pending) == 1
        assert pending[0]["id"] == queue_id3

    def test_get_pending_files_respects_limit(self, manager):
        """Test that limit parameter is respected."""
        for i in range(5):
            manager.add_file(f"/path/to/movie{i}.mp4", "movie")

        pending = manager.get_pending_files(limit=3)
        assert len(pending) == 3

    def test_get_pending_files_ordered_by_created_at(self, manager):
        """Test that pending files are ordered by creation time."""
        queue_id1 = manager.add_file("/path/to/movie1.mp4", "movie")
        queue_id2 = manager.add_file("/path/to/movie2.mp4", "movie")
        queue_id3 = manager.add_file("/path/to/movie3.mp4", "movie")

        pending = manager.get_pending_files()
        assert pending[0]["id"] == queue_id1
        assert pending[1]["id"] == queue_id2
        assert pending[2]["id"] == queue_id3

    def test_get_pending_files_invalid_limit_raises_error(self, manager):
        """Test that invalid limit raises ValueError."""
        with pytest.raises(ValueError, match="limit must be positive"):
            manager.get_pending_files(limit=0)

    def test_get_pending_files_includes_required_fields(self, manager):
        """Test that pending files include all required fields."""
        manager.add_file("/path/to/movie.mp4", "movie")
        pending = manager.get_pending_files()
        required_fields = ["id", "file_path", "media_type", "status", "created_at"]
        for field in required_fields:
            assert field in pending[0]


class TestClearCompletedFiles:
    """Tests for clearing old completed files."""

    def test_clear_completed_files_success(self, manager):
        """Test clearing old completed files."""
        # Add and complete a file
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        manager.mark_processing(queue_id)
        manager.mark_completed(queue_id)

        # Manually set processed_at to 8 days ago using manager's session
        entry = manager.session.query(FileQueue).filter(FileQueue.id == queue_id).first()
        entry.processed_at = datetime.utcnow() - timedelta(days=8)
        manager.session.commit()

        # Clear files older than 7 days
        deleted_count = manager.clear_completed_files(days_old=7)
        assert deleted_count == 1

    def test_clear_completed_files_keeps_recent(self, manager):
        """Test that recent completed files are not cleared."""
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        manager.mark_processing(queue_id)
        manager.mark_completed(queue_id)

        # Clear files older than 7 days (file is recent)
        deleted_count = manager.clear_completed_files(days_old=7)
        assert deleted_count == 0

    def test_clear_completed_files_only_completed(self, manager):
        """Test that only completed files are cleared."""
        queue_id1 = manager.add_file("/path/to/movie1.mp4", "movie")
        queue_id2 = manager.add_file("/path/to/movie2.mp4", "movie")

        manager.mark_processing(queue_id1)
        manager.mark_completed(queue_id1)
        manager.mark_processing(queue_id2)
        manager.mark_failed(queue_id2, "Error")

        # Manually set processed_at to 8 days ago for both using manager's session
        for entry in manager.session.query(FileQueue).all():
            entry.processed_at = datetime.utcnow() - timedelta(days=8)
        manager.session.commit()

        # Clear files older than 7 days
        deleted_count = manager.clear_completed_files(days_old=7)
        assert deleted_count == 1  # Only completed file

    def test_clear_completed_files_invalid_days_raises_error(self, manager):
        """Test that invalid days_old raises ValueError."""
        with pytest.raises(ValueError, match="days_old must be positive"):
            manager.clear_completed_files(days_old=0)


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_add_file_with_special_characters_in_path(self, manager):
        """Test adding file with special characters in path."""
        queue_id = manager.add_file("/path/to/movie [2024] (1080p).mp4", "movie")
        assert isinstance(queue_id, int)

    def test_add_file_with_unicode_in_path(self, manager):
        """Test adding file with unicode characters in path."""
        queue_id = manager.add_file("/path/to/фильм.mp4", "movie")
        assert isinstance(queue_id, int)

    def test_add_file_with_very_long_path(self, manager):
        """Test adding file with very long path."""
        long_path = "/path/" + "a" * 400 + ".mp4"
        queue_id = manager.add_file(long_path, "movie")
        assert isinstance(queue_id, int)

    def test_mark_failed_with_long_error_message(self, manager):
        """Test marking failed with long error message."""
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        long_error = "Error: " + "x" * 1000
        result = manager.mark_failed(queue_id, long_error)
        assert result is True

    def test_concurrent_operations_on_same_file(self, manager):
        """Test handling concurrent operations on same file."""
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        manager.mark_processing(queue_id)
        manager.mark_completed(queue_id)
        status = manager.get_file_status(queue_id)
        assert status["status"] == "completed"


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_complete_workflow_success(self, manager):
        """Test complete workflow: add → process → complete."""
        # Add file
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")
        assert manager.is_duplicate("/path/to/movie.mp4")

        # Get pending
        pending = manager.get_pending_files()
        assert len(pending) == 1

        # Mark processing
        manager.mark_processing(queue_id)
        status = manager.get_file_status(queue_id)
        assert status["status"] == "processing"

        # Mark completed
        manager.mark_completed(queue_id)
        status = manager.get_file_status(queue_id)
        assert status["status"] == "completed"

        # Check stats
        stats = manager.get_queue_stats()
        assert stats["completed"] == 1

    def test_complete_workflow_with_retry(self, manager):
        """Test workflow with failure and retry."""
        # Add file
        queue_id = manager.add_file("/path/to/movie.mp4", "movie")

        # Mark processing and fail
        manager.mark_processing(queue_id)
        manager.mark_failed(queue_id, "Processing error")

        # Check stats
        stats = manager.get_queue_stats()
        assert stats["failed"] == 1

        # Retry
        manager.retry_failed_file(queue_id)
        status = manager.get_file_status(queue_id)
        assert status["status"] == "pending"

        # Process again
        manager.mark_processing(queue_id)
        manager.mark_completed(queue_id)
        status = manager.get_file_status(queue_id)
        assert status["status"] == "completed"

    def test_batch_workflow(self, manager):
        """Test batch workflow."""
        files = [{"file_path": f"/path/to/movie{i}.mp4", "file_type": "movie"} for i in range(5)]

        queue_ids = manager.add_files_batch(files)
        assert len(queue_ids) == 5

        # Get pending
        pending = manager.get_pending_files(limit=10)
        assert len(pending) == 5

        # Process all
        for queue_id in queue_ids:
            manager.mark_processing(queue_id)
            manager.mark_completed(queue_id)

        # Check stats
        stats = manager.get_queue_stats()
        assert stats["completed"] == 5
        assert stats["pending"] == 0
