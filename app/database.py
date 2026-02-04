"""Database configuration and session management"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool, QueuePool
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create database engine with connection pooling
if settings.database_url.startswith("sqlite"):
    # SQLite specific configuration
    # SQLite doesn't benefit from connection pooling, use StaticPool
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.database_echo,
    )
    
    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL or other databases with connection pooling
    engine = create_engine(
        settings.database_url,
        echo=settings.database_echo,
        pool_pre_ping=True,
        poolclass=QueuePool,
        pool_size=10,  # Number of connections to keep in the pool
        max_overflow=20,  # Maximum overflow connections
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_timeout=30,  # Timeout for getting a connection from the pool
    )

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
    Base.metadata.create_all(bind=engine)


def get_engine():
    """Get the database engine"""
    return engine


def get_session_local():
    """Get the session factory"""
    return SessionLocal
