# Media Management Web Tool - Technical Specifications

## Document Overview

This document provides detailed technical specifications for the media management web tool, serving as a reference for developers during implementation.

---

## 1. API Specifications

### 1.1 Base URL
```
http://localhost:8000/api
```

### 1.2 Authentication
- No authentication required for MVP
- Future: JWT-based authentication

### 1.3 Response Format

**Success Response (200):**
```json
{
  "status": "success",
  "data": {},
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Error Response (4xx/5xx):**
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Detailed error message",
    "details": {}
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 1.4 Pagination

**Query Parameters:**
- `page` (int, default: 1) - Page number
- `limit` (int, default: 20, max: 100) - Items per page
- `sort` (string, default: "-created_at") - Sort field (prefix with `-` for descending)

**Response:**
```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

### 1.5 Filtering

**Query Parameters:**
- `search` (string) - Full-text search
- `genre` (string) - Filter by genre
- `year` (int) - Filter by year
- `rating_min` (float) - Minimum rating
- `rating_max` (float) - Maximum rating

---

## 2. Movie API Endpoints

### 2.1 List Movies

**Endpoint:** `GET /movies`

**Query Parameters:**
```
page=1
limit=20
sort=-created_at
search=matrix
genre=action
year=1999
rating_min=7.0
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "title": "The Matrix",
      "year": 1999,
      "omdb_id": "tt0133093",
      "plot": "A computer hacker learns...",
      "rating": 8.7,
      "runtime": 136,
      "genres": ["Action", "Sci-Fi"],
      "file_count": 1,
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "pages": 1
  }
}
```

**Status Codes:**
- 200: Success
- 400: Invalid parameters
- 500: Server error

---

### 2.2 Get Movie Details

**Endpoint:** `GET /movies/{id}`

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "title": "The Matrix",
    "year": 1999,
    "omdb_id": "tt0133093",
    "plot": "A computer hacker learns...",
    "rating": 8.7,
    "runtime": 136,
    "genres": ["Action", "Sci-Fi"],
    "files": [
      {
        "id": 1,
        "file_path": "/media/movies/The Matrix (1999).mkv",
        "file_size": 2147483648,
        "resolution": "1920x1080",
        "bitrate": 5000,
        "codec_video": "h264",
        "codec_audio": "aac",
        "duration": 8160,
        "last_modified": "2024-01-01T12:00:00Z"
      }
    ],
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

**Status Codes:**
- 200: Success
- 404: Movie not found
- 500: Server error

---

### 2.3 Create Movie

**Endpoint:** `POST /movies`

