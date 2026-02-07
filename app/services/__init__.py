"""Services package for business logic"""

# Import service classes for public API
# Note: Lazy imports are used to avoid circular dependencies with database module
from app.services.search_service import SearchFilters
from app.services.monitoring import MonitoringService


# Lazy imports to avoid circular dependency: database -> services -> redis_cache
def __getattr__(name):
    """Lazy load services to avoid circular imports"""
    if name == "RedisCacheService":
        from app.services.redis_cache import RedisCacheService

        return RedisCacheService
    elif name == "BatchOperationService":
        from app.services.batch_operations import BatchOperationService

        return BatchOperationService
    elif name == "QueryPerformanceTracker":
        from app.services.db_optimization import QueryPerformanceTracker

        return QueryPerformanceTracker
    elif name == "MediaFileEventHandler":
        from app.services.file_monitor import MediaFileEventHandler

        return MediaFileEventHandler
    elif name == "FileQueueManager":
        from app.services.file_queue_manager import FileQueueManager

        return FileQueueManager
    elif name == "PatternRecognizer":
        from app.services.pattern_recognition import PatternRecognizer

        return PatternRecognizer
    elif name == "app_registry":
        from app.services.prometheus_metrics import app_registry

        return app_registry
    elif name == "http_requests_total":
        from app.services.prometheus_metrics import http_requests_total

        return http_requests_total
    elif name == "http_request_duration_seconds":
        from app.services.prometheus_metrics import http_request_duration_seconds

        return http_request_duration_seconds
    elif name == "http_request_size_bytes":
        from app.services.prometheus_metrics import http_request_size_bytes

        return http_request_size_bytes
    elif name == "http_response_size_bytes":
        from app.services.prometheus_metrics import http_response_size_bytes

        return http_response_size_bytes
    elif name == "TaskErrorHandler":
        from app.services.task_error_handler import TaskErrorHandler

        return TaskErrorHandler
    elif name == "FFProbeWrapper":
        from app.services.ffprobe_wrapper import FFProbeWrapper

        return FFProbeWrapper
    elif name == "CacheService":
        from app.services_impl import CacheService

        return CacheService
    elif name == "OMDBService":
        from app.services_impl import OMDBService

        return OMDBService
    elif name == "TVDBService":
        from app.services_impl import TVDBService

        return TVDBService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "RedisCacheService",
    "SearchFilters",
    "BatchOperationService",
    "QueryPerformanceTracker",
    "MediaFileEventHandler",
    "FileQueueManager",
    "MonitoringService",
    "PatternRecognizer",
    "app_registry",
    "http_requests_total",
    "http_request_duration_seconds",
    "http_request_size_bytes",
    "http_response_size_bytes",
    "TaskErrorHandler",
    "FFProbeWrapper",
    "CacheService",
    "OMDBService",
    "TVDBService",
]
