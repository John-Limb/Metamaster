"""Backward compatibility shim for legacy imports."""

from app.core.database import (
    Base,
    SessionLocal,
    engine,
    get_db,
    init_db,
    get_engine,
    get_session_local,
)

__all__ = [
    "Base",
    "SessionLocal",
    "engine",
    "get_db",
    "init_db",
    "get_engine",
    "get_session_local",
]
