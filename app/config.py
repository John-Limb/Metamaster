"""Application configuration settings"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "Media Management Web Tool"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./media.db"
    database_echo: bool = False

    # Database Connection Pool
    db_pool_size: int = 10  # Number of connections to keep in the pool
    db_max_overflow: int = 20  # Maximum overflow connections
    db_pool_recycle: int = 3600  # Recycle connections after 1 hour (seconds)
    db_pool_timeout: int = (
        30  # Timeout for getting a connection from the pool (seconds)
    )
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

    # OMDB API
    omdb_api_key: Optional[str] = None
    omdb_rate_limit: int = 1  # requests per second
    omdb_cache_ttl: int = 2592000  # 30 days in seconds

    # TVDB API
    tvdb_api_key: Optional[str] = None
    tvdb_pin: Optional[str] = None
    tvdb_rate_limit: int = 3  # requests per second (30/10)
    tvdb_cache_ttl: int = 2592000  # 30 days in seconds

    # File Monitoring
    media_directory: str = "./media"
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

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
