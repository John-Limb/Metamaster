"""FastAPI application entry point"""

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api import cache, files, health, movies, tasks, tv_shows
from app.api.v1.auth import router as auth_router
from app.api.v1.config import router as config_router
from app.api.v1.enrichment.endpoints import router as enrichment_router
from app.api.v1.organisation.endpoints import router as organisation_router
from app.api.v1.plex.router import router as plex_router
from app.api.v1.queue.endpoints import router as queue_router
from app.api.v1.storage.endpoints import router as storage_router
from app.core.config import MEDIA_DIRECTORIES, settings
from app.core.database import SessionLocal
from app.core.init_db import init_database
from app.core.logging_config import setup_logging
from app.domain.files.service import FileService
from app.domain.movies.models import Movie
from app.domain.movies.scanner import create_movies_from_files
from app.domain.tv_shows.models import TVShow
from app.domain.tv_shows.scanner import create_tv_shows_from_files
from app.tasks.celery_app import celery_app
from app.tasks.enrichment import enrich_movie_external, enrich_tv_show_external

# Configure structured logging with daily rotation
setup_logging()
logger = logging.getLogger(__name__)
access_logger = logging.getLogger("access")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    init_database()
    logger.info("Database initialized")

    # Sync media directories to database
    logger.info("Syncing media directories to database...")
    db = SessionLocal()
    try:
        file_service = FileService(db)
        total_synced = 0
        for media_dir in MEDIA_DIRECTORIES:
            try:
                synced = file_service.sync_directory(media_dir)
                total_synced += synced
                logger.info(f"Synced {synced} items from {media_dir}")
            except ValueError as e:
                logger.warning(f"Could not sync {media_dir}: {e}")
            except Exception as e:
                logger.error(f"Error syncing {media_dir}: {e}", exc_info=True)
        logger.info(f"Media directory sync complete: {total_synced} total items")

        # Create Movie/TVShow records for video files that don't have records yet
        create_movies_from_files(db)
        create_tv_shows_from_files(db)

        # Dispatch async enrichment for all unenriched items
        pending_movies = (
            db.query(Movie)
            .filter(Movie.enrichment_status.in_(["local_only", "external_failed"]))
            .all()
        )
        for m in pending_movies:
            enrich_movie_external(
                m.id
            )  # Call directly (not .delay()) since Celery may not be running at startup

        pending_shows = (
            db.query(TVShow)
            .filter(TVShow.enrichment_status.in_(["local_only", "external_failed"]))
            .all()
        )
        for s in pending_shows:
            enrich_tv_show_external(s.id)

    finally:
        db.close()

    # Initialize Celery app
    logger.info("Initializing Celery app")
    celery_app.conf.update(
        broker_url=settings.celery_broker_url,
        result_backend=settings.celery_result_backend,
    )
    logger.info(f"Celery broker: {settings.celery_broker_url}")
    logger.info(f"Celery result backend: {settings.celery_result_backend}")

    yield
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Media Management Web Tool - Organize and manage your media library",
    lifespan=lifespan,
)

# Add middleware stack (order matters - innermost first)

# Request/Response logging middleware


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.time()
    client_host = request.client.host if request.client else "unknown"
    origin = request.headers.get("origin")
    host_header = request.headers.get("host")
    acr_method = request.headers.get("access-control-request-method")
    acr_headers = request.headers.get("access-control-request-headers")

    access_logger.info(
        f"[{request_id}] {request.method} {request.url.path} - Client: {client_host}"
    )

    if request.method.upper() == "OPTIONS":
        access_logger.info(
            f"[{request_id}] Preflight details - Origin: {origin or 'unset'}, "
            f"Host: {host_header or 'unset'}, "
            f"Access-Control-Request-Method: {acr_method or 'unset'}, "
            f"Access-Control-Request-Headers: {acr_headers or 'unset'}"
        )

    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        log_message = (
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Duration: {process_time:.3f}s"
        )
        if response.status_code >= 400 and origin:
            log_message += f" - Origin: {origin}"
        access_logger.info(log_message)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Error: {str(e)} - Duration: {process_time:.3f}s",
            exc_info=True,
        )
        raise


# Error handling middleware
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with structured response"""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        f"[{request_id}] Validation error: {exc.error_count()} error(s)",
        extra={"errors": exc.errors()},
    )
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "request_id": request_id,
        },
    )


# Add CORS middleware with env-driven configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.trusted_hosts,
)


# Include routers
app.include_router(health.router, tags=["Health"])  # /health/ — Docker health checks
app.include_router(
    health.router, prefix="/api/v1", tags=["Health"]
)  # /api/v1/health/ — frontend API
app.include_router(movies.router, prefix="/api/v1")
app.include_router(tv_shows.router, prefix="/api/v1")
app.include_router(cache.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
app.include_router(config_router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(queue_router, prefix="/api/v1")
app.include_router(enrichment_router, prefix="/api/v1")
app.include_router(storage_router, prefix="/api/v1")
app.include_router(organisation_router, prefix="/api/v1")
app.include_router(plex_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Media Management Web Tool",
        "version": settings.app_version,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
