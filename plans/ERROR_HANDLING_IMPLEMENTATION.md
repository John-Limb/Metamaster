# Error Handling and Notifications Implementation

## Overview

A comprehensive error handling and notification system has been implemented for failed Celery background tasks. This ensures visibility into task failures and enables proactive issue detection.

## Components Implemented

### 1. Database Model - `TaskError` ([`app/models.py`](app/models.py:169))

Added a new `TaskError` model to track task failures with the following fields:

- `id` (Integer, Primary Key)
- `task_id` (String, indexed) - Celery task ID
- `task_name` (String) - Name of the task
- `error_message` (Text) - Exception message
- `error_traceback` (Text) - Full traceback for debugging
- `severity` (String, indexed) - Error severity level (critical/warning/info)
- `retry_count` (Integer) - Number of retries attempted
- `created_at` (DateTime, indexed) - Error creation timestamp
- `resolved_at` (DateTime, nullable) - When error was resolved

**Indexes:**
- `idx_task_errors_task_id` - For efficient task lookup
- `idx_task_errors_created` - For time-based queries
- `idx_task_errors_severity` - For severity filtering

### 2. Error Handler Service - [`app/services/task_error_handler.py`](app/services/task_error_handler.py)

Implemented `TaskErrorHandler` class with the following methods:

#### Core Methods

- **`handle_task_failure(task_id, task_name, exception, traceback, retry_count)`**
  - Main entry point for handling task failures
  - Logs error, stores in database, and sends notifications
  - Automatically determines severity based on task name

- **`notify_failure(task_id, task_name, error_message, severity)`**
  - Sends notifications for task failures
  - Currently logs to appropriate level (ERROR for critical, WARNING for others)
  - Extensible for email/webhook notifications

- **`log_task_error(task_id, task_name, error_details)`**
  - Structured error logging with full context
  - Includes task ID, name, severity, retry count, and error message

#### Utility Methods

- **`mark_error_resolved(task_id)`** - Mark an error as resolved
- **`get_recent_errors(severity, limit, offset)`** - Retrieve paginated error list
- **`get_error_by_id(error_id)`** - Get specific error details

#### Severity Classification

- **CRITICAL**: Tasks impacting core functionality
  - `app.tasks.analyze_file`
  - `app.tasks.enrich_metadata`

- **WARNING**: Tasks impacting non-critical features
  - `app.tasks.cleanup_cache`
  - `app.tasks.cleanup_queue`

- **INFO**: Other tasks and retries

### 3. Celery Signal Handlers - [`app/celery_app.py`](app/celery_app.py:98)

Registered three Celery signal handlers for task lifecycle events:

#### `task_failure_handler`
- Triggered when a task fails after all retries
- Calls `TaskErrorHandler.handle_task_failure()`
- Logs error with full context

#### `task_retry_handler`
- Triggered when a task is retried due to failure
- Logs retry event for debugging
- Helps track retry patterns

#### `task_revoked_handler`
- Triggered when a task is cancelled/revoked
- Logs revocation reason (terminated, expired, or revoked)
- Tracks task lifecycle events

### 4. Task Integration - [`app/tasks.py`](app/tasks.py)

Updated all Celery tasks to integrate error handling:

#### Critical Tasks (with retries)
- **`analyze_file`** - Calls error handler on final failure
- **`enrich_metadata`** - Calls error handler on final failure

#### Non-Critical Tasks (no retries)
- **`cleanup_cache`** - Calls error handler on any failure
- **`cleanup_queue`** - Calls error handler on any failure
- **`sync_metadata`** - Calls error handler on any failure

Error handling is called only after all retries are exhausted for critical tasks, or immediately for non-critical tasks.

### 5. API Endpoints - [`app/api/tasks.py`](app/api/tasks.py:328)

Added two new endpoints for error monitoring:

#### `GET /api/tasks/errors`
List recent task errors with optional filtering and pagination.

