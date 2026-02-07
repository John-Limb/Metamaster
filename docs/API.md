# Media Management API Documentation

## Quick Start

Welcome to the Media Management Web Tool API documentation. This is your central hub for all API-related information.

### Base URL

```
http://localhost:8000
```

### Interactive Documentation

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### First Request

```bash
# Check if API is running
curl http://localhost:8000/health

# List movies
curl http://localhost:8000/movies
```

---

## Documentation Index

### Core Documentation

| Document | Purpose |
|----------|---------|
| [API Reference](./API_REFERENCE.md) | Complete API overview and reference |
| [Error Reference](./API_ERRORS.md) | Error codes and handling strategies |
| [Authentication Guide](./API_AUTHENTICATION.md) | Authentication methods and security |

### Endpoint Documentation

| Document | Coverage |
|----------|----------|
| [Movie Endpoints](./ENDPOINTS_MOVIES.md) | Movie CRUD operations and metadata sync |
| [TV Show Endpoints](./ENDPOINTS_TV_SHOWS.md) | TV show management and episode browsing |
| [Cache Endpoints](./ENDPOINTS_CACHE.md) | Cache management and optimization |
| [Task Endpoints](./ENDPOINTS_TASKS.md) | Task monitoring and error tracking |
| [Batch Endpoints](./ENDPOINTS_BATCH.md) | Bulk operations and batch processing |
| [Health Endpoints](./ENDPOINTS_HEALTH.md) | Health checks and monitoring |

### Client Examples

| Document | Content |
|----------|---------|
| [API Client Examples](./API_CLIENT_EXAMPLES.md) | Python, JavaScript, cURL examples |
| [Postman Collection](./postman_collection.json) | Ready-to-use Postman collection |

---

## API Overview

### What is the Media Management API?

The Media Management API provides a comprehensive REST interface for managing your media library. It allows you to:

- **Manage Movies**: Create, read, update, delete movie records
- **Manage TV Shows**: Organize TV shows, seasons, and episodes
- **Sync Metadata**: Automatically fetch and update metadata from OMDB and TVDB
- **Monitor Tasks**: Track background jobs and batch operations
- **Optimize Performance**: Manage caching and database optimization
- **Monitor Health**: Check application and database status

### Key Features

✅ **RESTful API** - Standard HTTP methods and status codes  
✅ **JSON Format** - All requests and responses use JSON  
✅ **Pagination** - Efficient data retrieval with limit/offset  
✅ **Filtering & Sorting** - Advanced search and filtering capabilities  
✅ **Caching** - Redis-backed caching for performance  
✅ **Batch Operations** - Bulk metadata sync and file imports  
✅ **Task Monitoring** - Track long-running operations  
✅ **Error Handling** - Comprehensive error codes and messages  
✅ **Health Checks** - Built-in health monitoring endpoints  

---

## Common Use Cases

### Use Case 1: Browse Your Movie Library

```bash
# List all action movies with rating > 7.0
curl "http://localhost:8000/movies?genre=action&min_rating=7.0&limit=20"

# Search for a specific movie
curl "http://localhost:8000/movies/search?q=inception"

# Get movie details
curl "http://localhost:8000/movies/1"
```

### Use Case 2: Add New Movies

```bash
# Create a new movie
curl -X POST "http://localhost:8000/movies" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Movie",
    "year": 2026,
    "rating": 8.0,
    "genres": ["action", "drama"]
  }'

# Sync metadata from OMDB
curl -X POST "http://localhost:8000/movies/1/sync-metadata"
```

### Use Case 3: Bulk Metadata Sync

```bash
# Start batch metadata sync for multiple movies
curl -X POST "http://localhost:8000/api/tasks/batch/metadata-sync" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "metadata_sync",
    "media_ids": [1, 2, 3, 4, 5],
    "media_type": "movie"
  }'

# Monitor batch progress
curl "http://localhost:8000/api/tasks/batch/1/progress"
```

### Use Case 4: Monitor Application Health

```bash
# Check if API is running
curl "http://localhost:8000/health"

# Check database connectivity
curl "http://localhost:8000/health/db"

# Get cache statistics
curl "http://localhost:8000/cache/stats"
```

