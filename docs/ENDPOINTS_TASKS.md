# Task Monitoring Endpoints Documentation

## Overview

The Task Monitoring API provides endpoints for tracking background tasks, managing task errors, and monitoring task execution. All endpoints are prefixed with `/api/tasks`.

**Base URL:** `/api/tasks`

---

## Table of Contents

1. [Get Task Status](#get-task-status)
2. [List Tasks](#list-tasks)
3. [Retry Task](#retry-task)
4. [Cancel Task](#cancel-task)
5. [List Task Errors](#list-task-errors)
6. [Get Task Error Details](#get-task-error-details)

---

## Get Task Status

Retrieve the status and result of a specific task.

### Endpoint

```
GET /api/tasks/{task_id}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | string | Celery task ID (UUID format) |

### Request Example

```bash
curl -X GET "http://localhost:8000/api/tasks/550e8400-e29b-41d4-a716-446655440000"
```

### Response (200 OK)

**Pending Task:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "result": null,
  "error": null,
  "created_at": null,
  "updated_at": null
}
```

**Running Task:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "started",
  "result": {
    "processed": 25,
    "total": 100,
    "progress_percent": 25
  },
  "error": null,
  "created_at": "2026-02-07T14:00:00.000Z",
  "updated_at": "2026-02-07T14:05:00.000Z"
}
```

**Completed Task:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "result": {
    "processed": 100,
    "failed": 0,
    "duration_seconds": 45.5
  },
  "error": null,
  "created_at": "2026-02-07T14:00:00.000Z",
  "updated_at": "2026-02-07T14:05:00.000Z"
}
```

**Failed Task:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failure",
  "result": null,
  "error": "Connection timeout while fetching metadata",
  "created_at": "2026-02-07T14:00:00.000Z",
  "updated_at": "2026-02-07T14:05:00.000Z"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Celery task ID |
| `status` | string | Task status (pending, started, success, failure, retry) |
| `result` | object | Task result (null if not completed) |
| `error` | string | Error message (null if successful) |
| `created_at` | string | ISO 8601 creation timestamp |
| `updated_at` | string | ISO 8601 last update timestamp |

### Task Statuses

| Status | Description |
|--------|-------------|
| `pending` | Task is queued and waiting to start |
| `started` | Task is currently executing |
| `success` | Task completed successfully |
| `failure` | Task failed with an error |
| `retry` | Task is being retried after failure |

### Error Responses

**500 Internal Server Error** - Failed to fetch task status:
```json
{
  "detail": "Error fetching task status: Connection refused",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

---

## List Tasks

Retrieve a paginated list of recent tasks with optional filtering by status.

### Endpoint

```
GET /api/tasks
```

### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `status` | string | null | - | Filter by status (pending, started, success, failure, retry) |
| `limit` | integer | 50 | 100 | Items per page |
| `offset` | integer | 0 | - | Offset from start |

### Request Example

```bash
curl -X GET "http://localhost:8000/api/tasks?status=started&limit=20&offset=0"
```

### Response (200 OK)

```json
{
  "items": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "started",
      "created_at": "2026-02-07T14:00:00.000Z",
      "updated_at": "2026-02-07T14:05:00.000Z"
    },
    {
      "task_id": "660e8400-e29b-41d4-a716-446655440001",
      "status": "started",
      "created_at": "2026-02-07T13:55:00.000Z",
      "updated_at": "2026-02-07T14:02:00.000Z"
    }
  ],
  "total": 5,
  "limit": 20,
  "offset": 0
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `items` | array | List of task items |
| `total` | integer | Total number of tasks matching filter |
| `limit` | integer | Items per page |
| `offset` | integer | Offset from start |

### Error Responses

**400 Bad Request** - Invalid status filter:
```json
{
  "detail": "Invalid status. Must be one of: pending, started, success, failure, retry",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

**500 Internal Server Error** - Failed to list tasks:
```json
{
  "detail": "Error listing tasks: Celery connection failed",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

---

## Retry Task

Retry a failed task.

### Endpoint

```
POST /api/tasks/{task_id}/retry
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | string | Celery task ID of failed task |

### Request Example

```bash
curl -X POST "http://localhost:8000/api/tasks/550e8400-e29b-41d4-a716-446655440000/retry"
```

### Response (200 OK)

```json
{
  "success": true,
  "message": "Task retry initiated successfully",
  "original_task_id": "550e8400-e29b-41d4-a716-446655440000",
  "new_task_id": "770e8400-e29b-41d4-a716-446655440002"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether retry was initiated |
| `message` | string | Operation message |
| `original_task_id` | string | Original task ID |
| `new_task_id` | string | New task ID for retry attempt |

### Error Responses

**400 Bad Request** - Task cannot be retried:
```json
{
  "detail": "Task cannot be retried. Current state: SUCCESS. Only failed tasks can be retried.",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

**400 Bad Request** - Task name not available:
```json
{
  "detail": "Cannot retry task: task name not available",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

**500 Internal Server Error** - Failed to retry:
```json
{
  "detail": "Error retrying task: Celery connection failed",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

### Requirements

- Task must be in FAILURE or RETRY state
- Task name must be available in Celery
- Celery workers must be running

---

## Cancel Task

Cancel or revoke a task that is pending or running.

### Endpoint

```
DELETE /api/tasks/{task_id}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | string | Celery task ID |

### Request Example

```bash
curl -X DELETE "http://localhost:8000/api/tasks/550e8400-e29b-41d4-a716-446655440000"
```

### Response (200 OK)

```json
{
  "success": true,
  "message": "Task cancelled successfully",
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether cancellation was successful |
| `message` | string | Operation message |
| `task_id` | string | Task ID that was cancelled |

### Error Responses

**400 Bad Request** - Task cannot be cancelled:
```json
{
  "detail": "Task cannot be cancelled. Current state: SUCCESS. Only pending or running tasks can be cancelled.",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

**500 Internal Server Error** - Failed to cancel:
```json
{
  "detail": "Error cancelling task: Celery connection failed",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

### Requirements

- Task must be in PENDING or STARTED state
- Celery workers must be running

### Side Effects

- Task execution is terminated
- Task is marked as revoked
- Cannot be retried after cancellation

---

## List Task Errors

Retrieve a paginated list of task errors with optional filtering by severity.

### Endpoint

```
GET /api/tasks/errors
```

### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `severity` | string | null | - | Filter by severity (critical, warning, info) |
| `limit` | integer | 50 | 100 | Items per page |
| `offset` | integer | 0 | - | Offset from start |

### Request Example

```bash
curl -X GET "http://localhost:8000/api/tasks/errors?severity=critical&limit=20&offset=0"
```

### Response (200 OK)

```json
{
  "items": [
    {
      "id": 1,
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "task_name": "bulk_metadata_sync_task",
      "error_message": "Connection timeout while fetching metadata",
      "error_type": "TimeoutError",
      "severity": "critical",
      "traceback": "Traceback (most recent call last):\n  File ...",
      "created_at": "2026-02-07T14:00:00.000Z"
    },
    {
      "id": 2,
      "task_id": "660e8400-e29b-41d4-a716-446655440001",
      "task_name": "bulk_file_import_task",
      "error_message": "File not found: /path/to/file.mp4",
      "error_type": "FileNotFoundError",
      "severity": "warning",
      "traceback": "Traceback (most recent call last):\n  File ...",
      "created_at": "2026-02-07T13:55:00.000Z"
    }
  ],
  "total": 15,
  "limit": 20,
  "offset": 0
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `items` | array | List of error objects |
| `total` | integer | Total number of errors matching filter |
| `limit` | integer | Items per page |
| `offset` | integer | Offset from start |

### Error Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Error record ID |
| `task_id` | string | Celery task ID |
| `task_name` | string | Task function name |
| `error_message` | string | Error message |
| `error_type` | string | Exception type |
| `severity` | string | Error severity (critical, warning, info) |
| `traceback` | string | Full Python traceback |
| `created_at` | string | ISO 8601 timestamp |

### Error Responses

**400 Bad Request** - Invalid severity filter:
```json
{
  "detail": "Invalid severity. Must be one of: critical, warning, info",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

**500 Internal Server Error** - Failed to list errors:
```json
{
  "detail": "Error listing task errors: Database connection failed",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

---

## Get Task Error Details

Retrieve detailed information about a specific task error.

### Endpoint

```
GET /api/tasks/errors/{error_id}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `error_id` | integer | Task error record ID |

### Request Example

```bash
curl -X GET "http://localhost:8000/api/tasks/errors/1"
```

### Response (200 OK)

```json
{
  "id": 1,
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_name": "bulk_metadata_sync_task",
  "error_message": "Connection timeout while fetching metadata",
  "error_type": "TimeoutError",
  "severity": "critical",
  "traceback": "Traceback (most recent call last):\n  File \"app/tasks.py\", line 45, in bulk_metadata_sync_task\n    result = await fetch_metadata(item_id)\n  File \"app/services/omdb_service.py\", line 120, in get_movie_details\n    response = await client.get(url, timeout=5)\nTimeoutError: Connection timeout",
  "created_at": "2026-02-07T14:00:00.000Z"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Error record ID |
| `task_id` | string | Celery task ID |
| `task_name` | string | Task function name |
| `error_message` | string | Error message |
| `error_type` | string | Exception type |
| `severity` | string | Error severity |
| `traceback` | string | Full Python traceback |
| `created_at` | string | ISO 8601 timestamp |

### Error Responses

**404 Not Found** - Error not found:
```json
{
  "detail": "Task error not found: 999",
  "status": "error",
  "error_code": "NOT_FOUND"
}
```

**500 Internal Server Error** - Failed to fetch error:
```json
{
  "detail": "Error fetching task error: Database connection failed",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

---

## Common Workflows

### Workflow 1: Monitor Task Progress

```bash
# 1. Start a task (via batch operations endpoint)
curl -X POST "http://localhost:8000/api/tasks/batch/metadata-sync" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "metadata_sync",
    "media_ids": [1, 2, 3],
    "media_type": "movie"
  }'

# 2. Poll task status
curl -X GET "http://localhost:8000/api/tasks/550e8400-e29b-41d4-a716-446655440000"

# 3. Wait for completion
# Repeat step 2 until status is "success" or "failure"
```

### Workflow 2: Handle Failed Task

```bash
# 1. List failed tasks
curl -X GET "http://localhost:8000/api/tasks?status=failure&limit=10"

# 2. Get error details
curl -X GET "http://localhost:8000/api/tasks/errors/1"

# 3. Retry the task
curl -X POST "http://localhost:8000/api/tasks/550e8400-e29b-41d4-a716-446655440000/retry"

# 4. Monitor retry progress
curl -X GET "http://localhost:8000/api/tasks/770e8400-e29b-41d4-a716-446655440002"
```

### Workflow 3: Cancel Long-Running Task

```bash
# 1. List running tasks
curl -X GET "http://localhost:8000/api/tasks?status=started&limit=10"

# 2. Cancel task
curl -X DELETE "http://localhost:8000/api/tasks/550e8400-e29b-41d4-a716-446655440000"

# 3. Verify cancellation
curl -X GET "http://localhost:8000/api/tasks/550e8400-e29b-41d4-a716-446655440000"
```

### Workflow 4: Analyze Task Errors

```bash
# 1. List critical errors
curl -X GET "http://localhost:8000/api/tasks/errors?severity=critical&limit=20"

# 2. Get detailed error information
curl -X GET "http://localhost:8000/api/tasks/errors/1"

# 3. Review traceback for debugging
# Use traceback to identify root cause
```

---

## Error Severity Levels

| Severity | Description | Action |
|----------|-------------|--------|
| `critical` | Task failed completely, requires immediate attention | Investigate and retry |
| `warning` | Task partially failed or encountered issues | Review and monitor |
| `info` | Task completed with informational messages | No action needed |

---

## Task Lifecycle

```
┌─────────────┐
│   PENDING   │ Task is queued
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   STARTED   │ Task is executing
└──────┬──────┘
       │
       ├─────────────────────┐
       │                     │
       ▼                     ▼
┌─────────────┐        ┌─────────────┐
│   SUCCESS   │        │   FAILURE   │
└─────────────┘        └──────┬──────┘
                               │
                               ▼
                        ┌─────────────┐
                        │    RETRY    │
                        └──────┬──────┘
                               │
                               ├─────────────────────┐
                               │                     │
                               ▼                     ▼
                        ┌─────────────┐        ┌─────────────┐
                        │   SUCCESS   │        │   FAILURE   │
                        └─────────────┘        └─────────────┘
```

---

## Related Documentation

- [API Reference](./API_REFERENCE.md)
- [Batch Operations Endpoints](./ENDPOINTS_BATCH.md)
- [Error Reference](./API_ERRORS.md)
- [API Client Examples](./API_CLIENT_EXAMPLES.md)
