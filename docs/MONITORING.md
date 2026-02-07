# Monitoring Architecture and Configuration

## Overview

The Media Management Web Tool implements comprehensive monitoring infrastructure for production systems. The monitoring system collects metrics from multiple layers (system, application, database, cache, tasks) and provides real-time visibility into application health and performance.

## Monitoring Architecture

### Components

1. **Monitoring Service** (`app/services/monitoring.py`)
   - Centralized metrics collection
   - System metrics (CPU, memory, disk)
   - Application metrics (requests, errors, latency)
   - Database metrics (connections, queries, performance)
   - Cache metrics (hit rate, memory usage)
   - Task metrics (queue size, execution time)
   - Health check utilities

2. **Prometheus Integration** (`app/services/prometheus_metrics.py`)
   - Prometheus-compatible metrics
   - Metric decorators for automatic tracking
   - Metrics aggregation and reporting
   - Prometheus scrape endpoint

3. **Health Check Endpoints** (`app/api/health.py`)
   - Basic health check
   - Kubernetes liveness probe
   - Kubernetes readiness probe
   - Detailed health check with dependencies
   - System metrics endpoint
   - Prometheus metrics endpoint

## Metrics Collection

### System Metrics

System-level metrics collected every health check:

```python
from app.services.monitoring import get_monitoring_service

monitoring = get_monitoring_service()
system_metrics = monitoring.get_system_metrics()

# Returns:
# - cpu_percent: System CPU usage (0-100%)
# - memory_percent: System memory usage (0-100%)
# - memory_available_mb: Available memory in MB
# - disk_percent: Disk usage (0-100%)
# - disk_available_mb: Available disk space in MB
# - process_cpu_percent: Process CPU usage (0-100%)
# - process_memory_mb: Process memory usage in MB
# - process_memory_percent: Process memory percentage
```

### Application Metrics

Application-level metrics tracked throughout request lifecycle:

```python
# Request metrics
monitoring.record_request(duration_ms=45.23, status_code=200)

# Returns:
# - total_requests: Total HTTP requests
# - total_errors: Total error responses (4xx, 5xx)
# - avg_response_time_ms: Average response time
# - requests_per_second: Request throughput
# - error_rate: Percentage of failed requests
```

### Database Metrics

Database operation metrics:

```python
# Query metrics
monitoring.record_query(duration_ms=5.2, is_slow=False)

# Returns:
# - active_connections: Active database connections
# - total_queries: Total queries executed
# - slow_queries: Queries exceeding threshold
# - avg_query_time_ms: Average query duration
# - connection_errors: Failed connections
```

### Cache Metrics

Cache operation metrics:

```python
# Cache operations
monitoring.record_cache_hit()
monitoring.record_cache_miss()
monitoring.record_cache_eviction()

# Returns:
# - hit_count: Total cache hits
# - miss_count: Total cache misses
# - hit_rate: Hit rate percentage
# - memory_used_mb: Cache memory usage
# - eviction_count: Total evictions
```

### Task Metrics

Background task metrics:

```python
# Task execution
monitoring.record_task_execution(duration_ms=1234, success=True)

# Returns:
# - queue_size: Pending tasks in queue
# - active_tasks: Currently executing tasks
# - completed_tasks: Successfully completed tasks
# - failed_tasks: Failed task executions
# - avg_execution_time_ms: Average execution time
```

## Health Checks

### Basic Health Check

```bash
curl http://localhost:8000/health/
```

Response:
```json
{
  "status": "healthy",
  "message": "Application is running"
}
```

### Kubernetes Liveness Probe

```bash
curl http://localhost:8000/health/live
```

Response:
```json
{
  "status": "alive",
  "message": "Application is running"
}
```

**Configuration in Kubernetes:**
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### Kubernetes Readiness Probe

```bash
curl http://localhost:8000/health/ready
```

Response:
```json
{
  "status": "ready",
  "message": "Application is ready to serve traffic"
}
```

**Configuration in Kubernetes:**
```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 5
  failureThreshold: 3
```

