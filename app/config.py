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

    # Redis
    redis_url: str = "redis://localhost:6379/0"

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
        ".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv",
        ".webm", ".m4v", ".mpg", ".mpeg", ".3gp"
    ]

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
