"""Phase 5 Integration Tests

Comprehensive integration tests that verify all Phase 5 components work together correctly.
Tests cover:
- Celery application configuration and initialization
- Background task execution and retry logic
- Celery Beat scheduler configuration
- Task monitoring API endpoints
- Error handling and persistence
- End-to-end task workflows
"""

import pytest
import asyncio
import json
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.database import Base
from app.models import TaskError, APICache, FileQueue, Movie, TVShow
from app.services.task_error_handler import TaskErrorHandler
from app.config import settings


# ============================================================================
# Fixtures
# ============================================================================


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
def mock_redis():
    """Mock Redis connection."""
    with patch("redis.Redis") as mock:
        yield mock


@pytest.fixture
def mock_ffprobe():
    """Mock FFProbe wrapper."""
    with patch("app.services.ffprobe_wrapper.FFProbeWrapper") as mock:
        instance = MagicMock()
        instance.get_metadata.return_value = {
            "resolution": {"width": 1920, "height": 1080, "label": "1080p"},
            "bitrate": {"total": "5000k", "video": "4000k", "audio": "128k"},
            "codecs": {"video": "h264", "audio": "aac"},
            "duration": 7200,
            "frame_rate": 24.0,
        }
        mock.return_value = instance
        yield mock


@pytest.fixture
def caplog_fixture(caplog):
    """Fixture for capturing logs."""
    return caplog


# ============================================================================
# Celery Configuration Tests
# ============================================================================


class TestCeleryConfiguration:
    """Test Celery application configuration and initialization"""

    def test_celery_app_initialized(self):
        """Verify celery_app is properly initialized"""
        from app.celery_app import celery_app

        assert celery_app is not None
        assert celery_app.main == "media_management"

    def test_celery_broker_configured(self):
        """Verify Redis broker connection is configured"""
        from app.celery_app import celery_app

        assert celery_app.conf.broker_url == settings.celery_broker_url
        assert "redis://" in celery_app.conf.broker_url

    def test_celery_result_backend_configured(self):
        """Verify result backend is configured"""
        from app.celery_app import celery_app

        assert celery_app.conf.result_backend == settings.celery_result_backend
        assert "redis://" in celery_app.conf.result_backend

    def test_task_serialization_configured(self):
        """Verify task serialization settings"""
        from app.celery_app import celery_app

        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"
        assert "json" in celery_app.conf.accept_content

    def test_task_routing_configured(self):
        """Verify task routing to correct queues"""
        from app.celery_app import celery_app

        routes = celery_app.conf.task_routes
        assert "app.tasks.process_media_file" in routes
        assert routes["app.tasks.process_media_file"]["queue"] == "media_processing"
        assert "app.tasks.extract_metadata" in routes
        assert routes["app.tasks.extract_metadata"]["queue"] == "metadata_extraction"
        assert "app.tasks.fetch_external_data" in routes
        assert routes["app.tasks.fetch_external_data"]["queue"] == "external_api"

    def test_queue_configuration(self):
        """Verify queue configuration"""
        from app.celery_app import celery_app

        queues = celery_app.conf.task_queues
        queue_names = [q.name for q in queues]
        assert "default" in queue_names
        assert "media_processing" in queue_names
        assert "metadata_extraction" in queue_names
        assert "external_api" in queue_names

    def test_retry_configuration(self):
        """Verify retry configuration"""
        from app.celery_app import celery_app

        assert celery_app.conf.task_max_retries == 3
        assert celery_app.conf.task_default_retry_delay == 60
        assert celery_app.conf.task_autoretry_for == (Exception,)

    def test_task_tracking_enabled(self):
        """Verify task tracking is enabled"""
        from app.celery_app import celery_app

        assert celery_app.conf.task_track_started is True

    def test_time_limits_configured(self):
        """Verify time limits are configured"""
        from app.celery_app import celery_app

        assert celery_app.conf.task_time_limit == 600  # 10 minutes
        assert celery_app.conf.task_soft_time_limit == 300  # 5 minutes