### Detailed Health Check

```bash
curl http://localhost:8000/health/detailed
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-07T14:30:28.748Z",
  "checks": {
    "system": {
      "status": "healthy",
      "cpu_percent": 25.5,
      "memory_percent": 45.2,
      "disk_percent": 60.1
    },
    "application": {
      "status": "healthy",
      "error_rate": 0.5,
      "requests_per_second": 12.3
    },
    "cache": {
      "status": "healthy"
    },
    "database": {
      "status": "healthy"
    }
  }
}
```

### Database Health Check

```bash
curl http://localhost:8000/health/db
```

Response:
```json
{
  "status": "healthy",
  "message": "Database connection is working"
}
```

## Metrics Endpoints

### System Metrics

```bash
curl http://localhost:8000/health/metrics
```

Response:
```json
{
  "system": {
    "timestamp": "2026-02-07T14:30:28.748Z",
    "cpu_percent": 25.5,
    "memory_percent": 45.2,
    "memory_available_mb": 8192.5,
    "disk_percent": 60.1,
    "disk_available_mb": 204800.0,
    "process_cpu_percent": 5.2,
    "process_memory_mb": 256.3,
    "process_memory_percent": 2.1
  },
  "application": {
    "timestamp": "2026-02-07T14:30:28.748Z",
    "total_requests": 1234,
    "total_errors": 6,
    "avg_response_time_ms": 45.23,
    "requests_per_second": 12.3,
    "error_rate": 0.49
  },
  "database": {
    "timestamp": "2026-02-07T14:30:28.748Z",
    "active_connections": 5,
    "total_queries": 5678,
    "slow_queries": 12,
    "avg_query_time_ms": 5.2,
    "connection_errors": 0
  },
  "cache": {
    "timestamp": "2026-02-07T14:30:28.748Z",
    "hit_count": 3456,
    "miss_count": 234,
    "hit_rate": 93.65,
    "memory_used_mb": 512.5,
    "eviction_count": 0
  },
  "tasks": {
    "timestamp": "2026-02-07T14:30:28.748Z",
    "queue_size": 0,
    "active_tasks": 2,
    "completed_tasks": 890,
    "failed_tasks": 2,
    "avg_execution_time_ms": 1234.5
  }
}
```

### Prometheus Metrics

```bash
curl http://localhost:8000/health/metrics/prometheus
```

Response (Prometheus format):
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/movies",status="200"} 1234.0

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/api/movies",le="0.01"} 234.0
http_request_duration_seconds_bucket{method="GET",endpoint="/api/movies",le="0.025"} 456.0
...
```

## Prometheus Metrics

### HTTP Request Metrics

```
http_requests_total{method, endpoint, status}
http_request_duration_seconds{method, endpoint}
http_request_size_bytes{method, endpoint}
http_response_size_bytes{method, endpoint}
```

### Database Metrics

```
db_queries_total{operation, status}
db_query_duration_seconds{operation}
db_connections_active
db_connections_total{status}
db_slow_queries_total
```

### Cache Metrics

```
cache_hits_total{cache_name}
cache_misses_total{cache_name}
cache_evictions_total{cache_name}
cache_memory_bytes{cache_name}
cache_operation_duration_seconds{operation}
```

### Task Metrics

```
celery_tasks_total{task_name, status}
celery_task_duration_seconds{task_name}
celery_queue_size{queue_name}
celery_active_tasks
```

### System Metrics

```
system_cpu_percent
system_memory_percent
system_memory_available_bytes
system_disk_percent
system_disk_available_bytes
process_cpu_percent
process_memory_bytes
```

### Application Metrics

```
app_errors_total{error_type}
app_uptime_seconds
media_items_total{media_type}
search_queries_total{search_type}
```

## Using Monitoring Service

### Basic Usage

```python
from app.services.monitoring import get_monitoring_service

monitoring = get_monitoring_service()

# Record HTTP request
monitoring.record_request(duration_ms=45.23, status_code=200)