### Use Case 5: Handle Errors

```bash
# Try to get non-existent movie
curl "http://localhost:8000/movies/99999"

# Response: 404 Not Found
# {
#   "detail": "Movie not found",
#   "status": "error",
#   "error_code": "NOT_FOUND"
# }
```

---

## API Endpoints Summary

### Movies
- `GET /movies` - List movies
- `GET /movies/search` - Search movies
- `GET /movies/{id}` - Get movie
- `POST /movies` - Create movie
- `PUT /movies/{id}` - Update movie
- `DELETE /movies/{id}` - Delete movie
- `POST /movies/{id}/sync-metadata` - Sync metadata

### TV Shows
- `GET /tv-shows` - List TV shows
- `GET /tv-shows/{id}` - Get TV show
- `GET /tv-shows/{id}/seasons` - Get seasons
- `GET /tv-shows/{id}/seasons/{season_id}/episodes` - Get episodes
- `POST /tv-shows` - Create TV show
- `PUT /tv-shows/{id}` - Update TV show
- `DELETE /tv-shows/{id}` - Delete TV show
- `POST /tv-shows/{id}/sync-metadata` - Sync metadata

### Tasks
- `GET /api/tasks` - List tasks
- `GET /api/tasks/{id}` - Get task status
- `POST /api/tasks/{id}/retry` - Retry task
- `DELETE /api/tasks/{id}` - Cancel task
- `GET /api/tasks/errors` - List errors
- `GET /api/tasks/errors/{id}` - Get error details

### Batch Operations
- `POST /api/tasks/batch/metadata-sync` - Start metadata sync
- `POST /api/tasks/batch/file-import` - Start file import
- `GET /api/tasks/batch/{id}` - Get batch status
- `GET /api/tasks/batch/{id}/progress` - Get batch progress
- `DELETE /api/tasks/batch/{id}` - Cancel batch

### Cache
- `GET /cache/stats` - Get cache statistics
- `GET /cache/{type}` - List cache by type
- `DELETE /cache/{type}` - Invalidate cache
- `DELETE /cache/expired` - Delete expired entries
- `GET /cache/redis/stats` - Get Redis stats
- `DELETE /cache/redis/clear` - Clear Redis cache
- `POST /cache/redis/warmup` - Warmup cache
- `GET /cache/db-stats` - Get database stats
- `GET /cache/slow-queries` - Get slow queries

### Health
- `GET /health` - Basic health check
- `GET /health/db` - Database health check

---

## Response Format

### Success Response

```json
{
  "items": [],
  "total": 100,
  "limit": 10,
  "offset": 0
}
```

### Error Response

```json
{
  "detail": "Error message",
  "status": "error",
  "error_code": "ERROR_CODE",
  "timestamp": "2026-02-07T14:11:14.391Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 204 | No Content - Success, no body |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |
| 503 | Service Unavailable - Service down |

---

## Authentication

Currently, the API operates without authentication. All endpoints are publicly accessible.

**Future**: Authentication will be implemented with API keys and JWT tokens.

See [Authentication Guide](./API_AUTHENTICATION.md) for details.

---

## Rate Limiting

Currently, no rate limiting is enforced.

**Future**: Rate limits will be implemented:
- Standard endpoints: 1000 requests/hour
- Search endpoints: 500 requests/hour
- Batch operations: 100 requests/hour

---

## Pagination

All list endpoints support pagination:

```bash
curl "http://localhost:8000/movies?limit=20&offset=40"
```

Parameters:
- `limit`: Items per page (1-100, default: 10)
- `offset`: Offset from start (default: 0)

---

## Filtering & Sorting

### Movie Filters

```bash
# Filter by genre
curl "http://localhost:8000/movies?genre=action"

# Filter by rating range
curl "http://localhost:8000/movies?min_rating=7.0&max_rating=9.0"

# Filter by year
curl "http://localhost:8000/movies?year=2020"

# Sort by rating
curl "http://localhost:8000/movies?sort_by=rating"
```

### TV Show Filters

```bash
# Filter by genre
curl "http://localhost:8000/tv-shows?genre=drama"

# Filter by rating
curl "http://localhost:8000/tv-shows?min_rating=7.5"

