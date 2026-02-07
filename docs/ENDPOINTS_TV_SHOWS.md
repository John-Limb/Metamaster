# TV Show Endpoints Documentation

## Overview

The TV Show API provides comprehensive endpoints for managing TV show records, seasons, and episodes in the media library. All endpoints support filtering, sorting, pagination, and caching for optimal performance.

**Base URL:** `/tv-shows`

---

## Table of Contents

1. [List TV Shows](#list-tv-shows)
2. [Get TV Show Details](#get-tv-show-details)
3. [Get TV Show Seasons](#get-tv-show-seasons)
4. [Get Season Episodes](#get-season-episodes)
5. [Create TV Show](#create-tv-show)
6. [Update TV Show](#update-tv-show)
7. [Delete TV Show](#delete-tv-show)
8. [Sync TV Show Metadata](#sync-tv-show-metadata)

---

## List TV Shows

Retrieve a paginated list of TV shows with advanced filtering and sorting capabilities.

### Endpoint

```
GET /tv-shows
```

### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `genre` | string | null | - | Filter by genre (case-insensitive) |
| `min_rating` | float | null | - | Minimum rating (0-10) |
| `max_rating` | float | null | - | Maximum rating (0-10) |
| `sort_by` | string | "title" | - | Sort field: title, rating, date_added |
| `limit` | integer | 10 | 100 | Items per page |
| `skip` | integer | 0 | - | Offset from start |

### Request Example

```bash
curl -X GET "http://localhost:8000/tv-shows?genre=drama&min_rating=7.5&limit=20&skip=0"
```

### Response (200 OK)

```json
{
  "items": [
    {
      "id": 1,
      "title": "Drama Series",
      "plot": "An engaging drama series about...",
      "rating": 8.2,
      "genres": ["drama", "thriller"],
      "status": "ongoing",
      "tvdb_id": "tt1234567",
      "season_count": 5,
      "episode_count": 52,
      "created_at": "2026-02-07T14:11:14.391Z",
      "updated_at": "2026-02-07T14:11:14.391Z"
    },
    {
      "id": 2,
      "title": "Another Drama",
      "plot": "More dramatic storytelling...",
      "rating": 7.9,
      "genres": ["drama", "mystery"],
      "status": "completed",
      "tvdb_id": "tt2345678",
      "season_count": 3,
      "episode_count": 30,
      "created_at": "2026-02-07T14:11:14.391Z",
      "updated_at": "2026-02-07T14:11:14.391Z"
    }
  ],
  "total": 28,
  "limit": 20,
  "offset": 0,
  "filters": {
    "applied_filters": {
      "genre": "drama",
      "min_rating": 7.5
    },
    "sort_by": "title",
    "total_results": 28
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `items` | array | List of TV show objects |
| `total` | integer | Total number of TV shows matching filters |
| `limit` | integer | Items per page |
| `offset` | integer | Offset from start |
| `filters` | object | Applied filters and sorting information |

### Error Responses

**400 Bad Request** - Invalid filter parameters:
```json
{
  "detail": "Invalid filter parameters",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

### Caching

- **Cache Key**: `tv_shows:list:genre={genre}:min_rating={min_rating}:...`
- **TTL**: 3600 seconds (1 hour)
- **Invalidation**: Cleared when TV shows are created, updated, or deleted

---

## Get TV Show Details

Retrieve detailed information about a specific TV show.

### Endpoint

```
GET /tv-shows/{show_id}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `show_id` | integer | TV show ID |

### Request Example

```bash
curl -X GET "http://localhost:8000/tv-shows/1"
```

### Response (200 OK)

```json
{
  "id": 1,
  "title": "Drama Series",
  "plot": "An engaging drama series about...",
  "rating": 8.2,
  "genres": ["drama", "thriller"],
  "status": "ongoing",
  "tvdb_id": "tt1234567",
  "season_count": 5,
  "episode_count": 52,
  "created_at": "2026-02-07T14:11:14.391Z",
  "updated_at": "2026-02-07T14:11:14.391Z"
}
```

### Error Responses

**404 Not Found** - TV show not found:
```json
{
  "detail": "TV show not found",
  "status": "error",
  "error_code": "NOT_FOUND"
}
```

### Caching

- **Cache Key**: `tv_shows:{show_id}`
- **TTL**: 3600 seconds (1 hour)
- **Invalidation**: Cleared when TV show is updated or deleted

---

## Get TV Show Seasons

Retrieve all seasons for a specific TV show with pagination.

### Endpoint

```
GET /tv-shows/{show_id}/seasons
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `show_id` | integer | TV show ID |

### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `limit` | integer | 10 | 100 | Items per page |
| `offset` | integer | 0 | - | Offset from start |

### Request Example

```bash
curl -X GET "http://localhost:8000/tv-shows/1/seasons?limit=10&offset=0"
```

### Response (200 OK)

```json
{
  "items": [
    {
      "id": 1,
      "season_number": 1,
      "tvdb_id": "season_123",
      "episode_count": 10,
      "created_at": "2026-02-07T14:11:14.391Z"
    },
    {
      "id": 2,
      "season_number": 2,
      "tvdb_id": "season_124",
      "episode_count": 12,
      "created_at": "2026-02-07T14:11:14.391Z"
    },
    {
      "id": 3,
      "season_number": 3,
      "tvdb_id": "season_125",
      "episode_count": 10,
      "created_at": "2026-02-07T14:11:14.391Z"
    }
  ],
  "total": 5,
  "limit": 10,
  "offset": 0
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `items` | array | List of season objects |
| `total` | integer | Total number of seasons |
| `limit` | integer | Items per page |
| `offset` | integer | Offset from start |

### Error Responses

**404 Not Found** - TV show not found:
```json
{
  "detail": "TV show not found",
  "status": "error",
  "error_code": "NOT_FOUND"
}
```

---

## Get Season Episodes

Retrieve all episodes for a specific season with pagination.

### Endpoint

```
GET /tv-shows/{show_id}/seasons/{season_id}/episodes
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `show_id` | integer | TV show ID |
| `season_id` | integer | Season ID |

### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `limit` | integer | 10 | 100 | Items per page |
| `offset` | integer | 0 | - | Offset from start |

### Request Example

```bash
curl -X GET "http://localhost:8000/tv-shows/1/seasons/1/episodes?limit=10&offset=0"
```

### Response (200 OK)

```json
{
  "items": [
    {
      "id": 1,
      "episode_number": 1,
      "season_number": 1,
      "title": "Pilot",
      "plot": "The first episode introduces...",
      "air_date": "2020-01-15",
      "tvdb_id": "episode_001",
      "created_at": "2026-02-07T14:11:14.391Z"
    },
    {
      "id": 2,
      "episode_number": 2,
      "season_number": 1,
      "title": "Episode 2",
      "plot": "The story continues...",
      "air_date": "2020-01-22",
      "tvdb_id": "episode_002",
      "created_at": "2026-02-07T14:11:14.391Z"
    }
  ],
  "total": 10,
  "limit": 10,
  "offset": 0
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `items` | array | List of episode objects |
| `total` | integer | Total number of episodes |
| `limit` | integer | Items per page |
| `offset` | integer | Offset from start |

### Error Responses

**404 Not Found** - TV show or season not found:
```json
{
  "detail": "TV show or season not found",
  "status": "error",
  "error_code": "NOT_FOUND"
}
```

---

## Create TV Show

Create a new TV show record in the library.

### Endpoint

```
POST /tv-shows
```

### Request Body

```json
{
  "title": "New TV Series",
  "plot": "Series description and plot summary",
  "rating": 8.0,
  "genres": ["drama", "thriller"],
  "status": "ongoing",
  "tvdb_id": "tt9876543"
}
```

### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | TV show title |
| `plot` | string | No | Series plot/description |
| `rating` | float | No | Rating (0-10) |
| `genres` | array | No | List of genres |
| `status` | string | No | Status (ongoing, completed, cancelled) |
| `tvdb_id` | string | No | TVDB ID for metadata sync |

### Request Example

```bash
curl -X POST "http://localhost:8000/tv-shows" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New TV Series",
    "plot": "An exciting new series",
    "rating": 8.0,
    "genres": ["drama", "thriller"],
    "status": "ongoing",
    "tvdb_id": "tt9876543"
  }'
```

### Response (201 Created)

```json
{
  "id": 10,
  "title": "New TV Series",
  "plot": "An exciting new series",
  "rating": 8.0,
  "genres": ["drama", "thriller"],
  "status": "ongoing",
  "tvdb_id": "tt9876543",
  "season_count": 0,
  "episode_count": 0,
  "created_at": "2026-02-07T14:11:14.391Z",
  "updated_at": "2026-02-07T14:11:14.391Z"
}
```

### Error Responses

**422 Unprocessable Entity** - Validation error:
```json
{
  "detail": "Validation error",
  "errors": [
    {
      "field": "title",
      "message": "Title is required"
    }
  ],
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

### Side Effects

- TV show list cache is invalidated
- New TV show is immediately available for queries

---

## Update TV Show

Update an existing TV show record.

### Endpoint

```
PUT /tv-shows/{show_id}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `show_id` | integer | TV show ID |

### Request Body

```json
{
  "title": "Updated Series Title",
  "plot": "Updated plot description",
  "rating": 8.5,
  "genres": ["drama", "thriller", "mystery"],
  "status": "completed",
  "tvdb_id": "tt9876543"
}
```

### Request Fields

All fields are optional. Only provided fields will be updated.

### Request Example

```bash
curl -X PUT "http://localhost:8000/tv-shows/1" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 8.5,
    "status": "completed"
  }'
```

### Response (200 OK)

```json
{
  "id": 1,
  "title": "Drama Series",
  "plot": "An engaging drama series about...",
  "rating": 8.5,
  "genres": ["drama", "thriller"],
  "status": "completed",
  "tvdb_id": "tt1234567",
  "season_count": 5,
  "episode_count": 52,
  "created_at": "2026-02-07T14:11:14.391Z",
  "updated_at": "2026-02-07T14:11:14.391Z"
}
```

### Error Responses

**404 Not Found** - TV show not found:
```json
{
  "detail": "TV show not found",
  "status": "error",
  "error_code": "NOT_FOUND"
}
```

### Side Effects

- TV show cache is invalidated
- TV show list cache is invalidated
- Updated timestamp is automatically set

---

## Delete TV Show

Delete a TV show record from the library.

### Endpoint

```
DELETE /tv-shows/{show_id}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `show_id` | integer | TV show ID |

### Request Example

```bash
curl -X DELETE "http://localhost:8000/tv-shows/1"
```

### Response (204 No Content)

No response body is returned on successful deletion.

### Error Responses

**404 Not Found** - TV show not found:
```json
{
  "detail": "TV show not found",
  "status": "error",
  "error_code": "NOT_FOUND"
}
```

### Side Effects

- TV show cache is invalidated
- TV show list cache is invalidated
- All associated seasons and episodes are deleted
- TV show is permanently removed from database

---

## Sync TV Show Metadata

Fetch updated TV show metadata from TVDB and update the TV show record.

### Endpoint

```
POST /tv-shows/{show_id}/sync-metadata
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `show_id` | integer | TV show ID |

### Request Example

```bash
curl -X POST "http://localhost:8000/tv-shows/1/sync-metadata"
```

### Response (200 OK)

```json
{
  "success": true,
  "message": "TV show metadata synced successfully. Updated 3 field(s).",
  "movie_id": null,
  "show_id": 1,
  "updated_fields": ["title", "rating", "plot"],
  "metadata": {
    "title": "Updated Series Title",
    "plot": "Updated plot from TVDB",
    "rating": 8.7,
    "status": "ongoing",
    "genres": ["drama", "thriller"],
    "tvdb_id": "tt1234567"
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether sync was successful |
| `message` | string | Operation message |
| `movie_id` | null | Always null for TV shows |
| `show_id` | integer | ID of synced TV show |
| `updated_fields` | array | List of fields that were updated |
| `metadata` | object | Updated metadata |

### Error Responses

**404 Not Found** - TV show not found:
```json
{
  "detail": "TV show not found",
  "status": "error",
  "error_code": "NOT_FOUND"
}
```

**400 Bad Request** - TV show has no TVDB ID:
```json
{
  "detail": "TV show does not have a TVDB ID. Cannot sync metadata.",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

**500 Internal Server Error** - TVDB service unavailable:
```json
{
  "detail": "Failed to fetch metadata from TVDB. Please try again later.",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

### Requirements

- TV show must have a TVDB ID (`tvdb_id` field)
- TVDB API must be accessible and responding
- TV show record must exist in database

### Side Effects

- TV show cache is invalidated
- TV show list cache is invalidated
- Updated timestamp is automatically set
- Only changed fields are updated

---

## Data Model

### TV Show Object

```json
{
  "id": 1,
  "title": "Drama Series",
  "plot": "Series description",
  "rating": 8.2,
  "genres": ["drama", "thriller"],
  "status": "ongoing",
  "tvdb_id": "tt1234567",
  "season_count": 5,
  "episode_count": 52,
  "created_at": "2026-02-07T14:11:14.391Z",
  "updated_at": "2026-02-07T14:11:14.391Z"
}
```

### Season Object

```json
{
  "id": 1,
  "season_number": 1,
  "tvdb_id": "season_123",
  "episode_count": 10,
  "created_at": "2026-02-07T14:11:14.391Z"
}
```

### Episode Object

```json
{
  "id": 1,
  "episode_number": 1,
  "season_number": 1,
  "title": "Pilot",
  "plot": "Episode description",
  "air_date": "2020-01-15",
  "tvdb_id": "episode_001",
  "created_at": "2026-02-07T14:11:14.391Z"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique identifier |
| `title` | string | Title |
| `plot` | string | Description/plot |
| `rating` | float | Rating (0-10) |
| `genres` | array | List of genre strings |
| `status` | string | Status (ongoing, completed, cancelled) |
| `tvdb_id` | string | TVDB ID for external metadata |
| `season_count` | integer | Number of seasons |
| `episode_count` | integer | Total number of episodes |
| `created_at` | string | ISO 8601 creation timestamp |
| `updated_at` | string | ISO 8601 last update timestamp |

---

## Common Workflows

### Workflow 1: Browse Series and Episodes

```bash
# 1. List TV shows
curl -X GET "http://localhost:8000/tv-shows?genre=drama&limit=10"

# 2. Get show details
curl -X GET "http://localhost:8000/tv-shows/1"

# 3. Get seasons
curl -X GET "http://localhost:8000/tv-shows/1/seasons"

# 4. Get episodes for season 1
curl -X GET "http://localhost:8000/tv-shows/1/seasons/1/episodes"
```

### Workflow 2: Update Show Status

```bash
# 1. Get show details
curl -X GET "http://localhost:8000/tv-shows/1"

# 2. Update status to completed
curl -X PUT "http://localhost:8000/tv-shows/1" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

### Workflow 3: Sync and Update Metadata

```bash
# 1. Sync metadata from TVDB
curl -X POST "http://localhost:8000/tv-shows/1/sync-metadata"

# 2. Verify updated data
curl -X GET "http://localhost:8000/tv-shows/1"
```

---

## Rate Limiting

Currently, no rate limiting is enforced. When implemented:
- Standard endpoints: 1000 requests/hour
- Search endpoints: 500 requests/hour

---

## Related Documentation

- [API Reference](./API_REFERENCE.md)
- [Movie Endpoints](./ENDPOINTS_MOVIES.md)
- [API Client Examples](./API_CLIENT_EXAMPLES.md)
- [Error Reference](./API_ERRORS.md)
