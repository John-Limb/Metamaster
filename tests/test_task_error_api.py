"""Tests for task error API endpoints"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from app.main import app
from app.services.task_error_handler import TaskErrorHandler
from app.database import SessionLocal
from app.models import TaskError


client = TestClient(app)


class TestTaskErrorEndpoints:
    """Test suite for task error API endpoints"""

    def setup_method(self):
        """Setup test data before each test"""
        # Create test errors
        self.test_errors = []
        for i in range(5):
            task_id = f"test-api-{i}"
            task_name = "app.tasks.analyze_file" if i < 3 else "app.tasks.cleanup_cache"
            exception = RuntimeError(f"API test error {i}")

            TaskErrorHandler.handle_task_failure(
                task_id=task_id,
                task_name=task_name,
                exception=exception,
                tb="API test traceback",
                retry_count=i,
            )
            self.test_errors.append(task_id)

    def test_list_task_errors(self):
        """Test listing task errors"""
        response = client.get("/api/tasks/errors")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

        assert data["total"] >= 5
        assert len(data["items"]) >= 5
        assert data["limit"] == 50
        assert data["offset"] == 0

    def test_list_task_errors_with_severity_filter(self):
        """Test listing task errors with severity filter"""
        response = client.get("/api/tasks/errors?severity=critical")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert data["total"] >= 3

        # Verify all items have critical severity
        for item in data["items"]:
            assert item["severity"] == "critical"

    def test_list_task_errors_with_pagination(self):
        """Test listing task errors with pagination"""
        # Get first page
        response1 = client.get("/api/tasks/errors?limit=2&offset=0")
        assert response1.status_code == 200
        data1 = response1.json()

        assert len(data1["items"]) == 2
        assert data1["limit"] == 2
        assert data1["offset"] == 0

        # Get second page
        response2 = client.get("/api/tasks/errors?limit=2&offset=2")
        assert response2.status_code == 200
        data2 = response2.json()

        assert len(data2["items"]) == 2
        assert data2["limit"] == 2
        assert data2["offset"] == 2

        # Verify pages are different
        page1_ids = {item["task_id"] for item in data1["items"]}
        page2_ids = {item["task_id"] for item in data2["items"]}
        assert page1_ids.isdisjoint(page2_ids)

    def test_list_task_errors_invalid_severity(self):
        """Test listing task errors with invalid severity"""
        response = client.get("/api/tasks/errors?severity=invalid")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid severity" in data["detail"]

    def test_list_task_errors_invalid_limit(self):
        """Test listing task errors with invalid limit"""
        response = client.get("/api/tasks/errors?limit=101")

        assert response.status_code == 422  # Validation error

    def test_get_task_error_by_id(self):
        """Test getting a specific task error by ID"""
        # Get first error ID
        db = SessionLocal()
        try:
            error = (
                db.query(TaskError)
                .filter(TaskError.task_id == self.test_errors[0])
                .first()
            )
            assert error is not None
            error_id = error.id
        finally:
            db.close()

        # Get error via API
        response = client.get(f"/api/tasks/errors/{error_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == error_id
        assert data["task_id"] == self.test_errors[0]
        assert data["task_name"] == "app.tasks.analyze_file"
        assert data["error_message"] == "API test error 0"
        assert data["severity"] == "critical"
        assert data["retry_count"] == 0
        assert data["created_at"] is not None
        assert data["resolved_at"] is None

    def test_get_task_error_not_found(self):
        """Test getting a non-existent task error"""
        response = client.get("/api/tasks/errors/99999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_task_error_response_schema(self):
        """Test that task error response matches schema"""
        response = client.get("/api/tasks/errors?limit=1")

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) > 0
        error = data["items"][0]

        # Verify all required fields are present
        required_fields = [
            "id",
            "task_id",
            "task_name",
            "error_message",
            "severity",
            "retry_count",
            "created_at",
        ]
        for field in required_fields:
            assert field in error
            assert error[field] is not None

    def test_task_error_with_traceback(self):
        """Test that task error includes traceback"""
        # Get first error ID
        db = SessionLocal()
        try:
            error = (
                db.query(TaskError)
                .filter(TaskError.task_id == self.test_errors[0])
                .first()
            )
            assert error is not None
            error_id = error.id
        finally:
            db.close()

        # Get error via API
        response = client.get(f"/api/tasks/errors/{error_id}")

        assert response.status_code == 200
        data = response.json()

        # Traceback should be present
        assert "error_traceback" in data
        assert data["error_traceback"] is not None

    def test_list_errors_ordering(self):
        """Test that errors are ordered by creation time (newest first)"""
        response = client.get("/api/tasks/errors?limit=10")

        assert response.status_code == 200
        data = response.json()

        items = data["items"]
        if len(items) > 1:
            # Verify items are ordered by created_at descending
            for i in range(len(items) - 1):
                current_time = datetime.fromisoformat(
                    items[i]["created_at"].replace("Z", "+00:00")
                )
                next_time = datetime.fromisoformat(
                    items[i + 1]["created_at"].replace("Z", "+00:00")
                )
                assert current_time >= next_time


class TestTaskErrorIntegration:
    """Integration tests for task error endpoints"""

    def test_error_creation_and_retrieval(self):
        """Test creating an error and retrieving it via API"""
        task_id = "integration-test-123"
        task_name = "app.tasks.analyze_file"
        exception = RuntimeError("Integration test error")

        # Create error
        TaskErrorHandler.handle_task_failure(
            task_id=task_id,
            task_name=task_name,
            exception=exception,
            tb="Integration test traceback",
            retry_count=0,
        )

        # Get error via API
        response = client.get("/api/tasks/errors?limit=1")
        assert response.status_code == 200
        data = response.json()

        # Find our error
        found = False
        for item in data["items"]:
            if item["task_id"] == task_id:
                found = True
                assert item["task_name"] == task_name
                assert item["error_message"] == "Integration test error"
                assert item["severity"] == "critical"
                break

        assert found, "Created error not found in API response"

    def test_error_severity_levels(self):
        """Test that different task types have correct severity levels"""
        # Create critical error
        TaskErrorHandler.handle_task_failure(
            task_id="critical-test",
            task_name="app.tasks.analyze_file",
            exception=RuntimeError("Critical error"),
            tb="Traceback",
            retry_count=0,
        )

        # Create warning error
        TaskErrorHandler.handle_task_failure(
            task_id="warning-test",
            task_name="app.tasks.cleanup_cache",
            exception=RuntimeError("Warning error"),
            tb="Traceback",
            retry_count=0,
        )

        # Get critical errors
        response_critical = client.get("/api/tasks/errors?severity=critical")
        assert response_critical.status_code == 200
        critical_data = response_critical.json()

        critical_found = any(
            item["task_id"] == "critical-test" for item in critical_data["items"]
        )
        assert critical_found

        # Get warning errors
        response_warning = client.get("/api/tasks/errors?severity=warning")
        assert response_warning.status_code == 200
        warning_data = response_warning.json()

        warning_found = any(
            item["task_id"] == "warning-test" for item in warning_data["items"]
        )
        assert warning_found


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
