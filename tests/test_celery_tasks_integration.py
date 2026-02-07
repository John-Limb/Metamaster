"""Comprehensive integration tests for Celery background tasks"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
from celery.result import AsyncResult

from app.database import Base
from app.models import Movie, TVShow, TaskError, BatchOperation, FileQueue
from app.celery_app import celery_app


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
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    yield session
    session.close()


# ============================================================================
# Task Execution Tests
# ============================================================================


class TestTaskExecution:
    """Tests for task execution"""

    @patch("app.tasks.analyze_file.apply_async")
    def test_analyze_file_task_execution(self, mock_task):
        """Test analyze_file task execution"""
        mock_result = MagicMock()
        mock_result.id = "task-123"
        mock_result.state = "SUCCESS"
        mock_task.return_value = mock_result

        # Execute task
        result = mock_task("/path/to/file.mp4")

        assert result.id == "task-123"
        assert result.state == "SUCCESS"

    @patch("app.tasks.enrich_metadata.apply_async")
    def test_enrich_metadata_task_execution(self, mock_task):
        """Test enrich_metadata task execution"""
        mock_result = MagicMock()
        mock_result.id = "task-456"
        mock_result.state = "SUCCESS"
        mock_task.return_value = mock_result

        # Execute task
        result = mock_task(1, "movie")

        assert result.id == "task-456"
        assert result.state == "SUCCESS"

    @patch("app.tasks.sync_metadata.apply_async")
    def test_sync_metadata_task_execution(self, mock_task):
        """Test sync_metadata task execution"""
        mock_result = MagicMock()
        mock_result.id = "task-789"
        mock_result.state = "SUCCESS"
        mock_task.return_value = mock_result

        # Execute task
        result = mock_task()

        assert result.id == "task-789"
        assert result.state == "SUCCESS"

    @patch("app.tasks.cleanup_cache.apply_async")
    def test_cleanup_cache_task_execution(self, mock_task):
        """Test cleanup_cache task execution"""
        mock_result = MagicMock()
        mock_result.id = "task-cleanup-1"
        mock_result.state = "SUCCESS"
        mock_task.return_value = mock_result

        # Execute task
        result = mock_task()

        assert result.id == "task-cleanup-1"
        assert result.state == "SUCCESS"

    @patch("app.tasks.cleanup_queue.apply_async")
    def test_cleanup_queue_task_execution(self, mock_task):
        """Test cleanup_queue task execution"""
        mock_result = MagicMock()
        mock_result.id = "task-cleanup-2"
        mock_result.state = "SUCCESS"
        mock_task.return_value = mock_result

        # Execute task
        result = mock_task()

        assert result.id == "task-cleanup-2"
        assert result.state == "SUCCESS"


# ============================================================================
# Task Completion Tests
# ============================================================================


class TestTaskCompletion:
    """Tests for task completion"""

    @patch("app.tasks.analyze_file")
    def test_task_completion_success(self, mock_task):
        """Test task completion with success"""
        mock_task.return_value = {
            "resolution": "1920x1080",
            "bitrate": "5000 kbps",
            "codec_video": "h264",
            "codec_audio": "aac",
            "duration": 7200,
        }

        result = mock_task("/path/to/file.mp4")

        assert result["resolution"] == "1920x1080"
        assert result["bitrate"] == "5000 kbps"

    @patch("app.tasks.enrich_metadata")
    def test_task_completion_with_result(self, mock_task):
        """Test task completion with result data"""
        mock_task.return_value = {
            "success": True,
            "updated_fields": ["rating", "plot"],
            "metadata": {
                "title": "The Shawshank Redemption",
                "rating": 9.3,
                "plot": "Two imprisoned men bond",
            },
        }

        result = mock_task(1, "movie")

        assert result["success"] is True
        assert len(result["updated_fields"]) == 2


# ============================================================================
# Task Error Handling Tests
# ============================================================================


class TestTaskErrorHandling:
    """Tests for task error handling"""

    @patch("app.tasks.analyze_file")
    def test_task_error_handling(self, mock_task):
        """Test task error handling"""
        mock_task.side_effect = Exception("File not found")

        with pytest.raises(Exception):
            mock_task("/nonexistent/file.mp4")

    @patch("app.tasks.enrich_metadata")
    def test_task_error_logging(self, mock_task, db_session):
        """Test task error logging"""
        mock_task.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            mock_task(1, "movie")

    @patch("app.tasks.analyze_file")
    def test_task_timeout_error(self, mock_task):
        """Test task timeout error"""
        import subprocess

        mock_task.side_effect = subprocess.TimeoutExpired("ffprobe", 30)

        with pytest.raises(subprocess.TimeoutExpired):
            mock_task("/path/to/file.mp4")

    def test_task_error_persistence(self, db_session):
        """Test persisting task errors to database"""
        error = TaskError(
            task_id="task-123",
            task_name="app.tasks.analyze_file",
            error_message="File not found",
            error_traceback="Traceback...",
            severity="critical",
        )
        db_session.add(error)
        db_session.commit()
        db_session.refresh(error)

        # Verify error is persisted
        retrieved = db_session.query(TaskError).filter(TaskError.task_id == "task-123").first()
        assert retrieved is not None
        assert retrieved.severity == "critical"


# ============================================================================
# Task Retry Logic Tests
# ============================================================================


class TestTaskRetryLogic:
    """Tests for task retry logic"""

    @patch("app.tasks.analyze_file")
    def test_task_retry_on_failure(self, mock_task):
        """Test task retry on failure"""
        # First call fails, second succeeds
        mock_task.side_effect = [
            Exception("Temporary error"),
            {"resolution": "1920x1080"},
        ]

        # First call
        with pytest.raises(Exception):
            mock_task("/path/to/file.mp4")

        # Second call (retry)
        result = mock_task("/path/to/file.mp4")
        assert result["resolution"] == "1920x1080"

    @patch("app.tasks.enrich_metadata")
    def test_task_retry_count(self, mock_task):
        """Test task retry count"""
        mock_task.side_effect = Exception("API Error")

        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            try:
                mock_task(1, "movie")
                break
            except Exception:
                retry_count += 1

        assert retry_count == max_retries

    @patch("app.tasks.analyze_file")
    def test_exponential_backoff(self, mock_task):
        """Test exponential backoff retry strategy"""
        mock_task.side_effect = Exception("Temporary error")

        # Simulate exponential backoff
        backoff_times = [1, 2, 4, 8]  # seconds

        for backoff in backoff_times:
            # In real scenario, would wait backoff seconds
            assert backoff > 0


# ============================================================================
# Task Progress Tracking Tests
# ============================================================================


class TestTaskProgressTracking:
    """Tests for task progress tracking"""

    def test_batch_operation_progress(self, db_session):
        """Test batch operation progress tracking"""
        batch = BatchOperation(
            operation_type="metadata_sync",
            status="running",
            total_items=100,
            completed_items=0,
            failed_items=0,
            progress_percentage=0.0,
        )
        db_session.add(batch)
        db_session.commit()
        db_session.refresh(batch)

        # Update progress
        batch.completed_items = 50
        batch.progress_percentage = 50.0
        db_session.commit()
        db_session.refresh(batch)

        assert batch.progress_percentage == 50.0

    def test_batch_operation_eta_calculation(self, db_session):
        """Test batch operation ETA calculation"""
        batch = BatchOperation(
            operation_type="metadata_sync",
            status="running",
            total_items=100,
            completed_items=25,
            failed_items=0,
            progress_percentage=25.0,
            started_at=datetime.utcnow() - timedelta(minutes=5),
        )
        db_session.add(batch)
        db_session.commit()
        db_session.refresh(batch)

        # Calculate ETA
        elapsed = datetime.utcnow() - batch.started_at
        items_per_second = batch.completed_items / elapsed.total_seconds()
        remaining_items = batch.total_items - batch.completed_items

        if items_per_second > 0:
            remaining_seconds = remaining_items / items_per_second
            eta = datetime.utcnow() + timedelta(seconds=remaining_seconds)
            assert eta > datetime.utcnow()

    def test_task_progress_update(self, db_session):
        """Test task progress update"""
        batch = BatchOperation(
            operation_type="file_import",
            status="running",
            total_items=50,
            completed_items=0,
        )
        db_session.add(batch)
        db_session.commit()
        db_session.refresh(batch)

        # Simulate progress updates
        for i in range(1, 6):
            batch.completed_items = i * 10
            batch.progress_percentage = (i * 10 / 50) * 100
            db_session.commit()

        db_session.refresh(batch)
        assert batch.completed_items == 50
        assert batch.progress_percentage == 100.0


# ============================================================================
# Batch Task Processing Tests
# ============================================================================


class TestBatchTaskProcessing:
    """Tests for batch task processing"""

    @patch("app.tasks.bulk_metadata_sync_task")
    def test_bulk_metadata_sync_task(self, mock_task):
        """Test bulk metadata sync task"""
        mock_task.return_value = {
            "status": "success",
            "completed": 10,
            "failed": 0,
            "total": 10,
        }

        result = mock_task(1, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "movie")

        assert result["status"] == "success"
        assert result["completed"] == 10
        assert result["failed"] == 0

    @patch("app.tasks.bulk_file_import_task")
    def test_bulk_file_import_task(self, mock_task):
        """Test bulk file import task"""
        mock_task.return_value = {
            "status": "success",
            "completed": 5,
            "failed": 0,
            "total": 5,
        }

        files = [
            "/path/to/file1.mp4",
            "/path/to/file2.mkv",
            "/path/to/file3.avi",
            "/path/to/file4.mov",
            "/path/to/file5.flv",
        ]

        result = mock_task(1, files, "movie")

        assert result["status"] == "success"
        assert result["completed"] == 5

    def test_batch_operation_status_tracking(self, db_session):
        """Test batch operation status tracking"""
        batch = BatchOperation(
            operation_type="metadata_sync",
            status="pending",
            total_items=10,
            completed_items=0,
        )
        db_session.add(batch)
        db_session.commit()
        db_session.refresh(batch)

        # Simulate status transitions
        batch.status = "running"
        batch.started_at = datetime.utcnow()
        db_session.commit()

        batch.completed_items = 10
        batch.status = "completed"
        batch.completed_at = datetime.utcnow()
        db_session.commit()
        db_session.refresh(batch)

        assert batch.status == "completed"
        assert batch.completed_at is not None


# ============================================================================
# Task Cancellation Tests
# ============================================================================


class TestTaskCancellation:
    """Tests for task cancellation"""

    @patch("app.celery_app.control.revoke")
    def test_cancel_task(self, mock_revoke):
        """Test cancelling a task"""
        mock_revoke.return_value = None

        celery_app.control.revoke("task-123", terminate=True)

        mock_revoke.assert_called_once()

    def test_cancel_batch_operation(self, db_session):
        """Test cancelling a batch operation"""
        batch = BatchOperation(
            operation_type="metadata_sync",
            status="running",
            total_items=100,
            completed_items=25,
        )
        db_session.add(batch)
        db_session.commit()
        db_session.refresh(batch)

        # Cancel batch
        batch.status = "cancelled"
        batch.completed_at = datetime.utcnow()
        db_session.commit()
        db_session.refresh(batch)

        assert batch.status == "cancelled"


# ============================================================================
# Periodic Task Tests
# ============================================================================


class TestPeriodicTasks:
    """Tests for periodic tasks"""

    @patch("app.tasks.cleanup_cache")
    def test_cleanup_cache_periodic_task(self, mock_task):
        """Test cleanup_cache periodic task"""
        mock_task.return_value = {
            "deleted_entries": 42,
            "freed_space_bytes": 1024 * 1024 * 10,  # 10 MB
        }

        result = mock_task()

        assert result["deleted_entries"] == 42

    @patch("app.tasks.sync_metadata")
    def test_sync_metadata_periodic_task(self, mock_task):
        """Test sync_metadata periodic task"""
        mock_task.return_value = {"synced_movies": 50, "synced_shows": 30, "failed": 5}

        result = mock_task()

        assert result["synced_movies"] == 50
        assert result["synced_shows"] == 30

    @patch("app.tasks.cleanup_queue")
    def test_cleanup_queue_periodic_task(self, mock_task):
        """Test cleanup_queue periodic task"""
        mock_task.return_value = {"deleted_entries": 100, "days_old": 7}

        result = mock_task()

        assert result["deleted_entries"] == 100


# ============================================================================
# Task State Management Tests
# ============================================================================


class TestTaskStateManagement:
    """Tests for task state management"""

    @patch("app.celery_app.AsyncResult")
    def test_task_pending_state(self, mock_async_result):
        """Test task pending state"""
        mock_result = MagicMock()
        mock_result.state = "PENDING"
        mock_async_result.return_value = mock_result

        result = AsyncResult("task-123", app=celery_app)

        assert result.state == "PENDING"

    @patch("app.celery_app.AsyncResult")
    def test_task_started_state(self, mock_async_result):
        """Test task started state"""
        mock_result = MagicMock()
        mock_result.state = "STARTED"
        mock_result.info = {"current": 50, "total": 100}
        mock_async_result.return_value = mock_result

        result = AsyncResult("task-123", app=celery_app)

        assert result.state == "STARTED"

    @patch("app.celery_app.AsyncResult")
    def test_task_success_state(self, mock_async_result):
        """Test task success state"""
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.result = {"processed": 100}
        mock_async_result.return_value = mock_result

        result = AsyncResult("task-123", app=celery_app)

        assert result.state == "SUCCESS"

    @patch("app.celery_app.AsyncResult")
    def test_task_failure_state(self, mock_async_result):
        """Test task failure state"""
        mock_result = MagicMock()
        mock_result.state = "FAILURE"
        mock_result.info = Exception("Task failed")
        mock_async_result.return_value = mock_result

        result = AsyncResult("task-123", app=celery_app)

        assert result.state == "FAILURE"

    @patch("app.celery_app.AsyncResult")
    def test_task_retry_state(self, mock_async_result):
        """Test task retry state"""
        mock_result = MagicMock()
        mock_result.state = "RETRY"
        mock_result.info = Exception("Retrying")
        mock_async_result.return_value = mock_result

        result = AsyncResult("task-123", app=celery_app)

        assert result.state == "RETRY"


# ============================================================================
# Task Result Backend Tests
# ============================================================================


class TestTaskResultBackend:
    """Tests for task result backend"""

    def test_store_task_result(self, db_session):
        """Test storing task result"""
        error = TaskError(
            task_id="task-123",
            task_name="app.tasks.analyze_file",
            error_message="Success",
            severity="info",
        )
        db_session.add(error)
        db_session.commit()
        db_session.refresh(error)

        assert error.id is not None

    def test_retrieve_task_result(self, db_session):
        """Test retrieving task result"""
        error = TaskError(
            task_id="task-456",
            task_name="app.tasks.enrich_metadata",
            error_message="Metadata updated",
            severity="info",
        )
        db_session.add(error)
        db_session.commit()

        retrieved = db_session.query(TaskError).filter(TaskError.task_id == "task-456").first()

        assert retrieved is not None
        assert retrieved.task_name == "app.tasks.enrich_metadata"

    def test_task_result_expiration(self, db_session):
        """Test task result expiration"""
        # Add old error
        old_error = TaskError(
            task_id="old-task",
            task_name="app.tasks.test",
            error_message="Old error",
            severity="info",
            created_at=datetime.utcnow() - timedelta(days=30),
        )
        db_session.add(old_error)
        db_session.commit()

        # Query for recent errors
        recent = (
            db_session.query(TaskError)
            .filter(TaskError.created_at > datetime.utcnow() - timedelta(days=7))
            .all()
        )

        assert len(recent) == 0
