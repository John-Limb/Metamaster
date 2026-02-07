# Logging Architecture and Configuration

## Overview

The Media Management Web Tool implements a comprehensive, structured logging system designed for production environments. The logging infrastructure provides centralized configuration, multiple output formats, and specialized loggers for different application components.

## Logging Architecture

### Components

1. **Centralized Configuration** (`app/logging_config.py`)
   - Single point of configuration for all logging
   - Structured JSON format for machine parsing
   - Multiple handlers for different log levels and purposes
   - Automatic log rotation and retention

2. **Log Handlers**
   - Console handler: Real-time logs to stdout
   - File handler: General application logs
   - Error handler: Error-specific logs
   - Performance handler: Performance metrics
   - Database handler: Database query logs
   - Cache handler: Cache operation logs
   - Task handler: Background task logs
   - API handler: API request/response logs

3. **Log Levels**
   - DEBUG: Detailed diagnostic information
   - INFO: General informational messages
   - WARNING: Warning messages for potentially problematic situations
   - ERROR: Error messages for serious problems
   - CRITICAL: Critical messages for very serious problems

## Log Levels and Usage

### DEBUG
Used for detailed diagnostic information useful during development and troubleshooting:
```python
logger.debug("Cache key lookup", extra={"cache_key": key, "ttl": ttl})
logger.debug("Query executed", extra={"query": sql, "duration_ms": 5.2})
```

### INFO
Used for general informational messages about application flow:
```python
logger.info("Application started", extra={"version": "0.1.0"})
logger.info("Database initialized")
logger.info("Task completed", extra={"task_id": task_id, "duration_ms": 1234})
```

### WARNING
Used for potentially problematic situations that should be investigated:
```python
logger.warning("Slow query detected", extra={"duration_ms": 1500, "query": sql})
logger.warning("High memory usage", extra={"memory_percent": 85})
logger.warning("Cache miss rate high", extra={"miss_rate": 0.45})
```

### ERROR
Used for error conditions that need attention:
```python
logger.error("Database connection failed", exc_info=True)
logger.error("Task execution failed", extra={"task_id": task_id, "error": str(e)})
logger.error("API request failed", extra={"endpoint": "/api/movies", "status": 500})
```

### CRITICAL
Used for critical failures that may require immediate action:
```python
logger.critical("Database unavailable - application cannot continue")
logger.critical("Redis connection lost - cache unavailable")
```

## Structured Logging Format

All logs are output in JSON format for easy parsing and analysis:

```json
{
  "timestamp": "2026-02-07T14:30:28.748Z",
  "level": "INFO",
  "logger": "app.api.movies",
  "message": "GET /api/movies - Status: 200 - Duration: 45.23ms",
  "module": "movies",
  "function": "get_movies",
  "line": 42,
  "method": "GET",
  "endpoint": "/api/movies",
  "status_code": 200,
  "duration_ms": 45.23,
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Standard Fields

- `timestamp`: ISO 8601 UTC timestamp
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logger`: Logger name (module path)
- `message`: Human-readable log message
- `module`: Python module name
- `function`: Function name
- `line`: Line number in source code
- `exception`: Exception traceback (if applicable)

### Context Fields

Additional fields added based on context:

- `request_id`: Unique request identifier for tracing
- `user_id`: User identifier (if applicable)
- `duration_ms`: Operation duration in milliseconds
- `status_code`: HTTP status code
- `endpoint`: API endpoint path
- `method`: HTTP method
- `query_time_ms`: Database query duration
- `query`: SQL query (truncated to 200 chars)
- `cache_key`: Cache key being accessed
- `cache_hit`: Boolean indicating cache hit/miss
- `task_id`: Celery task identifier
- `task_name`: Task name
- `task_status`: Task status (pending, started, completed, error)

## Log Files and Rotation

### Log File Locations

All logs are stored in the `logs/` directory:

```
logs/
├── app.log              # General application logs
├── error.log            # Error-level logs only
├── performance.log      # Performance metrics
├── database.log         # Database queries
├── cache.log            # Cache operations
├── tasks.log            # Background tasks
└── api.log              # API requests/responses
```

### Log Rotation

Each log file is automatically rotated when it reaches 10 MB:

- **Max File Size**: 10 MB
- **Backup Count**: 10 files
- **Naming**: `app.log`, `app.log.1`, `app.log.2`, etc.
- **Retention**: ~100 MB per log type (10 files × 10 MB)

### Rotation Example

```
app.log          (10 MB - current)
app.log.1        (10 MB - rotated)
app.log.2        (10 MB - rotated)
...
app.log.10       (10 MB - oldest)
```

When a new rotation occurs, `app.log.10` is deleted.

## Specialized Loggers

### Performance Logger

Tracks performance metrics and slow operations:

```python
from app.logging_config import get_logger

perf_logger = get_logger("performance")
perf_logger.info("Slow query detected", extra={
    "query_time_ms": 1500,
    "query": "SELECT * FROM movies WHERE ...",
    "threshold_ms": 1000
})
```

### Database Logger

Logs all database operations:

```python
db_logger = get_logger("database")
db_logger.debug("Query executed", extra={
    "query": "SELECT * FROM movies",
    "duration_ms": 5.2,
    "rows_affected": 150
})
```

### Cache Logger

Logs cache operations:

```python
cache_logger = get_logger("cache")
cache_logger.debug("Cache operation", extra={
    "operation": "get",
    "cache_key": "movies:list:page:1",
    "hit": True,
    "duration_ms": 0.5
})
```

### Task Logger

Logs background task execution:

