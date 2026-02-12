"""Centralized logging configuration with structured logging support"""

import logging
import logging.handlers
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import structlog

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if hasattr(record, "duration"):
            log_data["duration_ms"] = record.duration

        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code

        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint

        if hasattr(record, "method"):
            log_data["method"] = record.method

        if hasattr(record, "query_time"):
            log_data["query_time_ms"] = record.query_time

        if hasattr(record, "query"):
            log_data["query"] = record.query

        if hasattr(record, "cache_key"):
            log_data["cache_key"] = record.cache_key

        if hasattr(record, "cache_hit"):
            log_data["cache_hit"] = record.cache_hit

        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id

        if hasattr(record, "task_name"):
            log_data["task_name"] = record.task_name

        if hasattr(record, "task_status"):
            log_data["task_status"] = record.task_status

        return json.dumps(log_data)


def setup_logging() -> None:
    """Configure centralized logging with structured format"""

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level))
    console_formatter = JSONFormatter()
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,  # Keep 10 backup files
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, settings.log_level))
    file_handler.setFormatter(console_formatter)
    root_logger.addHandler(file_handler)

    # Error file handler with rotation
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "error.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(console_formatter)
    root_logger.addHandler(error_handler)

    # Performance file handler with rotation
    perf_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "performance.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,
        encoding="utf-8",
    )
    perf_handler.setLevel(logging.INFO)
    perf_handler.setFormatter(console_formatter)
    perf_logger = logging.getLogger("performance")
    perf_logger.addHandler(perf_handler)

    # Database query logger
    db_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "database.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,
        encoding="utf-8",
    )
    db_handler.setLevel(logging.DEBUG)
    db_handler.setFormatter(console_formatter)
    db_logger = logging.getLogger("database")
    db_logger.addHandler(db_handler)

    # Cache logger
    cache_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "cache.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,
        encoding="utf-8",
    )
    cache_handler.setLevel(logging.DEBUG)
    cache_handler.setFormatter(console_formatter)
    cache_logger = logging.getLogger("cache")
    cache_logger.addHandler(cache_handler)

    # Task logger
    task_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "tasks.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,
        encoding="utf-8",
    )
    task_handler.setLevel(logging.DEBUG)
    task_handler.setFormatter(console_formatter)
    task_logger = logging.getLogger("tasks")
    task_logger.addHandler(task_handler)

    # API logger
    api_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "api.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,
        encoding="utf-8",
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(console_formatter)
    api_logger = logging.getLogger("api")
    api_logger.addHandler(api_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module"""
    return logging.getLogger(name)


def log_request(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> None:
    """Log HTTP request with structured data"""
    extra = {
        "method": method,
        "endpoint": endpoint,
        "status_code": status_code,
        "duration": duration_ms,
    }
    if request_id:
        extra["request_id"] = request_id
    if user_id:
        extra["user_id"] = user_id

    logger.info(
        f"{method} {endpoint} - Status: {status_code} - Duration: {duration_ms:.2f}ms",
        extra=extra,
    )


def log_database_query(
    logger: logging.Logger,
    query: str,
    duration_ms: float,
    status: str = "success",
    error: Optional[str] = None,
) -> None:
    """Log database query with performance metrics"""
    extra = {
        "query": query[:200],  # Truncate long queries
        "query_time": duration_ms,
        "status": status,
    }
    if error:
        extra["error"] = error

    if duration_ms > settings.db_slow_query_threshold * 1000:
        logger.warning(f"Slow query detected: {duration_ms:.2f}ms", extra=extra)
    else:
        logger.debug(f"Query executed: {duration_ms:.2f}ms", extra=extra)


def log_cache_operation(
    logger: logging.Logger,
    operation: str,
    cache_key: str,
    hit: bool,
    duration_ms: float,
) -> None:
    """Log cache operation with metrics"""
    extra = {
        "cache_key": cache_key,
        "cache_hit": hit,
        "duration": duration_ms,
    }
    logger.debug(f"Cache {operation}: {cache_key} - Hit: {hit}", extra=extra)


def log_task_execution(
    logger: logging.Logger,
    task_name: str,
    task_id: str,
    status: str,
    duration_ms: Optional[float] = None,
    error: Optional[str] = None,
) -> None:
    """Log task execution with metrics"""
    extra = {
        "task_name": task_name,
        "task_id": task_id,
        "task_status": status,
    }
    if duration_ms:
        extra["duration"] = duration_ms
    if error:
        extra["error"] = error

    if status == "error":
        logger.error(f"Task {task_name} failed: {error}", extra=extra)
    elif status == "completed":
        logger.info(f"Task {task_name} completed in {duration_ms:.2f}ms", extra=extra)
    else:
        logger.info(f"Task {task_name} {status}", extra=extra)


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> None:
    """Log error with context information"""
    extra = {}
    if context:
        extra.update(context)
    if request_id:
        extra["request_id"] = request_id

    logger.error(f"Error: {str(error)}", exc_info=True, extra=extra)
