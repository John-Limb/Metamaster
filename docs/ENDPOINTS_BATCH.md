# Batch Operations Endpoints Documentation

## Overview

The Batch Operations API provides endpoints for performing bulk operations on media items. These endpoints allow you to start, monitor, and manage batch operations like metadata synchronization and file imports.

**Base URL:** `/api/tasks/batch`

---

## Table of Contents

1. [Start Metadata Sync Batch](#start-metadata-sync-batch)
2. [Start File Import Batch](#start-file-import-batch)
3. [Get Batch Operation Status](#get-batch-operation-status)
4. [Get Batch Progress](#get-batch-progress)
5. [Cancel Batch Operation](#cancel-batch-operation)

---

## Start Metadata Sync Batch

Start a bulk metadata synchronization operation for multiple movies or TV shows.

### Endpoint

```
POST /api/tasks/batch/metadata-sync
```

### Request Body

```json
{
  "operation_type": "metadata_sync",
  "media_ids": [1, 2, 3, 4, 5],
  "media_type": "movie"
}
```

### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `operation_type` | string | Yes | Must be "metadata_sync" |
| `media_ids` | array | Yes | List of movie or TV show IDs to sync |
| `media_type` | string | Yes | Type of media: "movie" or "tv_show" |

### Request Example

```bash
curl -X POST "http://localhost:8000/api/tasks/batch/metadata-sync" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "metadata_sync",
    "media_ids": [1, 2, 3, 4, 5],
    "media_type": "movie"
  }'
```

### Response (200 OK)

```json
{
  "id": 1,
  "operation_type": "metadata_sync",
  "status": "pending",
  "total_items": 5,
  "processed_items": 0,
  "failed_items": 0,
  "metadata": {
    "media_type": "movie"
  },
  "created_at": "2026-02-07T14:11:14.391Z",
  "updated_at": "2026-02-07T14:11:14.391Z"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Batch operation ID |
| `operation_type` | string | Type of operation |
| `status` | string | Current status (pending, running, completed, failed) |
| `total_items` | integer | Total items to process |
| `processed_items` | integer | Items successfully processed |
| `failed_items` | integer | Items that failed |
| `metadata` | object | Operation metadata |
| `created_at` | string | ISO 8601 creation timestamp |
| `updated_at` | string | ISO 8601 last update timestamp |

### Error Responses

**400 Bad Request** - Invalid operation type:
```json
{
  "detail": "Invalid operation_type for metadata sync endpoint",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

**400 Bad Request** - Empty media IDs:
```json
{
  "detail": "media_ids list cannot be empty",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

**400 Bad Request** - Invalid media type:
```json
{
  "detail": "media_type must be 'movie' or 'tv_show'",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

**500 Internal Server Error** - Failed to start batch:
```json
{
  "detail": "Error starting metadata sync batch: Database connection failed",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

### Requirements

- All media IDs must exist in the database
- Media items must have external IDs (OMDB ID for movies, TVDB ID for TV shows)
- External APIs (OMDB/TVDB) must be accessible

### Side Effects

- Batch operation record is created in database
- Async task is queued for processing
- Cache is invalidated for affected items

---

## Start File Import Batch

Start a bulk file import operation for multiple media files.

### Endpoint

```
POST /api/tasks/batch/file-import
```

### Request Body

```json
{
  "operation_type": "file_import",
  "file_paths": [
    "/media/movies/movie1.mp4",
    "/media/movies/movie2.mkv",
    "/media/tv/show1/s01e01.mp4"
  ],
  "media_type": "movie"
}
```

### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `operation_type` | string | Yes | Must be "file_import" |
| `file_paths` | array | Yes | List of file paths to import |
| `media_type` | string | Yes | Type of media: "movie" or "tv_show" |

### Request Example

```bash
curl -X POST "http://localhost:8000/api/tasks/batch/file-import" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "file_import",
    "file_paths": [
      "/media/movies/movie1.mp4",
      "/media/movies/movie2.mkv"
    ],
    "media_type": "movie"
  }'
```

### Response (200 OK)

```json
{
  "id": 2,
  "operation_type": "file_import",
  "status": "pending",
  "total_items": 2,
  "processed_items": 0,
  "failed_items": 0,
  "metadata": {
    "media_type": "movie"
  },
  "created_at": "2026-02-07T14:11:14.391Z",
  "updated_at": "2026-02-07T14:11:14.391Z"
}
```

### Response Fields

Same as metadata sync batch response.

### Error Responses

**400 Bad Request** - Invalid operation type:
```json
{
  "detail": "Invalid operation_type for file import endpoint",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

**400 Bad Request** - Empty file paths:
```json
{
  "detail": "file_paths list cannot be empty",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

**400 Bad Request** - Invalid media type:
```json
{
  "detail": "media_type must be 'movie' or 'tv_show'",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

**500 Internal Server Error** - Failed to start batch:
```json
{
  "detail": "Error starting file import batch: Database connection failed",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

### Requirements

- All file paths must be accessible
- Files must be in supported formats (mp4, mkv, avi, mov, etc.)
- Sufficient disk space must be available
- File monitor service must be running

### Side Effects

- Batch operation record is created in database
- Async task is queued for processing
- Files are analyzed and imported

---

## Get Batch Operation Status

Retrieve the current status of a batch operation.

### Endpoint

```
GET /api/tasks/batch/{batch_id}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `batch_id` | integer | Batch operation ID |

### Request Example

```bash
curl -X GET "http://localhost:8000/api/tasks/batch/1"
```

### Response (200 OK)

```json
{
  "id": 1,
  "operation_type": "metadata_sync",
  "status": "running",
  "total_items": 5,
  "processed_items": 3,
  "failed_items": 0,
  "metadata": {
    "media_type": "movie"
  },
  "created_at": "2026-02-07T14:11:14.391Z",
  "updated_at": "2026-02-07T14:12:00.000Z"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Batch operation ID |
| `operation_type` | string | Type of operation |
| `status` | string | Current status |
| `total_items` | integer | Total items to process |
| `processed_items` | integer | Items successfully processed |
| `failed_items` | integer | Items that failed |
| `metadata` | object | Operation metadata |
| `created_at` | string | ISO 8601 creation timestamp |
| `updated_at` | string | ISO 8601 last update timestamp |

### Batch Statuses

| Status | Description |
|--------|-------------|
| `pending` | Batch is queued and waiting to start |
| `running` | Batch is currently processing |
| `completed` | Batch completed successfully |
| `failed` | Batch failed with errors |
| `cancelled` | Batch was cancelled by user |

### Error Responses

**404 Not Found** - Batch operation not found:
```json
{
  "detail": "Batch operation not found: 999",
  "status": "error",
  "error_code": "NOT_FOUND"
}
```

**500 Internal Server Error** - Failed to fetch status:
```json
{
  "detail": "Error fetching batch status: Database connection failed",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

---

## Get Batch Progress

Retrieve detailed progress information for a batch operation.

### Endpoint

```
GET /api/tasks/batch/{batch_id}/progress
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `batch_id` | integer | Batch operation ID |

### Request Example

```bash
curl -X GET "http://localhost:8000/api/tasks/batch/1/progress"
```

### Response (200 OK)

```json
{
  "batch_id": 1,
  "operation_type": "metadata_sync",
  "status": "running",
  "progress_percent": 60,
  "total_items": 5,
  "processed_items": 3,
  "failed_items": 0,
  "pending_items": 2,
  "estimated_time_remaining_seconds": 45,
  "items": [
    {
      "item_id": 1,
      "status": "completed",
      "result": {
        "updated_fields": ["title", "rating"]
      },
      "error": null
    },
    {
      "item_id": 2,
      "status": "completed",
      "result": {
        "updated_fields": ["plot"]
      },
      "error": null
    },
    {
      "item_id": 3,
      "status": "in_progress",
      "result": null,
      "error": null
    }
  ],
  "created_at": "2026-02-07T14:11:14.391Z",
  "updated_at": "2026-02-07T14:12:00.000Z"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `batch_id` | integer | Batch operation ID |
| `operation_type` | string | Type of operation |
| `status` | string | Current status |
| `progress_percent` | float | Progress percentage (0-100) |
| `total_items` | integer | Total items to process |
| `processed_items` | integer | Items successfully processed |
| `failed_items` | integer | Items that failed |
| `pending_items` | integer | Items waiting to be processed |
| `estimated_time_remaining_seconds` | integer | Estimated time remaining |
| `items` | array | Detailed item progress |
| `created_at` | string | ISO 8601 creation timestamp |
| `updated_at` | string | ISO 8601 last update timestamp |

### Item Status Values

| Status | Description |
|--------|-------------|
| `pending` | Item is queued |
| `in_progress` | Item is being processed |
| `completed` | Item processed successfully |
| `failed` | Item processing failed |
| `skipped` | Item was skipped |

### Error Responses

**404 Not Found** - Batch operation not found:
```json
{
  "detail": "Batch operation not found: 999",
  "status": "error",
  "error_code": "NOT_FOUND"
}
```

**500 Internal Server Error** - Failed to fetch progress:
```json
{
  "detail": "Error fetching batch progress: Database connection failed",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

---

## Cancel Batch Operation

Cancel a batch operation that is pending or running.

### Endpoint

```
DELETE /api/tasks/batch/{batch_id}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `batch_id` | integer | Batch operation ID |

### Request Example

```bash
curl -X DELETE "http://localhost:8000/api/tasks/batch/1"
```

### Response (200 OK)

```json
{
  "success": true,
  "message": "Batch operation cancelled successfully",
  "batch_id": 1,
  "processed_items": 3,
  "remaining_items": 2
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether cancellation was successful |
| `message` | string | Operation message |
| `batch_id` | integer | Batch operation ID |
| `processed_items` | integer | Items already processed |
| `remaining_items` | integer | Items that were not processed |

### Error Responses

**400 Bad Request** - Batch cannot be cancelled:
```json
{
  "detail": "Batch operation cannot be cancelled. Current status: completed",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

**404 Not Found** - Batch operation not found:
```json
{
  "detail": "Batch operation not found: 999",
  "status": "error",
  "error_code": "NOT_FOUND"
}
```

**500 Internal Server Error** - Failed to cancel:
```json
{
  "detail": "Error cancelling batch: Database connection failed",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

### Requirements

- Batch must be in PENDING or RUNNING state
- Celery workers must be running

### Side Effects

- Batch operation is marked as cancelled
- Running tasks are terminated
- Processed items are retained
- Remaining items are not processed

---

## Common Workflows

### Workflow 1: Sync Metadata for Multiple Movies

```bash
# 1. Start metadata sync batch
BATCH_ID=$(curl -X POST "http://localhost:8000/api/tasks/batch/metadata-sync" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "metadata_sync",
    "media_ids": [1, 2, 3, 4, 5],
    "media_type": "movie"
  }' | jq -r '.id')

# 2. Monitor progress
curl -X GET "http://localhost:8000/api/tasks/batch/$BATCH_ID/progress"

# 3. Wait for completion
# Repeat step 2 until status is "completed" or "failed"
```

### Workflow 2: Import Multiple Files

```bash
# 1. Start file import batch
BATCH_ID=$(curl -X POST "http://localhost:8000/api/tasks/batch/file-import" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "file_import",
    "file_paths": [
      "/media/movies/movie1.mp4",
      "/media/movies/movie2.mkv"
    ],
    "media_type": "movie"
  }' | jq -r '.id')

# 2. Check status
curl -X GET "http://localhost:8000/api/tasks/batch/$BATCH_ID"

# 3. Get detailed progress
curl -X GET "http://localhost:8000/api/tasks/batch/$BATCH_ID/progress"
```

### Workflow 3: Cancel Long-Running Batch

```bash
# 1. Get batch status
curl -X GET "http://localhost:8000/api/tasks/batch/1"

# 2. If still running, cancel it
curl -X DELETE "http://localhost:8000/api/tasks/batch/1"

# 3. Verify cancellation
curl -X GET "http://localhost:8000/api/tasks/batch/1"
```

### Workflow 4: Handle Batch Failures

```bash
# 1. Get batch progress
curl -X GET "http://localhost:8000/api/tasks/batch/1/progress"

# 2. Review failed items
# Check items with status "failed"

# 3. Retry failed items
# Create new batch with only failed item IDs
curl -X POST "http://localhost:8000/api/tasks/batch/metadata-sync" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "metadata_sync",
    "media_ids": [3],
    "media_type": "movie"
  }'
```

---

## Performance Considerations

### Batch Size Recommendations

| Operation | Recommended Size | Max Size |
|-----------|------------------|----------|
| Metadata Sync | 50-100 items | 1000 items |
| File Import | 10-20 items | 100 items |

### Processing Time Estimates

- **Metadata Sync**: ~1-2 seconds per item
- **File Import**: ~5-10 seconds per item

### Resource Usage

- Each batch operation uses one Celery worker
- Monitor worker availability before starting large batches
- Consider scheduling batches during off-peak hours

---

## Related Documentation

- [API Reference](./API_REFERENCE.md)
- [Task Monitoring Endpoints](./ENDPOINTS_TASKS.md)
- [Error Reference](./API_ERRORS.md)
- [API Client Examples](./API_CLIENT_EXAMPLES.md)