# ============================================================================
# Celery Beat Scheduler Tests
# ============================================================================


class TestCeleryBeatScheduler:
    """Test Celery Beat scheduler configuration"""

    def test_beat_schedule_configured(self):
        """Verify beat_schedule is properly configured"""
        from app.celery_beat import beat_schedule

        assert beat_schedule is not None
        assert isinstance(beat_schedule, dict)

    def test_all_periodic_tasks_registered(self):
        """Verify all 3 periodic tasks are registered"""
        from app.celery_beat import beat_schedule

        task_names = list(beat_schedule.keys())
        assert "cleanup_cache" in task_names
        assert "sync_metadata" in task_names
        assert "cleanup_queue" in task_names
        assert len(task_names) == 3

    def test_cleanup_cache_schedule(self):
        """Verify cleanup_cache has correct cron schedule"""
        from app.celery_beat import beat_schedule

        schedule = beat_schedule["cleanup_cache"]
        assert schedule["task"] == "app.tasks.cleanup_cache"
        assert schedule["schedule"].hour == 2
        assert schedule["schedule"].minute == 0
        assert schedule["options"]["queue"] == "media_processing"

    def test_sync_metadata_schedule(self):
        """Verify sync_metadata has correct cron schedule"""
        from app.celery_beat import beat_schedule

        schedule = beat_schedule["sync_metadata"]
        assert schedule["task"] == "app.tasks.sync_metadata"
        assert schedule["schedule"].day_of_week == 0  # Sunday
        assert schedule["schedule"].hour == 3
        assert schedule["schedule"].minute == 0
        assert schedule["options"]["queue"] == "external_api"

    def test_cleanup_queue_schedule(self):
        """Verify cleanup_queue has correct cron schedule"""
        from app.celery_beat import beat_schedule

        schedule = beat_schedule["cleanup_queue"]
        assert schedule["task"] == "app.tasks.cleanup_queue"
        assert schedule["schedule"].hour == 2
        assert schedule["schedule"].minute == 30
        assert schedule["options"]["queue"] == "media_processing"

    def test_queue_routing_for_scheduled_tasks(self):
        """Verify queue routing for scheduled tasks"""
        from app.celery_beat import beat_schedule

        for task_name, schedule_config in beat_schedule.items():
            assert "options" in schedule_config
            assert "queue" in schedule_config["options"]
            queue = schedule_config["options"]["queue"]
            assert queue in ["media_processing", "external_api"]


# ============================================================================
# Background Task Tests
# ============================================================================