**Request Body:**
```json
{
  "title": "The Matrix",
  "year": 1999,
  "plot": "A computer hacker learns...",
  "rating": 8.7,
  "runtime": 136,
  "genres": ["Action", "Sci-Fi"]
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "title": "The Matrix",
    "year": 1999,
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

**Status Codes:**
- 201: Created
- 400: Invalid request
- 409: Movie already exists
- 500: Server error

---

### 2.4 Update Movie

**Endpoint:** `PUT /movies/{id}`

**Request Body:**
```json
{
  "title": "The Matrix",
  "year": 1999,
  "plot": "Updated plot...",
  "rating": 8.8,
  "runtime": 136,
  "genres": ["Action", "Sci-Fi", "Thriller"]
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "title": "The Matrix",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

**Status Codes:**
- 200: Success
- 400: Invalid request
- 404: Movie not found
- 500: Server error

---

### 2.5 Delete Movie

**Endpoint:** `DELETE /movies/{id}`

**Response:**
```json
{
  "status": "success",
  "message": "Movie deleted successfully"
}
```

**Status Codes:**
- 200: Success
- 404: Movie not found
- 500: Server error

---

### 2.6 Sync Movie Metadata

**Endpoint:** `POST /movies/{id}/sync-metadata`

**Request Body:**
```json
{
  "force": false
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "title": "The Matrix",
    "plot": "Updated from OMDB...",
    "rating": 8.7,
    "synced_at": "2024-01-01T12:00:00Z"
  }
}
```

**Status Codes:**
- 200: Success
- 404: Movie not found
- 503: OMDB API unavailable
- 500: Server error

---

## 3. TV Show API Endpoints

### 3.1 List TV Shows

**Endpoint:** `GET /tv-shows`

**Query Parameters:**
```
page=1
limit=20
sort=-created_at
search=breaking
genre=drama
status=Continuing
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "title": "Breaking Bad",
      "tvdb_id": "81189",
      "plot": "A high school chemistry teacher...",
      "rating": 9.5,
      "genres": ["Crime", "Drama", "Thriller"],
      "status": "Ended",
      "season_count": 5,
      "episode_count": 62,
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "pages": 1
  }
}
```

---

### 3.2 Get TV Show Details

**Endpoint:** `GET /tv-shows/{id}`

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "title": "Breaking Bad",
    "tvdb_id": "81189",
    "plot": "A high school chemistry teacher...",
    "rating": 9.5,
    "genres": ["Crime", "Drama", "Thriller"],
    "status": "Ended",
    "seasons": [
      {
        "id": 1,
        "season_number": 1,
        "episode_count": 7,
        "episodes": [
          {
            "id": 1,
            "episode_number": 1,
            "title": "Pilot",
            "plot": "A high school chemistry teacher...",
            "air_date": "2008-01-20",
            "rating": 8.9,
            "files": [
              {
                "id": 1,
                "file_path": "/media/tv_shows/Breaking Bad/S01E01.mkv",
                "resolution": "1920x1080",
                "bitrate": 5000
              }
            ]
          }
        ]
      }
    ],
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

---

### 3.3 Create TV Show

**Endpoint:** `POST /tv-shows`

**Request Body:**
```json
{
  "title": "Breaking Bad",
  "plot": "A high school chemistry teacher...",
  "rating": 9.5,
  "genres": ["Crime", "Drama", "Thriller"],
  "status": "Ended"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "title": "Breaking Bad",
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

---

### 3.4 Update TV Show

**Endpoint:** `PUT /tv-shows/{id}`

**Request Body:**
```json
{
  "title": "Breaking Bad",
  "plot": "Updated plot...",
  "rating": 9.6,
  "status": "Ended"
}
```

---

### 3.5 Delete TV Show

**Endpoint:** `DELETE /tv-shows/{id}`

---

### 3.6 Sync TV Show Metadata

**Endpoint:** `POST /tv-shows/{id}/sync-metadata`

**Request Body:**
```json
{
  "force": false,
  "sync_episodes": true
}
```

---

## 4. Search API Endpoints

### 4.1 Global Search

**Endpoint:** `GET /search`

**Query Parameters:**
```
q=matrix
type=all  # all, movie, tv_show
limit=20
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "movies": [
      {
        "id": 1,
        "title": "The Matrix",
        "year": 1999,
        "type": "movie"
      }
    ],
    "tv_shows": [
      {
        "id": 1,
        "title": "The Matrix",
        "type": "tv_show"
      }
    ]
  }
}
```

---

### 4.2 Advanced Search

**Endpoint:** `GET /search/advanced`

**Query Parameters:**
```
title=matrix
year=1999
genre=action
rating_min=7.0
rating_max=10.0
type=movie
limit=20
```

---

## 5. File Management Endpoints

### 5.1 List Files

**Endpoint:** `GET /files`

**Query Parameters:**
```
media_type=movie  # movie, episode
status=completed  # pending, processing, completed, failed
limit=20
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "file_path": "/media/movies/The Matrix (1999).mkv",
      "file_size": 2147483648,
      "resolution": "1920x1080",
      "bitrate": 5000,
      "codec_video": "h264",
      "codec_audio": "aac",
      "duration": 8160,
      "media_type": "movie",
      "media_id": 1,
      "status": "completed",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

