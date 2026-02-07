# API Error Reference Guide

## Overview

This document provides comprehensive information about error codes, error responses, and error handling strategies for the Media Management API.

---

## Table of Contents

1. [HTTP Status Codes](#http-status-codes)
2. [Error Response Format](#error-response-format)
3. [Error Codes](#error-codes)
4. [Common Error Scenarios](#common-error-scenarios)
5. [Error Recovery Strategies](#error-recovery-strategies)
6. [Troubleshooting Guide](#troubleshooting-guide)

---

## HTTP Status Codes

### Success Codes (2xx)

| Code | Name | Description |
|------|------|-------------|
| 200 | OK | Request successful, response body included |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request successful, no response body |

### Client Error Codes (4xx)

| Code | Name | Description |
|------|------|-------------|
| 400 | Bad Request | Invalid request parameters or malformed request |
| 401 | Unauthorized | Authentication required or invalid credentials |
| 403 | Forbidden | Authenticated but insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., duplicate entry) |
| 422 | Unprocessable Entity | Request validation failed |
| 429 | Too Many Requests | Rate limit exceeded |

### Server Error Codes (5xx)

| Code | Name | Description |
|------|------|-------------|
| 500 | Internal Server Error | Server error, request failed |
| 502 | Bad Gateway | Gateway error, service unavailable |
| 503 | Service Unavailable | Service temporarily unavailable |
| 504 | Gateway Timeout | Request timeout |

---

## Error Response Format

### Standard Error Response

```json
{
  "detail": "Descriptive error message",
  "status": "error",
  "error_code": "ERROR_CODE",
  "timestamp": "2026-02-07T14:11:14.391Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Validation Error Response

```json
{
  "detail": "Validation error",
  "status": "error",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2026-02-07T14:11:14.391Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "errors": [
    {
      "field": "title",
      "message": "Title is required"
    },
    {
      "field": "rating",
      "message": "Rating must be between 0 and 10"
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `detail` | string | Human-readable error message |
| `status` | string | Always "error" for error responses |
| `error_code` | string | Machine-readable error code |
| `timestamp` | string | ISO 8601 timestamp when error occurred |
| `request_id` | string | Unique request identifier for tracking |
| `errors` | array | Field-specific validation errors (optional) |

---

## Error Codes

### Validation Errors

| Code | HTTP Status | Description | Solution |
|------|-------------|-------------|----------|
| `VALIDATION_ERROR` | 422 | Request validation failed | Review error details and correct request |
| `INVALID_PARAMETER` | 400 | Invalid parameter value | Check parameter type and range |
| `MISSING_REQUIRED_FIELD` | 422 | Required field missing | Include all required fields |
| `INVALID_FILTER` | 400 | Invalid filter parameter | Use valid filter values |
| `INVALID_SORT_FIELD` | 400 | Invalid sort field | Use valid sort field names |

### Resource Errors

| Code | HTTP Status | Description | Solution |
|------|-------------|-------------|----------|
| `NOT_FOUND` | 404 | Resource not found | Verify resource ID exists |
| `RESOURCE_DELETED` | 404 | Resource was deleted | Check if resource still exists |
| `DUPLICATE_ENTRY` | 409 | Resource already exists | Use different values or update existing |
| `CONFLICT` | 409 | Resource conflict | Resolve conflict before retrying |

### Authentication & Authorization

| Code | HTTP Status | Description | Solution |
|------|-------------|-------------|----------|
| `UNAUTHORIZED` | 401 | Authentication required | Provide valid credentials |
| `INVALID_CREDENTIALS` | 401 | Invalid credentials | Check username/password |
| `FORBIDDEN` | 403 | Insufficient permissions | Request access or use different account |
| `TOKEN_EXPIRED` | 401 | Authentication token expired | Refresh token or re-authenticate |

### Rate Limiting

| Code | HTTP Status | Description | Solution |
|------|-------------|-------------|----------|
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests | Wait before retrying |
| `QUOTA_EXCEEDED` | 429 | Usage quota exceeded | Wait for quota reset |

### Server Errors

| Code | HTTP Status | Description | Solution |
|------|-------------|-------------|----------|
| `INTERNAL_ERROR` | 500 | Internal server error | Retry request or contact support |
| `DATABASE_ERROR` | 500 | Database operation failed | Retry or contact support |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable | Retry with exponential backoff |
| `TIMEOUT` | 504 | Request timeout | Retry with longer timeout |

### External Service Errors

| Code | HTTP Status | Description | Solution |
|------|-------------|-------------|----------|
| `EXTERNAL_API_ERROR` | 500 | External API call failed | Retry or check external service status |
| `OMDB_ERROR` | 500 | OMDB API error | Verify OMDB API key and status |
| `TVDB_ERROR` | 500 | TVDB API error | Verify TVDB API key and status |

---

## Common Error Scenarios

### Scenario 1: Movie Not Found

**Request:**
```bash
curl -X GET "http://localhost:8000/movies/99999"
```

**Response (404 Not Found):**
```json
{
  "detail": "Movie not found",
  "status": "error",
  "error_code": "NOT_FOUND",
  "timestamp": "2026-02-07T14:11:14.391Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Solution:**
1. Verify the movie ID is correct
2. Check if movie was deleted
3. List movies to find correct ID

### Scenario 2: Validation Error - Missing Required Field

**Request:**
```bash
curl -X POST "http://localhost:8000/movies" \
  -H "Content-Type: application/json" \
  -d '{"plot": "Movie description"}'
```

**Response (422 Unprocessable Entity):**
```json
{
  "detail": "Validation error",
  "status": "error",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2026-02-07T14:11:14.391Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "errors": [
    {
      "field": "title",
      "message": "Title is required"
    }
  ]
}
```

**Solution:**
1. Include the "title" field in request
2. Ensure all required fields are provided
3. Check field types match expected types

### Scenario 3: Invalid Filter Parameter

**Request:**
```bash
curl -X GET "http://localhost:8000/movies?min_rating=15"
```

**Response (400 Bad Request):**
```json
{
  "detail": "Invalid filter parameters",
  "status": "error",
  "error_code": "INVALID_FILTER",
  "timestamp": "2026-02-07T14:11:14.391Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Solution:**
1. Check filter value ranges (rating: 0-10)
2. Use valid filter values
3. Review API documentation for valid parameters

### Scenario 4: Rate Limit Exceeded

**Request:**
```bash
# Multiple rapid requests
for i in {1..1001}; do
  curl -X GET "http://localhost:8000/movies"
done
```

**Response (429 Too Many Requests):**
```json
{
  "detail": "Rate limit exceeded",
  "status": "error",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "timestamp": "2026-02-07T14:11:14.391Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Solution:**
1. Implement exponential backoff
2. Reduce request frequency
3. Cache responses locally
4. Use batch operations for bulk requests

### Scenario 5: External API Error

**Request:**
```bash
curl -X POST "http://localhost:8000/movies/1/sync-metadata"
```

**Response (500 Internal Server Error):**
```json
{
  "detail": "Failed to fetch metadata from OMDB. Please try again later.",
  "status": "error",
  "error_code": "EXTERNAL_API_ERROR",
  "timestamp": "2026-02-07T14:11:14.391Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Solution:**
1. Verify external API (OMDB/TVDB) is accessible
2. Check API key is valid
3. Retry after a delay
4. Check external service status page

### Scenario 6: Database Connection Error

**Request:**
```bash
curl -X GET "http://localhost:8000/movies"
```

**Response (500 Internal Server Error):**
```json
{
  "detail": "Error retrieving movies: Connection refused",
  "status": "error",
  "error_code": "DATABASE_ERROR",
  "timestamp": "2026-02-07T14:11:14.391Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Solution:**
1. Verify database is running
2. Check database connection string
3. Verify database credentials
4. Check network connectivity to database

---

## Error Recovery Strategies

### Strategy 1: Exponential Backoff

```python
import time
import requests

def retry_with_backoff(url, max_retries=3, base_delay=1):
    """Retry request with exponential backoff"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            
            delay = base_delay * (2 ** attempt)
            print(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
            time.sleep(delay)

# Usage
try:
    data = retry_with_backoff("http://localhost:8000/movies")
except Exception as e:
    print(f"Failed after retries: {e}")
```

### Strategy 2: Circuit Breaker Pattern

```python
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
    
    def on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Usage
breaker = CircuitBreaker(failure_threshold=5, timeout=60)

def get_movies():
    return breaker.call(requests.get, "http://localhost:8000/movies")
```

### Strategy 3: Fallback to Cache

```python
import json
from pathlib import Path

class CachedAPIClient:
    def __init__(self, cache_dir=".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_with_fallback(self, url, cache_key):
        """Get data from API, fallback to cache on error"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Update cache
            cache_file = self.cache_dir / f"{cache_key}.json"
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            
            return data
        except Exception as e:
            print(f"API call failed: {e}, using cache")
            
            # Try to load from cache
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    return json.load(f)
            
            raise Exception("API failed and no cache available")

# Usage
client = CachedAPIClient()
movies = client.get_with_fallback(
    "http://localhost:8000/movies",
    "movies_list"
)
```

### Strategy 4: Request Timeout

```python
import requests

def get_with_timeout(url, timeout=5):
    """Make request with timeout"""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print("Request timed out")
        raise
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise

# Usage
try:
    data = get_with_timeout("http://localhost:8000/movies", timeout=10)
except Exception as e:
    print(f"Error: {e}")
```

---

## Troubleshooting Guide

### Issue: "Connection refused"

**Symptoms:**
- Cannot connect to API
- Error: "Connection refused"

**Diagnosis:**
```bash
# Check if API is running
curl -v http://localhost:8000/health

# Check if port is listening
netstat -tlnp | grep 8000

# Check firewall
sudo ufw status
```

**Solutions:**
1. Start the API server: `python -m uvicorn app.main:app --reload`
2. Check port is not in use: `lsof -i :8000`
3. Verify firewall allows port 8000
4. Check API configuration

### Issue: "Database connection failed"

**Symptoms:**
- `/health/db` returns unhealthy
- Database operations fail

**Diagnosis:**
```bash
# Check database is running
docker ps | grep postgres

# Test database connection
psql -U user -d database -h localhost

# Check connection string
echo $DATABASE_URL
```

**Solutions:**
1. Start database: `docker-compose up -d db`
2. Verify credentials in `.env`
3. Check database exists
4. Verify network connectivity

### Issue: "Rate limit exceeded"

**Symptoms:**
- 429 Too Many Requests errors
- Requests being rejected

**Solutions:**
1. Implement exponential backoff
2. Reduce request frequency
3. Use batch operations
4. Cache responses locally
5. Wait for rate limit window to reset

### Issue: "External API error"

**Symptoms:**
- Metadata sync fails
- Error: "Failed to fetch metadata from OMDB"

**Diagnosis:**
```bash
# Check API key
echo $OMDB_API_KEY

# Test external API
curl "http://www.omdbapi.com/?apikey=YOUR_KEY&i=tt1375666"
```

**Solutions:**
1. Verify API key is valid
2. Check API key has quota remaining
3. Verify external service is up
4. Check network connectivity
5. Retry after delay

### Issue: "Timeout"

**Symptoms:**
- Requests hang and eventually fail
- Error: "Request timeout"

**Solutions:**
1. Increase timeout value
2. Check server performance
3. Reduce request complexity
4. Check network latency
5. Optimize database queries

---

## Error Logging Best Practices

### Log Error Details

```python
import logging

logger = logging.getLogger(__name__)

try:
    response = requests.get(url)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    logger.error(
        "API request failed",
        extra={
            "url": url,
            "status_code": e.response.status_code if e.response else None,
            "error": str(e),
            "request_id": request_id
        }
    )
```

### Monitor Error Rates

```python
from collections import defaultdict
from datetime import datetime, timedelta

class ErrorMonitor:
    def __init__(self, window_minutes=5):
        self.window_minutes = window_minutes
        self.errors = defaultdict(list)
    
    def record_error(self, error_code):
        self.errors[error_code].append(datetime.now())
    
    def get_error_rate(self, error_code):
        cutoff = datetime.now() - timedelta(minutes=self.window_minutes)
        recent = [t for t in self.errors[error_code] if t > cutoff]
        return len(recent) / (self.window_minutes * 60)  # errors per second

# Usage
monitor = ErrorMonitor()
monitor.record_error("VALIDATION_ERROR")
rate = monitor.get_error_rate("VALIDATION_ERROR")
if rate > 0.1:  # More than 0.1 errors per second
    logger.warning(f"High error rate: {rate} errors/sec")
```

---

## Related Documentation

- [API Reference](./API_REFERENCE.md)
- [API Client Examples](./API_CLIENT_EXAMPLES.md)
- [Authentication Guide](./API_AUTHENTICATION.md)
