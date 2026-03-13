"""Health check endpoints"""

import collections
import json
import logging
from pathlib import Path
from typing import Any

import redis
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.domain.plex.models import PlexConnection
from app.infrastructure.monitoring.monitoring_service import get_monitoring_service
from app.infrastructure.monitoring.prometheus_metrics import get_metrics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])

_LOG_DIR = Path(__file__).resolve().parents[4] / "logs"

_COMPONENT_LOG_FILES: dict[str, str] = {
    "database": str(_LOG_DIR / "database.log"),
    "cache": str(_LOG_DIR / "cache.log"),
    "tasks": str(_LOG_DIR / "tasks.log"),
    "api": str(_LOG_DIR / "api.log"),
    "external_api": str(_LOG_DIR / "external_api.log"),
    "plex": str(_LOG_DIR / "plex.log"),
}


def _tail_log(filepath: str, n: int) -> list[dict[str, Any]]:
    """Return the last n parsed log entries from a JSON-per-line log file."""
    path = Path(filepath)
    if not path.exists():
        return []
    try:
        with path.open(encoding="utf-8") as fh:
            tail = collections.deque(fh, maxlen=n)
        result: list[dict[str, Any]] = []
        for raw in tail:
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
                result.append(
                    {
                        "timestamp": entry.get("timestamp", ""),
                        "level": entry.get("level", ""),
                        "message": entry.get("message", ""),
                    }
                )
            except json.JSONDecodeError:
                result.append({"timestamp": "", "level": "RAW", "message": raw})
        return result
    except Exception as exc:
        logger.warning("Failed to read log file %s: %s", filepath, exc)
        return []


@router.get("/logs")
async def component_logs(
    lines: int = Query(10, ge=1, le=500, description="Number of log lines per component")
) -> dict[str, list[dict[str, Any]]]:
    """Return the last N log lines per component."""
    return {
        component: _tail_log(filepath, lines)
        for component, filepath in _COMPONENT_LOG_FILES.items()
    }


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "message": "Application is running",
    }


@router.get("/live")
async def liveness_probe():
    """Kubernetes liveness probe - checks if application is running"""
    return {
        "status": "alive",
        "message": "Application is running",
    }


@router.get("/ready")
async def readiness_probe(db: Session = Depends(get_db)):
    """Kubernetes readiness probe - checks if application is ready to serve traffic"""
    try:
        # Check database
        db.execute(text("SELECT 1"))

        # Check Redis
        try:
            redis_client = redis.from_url(settings.redis_url)
            redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            return {
                "status": "not_ready",
                "message": "Redis connection failed",
            }

        return {
            "status": "ready",
            "message": "Application is ready to serve traffic",
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "message": f"Application is not ready: {str(e)}",
        }


@router.get("/db")
async def database_health(db: Session = Depends(get_db)):
    """Database health check endpoint"""
    try:
        # Simple query to check database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "message": "Database connection is working",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }


@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with all dependencies"""
    monitoring_service = get_monitoring_service()
    health_status = monitoring_service.health_check()

    # Add database check
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"

    # Add Redis check
    try:
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        health_status["checks"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    # Add Plex check
    plex_conn = db.query(PlexConnection).filter(PlexConnection.is_active.is_(True)).first()
    if plex_conn:
        health_status["checks"]["plex"] = {
            "status": "healthy",
            "server": plex_conn.server_url,
        }
    else:
        health_status["checks"]["plex"] = {
            "status": "unavailable",
            "error": "No active connection configured",
        }

    return health_status


@router.get("/metrics")
async def system_metrics():
    """System metrics endpoint"""
    monitoring_service = get_monitoring_service()
    return monitoring_service.get_all_metrics()


@router.get("/metrics/prometheus")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    from fastapi.responses import Response

    metrics_data = get_metrics()
    return Response(content=metrics_data, media_type="text/plain")