# Record database query
monitoring.record_query(duration_ms=5.2, is_slow=False)

# Record cache operations
monitoring.record_cache_hit()
monitoring.record_cache_miss()

# Record task execution
monitoring.record_task_execution(duration_ms=1234, success=True)

# Get all metrics
all_metrics = monitoring.get_all_metrics()

# Get health status
health = monitoring.health_check()
```

### Using Prometheus Decorators

```python
from app.services.prometheus_metrics import (
    track_http_request,
    track_db_query,
    track_cache_operation,
    track_task_execution
)

@track_http_request("GET", "/api/movies")
async def get_movies():
    return {"movies": []}

@track_db_query("SELECT")
def fetch_movies():
    return db.query(Movie).all()

@track_cache_operation("get", "redis")
def get_from_cache(key):
    return cache.get(key)

@track_task_execution("process_media_file")
def process_media_file(file_path):
    # Process file
    pass
```

## Monitoring Dashboard Configuration

### Grafana Integration

Prometheus metrics can be visualized in Grafana:

1. **Add Prometheus Data Source**
   - URL: `http://prometheus:9090`
   - Access: Server

2. **Create Dashboards**
   - Import dashboard JSON from `docs/GRAFANA_DASHBOARDS.md`
   - Or create custom dashboards using Prometheus queries

3. **Key Metrics to Monitor**
   - Request rate and latency
   - Error rate and types
   - Database query performance
   - Cache hit rate
   - System resource usage
   - Task execution metrics

## Performance Monitoring

### Request Performance

Monitor HTTP request latency:

```promql
# Average request duration
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Request rate
rate(http_requests_total[5m])
```

### Database Performance

Monitor database query performance:

```promql
# Average query duration
rate(db_query_duration_seconds_sum[5m]) / rate(db_query_duration_seconds_count[5m])

# Slow query rate
rate(db_slow_queries_total[5m])

# Query error rate
rate(db_queries_total{status="error"}[5m]) / rate(db_queries_total[5m])
```

### Cache Performance

Monitor cache efficiency:

```promql
# Cache hit rate
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))

# Cache memory usage
cache_memory_bytes

# Eviction rate
rate(cache_evictions_total[5m])
```

### System Performance

Monitor system resources:

```promql
# CPU usage
system_cpu_percent

# Memory usage
system_memory_percent

# Disk usage
system_disk_percent

# Process memory
process_memory_bytes
```

## Troubleshooting with Metrics

### High Error Rate

1. Check `app_errors_total` by error type
2. Review error logs for details
3. Check database and cache health
4. Monitor system resources

### Slow Requests

1. Check `http_request_duration_seconds` percentiles
2. Identify slow endpoints
3. Check database query performance
4. Review cache hit rate

### Database Issues

1. Monitor `db_query_duration_seconds`
2. Check `db_slow_queries_total`
3. Monitor `db_connections_active`
4. Review database logs

### Cache Issues

1. Monitor `cache_hits_total` vs `cache_misses_total`
2. Check `cache_memory_bytes`
3. Monitor `cache_evictions_total`
4. Review cache operation duration

### Resource Exhaustion

1. Monitor `system_cpu_percent`
2. Monitor `system_memory_percent`
3. Monitor `system_disk_percent`
4. Check process-specific metrics

## Best Practices

1. **Monitor Key Metrics**: Focus on business-critical metrics
2. **Set Baselines**: Establish normal performance baselines
3. **Alert on Anomalies**: Configure alerts for deviations
4. **Regular Review**: Review metrics regularly for trends
5. **Correlate Metrics**: Look for correlations between metrics
6. **Document Thresholds**: Document alert thresholds and reasons
7. **Test Alerts**: Regularly test alert configurations
8. **Automate Response**: Automate responses to common issues

## Related Documentation

- [Logging Documentation](LOGGING.md)
- [Alerting Configuration](ALERTING.md)
- [Grafana Dashboards](GRAFANA_DASHBOARDS.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Troubleshooting Guide](DEPLOYMENT_TROUBLESHOOTING.md)