**Query Parameters:**
- `severity` (optional) - Filter by severity (critical/warning/info)
- `limit` (default: 50, max: 100) - Items per page
- `offset` (default: 0) - Pagination offset

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "task_id": "abc123def456",
      "task_name": "app.tasks.analyze_file",
      "error_message": "File not found: /path/to/file.mp4",
      "error_traceback": "Traceback (most recent call last):\n  ...",
      "severity": "critical",
      "retry_count": 3,
      "created_at": "2026-02-07T10:00:00Z",
      "resolved_at": null
    }
  ],
  "total": 10,
  "limit": 50,
  "offset": 0
}
```

#### `GET /api/tasks/errors/{error_id}`
Get detailed information about a specific task error.

**Response:**
```json
{
  "id": 1,
  "task_id": "abc123def456",
  "task_name": "app.tasks.analyze_file",
  "error_message": "File not found: /path/to/file.mp4",
  "error_traceback": "Traceback (most recent call last):\n  ...",
  "severity": "critical",
  "retry_count": 3,
  "created_at": "2026-02-07T10:00:00Z",
  "resolved_at": null
}
```

### 6. Response Schemas - [`app/schemas.py`](app/schemas.py:422)

Added two new Pydantic schemas:

- **`TaskErrorResponse`** - Individual task error details
- **`PaginatedTaskErrorResponse`** - Paginated list of task errors

### 7. Database Migration - [`alembic/versions/001_add_task_error_model.py`](alembic/versions/001_add_task_error_model.py)

Created Alembic migration to create the `task_errors` table with:
- All required columns
- Proper indexes for efficient querying
- Support for upgrade and downgrade

## Error Flow

### When a Task Fails

1. **Task Execution** - Task runs and encounters an exception
2. **Retry Logic** - For critical tasks, Celery retries with exponential backoff
3. **Final Failure** - After max retries exhausted, `task_failure` signal fires
4. **Signal Handler** - `task_failure_handler` is triggered
5. **Error Handler** - `TaskErrorHandler.handle_task_failure()` is called
6. **Processing**:
   - Determines severity based on task name
   - Logs error with full context
   - Stores error in database
   - Sends notification (logs to appropriate level)
7. **Audit Trail** - Error is available for querying via API

### Error Update on Retry

If a task fails multiple times:
1. First failure creates a new `TaskError` record
2. Subsequent failures update the existing record
3. `retry_count` is incremented
4. `error_message` and `error_traceback` are updated
5. `created_at` remains unchanged (original failure time)

## Testing

### Unit Tests - [`tests/test_task_error_handler.py`](tests/test_task_error_handler.py)

Tests for `TaskErrorHandler` class:
- Severity determination for different task types
- Error storage in database
- Error resolution marking
- Pagination and filtering
- Error updates on retry

### Integration Tests - [`tests/test_task_error_api.py`](tests/test_task_error_api.py)

Tests for API endpoints:
- Listing task errors with pagination
- Filtering by severity
- Getting specific error details
- Response schema validation
- Error ordering (newest first)
- Severity level classification

## Usage Examples

### Retrieve Recent Critical Errors

```bash
curl "http://localhost:8000/api/tasks/errors?severity=critical&limit=10"
```

### Get Specific Error Details

```bash
curl "http://localhost:8000/api/tasks/errors/1"
```

### List All Errors with Pagination

```bash
curl "http://localhost:8000/api/tasks/errors?limit=50&offset=0"
```

## Key Features

✅ **Comprehensive Error Tracking** - All task failures are logged with full context
✅ **Severity Classification** - Errors categorized by impact level
✅ **Audit Trail** - Complete history of task failures for debugging
✅ **Pagination Support** - Efficient querying of large error datasets
✅ **Filtering Capabilities** - Filter errors by severity level
✅ **Retry Tracking** - Track number of retries for each failure
✅ **Structured Logging** - Consistent error logging format
✅ **Signal Integration** - Automatic capture of Celery task lifecycle events
✅ **Database Persistence** - Errors stored for long-term analysis
✅ **API Endpoints** - RESTful access to error information

## Future Enhancements

- Email notifications for critical errors
- Webhook integration for external monitoring systems
- Error aggregation and statistics
- Automatic error resolution based on task success
- Error alerting thresholds
- Integration with monitoring/alerting platforms (Sentry, DataDog, etc.)

## No Circular Imports

The implementation carefully avoids circular imports:
- `task_error_handler.py` only imports from `models.py` and `database.py`
- `celery_app.py` imports `task_error_handler` inside signal handlers (lazy import)
- `tasks.py` imports `task_error_handler` at module level (safe, no circular dependency)
- API endpoints import `task_error_handler` at module level (safe)

## Database Session Management

All database operations follow existing patterns:
- `SessionLocal()` is used to create new sessions
- Sessions are properly closed in `finally` blocks
- No session leaks or connection pool exhaustion
- Consistent with existing codebase patterns
