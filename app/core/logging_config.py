"""Centralized logging configuration with structured logging support"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    # Maps LogRecord attribute name -> JSON output key.
    # Only attributes present on the record are included.
    _EXTRA_FIELDS: Dict[str, str] = {
        "request_id": "request_id",
        "trace_id": "trace_id",
        "user_id": "user_id",
        "duration": "duration_ms",
        "status_code": "status_code",
        "endpoint": "endpoint",
        "method": "method",
        "query_time": "query_time_ms",
        "query": "query",
        "cache_key": "cache_key",
        "cache_hit": "cache_hit",
        "task_id": "task_id",
        "task_name": "task_name",
        "task_status": "task_status",
        "api_service": "api_service",
        "api_url": "api_url",
        "response_status": "response_status",
        "response_size": "response_size",
        "attempt": "attempt",
    }

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

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        for attr, key in self._EXTRA_FIELDS.items():
            if hasattr(record, attr):
                log_data[key] = getattr(record, attr)

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

    # Daily rotation: one file per day, keep 3 days of history
    def _daily_handler(filename: str, level: int) -> logging.handlers.TimedRotatingFileHandler:
        handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_dir / filename,
            when="midnight",
            interval=1,
            backupCount=3,
            encoding="utf-8",
            utc=True,
        )
        handler.setLevel(level)
        handler.setFormatter(console_formatter)
        handler.suffix = "%Y-%m-%d"
        return handler

    # General application log
    root_logger.addHandler(_daily_handler("app.log", getattr(logging, settings.log_level)))

    # Error log
    root_logger.addHandler(_daily_handler("error.log", logging.ERROR))

    # Performance log
    perf_logger = logging.getLogger("performance")
    perf_logger.addHandler(_daily_handler("performance.log", logging.INFO))

    # Database query log — catches app.core.database and SQLAlchemy loggers
    logging.getLogger("app.core.database").addHandler(_daily_handler("database.log", logging.DEBUG))
    logging.getLogger("app.core.init_db").addHandler(_daily_handler("database.log", logging.DEBUG))
    logging.getLogger("sqlalchemy.engine").addHandler(
        _daily_handler("database.log", logging.WARNING)
    )

    # Cache log — catches app.infrastructure.cache.*
    logging.getLogger("app.infrastructure.cache").addHandler(
        _daily_handler("cache.log", logging.DEBUG)
    )

    # Task log — catches app.tasks.*
    logging.getLogger("app.tasks").addHandler(_daily_handler("tasks.log", logging.DEBUG))

    # API request log — catches app.api.*
    logging.getLogger("app.api").addHandler(_daily_handler("api.log", logging.INFO))

    # External API log — catches both the explicit named logger (services_impl.py)
    # and __name__-based loggers under app.infrastructure.external_apis.*
    logging.getLogger("external_api").addHandler(_daily_handler("external_api.log", logging.DEBUG))
    logging.getLogger("app.infrastructure.external_apis").addHandler(
        _daily_handler("external_api.log", logging.DEBUG)
    )

    # Plex log — dedicated file for Plex client, auth, and router
    logging.getLogger("app.infrastructure.external_apis.plex").addHandler(
        _daily_handler("plex.log", logging.DEBUG)
    )
    logging.getLogger("app.api.v1.plex").addHandler(_daily_handler("plex.log", logging.DEBUG))

    # HTTP access log — file + console
    # Captures the log_requests middleware and uvicorn.access at INFO+
    access_handler = _daily_handler("access.log", logging.INFO)
    access_logger = logging.getLogger("access")
    access_logger.addHandler(access_handler)
    access_logger.propagate = True  # also reaches root → console

    # Redirect uvicorn's own access logger to file; keep propagation so
    # HTTP request lines remain visible in docker-compose logs / stdout.
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers.clear()
    uvicorn_access.addHandler(access_handler)
    uvicorn_access.propagate = True  # propagate to root → console


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