```python
task_logger = get_logger("tasks")
task_logger.info("Task started", extra={
    "task_name": "process_media_file",
    "task_id": "abc123def456",
    "status": "started"
})
```

### API Logger

Logs API requests and responses:

```python
api_logger = get_logger("api")
api_logger.info("API request", extra={
    "method": "GET",
    "endpoint": "/api/movies",
    "status_code": 200,
    "duration_ms": 45.23,
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
})
```

## Using the Logging Utilities

### Basic Usage

```python
from app.logging_config import get_logger, log_request, log_database_query

logger = get_logger(__name__)

# Log a simple message
logger.info("Processing started")

# Log with context
logger.info("User action", extra={"user_id": 123, "action": "search"})

# Log HTTP request
log_request(
    logger,
    method="GET",
    endpoint="/api/movies",
    status_code=200,
    duration_ms=45.23,
    request_id="550e8400-e29b-41d4-a716-446655440000"
)

# Log database query
log_database_query(
    logger,
    query="SELECT * FROM movies WHERE id = ?",
    duration_ms=5.2,
    status="success"
)

# Log cache operation
from app.logging_config import log_cache_operation
log_cache_operation(
    logger,
    operation="get",
    cache_key="movies:list:page:1",
    hit=True,
    duration_ms=0.5
)

# Log task execution
from app.logging_config import log_task_execution
log_task_execution(
    logger,
    task_name="process_media_file",
    task_id="abc123def456",
    status="completed",
    duration_ms=1234
)

# Log error
from app.logging_config import log_error
try:
    # Some operation
    pass
except Exception as e:
    log_error(
        logger,
        error=e,
        context={"operation": "fetch_movies"},
        request_id="550e8400-e29b-41d4-a716-446655440000"
    )
```

## Log Analysis Procedures

### Finding Errors

```bash
# View all errors
grep '"level": "ERROR"' logs/error.log | jq .

# Find errors for specific request
grep 'request_id.*550e8400' logs/app.log | jq .

# Find errors in specific module
grep '"logger": "app.api.movies"' logs/error.log | jq .
```

### Performance Analysis

```bash
# Find slow queries
grep '"level": "WARNING"' logs/performance.log | jq 'select(.query_time_ms > 1000)'

# Find slow API requests
grep '"level": "INFO"' logs/api.log | jq 'select(.duration_ms > 100)'

# Calculate average response time
grep '"level": "INFO"' logs/api.log | jq '.duration_ms' | awk '{sum+=$1; count++} END {print sum/count}'
```

### Tracing Requests

```bash
# Trace a specific request through all logs
REQUEST_ID="550e8400-e29b-41d4-a716-446655440000"
grep "$REQUEST_ID" logs/*.log | jq . | sort -k 2
```

### Monitoring Specific Components

```bash
# Monitor database queries
tail -f logs/database.log | jq 'select(.query_time_ms > 1000)'

# Monitor cache operations
tail -f logs/cache.log | jq 'select(.cache_hit == false)'

# Monitor task execution
tail -f logs/tasks.log | jq 'select(.task_status == "error")'
```

## Log Retention Policies

### Retention Schedule

- **Active Logs**: Current day's logs in primary files
- **Backup Logs**: Up to 10 backup files per log type
- **Total Retention**: ~100 MB per log type
- **Time Retention**: Approximately 7-14 days depending on log volume

### Archival

For long-term retention, implement external archival:

```bash
# Archive logs older than 7 days
find logs/ -name "*.log.*" -mtime +7 -exec gzip {} \;
find logs/ -name "*.log.*.gz" -mtime +30 -delete
```

### Cleanup

To manually clean up old logs:

```bash
# Remove all backup logs
rm logs/*.log.*

# Remove specific log type backups
rm logs/app.log.*
```

## Configuration

### Environment Variables

Configure logging via environment variables in `.env`:

```env
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Database query logging
DB_QUERY_LOGGING_ENABLED=true
DB_SLOW_QUERY_THRESHOLD=1.0
```

### Programmatic Configuration

```python
from app.logging_config import setup_logging, get_logger

# Initialize logging system
setup_logging()

# Get logger for module
logger = get_logger(__name__)
```

## Integration with Monitoring

Logs are integrated with the monitoring system for comprehensive observability:

- **Request Tracing**: `request_id` field enables request tracing across logs
- **Performance Metrics**: Duration fields feed into performance dashboards
- **Error Tracking**: Error logs trigger alerts and notifications
- **Audit Trail**: All operations logged for compliance and debugging

## Best Practices

1. **Use Structured Logging**: Always include context in `extra` parameter
2. **Include Request IDs**: Trace requests through the system
3. **Log at Appropriate Levels**: Use correct level for message type
4. **Avoid Logging Sensitive Data**: Never log passwords, tokens, or PII
5. **Use Specialized Loggers**: Use appropriate logger for component
6. **Include Context**: Add relevant context for debugging
7. **Monitor Log Volume**: Watch for excessive logging
8. **Regular Cleanup**: Archive and delete old logs regularly

## Troubleshooting

### Logs Not Appearing

1. Check log level configuration
2. Verify `logs/` directory exists and is writable
3. Check file permissions
4. Verify logger name matches module path

### High Disk Usage

1. Check log file sizes
2. Verify rotation is working
3. Implement archival process
4. Reduce log level if necessary

### Performance Impact

1. Monitor logging overhead
2. Consider async logging for high-volume scenarios
3. Reduce log level in production if needed
4. Use sampling for high-frequency operations

## Related Documentation

- [Monitoring Documentation](MONITORING.md)
- [Alerting Configuration](ALERTING.md)
- [API Reference](API_REFERENCE.md)
- [Deployment Guide](DEPLOYMENT.md)