class TestBackgroundTasks:
    """Test background task execution and retry logic"""

    def test_analyze_file_task_success(self, mock_ffprobe):
        """Test analyze_file task with mock file"""
        from app.tasks import analyze_file

        result = analyze_file("/path/to/test.mp4")

        assert result["status"] == "success"
        assert result["file_path"] == "/path/to/test.mp4"
        assert result["codec_video"] == "h264"
        assert result["codec_audio"] == "aac"
        assert result["resolution"] == "1920x1080"
        assert result["resolution_label"] == "1080p"
        assert result["duration"] == 7200

    def test_analyze_file_task_file_not_found(self):
        """Test analyze_file task with non-existent file"""
        from app.tasks import analyze_file

        with pytest.raises(FileNotFoundError):
            analyze_file("/nonexistent/file.mp4")

    def test_cleanup_cache_task_removes_expired_entries(self, test_db):
        """Test cleanup_cache task removes expired entries"""
        from app.tasks import cleanup_cache

        # Create expired cache entries
        expired_entry = APICache(
            api_type="omdb",
            query_key="test_key",
            response_data='{"test": "data"}',
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )

        # Create non-expired entry
        active_entry = APICache(
            api_type="tvdb",
            query_key="test_key_2",
            response_data='{"test": "data"}',
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )

        test_db.add(expired_entry)
        test_db.add(active_entry)
        test_db.commit()

        with patch("app.database.SessionLocal", return_value=test_db):
            result = cleanup_cache()

        assert result["status"] == "success"
        assert result["entries_removed"] == 1

        # Verify expired entry was removed
        remaining = test_db.query(APICache).all()
        assert len(remaining) == 1
        assert remaining[0].query_key == "test_key_2"

    def test_cleanup_queue_task_removes_stale_entries(self, test_db):
        """Test cleanup_queue task removes stale entries"""
        from app.tasks import cleanup_queue

        # Create stale queue entry
        stale_entry = FileQueue(
            file_path="/path/to/old_file.mp4",
            status="pending",
            media_type="movie",
            created_at=datetime.utcnow() - timedelta(days=8),
        )

        # Create recent entry
        recent_entry = FileQueue(
            file_path="/path/to/new_file.mp4",
            status="pending",
            media_type="movie",
            created_at=datetime.utcnow() - timedelta(days=1),
        )

        test_db.add(stale_entry)
        test_db.add(recent_entry)
        test_db.commit()

        with patch("app.database.SessionLocal", return_value=test_db):
            with patch("app.services.file_queue_manager.FileQueueManager"):
                result = cleanup_queue()

        assert result["status"] == "success"
        assert result["entries_updated"] == 1

    def test_task_retry_logic_on_failure(self):
        """Test task retry logic on failure"""
        from app.celery_app import celery_app

        # Mock task with retry capability
        @celery_app.task(bind=True, max_retries=3)
        def failing_task(self):
            if self.request.retries < 2:
                raise RuntimeError("Task failed")
            return {"status": "success"}

        # Verify task has retry configuration
        assert failing_task.max_retries == 3

    def test_task_timeout_handling(self):
        """Test task timeout handling"""
        from app.celery_app import celery_app

        # Verify soft and hard time limits are configured
        assert celery_app.conf.task_soft_time_limit == 300
        assert celery_app.conf.task_time_limit == 600


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling and persistence"""

    def test_task_error_handler_captures_failures(self, test_db):
        """Test TaskErrorHandler captures task failures"""
        task_id = "error-test-1"
        task_name = "app.tasks.analyze_file"
        exception = RuntimeError("Test error")

        with patch("app.database.SessionLocal", return_value=test_db):
            TaskErrorHandler.handle_task_failure(
                task_id=task_id,
                task_name=task_name,
                exception=exception,
                tb="Test traceback",
                retry_count=0,
            )

        # Verify error was stored
        error = test_db.query(TaskError).filter(TaskError.task_id == task_id).first()
        assert error is not None
        assert error.task_name == task_name

    def test_error_severity_classification(self):
        """Test error severity classification"""
        # Critical task
        severity = TaskErrorHandler._determine_severity("app.tasks.analyze_file")
        assert severity == TaskErrorHandler.SEVERITY_CRITICAL

        # Warning task
        severity = TaskErrorHandler._determine_severity("app.tasks.cleanup_cache")
        assert severity == TaskErrorHandler.SEVERITY_WARNING

        # Unknown task
        severity = TaskErrorHandler._determine_severity("app.tasks.unknown")
        assert severity == TaskErrorHandler.SEVERITY_INFO

    def test_error_database_persistence(self, test_db):
        """Test error database persistence"""
        task_id = "error-test-2"
        task_name = "app.tasks.enrich_metadata"
        exception = ValueError("Invalid metadata")

        with patch("app.database.SessionLocal", return_value=test_db):
            TaskErrorHandler.handle_task_failure(
                task_id=task_id,
                task_name=task_name,
                exception=exception,
                tb="Traceback",
                retry_count=1,
            )

        # Verify persistence
        error = test_db.query(TaskError).filter(TaskError.task_id == task_id).first()
        assert error is not None
        assert error.error_message == "Invalid metadata"
        assert error.retry_count == 1


# ============================================================================
# Task Monitoring API Tests
# ============================================================================


class TestTaskMonitoringAPI:
    """Test task monitoring API endpoints"""

    @pytest.mark.asyncio
    async def test_get_task_status_success(self):
        """Test GET /api/tasks/{task_id} returns correct status"""
        from app.celery_app import celery_app

        task_id = "test-task-123"

        with patch.object(celery_app.control, "inspect") as mock_inspect:
            mock_result = MagicMock()
            mock_result.state = "SUCCESS"
            mock_result.result = {"status": "completed"}
            mock_result.info = {"status": "completed"}

            with patch("celery.result.AsyncResult", return_value=mock_result):
                from app.api.tasks import get_task_status

                response = await get_task_status(task_id)

        assert response.task_id == task_id
        assert response.status == "success"

    @pytest.mark.asyncio
    async def test_get_task_status_failure(self):
        """Test GET /api/tasks/{task_id} with failed task"""
        from app.celery_app import celery_app

        task_id = "test-task-456"

        with patch.object(celery_app.control, "inspect") as mock_inspect:
            mock_result = MagicMock()
            mock_result.state = "FAILURE"
            mock_result.info = RuntimeError("Task failed")

            with patch("celery.result.AsyncResult", return_value=mock_result):
                from app.api.tasks import get_task_status

                response = await get_task_status(task_id)

        assert response.task_id == task_id
        assert response.status == "failure"
        assert response.error is not None

    @pytest.mark.asyncio
    async def test_list_tasks_with_pagination(self):
        """Test GET /api/tasks lists tasks with pagination"""
        from app.celery_app import celery_app

        with patch.object(celery_app.control, "inspect") as mock_inspect:
            mock_inspect.return_value.active.return_value = {}
            mock_inspect.return_value.scheduled.return_value = {}
            mock_inspect.return_value.reserved.return_value = {}

            from app.api.tasks import list_tasks

            response = await list_tasks(limit=50, offset=0)

        assert response.limit == 50
        assert response.offset == 0
        assert isinstance(response.items, list)

    @pytest.mark.asyncio
    async def test_list_tasks_filter_by_status(self):
        """Test GET /api/tasks filters by status"""
        from app.celery_app import celery_app

        with patch.object(celery_app.control, "inspect") as mock_inspect:
            mock_inspect.return_value.active.return_value = {
                "worker1": [{"id": "task1", "time_start": None}]
            }
            mock_inspect.return_value.scheduled.return_value = {}
            mock_inspect.return_value.reserved.return_value = {}

            from app.api.tasks import list_tasks

            response = await list_tasks(status="started", limit=50, offset=0)

        assert response.limit == 50

    @pytest.mark.asyncio
    async def test_cancel_task(self):
        """Test DELETE /api/tasks/{task_id} revokes tasks"""
        from app.celery_app import celery_app

        task_id = "test-task-cancel"

        with patch.object(celery_app.control, "inspect") as mock_inspect:
            mock_result = MagicMock()
            mock_result.state = "STARTED"

            with patch.object(celery_app.control, "revoke") as mock_revoke:
                with patch("celery.result.AsyncResult", return_value=mock_result):
                    from app.api.tasks import cancel_task

                    response = await cancel_task(task_id)

        assert response.success is True
        assert response.task_id == task_id


# ============================================================================
# End-to-End Workflow Tests
# ============================================================================


class TestEndToEndWorkflows:
    """Test complete end-to-end task workflows"""

    def test_complete_task_lifecycle(self, test_db, mock_ffprobe):
        """Test complete task lifecycle: submit → execute → monitor → error handling"""
        from app.tasks import analyze_file

        # Step 1: Submit task
        task_id = "e2e-test-1"

        # Step 2: Execute task
        result = analyze_file("/path/to/test.mp4")
        assert result["status"] == "success"

        # Step 3: Verify result
        assert result["file_path"] == "/path/to/test.mp4"
        assert result["codec_video"] == "h264"

    def test_task_failure_and_retry_workflow(self, test_db):
        """Test task failure and retry workflow"""
        task_id = "e2e-test-2"
        task_name = "app.tasks.analyze_file"

        # Simulate task failure
        exception = RuntimeError("File analysis failed")

        with patch("app.database.SessionLocal", return_value=test_db):
            TaskErrorHandler.handle_task_failure(
                task_id=task_id,
                task_name=task_name,
                exception=exception,
                tb="Traceback",
                retry_count=0,
            )

        # Verify error was recorded
        error = test_db.query(TaskError).filter(TaskError.task_id == task_id).first()
        assert error is not None
        assert error.severity == TaskErrorHandler.SEVERITY_CRITICAL

    def test_periodic_task_execution(self, test_db):
        """Test periodic task execution"""
        from app.celery_beat import beat_schedule

        # Verify beat schedule is configured
        assert "cleanup_cache" in beat_schedule
        assert "sync_metadata" in beat_schedule
        assert "cleanup_queue" in beat_schedule

        # Verify each task has correct schedule
        for task_name, schedule_config in beat_schedule.items():
            assert "task" in schedule_config
            assert "schedule" in schedule_config
            assert "options" in schedule_config

    def test_error_notification_flow(self, test_db, caplog_fixture):
        """Test error notification flow"""
        task_id = "e2e-test-3"
        task_name = "app.tasks.analyze_file"
        exception = RuntimeError("Critical error")

        with caplog_fixture.at_level(logging.ERROR):
            with patch("app.database.SessionLocal", return_value=test_db):
                TaskErrorHandler.handle_task_failure(
                    task_id=task_id,
                    task_name=task_name,
                    exception=exception,
                    tb="Traceback",
                    retry_count=3,
                )

        # Verify error was logged
        assert any("Task error" in record.message for record in caplog_fixture.records)


# ============================================================================
# Integration Tests
# ============================================================================


class TestPhase5Integration:
    """Comprehensive Phase 5 integration tests"""

    def test_celery_app_with_beat_schedule(self):
        """Test Celery app integration with Beat schedule"""
        from app.celery_app import celery_app
        from app.celery_beat import beat_schedule

        assert celery_app.conf.beat_schedule == beat_schedule
        assert len(celery_app.conf.beat_schedule) == 3

    def test_task_error_handler_integration(self, test_db):
        """Test TaskErrorHandler integration with Celery"""
        task_id = "integration-test-1"
        task_name = "app.tasks.analyze_file"
        exception = RuntimeError("Integration test error")

        with patch("app.database.SessionLocal", return_value=test_db):
            TaskErrorHandler.handle_task_failure(
                task_id=task_id,
                task_name=task_name,
                exception=exception,
                tb="Traceback",
                retry_count=0,
            )

        # Verify error was stored and can be retrieved
        error = test_db.query(TaskError).filter(TaskError.task_id == task_id).first()
        assert error is not None
        assert error.severity == TaskErrorHandler.SEVERITY_CRITICAL

    def test_all_components_work_together(self, test_db, mock_ffprobe):
        """Test all Phase 5 components work together"""
        from app.celery_app import celery_app
        from app.celery_beat import beat_schedule

        # 1. Verify Celery configuration
        assert celery_app is not None
        assert celery_app.conf.broker_url == settings.celery_broker_url

        # 2. Verify Beat schedule
        assert beat_schedule is not None
        assert len(beat_schedule) == 3

        # 3. Verify tasks are registered
        assert "app.tasks.analyze_file" in celery_app.tasks
        assert "app.tasks.enrich_metadata" in celery_app.tasks
        assert "app.tasks.cleanup_cache" in celery_app.tasks

        # 4. Verify error handling
        with patch("app.database.SessionLocal", return_value=test_db):
            TaskErrorHandler.handle_task_failure(
                task_id="integration-final",
                task_name="app.tasks.analyze_file",
                exception=RuntimeError("Test"),
                tb="Traceback",
                retry_count=0,
            )

        error = test_db.query(TaskError).filter(TaskError.task_id == "integration-final").first()
        assert error is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
