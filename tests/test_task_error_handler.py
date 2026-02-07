"""Tests for task error handling and notifications"""

import pytest
import logging
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from app.services.task_error_handler import TaskErrorHandler
from app.models import TaskError
from app.database import SessionLocal


class TestTaskErrorHandler:
    """Test suite for TaskErrorHandler"""

    def test_determine_severity_critical(self):
        """Test severity determination for critical tasks"""
        severity = TaskErrorHandler._determine_severity("app.tasks.analyze_file")
        assert severity == TaskErrorHandler.SEVERITY_CRITICAL

    def test_determine_severity_warning(self):
        """Test severity determination for warning tasks"""
        severity = TaskErrorHandler._determine_severity("app.tasks.cleanup_cache")
        assert severity == TaskErrorHandler.SEVERITY_WARNING

    def test_determine_severity_info(self):
        """Test severity determination for unknown tasks"""
        severity = TaskErrorHandler._determine_severity("app.tasks.unknown_task")
        assert severity == TaskErrorHandler.SEVERITY_INFO

    def test_handle_task_failure_stores_error(self):
        """Test that handle_task_failure stores error in database"""
        task_id = "test-task-123"
        task_name = "app.tasks.analyze_file"
        exception = RuntimeError("Test error")

        # Call handle_task_failure
        TaskErrorHandler.handle_task_failure(
            task_id=task_id,
            task_name=task_name,
            exception=exception,
            tb="Test traceback",
            retry_count=2,
        )

        # Verify error was stored
        db = SessionLocal()
        try:
            error = db.query(TaskError).filter(TaskError.task_id == task_id).first()
            assert error is not None
            assert error.task_name == task_name
            assert error.error_message == "Test error"
            assert error.severity == TaskErrorHandler.SEVERITY_CRITICAL
            assert error.retry_count == 2
        finally:
            db.close()

    def test_mark_error_resolved(self):
        """Test marking an error as resolved"""
        task_id = "test-task-456"
        task_name = "app.tasks.cleanup_cache"
        exception = RuntimeError("Test error")

        # Create error
        TaskErrorHandler.handle_task_failure(
            task_id=task_id,
            task_name=task_name,
            exception=exception,
            tb="Test traceback",
            retry_count=0,
        )

        # Mark as resolved
        TaskErrorHandler.mark_error_resolved(task_id)

        # Verify error is marked as resolved
        db = SessionLocal()
        try:
            error = db.query(TaskError).filter(TaskError.task_id == task_id).first()
            assert error is not None
            assert error.resolved_at is not None
        finally:
            db.close()

    def test_get_recent_errors(self):
        """Test retrieving recent errors"""
        # Create multiple errors
        for i in range(5):
            task_id = f"test-task-{i}"
            task_name = "app.tasks.analyze_file" if i < 3 else "app.tasks.cleanup_cache"
            exception = RuntimeError(f"Test error {i}")

            TaskErrorHandler.handle_task_failure(
                task_id=task_id,
                task_name=task_name,
                exception=exception,
                tb="Test traceback",
                retry_count=0,
            )

        # Get all errors
        errors, total = TaskErrorHandler.get_recent_errors(limit=10, offset=0)
        assert total >= 5
        assert len(errors) >= 5

        # Get critical errors only
        critical_errors, critical_total = TaskErrorHandler.get_recent_errors(
            severity=TaskErrorHandler.SEVERITY_CRITICAL,
            limit=10,
            offset=0,
        )
        assert critical_total >= 3
        assert all(e.severity == TaskErrorHandler.SEVERITY_CRITICAL for e in critical_errors)

    def test_get_error_by_id(self):
        """Test retrieving a specific error by ID"""
        task_id = "test-task-789"
        task_name = "app.tasks.analyze_file"
        exception = RuntimeError("Test error")

        # Create error
        TaskErrorHandler.handle_task_failure(
            task_id=task_id,
            task_name=task_name,
            exception=exception,
            tb="Test traceback",
            retry_count=1,
        )

        # Get error by ID
        db = SessionLocal()
        try:
            error = db.query(TaskError).filter(TaskError.task_id == task_id).first()
            assert error is not None

            retrieved_error = TaskErrorHandler.get_error_by_id(error.id)
            assert retrieved_error is not None
            assert retrieved_error.task_id == task_id
            assert retrieved_error.task_name == task_name
        finally:
            db.close()

    def test_pagination(self):
        """Test pagination of errors"""
        # Create 10 errors
        for i in range(10):
            task_id = f"test-task-page-{i}"
            task_name = "app.tasks.analyze_file"
            exception = RuntimeError(f"Test error {i}")

            TaskErrorHandler.handle_task_failure(
                task_id=task_id,
                task_name=task_name,
                exception=exception,
                tb="Test traceback",
                retry_count=0,
            )

        # Get first page
        errors_page1, total = TaskErrorHandler.get_recent_errors(limit=5, offset=0)
        assert len(errors_page1) == 5
        assert total >= 10

        # Get second page
        errors_page2, _ = TaskErrorHandler.get_recent_errors(limit=5, offset=5)
        assert len(errors_page2) == 5

        # Verify pages are different
        page1_ids = {e.task_id for e in errors_page1}
        page2_ids = {e.task_id for e in errors_page2}
        assert page1_ids.isdisjoint(page2_ids)

    def test_error_update_on_retry(self):
        """Test that error record is updated on retry"""
        task_id = "test-task-retry"
        task_name = "app.tasks.analyze_file"

        # First failure
        exception1 = RuntimeError("First error")
        TaskErrorHandler.handle_task_failure(
            task_id=task_id,
            task_name=task_name,
            exception=exception1,
            tb="First traceback",
            retry_count=0,
        )

        # Get initial error
        db = SessionLocal()
        try:
            error1 = db.query(TaskError).filter(TaskError.task_id == task_id).first()
            assert error1 is not None
            initial_created_at = error1.created_at
        finally:
            db.close()

        # Second failure (retry)
        exception2 = RuntimeError("Second error")
        TaskErrorHandler.handle_task_failure(
            task_id=task_id,
            task_name=task_name,
            exception=exception2,
            tb="Second traceback",
            retry_count=1,
        )

        # Verify error was updated
        db = SessionLocal()
        try:
            error2 = db.query(TaskError).filter(TaskError.task_id == task_id).first()
            assert error2 is not None
            assert error2.error_message == "Second error"
            assert error2.retry_count == 1
            assert error2.created_at == initial_created_at  # Created at should not change
        finally:
            db.close()


