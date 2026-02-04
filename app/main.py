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

from app.config import settings
from app.database import init_db
from app.api import health

# Configure logging with structured format
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    init_db()
    logger.info("Database initialized")
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
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Duration: {process_time:.3f}s"
        )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Error: {str(e)} - Duration: {process_time:.3f}s",
            exc_info=True
        )
        raise


# Error handling middleware
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with structured response"""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        f"[{request_id}] Validation error: {exc.error_count()} error(s)",
        extra={"errors": exc.errors()}
    )
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "request_id": request_id,
        },
    )


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],
)


# Include routers
app.include_router(health.router, tags=["Health"])


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