---

### 5.2 Get File Details

**Endpoint:** `GET /files/{id}`

---

### 5.3 Rescan File

**Endpoint:** `POST /files/{id}/rescan`

**Response:**
```json
{
  "status": "success",
  "message": "File queued for rescanning",
  "task_id": "abc123"
}
```

---

### 5.4 Manual File Import

**Endpoint:** `POST /files/import`

**Request Body:**
```json
{
  "file_path": "/media/movies/The Matrix (1999).mkv",
  "media_type": "movie",
  "media_id": 1
}
```

---

## 6. Cache Management Endpoints

### 6.1 Get Cache Statistics

**Endpoint:** `GET /cache/stats`

**Response:**
```json
{
  "status": "success",
  "data": {
    "total_entries": 1500,
    "omdb_entries": 800,
    "tvdb_entries": 700,
    "cache_size_mb": 45.2,
    "hit_rate": 0.87,
    "expired_entries": 120
  }
}
```

---

### 6.2 Clear Cache

**Endpoint:** `DELETE /cache`

**Query Parameters:**
```
type=all  # all, omdb, tvdb
```

**Response:**
```json
{
  "status": "success",
  "message": "Cache cleared",
  "entries_removed": 1500
}
```

---

### 6.3 Cleanup Expired Cache

**Endpoint:** `POST /cache/cleanup`

**Response:**
```json
{
  "status": "success",
  "message": "Expired cache entries removed",
  "entries_removed": 120
}
```

---

## 7. Health & Status Endpoints

### 7.1 Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "database": "ok",
    "redis": "ok",
    "celery": "ok"
  }
}
```

---

### 7.2 System Status

**Endpoint:** `GET /status`

**Response:**
```json
{
  "status": "success",
  "data": {
    "uptime_seconds": 86400,
    "version": "1.0.0",
    "environment": "production",
    "database": {
      "movies": 150,
      "tv_shows": 45,
      "episodes": 2500,
      "files": 195
    },
    "queue": {
      "pending": 5,
      "processing": 2,
      "completed": 1000,
      "failed": 3
    },
    "cache": {
      "entries": 1500,
      "hit_rate": 0.87
    }
  }
}
```

---

## 8. Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_REQUEST | 400 | Invalid request parameters |
| NOT_FOUND | 404 | Resource not found |
| DUPLICATE_ENTRY | 409 | Resource already exists |
| VALIDATION_ERROR | 422 | Validation failed |
| RATE_LIMIT_EXCEEDED | 429 | Rate limit exceeded |
| INTERNAL_ERROR | 500 | Internal server error |
| SERVICE_UNAVAILABLE | 503 | Service temporarily unavailable |
| API_ERROR | 503 | External API error |

---

## 9. Rate Limiting

### 9.1 API Rate Limits

- **Default:** 100 requests per minute per IP
- **Search:** 50 requests per minute per IP
- **Metadata Sync:** 10 requests per minute per IP

### 9.2 Response Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704110400
```

---

## 10. Database Connection Specifications

### 10.1 SQLite Configuration

```python
# Connection string
DATABASE_URL = "sqlite:///./data/media.db"

# Connection pool settings
SQLALCHEMY_POOL_SIZE = 5
SQLALCHEMY_MAX_OVERFLOW = 10
SQLALCHEMY_POOL_TIMEOUT = 30
SQLALCHEMY_POOL_RECYCLE = 3600
```

### 10.2 Query Optimization

- Use indexes on frequently queried columns
- Implement query result caching
- Use connection pooling
- Batch operations when possible

---

## 11. File Monitoring Specifications

### 11.1 Supported File Extensions

```
Video: .mp4, .mkv, .avi, .mov, .flv, .wmv, .webm, .m4v
Audio: .mp3, .aac, .flac, .wav, .ogg
```

### 11.2 Pattern Matching Rules