class TestTaskErrorHandlerIntegration:
    """Integration tests for task error handling"""

    def test_error_handler_with_celery_signal(self):
        """Test error handler integration with Celery signals"""
        # This test verifies that the error handler can be called from Celery signals
        task_id = "celery-test-123"
        task_name = "app.tasks.analyze_file"
        exception = RuntimeError("Celery test error")

        # Simulate Celery signal call
        TaskErrorHandler.handle_task_failure(
            task_id=task_id,
            task_name=task_name,
            exception=exception,
            tb="Celery traceback",
            retry_count=3,
        )

        # Verify error was stored
        db = SessionLocal()
        try:
            error = db.query(TaskError).filter(TaskError.task_id == task_id).first()
            assert error is not None
            assert error.severity == TaskErrorHandler.SEVERITY_CRITICAL
        finally:
            db.close()

    def test_error_handler_with_logging(self, caplog):
        """Test that error handler logs appropriately"""
        task_id = "logging-test-123"
        task_name = "app.tasks.analyze_file"
        exception = RuntimeError("Logging test error")

        with caplog.at_level(logging.ERROR):
            TaskErrorHandler.handle_task_failure(
                task_id=task_id,
                task_name=task_name,
                exception=exception,
                tb="Logging traceback",
                retry_count=0,
            )

        # Verify logging occurred
        assert any("Task error" in record.message for record in caplog.records)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
