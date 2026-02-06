"""Database initialization script"""

import logging
from sqlalchemy import inspect
from app.database import engine, Base, SessionLocal
from app.models import (
    Movie, MovieFile, TVShow, Season, Episode, EpisodeFile,
    APICache, FileQueue
)

logger = logging.getLogger(__name__)


def init_database():
    """Initialize database tables and create default data if needed"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Verify tables were created
        inspector_obj = inspect(engine)
        inspector_tables = inspector_obj.get_table_names()
        logger.info(f"Created tables: {inspector_tables}")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def drop_database():
    """Drop all database tables (use with caution)"""
    try:
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
        return True
    except Exception as e:
        logger.error(f"Error dropping database: {e}")
        raise


def reset_database():
    """Reset database by dropping and recreating all tables"""
    try:
        logger.warning("Resetting database...")
        drop_database()
        init_database()
        logger.info("Database reset successfully")
        return True
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "reset":
            reset_database()
        elif command == "drop":
            drop_database()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python -m app.init_db [init|reset|drop]")
    else:
        init_database()
