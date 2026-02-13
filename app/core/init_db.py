"""Database initialization script"""

import logging
import secrets
import string
from datetime import datetime

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.database import engine, Base, SessionLocal
from app.domain.movies.models import Movie, MovieFile
from app.domain.tv_shows.models import TVShow, Season, Episode, EpisodeFile
from app.domain.common.models import APICache, FileQueue
from app.domain.auth.models import User
from app.infrastructure.security.password import hash_password

logger = logging.getLogger(__name__)


def generate_random_password(length: int = 16) -> str:
    """Generate a secure random password.

    Args:
        length: The length of the password to generate. Defaults to 16.

    Returns:
        A secure random password containing letters, digits, and special characters.
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_admin_user(db: Session) -> str | None:
    """Create default admin user if no users exist.

    Checks if any users exist in the database. If not, creates a default
    admin user with a randomly generated password that must be changed
    on first login.

    Args:
        db: SQLAlchemy database session.

    Returns:
        The generated password if admin was created, None if users already exist.
    """
    # Check if any users exist
    existing_users = db.query(User).count()
    if existing_users > 0:
        logger.info("Users already exist, skipping admin creation")
        return None

    # Generate secure random password
    password = generate_random_password()

    # Create admin user
    admin_user = User(
        username="admin",
        email="admin@localhost",
        password_hash=hash_password(password),
        is_active=True,
        is_verified=True,
        requires_password_change=True,  # Force password change on first login
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(admin_user)
    db.commit()

    # Log the credentials prominently (visible in docker logs)
    logger.info("=" * 60)
    logger.info("DEFAULT ADMIN USER CREATED")
    logger.info("Username: admin")
    logger.info("Password: %s", password)
    logger.info("Please change this password on first login!")
    logger.info("=" * 60)

    return password


def log_startup_credentials(db: Session) -> dict:
    """
    Log all auto-generated credentials on first startup.
    Returns dict with all generated credentials.
    """
    credentials = {}
    
    # Create admin user if needed
    admin_password = create_admin_user(db)
    if admin_password:
        credentials["admin_password"] = admin_password
    
    # Get auto-generated secrets from settings
    from app.core.config import settings
    
    # Only log these on first run (when admin was created)
    if credentials:
        credentials["jwt_secret_key"] = settings.jwt_secret_key
        credentials["internal_api_key"] = settings.internal_api_key
        
        logger.info("=" * 60)
        logger.info("AUTO-GENERATED CREDENTIALS")
        logger.info("=" * 60)
        logger.info("These credentials are auto-generated on first startup.")
        logger.info("Save them securely - they won't be shown again!")
        logger.info("-" * 60)
        logger.info(f"Admin Username: admin")
        logger.info(f"Admin Password: {admin_password}")
        logger.info("-" * 60)
        logger.info(f"JWT Secret Key: {settings.jwt_secret_key}")
        logger.info("-" * 60)
        logger.info(f"Internal API Key: {settings.internal_api_key}")
        logger.info("=" * 60)
        logger.info("IMPORTANT: Save these credentials securely!")
        logger.info("=" * 60)
    
    return credentials


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

        # Create admin user and log all credentials if first run
        db = SessionLocal()
        try:
            log_startup_credentials(db)
        finally:
            db.close()

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
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "reset":
            reset_database()
        elif command == "drop":
            drop_database()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python -m app.core.init_db [init|reset|drop]")
    else:
        init_database()