# Sort by rating
curl "http://localhost:8000/tv-shows?sort_by=rating"
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 404 Not Found | Resource doesn't exist | Verify ID and check if resource exists |
| 422 Validation Error | Invalid request data | Check request format and required fields |
| 500 Internal Error | Server error | Retry or contact support |
| 503 Service Unavailable | Service down | Wait and retry |

See [Error Reference](./API_ERRORS.md) for comprehensive error handling guide.

---

## Client Libraries

### Python

```python
import requests

response = requests.get('http://localhost:8000/movies')
movies = response.json()
```

See [API Client Examples](./API_CLIENT_EXAMPLES.md) for full Python examples.

### JavaScript

```javascript
fetch('http://localhost:8000/movies')
  .then(response => response.json())
  .then(data => console.log(data));
```

See [API Client Examples](./API_CLIENT_EXAMPLES.md) for full JavaScript examples.

### cURL

```bash
curl http://localhost:8000/movies
```

See [API Client Examples](./API_CLIENT_EXAMPLES.md) for full cURL examples.

### Postman

Import the [Postman Collection](./postman_collection.json) for ready-to-use requests.

---

## Best Practices

### 1. Use Pagination

Always use pagination for list endpoints to avoid large responses:

```bash
curl "http://localhost:8000/movies?limit=20&offset=0"
```

### 2. Handle Errors Gracefully

Implement error handling and retry logic:

```python
import time

def retry_request(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
```

### 3. Cache Responses

Cache API responses locally to reduce requests:

```python
import json
from pathlib import Path

cache_dir = Path('.cache')
cache_dir.mkdir(exist_ok=True)

def get_with_cache(url, cache_key):
    cache_file = cache_dir / f"{cache_key}.json"
    
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)
    
    response = requests.get(url)
    data = response.json()
    
    with open(cache_file, 'w') as f:
        json.dump(data, f)
    
    return data
```

### 4. Use Batch Operations

For bulk operations, use batch endpoints instead of individual requests:

```bash
# Instead of multiple requests
curl -X POST "http://localhost:8000/api/tasks/batch/metadata-sync" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "metadata_sync",
    "media_ids": [1, 2, 3, 4, 5],
    "media_type": "movie"
  }'
```

### 5. Monitor Health

Regularly check API and database health:

```bash
curl "http://localhost:8000/health"
curl "http://localhost:8000/health/db"
```

---

## Troubleshooting

### API Not Responding

1. Check if API is running: `curl http://localhost:8000/health`
2. Check logs: `docker logs <container_id>`
3. Verify port 8000 is accessible
4. Check firewall settings

### Database Connection Error

1. Check database is running: `docker ps | grep postgres`
2. Verify connection string in `.env`
3. Check database credentials
4. Test connection: `psql -U user -d database -h localhost`

### Slow Responses

1. Check cache statistics: `curl http://localhost:8000/cache/stats`
2. Get slow queries: `curl http://localhost:8000/cache/slow-queries`
3. Check database performance: `curl http://localhost:8000/cache/db-stats`

See [Error Reference](./API_ERRORS.md) for comprehensive troubleshooting guide.

---

## Support & Resources

### Documentation

- [API Reference](./API_REFERENCE.md) - Complete API reference
- [Endpoint Documentation](./ENDPOINTS_MOVIES.md) - Detailed endpoint docs
- [Error Reference](./API_ERRORS.md) - Error codes and solutions
- [Authentication Guide](./API_AUTHENTICATION.md) - Auth methods

### Examples

- [Client Examples](./API_CLIENT_EXAMPLES.md) - Code examples
- [Postman Collection](./postman_collection.json) - Ready-to-use requests

### Tools

- [Swagger UI](http://localhost:8000/docs) - Interactive API explorer
- [ReDoc](http://localhost:8000/redoc) - API documentation viewer

---

## Version Information

- **API Version**: 1.0.0
- **Last Updated**: 2026-02-07
- **Status**: Production Ready

---

## Related Documentation

- [Architecture](../plans/ARCHITECTURE.md)
- [Deployment Guide](../plans/DEPLOYMENT_GUIDE.md)
- [Docker Setup](../DOCKER_SETUP.md)
- [README](../README.md)