**Movie Patterns (in order of priority):**
1. `Title (YYYY).ext` - Highest priority
2. `Title - YYYY.ext`
3. `Title [YYYY].ext`
4. `Title.ext` - Default to movie if no year found

**TV Show Patterns (in order of priority):**
1. `Title SxxExx.ext` - Highest priority
2. `Title - SxxExx.ext`
3. `Title/Season xx/SxxExx.ext`
4. `Title/Season xx/Episode xx.ext`

### 11.3 File Monitoring Events

- **Created:** New file detected
- **Modified:** File size or timestamp changed
- **Deleted:** File removed (cleanup)

---

## 12. Background Task Specifications

### 12.1 Task Types

| Task | Queue | Priority | Timeout | Retry |
|------|-------|----------|---------|-------|
| analyze_file | default | high | 300s | 3 |
| enrich_metadata | default | high | 60s | 3 |
| sync_metadata | default | medium | 120s | 2 |
| cleanup_cache | cleanup | low | 600s | 1 |
| cleanup_queue | cleanup | low | 600s | 1 |

### 12.2 Task Scheduling

```
# Cleanup expired cache - Daily at 2 AM
0 2 * * * cleanup_cache

# Cleanup old queue entries - Daily at 3 AM
0 3 * * * cleanup_queue

# Sync metadata - Weekly on Sunday at 1 AM
0 1 * * 0 sync_metadata
```

---

## 13. Logging Specifications

### 13.1 Log Levels

- **DEBUG:** Detailed information for debugging
- **INFO:** General informational messages
- **WARNING:** Warning messages for potential issues
- **ERROR:** Error messages for failures
- **CRITICAL:** Critical errors requiring immediate attention

### 13.2 Log Format

```
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "logger": "app.services.movie_service",
  "message": "Movie created successfully",
  "context": {
    "movie_id": 1,
    "title": "The Matrix"
  },
  "request_id": "abc123"
}
```

### 13.3 Log Retention

- **Application logs:** 30 days
- **Error logs:** 90 days
- **Audit logs:** 1 year

---

## 14. Performance Specifications

### 14.1 API Response Times (Target)

| Endpoint | Target (p95) | Target (p99) |
|----------|--------------|--------------|
| GET /movies | 100ms | 200ms |
| GET /movies/{id} | 50ms | 100ms |
| POST /movies | 200ms | 500ms |
| GET /search | 300ms | 1000ms |
| POST /sync-metadata | 2000ms | 5000ms |

### 14.2 Throughput

- **API:** 1000 requests/second
- **File Monitoring:** 100 files/second
- **Metadata Sync:** 10 items/second

### 14.3 Resource Usage

- **Memory:** <500MB baseline, <2GB peak
- **CPU:** <50% average, <80% peak
- **Disk:** <1GB for database (1000 movies)

---

## 15. Security Specifications

### 15.1 API Security

- HTTPS only in production
- CORS enabled for specified origins
- Rate limiting on all endpoints
- Input validation on all requests

### 15.2 Data Security

- API keys stored in environment variables
- Database file permissions: 600
- Backup encryption recommended
- No sensitive data in logs

### 15.3 Container Security

- Run as non-root user
- Read-only filesystem where possible
- Resource limits enforced
- Security scanning on images

---

## 16. Compliance & Standards

### 16.1 API Standards

- RESTful API design
- JSON request/response format
- HTTP status codes compliance
- OpenAPI 3.0 documentation

### 16.2 Code Standards

- PEP 8 Python style guide
- Type hints for all functions
- Comprehensive docstrings
- Unit test coverage >80%

### 16.3 Documentation Standards

- API documentation auto-generated
- Code comments for complex logic
- README with setup instructions
- Architecture documentation

---

## Conclusion

These technical specifications provide detailed guidance for implementing the media management web tool. All developers should refer to this document during implementation to ensure consistency and quality.
