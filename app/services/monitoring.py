"""Monitoring service for system and application metrics"""

import psutil
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import redis

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System metrics data class"""

    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_percent: float
    disk_available_mb: float
    process_cpu_percent: float
    process_memory_mb: float
    process_memory_percent: float


@dataclass
class ApplicationMetrics:
    """Application metrics data class"""

    timestamp: str
    total_requests: int
    total_errors: int
    avg_response_time_ms: float
    requests_per_second: float
    error_rate: float


@dataclass
class DatabaseMetrics:
    """Database metrics data class"""

    timestamp: str
    active_connections: int
    total_queries: int
    slow_queries: int
    avg_query_time_ms: float
    connection_errors: int


@dataclass
class CacheMetrics:
    """Cache metrics data class"""

    timestamp: str
    hit_count: int
    miss_count: int
    hit_rate: float
    memory_used_mb: float
    eviction_count: int


@dataclass
class TaskMetrics:
    """Task metrics data class"""

    timestamp: str
    queue_size: int
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    avg_execution_time_ms: float


class MonitoringService:
    """Service for collecting and managing application metrics"""

    def __init__(self):
        """Initialize monitoring service"""
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.slow_query_count = 0
        self.total_query_time = 0.0
        self.query_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_evictions = 0
        self.task_count = 0
        self.failed_task_count = 0
        self.total_task_time = 0.0

        # Try to connect to Redis for cache metrics
        try:
            self.redis_client = redis.from_url(settings.redis_url)
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Could not connect to Redis for metrics: {e}")
            self.redis_client = None

    def get_system_metrics(self) -> SystemMetrics:
        """Collect system metrics"""
        try:
            # System-wide metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Process-specific metrics
            process = psutil.Process()
            process_cpu = process.cpu_percent(interval=0.1)
            process_memory = process.memory_info()

            return SystemMetrics(
                timestamp=datetime.utcnow().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_mb=memory.available / (1024 * 1024),
                disk_percent=disk.percent,
                disk_available_mb=disk.free / (1024 * 1024),
                process_cpu_percent=process_cpu,
                process_memory_mb=process_memory.rss / (1024 * 1024),
                process_memory_percent=process.memory_percent(),
            )
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.utcnow().isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available_mb=0.0,
                disk_percent=0.0,
                disk_available_mb=0.0,
                process_cpu_percent=0.0,
                process_memory_mb=0.0,
                process_memory_percent=0.0,
            )

    def get_application_metrics(self) -> ApplicationMetrics:
        """Get application metrics"""
        uptime_seconds = time.time() - self.start_time
        requests_per_second = (
            self.request_count / uptime_seconds if uptime_seconds > 0 else 0
        )
        avg_response_time = (
            self.total_response_time / self.request_count
            if self.request_count > 0
            else 0
        )
        error_rate = (
            (self.error_count / self.request_count * 100)
            if self.request_count > 0
            else 0
        )

        return ApplicationMetrics(
            timestamp=datetime.utcnow().isoformat(),
            total_requests=self.request_count,
            total_errors=self.error_count,
            avg_response_time_ms=avg_response_time * 1000,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
        )

    def get_database_metrics(self) -> DatabaseMetrics:
        """Get database metrics"""
        avg_query_time = (
            self.total_query_time / self.query_count if self.query_count > 0 else 0
        )

        return DatabaseMetrics(
            timestamp=datetime.utcnow().isoformat(),
            active_connections=0,  # Would be populated from connection pool
            total_queries=self.query_count,
            slow_queries=self.slow_query_count,
            avg_query_time_ms=avg_query_time * 1000,
            connection_errors=0,
        )

    def get_cache_metrics(self) -> CacheMetrics:
        """Get cache metrics"""
        total_cache_ops = self.cache_hits + self.cache_misses
        hit_rate = (
            (self.cache_hits / total_cache_ops * 100) if total_cache_ops > 0 else 0
        )

        memory_used = 0.0
        if self.redis_client:
            try:
                info = self.redis_client.info("memory")
                memory_used = info.get("used_memory", 0) / (1024 * 1024)
            except Exception as e:
                logger.warning(f"Could not get Redis memory info: {e}")

        return CacheMetrics(
            timestamp=datetime.utcnow().isoformat(),
            hit_count=self.cache_hits,
            miss_count=self.cache_misses,
            hit_rate=hit_rate,
            memory_used_mb=memory_used,
            eviction_count=self.cache_evictions,
        )

    def get_task_metrics(self) -> TaskMetrics:
        """Get task metrics"""
        avg_execution_time = (
            self.total_task_time / self.task_count if self.task_count > 0 else 0
        )

        return TaskMetrics(
            timestamp=datetime.utcnow().isoformat(),
            queue_size=0,  # Would be populated from Celery
            active_tasks=0,  # Would be populated from Celery
            completed_tasks=self.task_count,
            failed_tasks=self.failed_task_count,
            avg_execution_time_ms=avg_execution_time * 1000,
        )

    def record_request(self, duration_ms: float, status_code: int) -> None:
        """Record HTTP request metrics"""
        self.request_count += 1
        self.total_response_time += duration_ms / 1000

        if status_code >= 400:
            self.error_count += 1

    def record_query(self, duration_ms: float, is_slow: bool = False) -> None:
        """Record database query metrics"""
        self.query_count += 1
        self.total_query_time += duration_ms / 1000

        if is_slow:
            self.slow_query_count += 1

    def record_cache_hit(self) -> None:
        """Record cache hit"""
        self.cache_hits += 1

    def record_cache_miss(self) -> None:
        """Record cache miss"""
        self.cache_misses += 1

    def record_cache_eviction(self) -> None:
        """Record cache eviction"""
        self.cache_evictions += 1

    def record_task_execution(self, duration_ms: float, success: bool = True) -> None:
        """Record task execution metrics"""
        self.task_count += 1
        self.total_task_time += duration_ms / 1000

        if not success:
            self.failed_task_count += 1

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        return {
            "system": asdict(self.get_system_metrics()),
            "application": asdict(self.get_application_metrics()),
            "database": asdict(self.get_database_metrics()),
            "cache": asdict(self.get_cache_metrics()),
            "tasks": asdict(self.get_task_metrics()),
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
        }

        # System health
        try:
            system_metrics = self.get_system_metrics()
            health_status["checks"]["system"] = {
                "status": "healthy",
                "cpu_percent": system_metrics.cpu_percent,
                "memory_percent": system_metrics.memory_percent,
                "disk_percent": system_metrics.disk_percent,
            }

            # Alert if thresholds exceeded
            if system_metrics.cpu_percent > 80:
                health_status["checks"]["system"]["status"] = "warning"
                health_status["status"] = "degraded"

            if system_metrics.memory_percent > 85:
                health_status["checks"]["system"]["status"] = "warning"
                health_status["status"] = "degraded"

            if system_metrics.disk_percent > 90:
                health_status["checks"]["system"]["status"] = "warning"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["checks"]["system"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "unhealthy"

        # Application health
        try:
            app_metrics = self.get_application_metrics()
            health_status["checks"]["application"] = {
                "status": "healthy",
                "error_rate": app_metrics.error_rate,
                "requests_per_second": app_metrics.requests_per_second,
            }

            if app_metrics.error_rate > 5:
                health_status["checks"]["application"]["status"] = "warning"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["checks"]["application"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_status["status"] = "unhealthy"

        # Cache health
        try:
            if self.redis_client:
                self.redis_client.ping()
                health_status["checks"]["cache"] = {"status": "healthy"}
            else:
                health_status["checks"]["cache"] = {"status": "unavailable"}
        except Exception as e:
            health_status["checks"]["cache"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"

        return health_status


# Global monitoring service instance
_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Get or create the global monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service
