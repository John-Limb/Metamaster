"""FastAPI application entry point"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
import uuid

from app.core.config import settings
from app.core.database import init_db
from app.tasks.celery_app import celery_app
from app.api import health
from app.api import movies
from app.api import tv_shows
from app.api import cache
from app.api import tasks
from app.api import files
from app.api.v1.config import router as config_router

# Configure logging with structured format
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    init_db()
    logger.info("Database initialized")

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

    logger.info(f"[{request_id}] {request.method} {request.url.path} - " f"Client: {client_host}")

    if request.method.upper() == "OPTIONS":
        logger.info(
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
        logger.info(log_message)
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
app.include_router(health.router, tags=["Health"])
app.include_router(movies.router, prefix="/api/v1")
app.include_router(tv_shows.router, prefix="/api/v1")
app.include_router(cache.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
app.include_router(config_router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")


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
