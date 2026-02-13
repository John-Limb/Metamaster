"""Core module - Application initialization and configuration"""

from app.core.config import settings, Settings
from app.core.database import (
    engine,
    SessionLocal,
    Base,
    get_db,
    init_db,
    get_engine,
    get_session_local,
)
from app.core.logging_config import (
    setup_logging,
    get_logger,
    log_request,
    log_database_query,
    log_cache_operation,
    log_task_execution,
    log_error,
)
from app.core.init_db import (
    init_database,
    drop_database,
    reset_database,
    create_admin_user,
    generate_random_password,
)

__all__ = [
    # Config
    "settings",
    "Settings",
    # Database
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "init_db",
    "get_engine",
    "get_session_local",
    # Logging
    "setup_logging",
    "get_logger",
    "log_request",
    "log_database_query",
    "log_cache_operation",
    "log_task_execution",
    "log_error",
    # Database initialization
    "init_database",
    "drop_database",
    "reset_database",
    "create_admin_user",
    "generate_random_password",
]
