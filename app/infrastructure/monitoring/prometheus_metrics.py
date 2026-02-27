"""Prometheus metrics integration for monitoring"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    CollectorRegistry,
    generate_latest,
)
import time
import asyncio
from typing import Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Create a custom registry for application metrics
app_registry = CollectorRegistry()

# HTTP Request Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=app_registry,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=app_registry,
)

http_request_size_bytes = Summary(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    registry=app_registry,
)

http_response_size_bytes = Summary(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
    registry=app_registry,
)

# Database Metrics
db_queries_total = Counter(
    "db_queries_total",
    "Total database queries",
    ["operation", "status"],
    registry=app_registry,
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
    registry=app_registry,
)

db_connections_active = Gauge(
    "db_connections_active",
    "Active database connections",
    registry=app_registry,
)

db_connections_total = Counter(
    "db_connections_total",
    "Total database connections created",
    ["status"],
    registry=app_registry,
)

db_slow_queries_total = Counter(
    "db_slow_queries_total",
    "Total slow database queries",
    registry=app_registry,
)

# Cache Metrics
cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_name"],
    registry=app_registry,
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_name"],
    registry=app_registry,
)

cache_evictions_total = Counter(
    "cache_evictions_total",
    "Total cache evictions",
    ["cache_name"],
    registry=app_registry,
)

cache_memory_bytes = Gauge(
    "cache_memory_bytes",
    "Cache memory usage in bytes",
    ["cache_name"],
    registry=app_registry,
)

cache_operation_duration_seconds = Histogram(
    "cache_operation_duration_seconds",
    "Cache operation duration in seconds",
    ["operation"],
    buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1),
    registry=app_registry,
)

# Task Metrics
celery_tasks_total = Counter(
    "celery_tasks_total",
    "Total Celery tasks",
    ["task_name", "status"],
    registry=app_registry,
)

celery_task_duration_seconds = Histogram(
    "celery_task_duration_seconds",
    "Celery task duration in seconds",
    ["task_name"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 300.0),
    registry=app_registry,
)

celery_queue_size = Gauge(
    "celery_queue_size",
    "Celery queue size",
    ["queue_name"],
    registry=app_registry,
)

celery_active_tasks = Gauge(
    "celery_active_tasks",
    "Active Celery tasks",
    registry=app_registry,
)

# System Metrics
system_cpu_percent = Gauge(
    "system_cpu_percent",
    "System CPU usage percentage",
    registry=app_registry,
)

system_memory_percent = Gauge(
    "system_memory_percent",
    "System memory usage percentage",
    registry=app_registry,
)

system_memory_available_bytes = Gauge(
    "system_memory_available_bytes",
    "Available system memory in bytes",
    registry=app_registry,
)

system_disk_percent = Gauge(
    "system_disk_percent",
    "System disk usage percentage",
    registry=app_registry,
)

system_disk_available_bytes = Gauge(
    "system_disk_available_bytes",
    "Available disk space in bytes",
    registry=app_registry,
)

process_cpu_percent = Gauge(
    "process_cpu_percent",
    "Process CPU usage percentage",
    registry=app_registry,
)

process_memory_bytes = Gauge(
    "process_memory_bytes",
    "Process memory usage in bytes",
    registry=app_registry,
)

# Application Metrics
app_errors_total = Counter(
    "app_errors_total",
    "Total application errors",
    ["error_type"],
    registry=app_registry,
)

app_uptime_seconds = Gauge(
    "app_uptime_seconds",
    "Application uptime in seconds",
    registry=app_registry,
)

# Business Metrics
media_items_total = Gauge(
    "media_items_total",
    "Total media items in database",
    ["media_type"],
    registry=app_registry,
)

search_queries_total = Counter(
    "search_queries_total",
    "Total search queries",
    ["search_type"],
    registry=app_registry,
)


def track_http_request(method: str, endpoint: str):
    """Decorator to track HTTP request metrics"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                status = getattr(result, "status_code", 200)
                http_requests_total.labels(
                    method=method, endpoint=endpoint, status=status
                ).inc()
                http_request_duration_seconds.labels(
                    method=method, endpoint=endpoint
                ).observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                http_requests_total.labels(
                    method=method, endpoint=endpoint, status=500
                ).inc()
                http_request_duration_seconds.labels(
                    method=method, endpoint=endpoint
                ).observe(duration)
                app_errors_total.labels(error_type=type(e).__name__).inc()
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                status = getattr(result, "status_code", 200)
                http_requests_total.labels(
                    method=method, endpoint=endpoint, status=status
                ).inc()
                http_request_duration_seconds.labels(
                    method=method, endpoint=endpoint
                ).observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                http_requests_total.labels(
                    method=method, endpoint=endpoint, status=500
                ).inc()
                http_request_duration_seconds.labels(
                    method=method, endpoint=endpoint
                ).observe(duration)
                app_errors_total.labels(error_type=type(e).__name__).inc()
                raise

        # Return async wrapper if function is async, otherwise sync wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def track_db_query(operation: str):
    """Decorator to track database query metrics"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                db_queries_total.labels(operation=operation, status="success").inc()
                db_query_duration_seconds.labels(operation=operation).observe(duration)

                # Track slow queries
                if duration > 1.0:  # 1 second threshold
                    db_slow_queries_total.inc()

                return result
            except Exception as e:
                duration = time.time() - start_time
                db_queries_total.labels(operation=operation, status="error").inc()
                db_query_duration_seconds.labels(operation=operation).observe(duration)
                app_errors_total.labels(error_type="database_error").inc()
                raise

        return wrapper

    return decorator


def track_cache_operation(operation: str, cache_name: str = "redis"):
    """Decorator to track cache operation metrics"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                cache_operation_duration_seconds.labels(operation=operation).observe(
                    duration
                )

                # Track hits/misses if applicable
                if operation == "get" and result is not None:
                    cache_hits_total.labels(cache_name=cache_name).inc()
                elif operation == "get":
                    cache_misses_total.labels(cache_name=cache_name).inc()

                return result
            except Exception as e:
                duration = time.time() - start_time
                cache_operation_duration_seconds.labels(operation=operation).observe(
                    duration
                )
                app_errors_total.labels(error_type="cache_error").inc()
                raise

        return wrapper

    return decorator


def track_task_execution(task_name: str):
    """Decorator to track Celery task execution metrics"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                celery_tasks_total.labels(task_name=task_name, status="success").inc()
                celery_task_duration_seconds.labels(task_name=task_name).observe(
                    duration
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                celery_tasks_total.labels(task_name=task_name, status="error").inc()
                celery_task_duration_seconds.labels(task_name=task_name).observe(
                    duration
                )
                app_errors_total.labels(error_type="task_error").inc()
                raise

        return wrapper

    return decorator


def update_system_metrics(monitoring_service) -> None:
    """Update system metrics from monitoring service"""
    try:
        metrics = monitoring_service.get_system_metrics()
        system_cpu_percent.set(metrics.cpu_percent)
        system_memory_percent.set(metrics.memory_percent)
        system_memory_available_bytes.set(metrics.memory_available_mb * 1024 * 1024)
        system_disk_percent.set(metrics.disk_percent)
        system_disk_available_bytes.set(metrics.disk_available_mb * 1024 * 1024)
        process_cpu_percent.set(metrics.process_cpu_percent)
        process_memory_bytes.set(metrics.process_memory_mb * 1024 * 1024)
    except Exception as e:
        logger.error(f"Error updating system metrics: {e}")


def get_metrics() -> bytes:
    """Get all metrics in Prometheus format"""
    return generate_latest(app_registry)
