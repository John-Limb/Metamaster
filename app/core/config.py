"""Application configuration settings"""

import secrets
from typing import Annotated, Any, List, Optional, Union

from pydantic import BeforeValidator, computed_field
from pydantic_settings import BaseSettings

# Generated once at import time. Module-level constants are never read from the
# environment, so these cannot be overridden via .env or container env vars.
JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
INTERNAL_API_KEY: str = secrets.token_urlsafe(32)


def _split_comma_separated(value: Any) -> Any:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


CommaSeparatedList = Annotated[Union[List[str], str], BeforeValidator(_split_comma_separated)]


# Fixed container paths — not user-configurable
# Host directories are bind-mounted to these paths via docker-compose
MOVIE_DIR = "/media/movies"
TV_DIR = "/media/tv"
MEDIA_DIRECTORIES = [MOVIE_DIR, TV_DIR]


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "Media Management Web Tool"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql+psycopg2://metamaster:metamaster@postgres:5432/metamaster"
    database_echo: bool = False

    # Database Connection Pool
    db_pool_size: int = 10  # Number of connections to keep in the pool
    db_max_overflow: int = 20  # Maximum overflow connections
    db_pool_recycle: int = 3600  # Recycle connections after 1 hour (seconds)
    db_pool_timeout: int = 30  # Timeout for getting a connection from the pool (seconds)
    db_pool_pre_ping: bool = True  # Test connections before using them

    # Query Performance
    db_slow_query_threshold: float = 1.0  # Time in seconds to consider a query as slow
    db_query_logging_enabled: bool = True  # Enable query execution logging

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_db: int = 2
    redis_cache_default_ttl: int = 3600  # 1 hour
    redis_cache_movie_ttl: int = 86400  # 24 hours
    redis_cache_tv_show_ttl: int = 86400  # 24 hours
    redis_cache_list_ttl: int = 1800  # 30 minutes

    # TMDB API (The Movie Database — covers both movies and TV shows)
    # tmdb_read_access_token: preferred — long JWT Bearer token (v4 auth)
    # tmdb_api_key: fallback — short v3 API key appended as ?api_key=
    tmdb_read_access_token: Optional[str] = None
    tmdb_api_key: Optional[str] = None
    tmdb_rate_limit: int = 4  # requests per second (~40/10s)
    tmdb_cache_ttl: int = 2592000  # 30 days in seconds

    # Plex Media Server
    plex_server_url: Optional[str] = None
    plex_token: Optional[str] = None  # manual fallback; OAuth stores token in DB
    plex_library_movies: str = "Movies"  # must match Plex library name exactly
    plex_library_tv: str = "TV Shows"  # must match Plex library name exactly
    plex_sync_poll_interval_seconds: int = 300

    watch_extensions: list = [
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".flv",
        ".wmv",
        ".webm",
        ".m4v",
        ".mpg",
        ".mpeg",
        ".3gp",
    ]

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: list = ["json"]
    celery_task_track_started: bool = True
    celery_task_time_limit: int = 600  # seconds
    celery_task_soft_time_limit: int = 300  # seconds

    # Media scanning schedule (cron expression, default 2AM daily)
    media_scan_schedule: str = "0 2 * * *"

    # Logging
    log_level: str = "INFO"

    # JWT Configuration
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    @computed_field  # type: ignore[prop-decorator]
    @property
    def jwt_secret_key(self) -> str:
        """Always returns the module-level constant — never read from environment."""
        return JWT_SECRET_KEY

    @computed_field  # type: ignore[prop-decorator]
    @property
    def internal_api_key(self) -> str:
        """Always returns the module-level constant — never read from environment."""
        return INTERNAL_API_KEY

    # Security / Networking
    allowed_origins: CommaSeparatedList = [
        "http://localhost",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "http://app",
        "http://app:8000",
        "http://frontend",
        "http://MetaMaster_frontend",
    ]
    trusted_hosts: CommaSeparatedList = [
        "localhost",
        "localhost:5173",
        "localhost:8000",
        "127.0.0.1",
        "127.0.0.1:5173",
        "127.0.0.1:8000",
        "app",
        "app:8000",
        "frontend",
        "MetaMaster_frontend",
        "testserver",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()
