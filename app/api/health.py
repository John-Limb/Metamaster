"""Health check endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.monitoring import get_monitoring_service
from app.services.prometheus_metrics import get_metrics
import logging
import redis
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])


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
        db.execute("SELECT 1")

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
        db.execute("SELECT 1")
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
        db.execute("SELECT 1")
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
