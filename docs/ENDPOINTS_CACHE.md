# Cache Management Endpoints Documentation

## Overview

The Cache Management API provides endpoints for monitoring, managing, and optimizing both database and Redis caches. These endpoints allow you to view cache statistics, invalidate entries, and optimize performance.

**Base URL:** `/cache`

---

## Table of Contents

1. [Get Cache Statistics](#get-cache-statistics)
2. [List Cache by Type](#list-cache-by-type)
3. [Invalidate Cache by Type](#invalidate-cache-by-type)
4. [Delete Expired Cache](#delete-expired-cache)
5. [Get Redis Cache Statistics](#get-redis-cache-statistics)
6. [Clear Redis Cache](#clear-redis-cache)
7. [Warmup Redis Cache](#warmup-redis-cache)
8. [Get Database Statistics](#get-database-statistics)
9. [Get Slow Queries](#get-slow-queries)

---

## Get Cache Statistics

Retrieve comprehensive cache statistics including size, count, and breakdown by API type.

### Endpoint

```
GET /cache/stats
```

### Query Parameters

None

### Request Example

```bash
curl -X GET "http://localhost:8000/cache/stats"
```

### Response (200 OK)

```json
{
  "total_entries": 1250,
  "active_entries": 1200,
  "expired_entries": 50,
  "total_size_bytes": 5242880,
  "total_size_mb": 5.0,
  "by_api_type": {
    "omdb": {
      "count": 450,
      "size_bytes": 1835008,
      "size_mb": 1.75
    },
    "tvdb": {
      "count": 350,
      "size_bytes": 1572864,
      "size_mb": 1.5
    },
    "generic": {
      "count": 400,
      "size_bytes": 1835008,
      "size_mb": 1.75
    }
  },
  "timestamp": "2026-02-07T14:11:14.391Z"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `total_entries` | integer | Total number of cache entries |
| `active_entries` | integer | Number of non-expired entries |
| `expired_entries` | integer | Number of expired entries |
| `total_size_bytes` | integer | Total cache size in bytes |
| `total_size_mb` | float | Total cache size in megabytes |
| `by_api_type` | object | Breakdown by API type |
| `timestamp` | string | ISO 8601 timestamp |

### Error Responses

**500 Internal Server Error** - Failed to retrieve statistics:
```json
{
  "detail": "Failed to retrieve cache statistics",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

---

## List Cache by Type

List cache entries for a specific API type with pagination.

### Endpoint

```
GET /cache/{cache_type}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `cache_type` | string | API type: omdb, tvdb, generic |

### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `limit` | integer | 10 | 100 | Items per page |
| `offset` | integer | 0 | - | Offset from start |

### Request Example

```bash
curl -X GET "http://localhost:8000/cache/omdb?limit=20&offset=0"
```

### Response (200 OK)

```json
{
  "items": [
    {
      "id": 1,
      "key": "omdb:tt1234567",
      "api_type": "omdb",
      "size_bytes": 4096,
      "created_at": "2026-02-07T14:00:00.000Z",
      "expires_at": "2026-02-08T14:00:00.000Z",
      "hit_count": 15
    },
    {
      "id": 2,
      "key": "omdb:tt2345678",
      "api_type": "omdb",
      "size_bytes": 3840,
      "created_at": "2026-02-07T13:50:00.000Z",
      "expires_at": "2026-02-08T13:50:00.000Z",
      "hit_count": 8
    }
  ],
  "total": 450,
  "limit": 20,
  "offset": 0
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `items` | array | List of cache entries |
| `total` | integer | Total entries for this type |
| `limit` | integer | Items per page |
| `offset` | integer | Offset from start |

### Error Responses

**400 Bad Request** - Invalid cache type:
```json
{
  "detail": "Invalid cache type. Must be one of: omdb, tvdb, generic",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

**500 Internal Server Error** - Failed to retrieve entries:
```json
{
  "detail": "Failed to retrieve cache entries",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

---

## Invalidate Cache by Type

Invalidate all cache entries for a specific API type.

### Endpoint

```
DELETE /cache/{cache_type}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `cache_type` | string | API type: omdb, tvdb, generic |

### Request Example

```bash
curl -X DELETE "http://localhost:8000/cache/omdb"
```

### Response (200 OK)

```json
{
  "success": true,
  "message": "Invalidated 450 cache entries for type: omdb",
  "affected_entries": 450
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether operation was successful |
| `message` | string | Operation message |
| `affected_entries` | integer | Number of entries invalidated |

### Error Responses

**400 Bad Request** - Invalid cache type:
```json
{
  "detail": "Invalid cache type. Must be one of: omdb, tvdb, generic",
  "status": "error",
  "error_code": "VALIDATION_ERROR"
}
```

**500 Internal Server Error** - Failed to invalidate:
```json
{
  "detail": "Failed to invalidate cache entries",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

### Side Effects

- All cache entries of specified type are removed
- Subsequent requests will fetch fresh data from source APIs
- Performance may temporarily decrease until cache is repopulated

---

## Delete Expired Cache

Delete all expired cache entries from the database.

### Endpoint

```
DELETE /cache/expired
```

### Request Example

```bash
curl -X DELETE "http://localhost:8000/cache/expired"
```

### Response (200 OK)

```json
{
  "success": true,
  "message": "Deleted 50 expired cache entries",
  "affected_entries": 50
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether operation was successful |
| `message` | string | Operation message |
| `affected_entries` | integer | Number of entries deleted |

### Error Responses

**500 Internal Server Error** - Failed to delete:
```json
{
  "detail": "Failed to delete expired cache entries",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

### Side Effects

- Expired entries are permanently removed
- Database storage is freed
- No impact on active cache entries

---

## Get Redis Cache Statistics

Retrieve Redis cache statistics including hit/miss rates and memory usage.

### Endpoint

```
GET /cache/redis/stats
```

### Request Example

```bash
curl -X GET "http://localhost:8000/cache/redis/stats"
```

### Response (200 OK)

```json
{
  "connected": true,
  "total_keys": 2500,
  "memory_usage_bytes": 10485760,
  "memory_usage_mb": 10.0,
  "hit_rate": 85.5,
  "total_hits": 8550,
  "total_misses": 1450,
  "timestamp": "2026-02-07T14:11:14.391Z"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `connected` | boolean | Whether Redis is connected |
| `total_keys` | integer | Total number of keys in cache |
| `memory_usage_bytes` | integer | Memory usage in bytes |
| `memory_usage_mb` | float | Memory usage in megabytes |
| `hit_rate` | float | Cache hit rate percentage |
| `total_hits` | integer | Total cache hits |
| `total_misses` | integer | Total cache misses |
| `timestamp` | string | ISO 8601 timestamp |

### Error Responses

**500 Internal Server Error** - Failed to retrieve statistics:
```json
{
  "detail": "Failed to retrieve Redis cache statistics",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

---

## Clear Redis Cache

Clear all Redis cache entries.

### Endpoint

```
DELETE /cache/redis/clear
```

### Request Example

```bash
curl -X DELETE "http://localhost:8000/cache/redis/clear"
```

### Response (200 OK)

```json
{
  "success": true,
  "message": "All Redis cache cleared successfully",
  "affected_entries": 0
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether operation was successful |
| `message` | string | Operation message |
| `affected_entries` | integer | Always 0 for Redis |

### Error Responses

**500 Internal Server Error** - Failed to clear:
```json
{
  "detail": "Failed to clear Redis cache",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

### Side Effects

- All Redis cache entries are removed
- All in-memory cached data is lost
- Subsequent requests will fetch fresh data
- Performance may temporarily decrease

---

## Warmup Redis Cache

Pre-populate Redis cache with frequently accessed data (movies and TV shows).

### Endpoint

```
POST /cache/redis/warmup
```

### Request Example

```bash
curl -X POST "http://localhost:8000/cache/redis/warmup"
```

### Response (200 OK)

```json
{
  "success": true,
  "message": "Cache warmup completed successfully",
  "movies_cached": 500,
  "tv_shows_cached": 350
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether operation was successful |
| `message` | string | Operation message |
| `movies_cached` | integer | Number of movies cached |
| `tv_shows_cached` | integer | Number of TV shows cached |

### Error Responses

**500 Internal Server Error** - Failed to warmup:
```json
{
  "detail": "Failed to warmup cache",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

### Side Effects

- Redis cache is populated with frequently accessed data
- Improves performance for initial requests
- Increases memory usage temporarily
- Should be run during off-peak hours

---

## Get Database Statistics

Retrieve database connection pool statistics and performance metrics.

### Endpoint

```
GET /cache/db-stats
```

### Request Example

```bash
curl -X GET "http://localhost:8000/cache/db-stats"
```

### Response (200 OK)

```json
{
  "timestamp": "2026-02-07T14:11:14.391Z",
  "query_performance": {
    "total_queries": 5000,
    "average_execution_time_ms": 12.5,
    "min_execution_time_ms": 0.5,
    "max_execution_time_ms": 250.0,
    "queries_over_100ms": 45
  },
  "slow_queries": [
    {
      "query": "SELECT * FROM movies WHERE ...",
      "execution_time_ms": 245.0,
      "count": 3
    }
  ],
  "connection_pool": {
    "pool_size": 20,
    "checked_out": 5,
    "available": 15,
    "overflow": 0
  },
  "index_recommendations": [
    {
      "table": "movies",
      "column": "genre",
      "reason": "Frequently filtered column"
    }
  ],
  "all_indexes": [
    {
      "table": "movies",
      "name": "idx_movies_title",
      "columns": ["title"]
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO 8601 timestamp |
| `query_performance` | object | Query execution statistics |
| `slow_queries` | array | List of slow queries |
| `connection_pool` | object | Connection pool statistics |
| `index_recommendations` | array | Recommended indexes |
| `all_indexes` | array | All existing indexes |

### Error Responses

**500 Internal Server Error** - Failed to retrieve statistics:
```json
{
  "detail": "Failed to retrieve database statistics",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

---

## Get Slow Queries

Get list of slow queries detected by the query performance tracker.

### Endpoint

```
GET /cache/slow-queries
```

### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `limit` | integer | 10 | 100 | Number of slow queries to return |

### Request Example

```bash
curl -X GET "http://localhost:8000/cache/slow-queries?limit=20"
```

### Response (200 OK)

```json
{
  "slow_queries": [
    {
      "query": "SELECT * FROM movies WHERE genre LIKE ? AND rating > ?",
      "execution_time_ms": 245.0,
      "count": 3,
      "last_executed": "2026-02-07T14:10:00.000Z"
    },
    {
      "query": "SELECT * FROM tv_shows WHERE status = ?",
      "execution_time_ms": 180.0,
      "count": 5,
      "last_executed": "2026-02-07T14:09:30.000Z"
    }
  ],
  "count": 2,
  "threshold": 100
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `slow_queries` | array | List of slow queries |
| `count` | integer | Number of slow queries returned |
| `threshold` | float | Slow query threshold in milliseconds |

### Error Responses

**500 Internal Server Error** - Failed to retrieve queries:
```json
{
  "detail": "Failed to retrieve slow queries",
  "status": "error",
  "error_code": "INTERNAL_ERROR"
}
```

---

## Cache Types

### OMDB Cache

Stores movie metadata fetched from OMDB API.

- **Prefix**: `omdb:`
- **TTL**: 86400 seconds (24 hours)
- **Use Case**: Movie details, ratings, plots

### TVDB Cache

Stores TV show metadata fetched from TVDB API.

- **Prefix**: `tvdb:`
- **TTL**: 86400 seconds (24 hours)
- **Use Case**: TV show details, seasons, episodes

### Generic Cache

Stores application-level cached data.

- **Prefix**: `generic:`
- **TTL**: 3600 seconds (1 hour)
- **Use Case**: Movie/TV show lists, search results

---

## Common Workflows

### Workflow 1: Monitor Cache Health

```bash
# 1. Get cache statistics
curl -X GET "http://localhost:8000/cache/stats"

# 2. Get Redis statistics
curl -X GET "http://localhost:8000/cache/redis/stats"

# 3. Get database statistics
curl -X GET "http://localhost:8000/cache/db-stats"
```

### Workflow 2: Clean Up Expired Cache

```bash
# 1. Check current statistics
curl -X GET "http://localhost:8000/cache/stats"

# 2. Delete expired entries
curl -X DELETE "http://localhost:8000/cache/expired"

# 3. Verify cleanup
curl -X GET "http://localhost:8000/cache/stats"
```

### Workflow 3: Optimize Performance

```bash
# 1. Get slow queries
curl -X GET "http://localhost:8000/cache/slow-queries?limit=10"

# 2. Get database statistics
curl -X GET "http://localhost:8000/cache/db-stats"

# 3. Warmup cache
curl -X POST "http://localhost:8000/cache/redis/warmup"
```

### Workflow 4: Invalidate Specific Cache Type

```bash
# 1. List OMDB cache entries
curl -X GET "http://localhost:8000/cache/omdb?limit=10"

# 2. Invalidate all OMDB cache
curl -X DELETE "http://localhost:8000/cache/omdb"

# 3. Verify invalidation
curl -X GET "http://localhost:8000/cache/stats"
```

---

## Performance Considerations

### Cache Hit Rate

- **Excellent**: > 90%
- **Good**: 70-90%
- **Fair**: 50-70%
- **Poor**: < 50%

### Memory Usage

- Monitor Redis memory usage
- Clear cache if usage exceeds 80% of available memory
- Use cache warmup during off-peak hours

### Query Performance

- Monitor slow queries regularly
- Queries over 100ms should be investigated
- Consider adding indexes for frequently filtered columns

---

## Related Documentation

- [API Reference](./API_REFERENCE.md)
- [Database Optimization Guide](../plans/ARCHITECTURE.md)
- [Performance Tuning](../plans/TECHNICAL_SPECIFICATIONS.md)
