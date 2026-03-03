"""Core module - Application initialization and configuration"""

from app.core.config import Settings, settings
from app.core.database import (
    Base,
    SessionLocal,
    engine,
    get_db,
    get_engine,
    get_session_local,
    init_db,
)
from app.core.init_db import (
    create_admin_user,
    drop_database,
    generate_random_password,
    init_database,
    reset_database,
)
from app.core.logging_config import (
    get_logger,
    log_cache_operation,
    log_database_query,
    log_error,
    log_request,
    log_task_execution,
    setup_logging,
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
