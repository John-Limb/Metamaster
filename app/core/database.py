"""Database configuration and session management"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create PostgreSQL engine with connection pooling
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=settings.db_pool_pre_ping,
    poolclass=QueuePool,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_recycle=settings.db_pool_recycle,
    pool_timeout=settings.db_pool_timeout,
)


# Setup query logging and pool monitoring if enabled
# Import here to avoid circular dependency
# Note: db_optimization module is not currently used but kept for future enhancement
# def _setup_db_optimization():
#     """Setup database optimization - called after models are loaded"""
#     try:
#         if settings.db_query_logging_enabled:
#             from app.infrastructure.monitoring.db_optimization import DatabaseOptimizationService
#
#             DatabaseOptimizationService.setup_query_logging(engine)
#             DatabaseOptimizationService.setup_pool_monitoring(engine)
#     except ImportError:
#         # If db_optimization cannot be imported, continue without it
#         logger.debug("Database optimization setup skipped")


# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database tables: {str(e)}", exc_info=True)
        raise


def get_engine():
    """Get the database engine"""
    return engine


def get_session_local():
    """Get the session factory"""
    return SessionLocal
