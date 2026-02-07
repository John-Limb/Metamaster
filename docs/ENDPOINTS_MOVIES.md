# Movie Endpoints Documentation

## Overview

The Movie API provides comprehensive endpoints for managing movie records in the media library. All endpoints support filtering, sorting, pagination, and caching for optimal performance.

**Base URL:** `/movies`

---

## Table of Contents

1. [List Movies](#list-movies)
2. [Search Movies](#search-movies)
3. [Get Movie Details](#get-movie-details)
4. [Create Movie](#create-movie)
5. [Update Movie](#update-movie)
6. [Delete Movie](#delete-movie)
7. [Sync Movie Metadata](#sync-movie-metadata)

---

## List Movies

Retrieve a paginated list of movies with advanced filtering and sorting capabilities.

### Endpoint

```
GET /movies
```

### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `genre` | string | null | - | Filter by genre (case-insensitive) |
| `min_rating` | float | null | - | Minimum rating (0-10) |
| `max_rating` | float | null | - | Maximum rating (0-10) |
| `year` | integer | null | - | Release year (1800-2100) |
| `sort_by` | string | "title" | - | Sort field: title, rating, year, date_added |
| `limit` | integer | 10 | 100 | Items per page |
| `skip` | integer | 0 | - | Offset from start |

### Request Example

```bash
curl -X GET "http://localhost:8000/movies?genre=action&min_rating=7.0&limit=20&skip=0"
```

### Response (200 OK)

```json
{
  "items": [
    {
      "id": 1,
      "title": "Action Movie Title",
      "plot": "An exciting action film about...",
      "year": 2020,
      "rating": 8.5,
      "genres": ["action", "thriller"],
      "runtime": 120,
      "omdb_id": "tt1234567",
      "created_at": "2026-02-07T14:11:14.391Z",
      "updated_at": "2026-02-07T14:11:14.391Z"
    },
    {
      "id": 2,
      "title": "Another Action Film",
      "plot": "More action-packed adventure...",
      "year": 2021,
      "rating": 7.8,
      "genres": ["action", "adventure"],
      "runtime": 135,
      "omdb_id": "tt2345678",
      "created_at": "2026-02-07T14:11:14.391Z",
      "updated_at": "2026-02-07T14:11:14.391Z"
    }
  ],
  "total": 45,
  "limit": 20,
  "offset": 0,
  "filters": {
    "applied_filters": {
      "genre": "action",
      "min_rating": 7.0
    },
    "sort_by": "title",
    "total_results": 45
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `items` | array | List of movie objects |
| `total` | integer | Total number of movies matching filters |
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

- **Cache Key**: `movies:list:genre={genre}:min_rating={min_rating}:...`
- **TTL**: 3600 seconds (1 hour)
- **Invalidation**: Cleared when movies are created, updated, or deleted

---

## Search Movies

Search for movies by title with pagination support.

### Endpoint

```
GET /movies/search
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query (min 1 character) |
| `limit` | integer | No | Items per page (1-100, default: 10) |
| `offset` | integer | No | Offset from start (default: 0) |

### Request Example

```bash
curl -X GET "http://localhost:8000/movies/search?q=inception&limit=10&offset=0"
```

### Response (200 OK)

```json
{
  "items": [
    {
      "id": 5,
      "title": "Inception",
      "plot": "A skilled thief who steals corporate secrets...",
      "year": 2010,
      "rating": 8.8,
      "genres": ["action", "sci-fi", "thriller"],
      "runtime": 148,
      "omdb_id": "tt1375666",
      "created_at": "2026-02-07T14:11:14.391Z",
      "updated_at": "2026-02-07T14:11:14.391Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

### Error Responses

**400 Bad Request** - Missing or invalid search query:
```json
{
  "detail": "Search query is required and must be at least 1 character",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

---

## Get Movie Details

Retrieve detailed information about a specific movie.

### Endpoint

```
GET /movies/{movie_id}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `movie_id` | integer | Movie ID |

### Request Example

```bash
curl -X GET "http://localhost:8000/movies/1"
```

### Response (200 OK)

```json
{
  "id": 1,
  "title": "Action Movie Title",
  "plot": "An exciting action film about...",
  "year": 2020,
  "rating": 8.5,
  "genres": ["action", "thriller"],
  "runtime": 120,
  "omdb_id": "tt1234567",
  "created_at": "2026-02-07T14:11:14.391Z",
  "updated_at": "2026-02-07T14:11:14.391Z"
}
```

### Error Responses

**404 Not Found** - Movie not found:
```json
{
  "detail": "Movie not found",
  "status": "error",
  "error_code": "NOT_FOUND"
}
```

### Caching

- **Cache Key**: `movies:{movie_id}`
- **TTL**: 3600 seconds (1 hour)
- **Invalidation**: Cleared when movie is updated or deleted

---

## Create Movie

Create a new movie record in the library.

### Endpoint

```
POST /movies
```

### Request Body

```json
{
  "title": "New Movie Title",
  "plot": "Movie description and plot summary",
  "year": 2026,
  "rating": 8.0,
  "genres": ["action", "drama"],
  "runtime": 130,
  "omdb_id": "tt9876543"
}
```

### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Movie title |
| `plot` | string | No | Movie plot/description |
| `year` | integer | No | Release year |
| `rating` | float | No | Rating (0-10) |
| `genres` | array | No | List of genres |
| `runtime` | integer | No | Runtime in minutes |
| `omdb_id` | string | No | OMDB ID for metadata sync |

### Request Example

```bash
curl -X POST "http://localhost:8000/movies" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Movie",
    "plot": "An exciting new film",
    "year": 2026,
    "rating": 8.0,
    "genres": ["action", "drama"],
    "runtime": 130,
    "omdb_id": "tt9876543"
  }'
```

### Response (201 Created)

```json
{
  "id": 10,
  "title": "New Movie",
  "plot": "An exciting new film",
  "year": 2026,
  "rating": 8.0,
  "genres": ["action", "drama"],
  "runtime": 130,
  "omdb_id": "tt9876543",
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

- Movie list cache is invalidated
- New movie is immediately available for queries

---

## Update Movie

Update an existing movie record.

### Endpoint

```
PUT /movies/{movie_id}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `movie_id` | integer | Movie ID |

### Request Body

```json
{
  "title": "Updated Movie Title",
  "plot": "Updated plot description",
  "year": 2026,
  "rating": 8.5,
  "genres": ["action", "drama", "thriller"],
  "runtime": 135,
  "omdb_id": "tt9876543"
}
```

### Request Fields

All fields are optional. Only provided fields will be updated.

### Request Example

```bash
curl -X PUT "http://localhost:8000/movies/1" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 8.5,
    "genres": ["action", "drama", "thriller"]
  }'
```

### Response (200 OK)

```json
{
  "id": 1,
  "title": "Action Movie Title",
  "plot": "An exciting action film about...",
  "year": 2020,
  "rating": 8.5,
  "genres": ["action", "drama", "thriller"],
  "runtime": 120,
  "omdb_id": "tt1234567",
  "created_at": "2026-02-07T14:11:14.391Z",
  "updated_at": "2026-02-07T14:11:14.391Z"
}
```

### Error Responses

**404 Not Found** - Movie not found:
```json
{
  "detail": "Movie not found",
  "status": "error",
  "error_code": "NOT_FOUND"
}
```

### Side Effects

- Movie cache is invalidated
- Movie list cache is invalidated
- Updated timestamp is automatically set

---

## Delete Movie

Delete a movie record from the library.

### Endpoint

```
DELETE /movies/{movie_id}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `movie_id` | integer | Movie ID |

### Request Example

```bash
curl -X DELETE "http://localhost:8000/movies/1"
```

### Response (204 No Content)

No response body is returned on successful deletion.

### Error Responses

**404 Not Found** - Movie not found:
```json
{
  "detail": "Movie not found",
  "status": "error",
  "error_code": "NOT_FOUND"
}
```

### Side Effects

- Movie cache is invalidated
- Movie list cache is invalidated
- Movie is permanently removed from database

---

## Sync Movie Metadata

Fetch updated movie metadata from OMDB and update the movie record.

### Endpoint

```
POST /movies/{movie_id}/sync-metadata
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `movie_id` | integer | Movie ID |

### Request Example

```bash
curl -X POST "http://localhost:8000/movies/1/sync-metadata"
```

### Response (200 OK)

```json
{
  "success": true,
  "message": "Movie metadata synced successfully. Updated 3 field(s).",
  "movie_id": 1,
  "show_id": null,
  "updated_fields": ["title", "rating", "plot"],
  "metadata": {
    "title": "Updated Title",
    "plot": "Updated plot from OMDB",
    "year": 2020,
    "rating": 8.7,
    "runtime": 120,
    "genres": ["action", "thriller"],
    "omdb_id": "tt1234567"
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether sync was successful |
| `message` | string | Operation message |
| `movie_id` | integer | ID of synced movie |
| `show_id` | null | Always null for movies |
| `updated_fields` | array | List of fields that were updated |
| `metadata` | object | Updated metadata |

### Error Responses

**404 Not Found** - Movie not found:
```json
{
  "detail": "Movie not found",
  "status": "error",
  "error_code": "NOT_FOUND"
}
```

**400 Bad Request** - Movie has no OMDB ID:
```json
{
  "detail": "Movie does not have an OMDB ID. Cannot sync metadata.",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

**500 Internal Server Error** - OMDB service unavailable:
```json
{
  "detail": "Failed to fetch metadata from OMDB. Please try again later.",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

### Requirements

- Movie must have an OMDB ID (`omdb_id` field)
- OMDB API must be accessible and responding
- Movie record must exist in database

### Side Effects

- Movie cache is invalidated
- Movie list cache is invalidated
- Updated timestamp is automatically set
- Only changed fields are updated

---

## Data Model

### Movie Object

```json
{
  "id": 1,
  "title": "Movie Title",
  "plot": "Movie description",
  "year": 2020,
  "rating": 8.5,
  "genres": ["action", "thriller"],
  "runtime": 120,
  "omdb_id": "tt1234567",
  "created_at": "2026-02-07T14:11:14.391Z",
  "updated_at": "2026-02-07T14:11:14.391Z"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique movie identifier |
| `title` | string | Movie title |
| `plot` | string | Movie plot/description |
| `year` | integer | Release year |
| `rating` | float | Rating (0-10) |
| `genres` | array | List of genre strings |
| `runtime` | integer | Runtime in minutes |
| `omdb_id` | string | OMDB ID for external metadata |
| `created_at` | string | ISO 8601 creation timestamp |
| `updated_at` | string | ISO 8601 last update timestamp |

---

## Common Workflows

### Workflow 1: Find and Update a Movie

```bash
# 1. Search for movie
curl -X GET "http://localhost:8000/movies/search?q=inception"

# 2. Get full details
curl -X GET "http://localhost:8000/movies/5"

# 3. Update rating
curl -X PUT "http://localhost:8000/movies/5" \
  -H "Content-Type: application/json" \
  -d '{"rating": 9.0}'
```

### Workflow 2: Sync Metadata and Update

```bash
# 1. Sync metadata from OMDB
curl -X POST "http://localhost:8000/movies/5/sync-metadata"

# 2. Verify updated data
curl -X GET "http://localhost:8000/movies/5"
```

### Workflow 3: Filter and Paginate

```bash
# 1. Get first page of action movies with rating > 7
curl -X GET "http://localhost:8000/movies?genre=action&min_rating=7.0&limit=20&skip=0"

# 2. Get next page
curl -X GET "http://localhost:8000/movies?genre=action&min_rating=7.0&limit=20&skip=20"

# 3. Sort by rating instead
curl -X GET "http://localhost:8000/movies?genre=action&min_rating=7.0&sort_by=rating&limit=20&skip=0"
```

---

## Rate Limiting

Currently, no rate limiting is enforced. When implemented:
- Standard endpoints: 1000 requests/hour
- Search endpoints: 500 requests/hour

---

## Related Documentation

- [API Reference](./API_REFERENCE.md)
- [TV Show Endpoints](./ENDPOINTS_TV_SHOWS.md)
- [API Client Examples](./API_CLIENT_EXAMPLES.md)
- [Error Reference](./API_ERRORS.md)
