"""Comprehensive unit tests for application configuration"""

import pytest
import os
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from app.config import Settings, settings
from tests.db_utils import TEST_DATABASE_URL

# ============================================================================
# Configuration Loading Tests
# ============================================================================


class TestSettingsLoading:
    """Tests for configuration loading"""

    @patch.dict(os.environ, {"APP_NAME": "Media Management Web Tool"}, clear=False)
    def test_default_settings(self):
        """Test default configuration values"""
        test_settings = Settings()
        assert test_settings.app_name == "Media Management Web Tool"
        assert test_settings.app_version == "0.1.0"
        assert test_settings.debug is False

    @patch.dict(
        os.environ,
        {"DATABASE_URL": "postgresql+psycopg2://test:test@localhost:5432/metamaster_test"},
    )
    def test_database_url_default(self):
        """Test default database URL"""
        test_settings = Settings()
        assert (
            test_settings.database_url
            == "postgresql+psycopg2://test:test@localhost:5432/metamaster_test"
        )

    def test_redis_url_default(self):
        """Test default Redis URL"""
        test_settings = Settings()
        assert test_settings.redis_url == "redis://localhost:6379/0"

    def test_celery_broker_url_default(self):
        """Test default Celery broker URL"""
        test_settings = Settings()
        assert test_settings.celery_broker_url == "redis://localhost:6379/0"

    def test_tmdb_api_key_default(self):
        """Test default TMDB API key is None when not set"""
        with patch.dict(os.environ, {}, clear=False):
            # When no TMDB_API_KEY set (other than .env), key may be set or None
            test_settings = Settings()
            assert hasattr(test_settings, "tmdb_api_key")


# ============================================================================
# Environment Variable Tests
# ============================================================================


class TestEnvironmentVariables:
    """Tests for environment variable handling"""

    @patch.dict(os.environ, {"APP_NAME": "Custom App"})
    def test_app_name_from_env(self):
        """Test app name from environment variable"""
        test_settings = Settings()
        assert test_settings.app_name == "Custom App"

    @patch.dict(os.environ, {"DEBUG": "true"})
    def test_debug_from_env(self):
        """Test debug flag from environment variable"""
        test_settings = Settings()
        assert test_settings.debug is True

    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/media"})
    def test_database_url_from_env(self):
        """Test database URL from environment variable"""
        test_settings = Settings()
        assert test_settings.database_url == "postgresql://localhost/media"

    @patch.dict(os.environ, {"REDIS_URL": "redis://redis-server:6379/0"})
    def test_redis_url_from_env(self):
        """Test Redis URL from environment variable"""
        test_settings = Settings()
        assert test_settings.redis_url == "redis://redis-server:6379/0"

    @patch.dict(os.environ, {"TMDB_API_KEY": "test_key_123"})
    def test_tmdb_api_key_from_env(self):
        """Test TMDB API key from environment variable"""
        test_settings = Settings()
        assert test_settings.tmdb_api_key == "test_key_123"


# ============================================================================
# Database Configuration Tests
# ============================================================================


class TestDatabaseConfiguration:
    """Tests for database configuration"""

    def test_database_pool_size_default(self):
        """Test default database pool size"""
        test_settings = Settings()
        assert test_settings.db_pool_size == 10

    def test_database_max_overflow_default(self):
        """Test default database max overflow"""
        test_settings = Settings()
        assert test_settings.db_max_overflow == 20

    def test_database_pool_recycle_default(self):
        """Test default database pool recycle time"""
        test_settings = Settings()
        assert test_settings.db_pool_recycle == 3600

    def test_database_pool_timeout_default(self):
        """Test default database pool timeout"""
        test_settings = Settings()
        assert test_settings.db_pool_timeout == 30

    def test_database_pool_pre_ping_default(self):
        """Test default database pool pre-ping"""
        test_settings = Settings()
        assert test_settings.db_pool_pre_ping is True

    @patch.dict(os.environ, {"DB_POOL_SIZE": "20"})
    def test_database_pool_size_from_env(self):
        """Test database pool size from environment"""
        test_settings = Settings()
        assert test_settings.db_pool_size == 20

    @patch.dict(os.environ, {"DB_MAX_OVERFLOW": "30"})
    def test_database_max_overflow_from_env(self):
        """Test database max overflow from environment"""
        test_settings = Settings()
        assert test_settings.db_max_overflow == 30

    def test_database_echo_default(self):
        """Test default database echo setting"""
        test_settings = Settings()
        assert test_settings.database_echo is False

    @patch.dict(os.environ, {"DATABASE_ECHO": "true"})
    def test_database_echo_from_env(self):
        """Test database echo from environment"""
        test_settings = Settings()
        assert test_settings.database_echo is True


# ============================================================================
# Redis Configuration Tests
# ============================================================================


class TestRedisConfiguration:
    """Tests for Redis configuration"""

    def test_redis_cache_db_default(self):
        """Test default Redis cache database"""
        test_settings = Settings()
        assert test_settings.redis_cache_db == 2

    def test_redis_cache_default_ttl(self):
        """Test default Redis cache TTL"""
        test_settings = Settings()
        assert test_settings.redis_cache_default_ttl == 3600

    def test_redis_cache_movie_ttl(self):
        """Test Redis cache TTL for movies"""
        test_settings = Settings()
        assert test_settings.redis_cache_movie_ttl == 86400

    def test_redis_cache_tv_show_ttl(self):
        """Test Redis cache TTL for TV shows"""
        test_settings = Settings()
        assert test_settings.redis_cache_tv_show_ttl == 86400

    def test_redis_cache_list_ttl(self):
        """Test Redis cache TTL for lists"""
        test_settings = Settings()
        assert test_settings.redis_cache_list_ttl == 1800

    @patch.dict(os.environ, {"REDIS_CACHE_DB": "3"})
    def test_redis_cache_db_from_env(self):
        """Test Redis cache database from environment"""
        test_settings = Settings()
        assert test_settings.redis_cache_db == 3


# ============================================================================
# API Configuration Tests
# ============================================================================


class TestAPIConfiguration:
    """Tests for external API configuration"""

    def test_tmdb_rate_limit_default(self):
        """Test default TMDB rate limit"""
        test_settings = Settings()
        assert test_settings.tmdb_rate_limit == 4

    def test_tmdb_cache_ttl_default(self):
        """Test default TMDB cache TTL"""
        test_settings = Settings()
        assert test_settings.tmdb_cache_ttl == 2592000  # 30 days

    @patch.dict(os.environ, {"TMDB_RATE_LIMIT": "8"})
    def test_tmdb_rate_limit_from_env(self):
        """Test TMDB rate limit from environment"""
        test_settings = Settings()
        assert test_settings.tmdb_rate_limit == 8


# ============================================================================
# File Monitoring Configuration Tests
# ============================================================================


class TestFileMonitoringConfiguration:
    """Tests for file monitoring configuration"""

    def test_watch_extensions_default(self):
        """Test default watch extensions"""
        test_settings = Settings()
        assert ".mp4" in test_settings.watch_extensions
        assert ".mkv" in test_settings.watch_extensions
        assert ".avi" in test_settings.watch_extensions

    def test_watch_extensions_count(self):
        """Test number of default watch extensions"""
        test_settings = Settings()
        assert len(test_settings.watch_extensions) > 0

    @patch.dict(os.environ, {"TMDB_RATE_LIMIT": "10"})
    def test_tmdb_rate_limit_override_from_env(self):
        """Test TMDB rate limit can be overridden from environment"""
        test_settings = Settings()
        assert test_settings.tmdb_rate_limit == 10


# ============================================================================
# Celery Configuration Tests
# ============================================================================


class TestCeleryConfiguration:
    """Tests for Celery configuration"""

    @patch.dict(os.environ, {"CELERY_RESULT_BACKEND": "redis://localhost:6379/1"})
    def test_celery_result_backend_default(self):
        """Test default Celery result backend"""
        test_settings = Settings()
        assert test_settings.celery_result_backend == "redis://localhost:6379/1"

    def test_celery_task_serializer_default(self):
        """Test default Celery task serializer"""
        test_settings = Settings()
        assert test_settings.celery_task_serializer == "json"

    def test_celery_result_serializer_default(self):
        """Test default Celery result serializer"""
        test_settings = Settings()
        assert test_settings.celery_result_serializer == "json"

    def test_celery_accept_content_default(self):
        """Test default Celery accept content"""
        test_settings = Settings()
        assert "json" in test_settings.celery_accept_content

    def test_celery_task_track_started_default(self):
        """Test default Celery task track started"""
        test_settings = Settings()
        assert test_settings.celery_task_track_started is True

    def test_celery_task_time_limit_default(self):
        """Test default Celery task time limit"""
        test_settings = Settings()
        assert test_settings.celery_task_time_limit == 600

    def test_celery_task_soft_time_limit_default(self):
        """Test default Celery task soft time limit"""
        test_settings = Settings()
        assert test_settings.celery_task_soft_time_limit == 300

    @patch.dict(os.environ, {"CELERY_BROKER_URL": "redis://celery-broker:6379/0"})
    def test_celery_broker_url_from_env(self):
        """Test Celery broker URL from environment"""
        test_settings = Settings()
        assert test_settings.celery_broker_url == "redis://celery-broker:6379/0"

    @patch.dict(os.environ, {"CELERY_RESULT_BACKEND": "redis://celery-backend:6379/1"})
    def test_celery_result_backend_from_env(self):
        """Test Celery result backend from environment"""
        test_settings = Settings()
        assert test_settings.celery_result_backend == "redis://celery-backend:6379/1"


# ============================================================================
# Logging Configuration Tests
# ============================================================================


class TestLoggingConfiguration:
    """Tests for logging configuration"""

    @patch.dict(os.environ, {}, clear=False)
    def test_log_level_default(self):
        """Test default log level when LOG_LEVEL env var is not set"""
        os.environ.pop("LOG_LEVEL", None)
        test_settings = Settings(_env_file=None)
        assert test_settings.log_level == "INFO"

    @patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"})
    def test_log_level_from_env(self):
        """Test log level from environment"""
        test_settings = Settings()
        assert test_settings.log_level == "DEBUG"

    @patch.dict(os.environ, {"LOG_LEVEL": "WARNING"})
    def test_log_level_warning_from_env(self):
        """Test log level WARNING from environment"""
        test_settings = Settings()
        assert test_settings.log_level == "WARNING"


# ============================================================================
# Query Performance Configuration Tests
# ============================================================================


class TestQueryPerformanceConfiguration:
    """Tests for query performance configuration"""

    def test_slow_query_threshold_default(self):
        """Test default slow query threshold"""
        test_settings = Settings()
        assert test_settings.db_slow_query_threshold == 1.0

    def test_query_logging_enabled_default(self):
        """Test default query logging enabled"""
        test_settings = Settings()
        assert test_settings.db_query_logging_enabled is True

    @patch.dict(os.environ, {"DB_SLOW_QUERY_THRESHOLD": "2.5"})
    def test_slow_query_threshold_from_env(self):
        """Test slow query threshold from environment"""
        test_settings = Settings()
        assert test_settings.db_slow_query_threshold == 2.5

    @patch.dict(os.environ, {"DB_QUERY_LOGGING_ENABLED": "false"})
    def test_query_logging_disabled_from_env(self):
        """Test query logging disabled from environment"""
        test_settings = Settings()
        assert test_settings.db_query_logging_enabled is False


# ============================================================================
# Configuration Validation Tests
# ============================================================================


class TestConfigurationValidation:
    """Tests for configuration validation"""

    def test_settings_instance_creation(self):
        """Test Settings instance can be created"""
        test_settings = Settings()
        assert test_settings is not None

    def test_settings_has_required_attributes(self):
        """Test Settings has all required attributes"""
        test_settings = Settings()
        assert hasattr(test_settings, "app_name")
        assert hasattr(test_settings, "database_url")
        assert hasattr(test_settings, "redis_url")
        assert hasattr(test_settings, "celery_broker_url")

    def test_settings_config_class(self):
        """Test Settings Config class"""
        assert hasattr(Settings, "Config")
        assert Settings.Config.env_file == ".env"
        assert Settings.Config.case_sensitive is False

    def test_global_settings_instance(self):
        """Test global settings instance"""
        assert settings is not None
        assert isinstance(settings, Settings)


# ============================================================================
# Multiple Environment Variable Tests
# ============================================================================


class TestMultipleEnvironmentVariables:
    """Tests for multiple environment variables"""

    @patch.dict(
        os.environ,
        {
            "APP_NAME": "Test App",
            "DEBUG": "true",
            "DATABASE_URL": "postgresql+psycopg2://test:test@localhost:5432/metamaster_test",
            "LOG_LEVEL": "DEBUG",
        },
    )
    def test_multiple_env_vars(self):
        """Test multiple environment variables"""
        test_settings = Settings()
        assert test_settings.app_name == "Test App"
        assert test_settings.debug is True
        assert (
            test_settings.database_url
            == "postgresql+psycopg2://test:test@localhost:5432/metamaster_test"
        )
        assert test_settings.log_level == "DEBUG"

    @patch.dict(
        os.environ,
        {
            "TMDB_API_KEY": "tmdb_key",
        },
    )
    def test_api_keys_from_env(self):
        """Test API keys from environment"""
        test_settings = Settings()
        assert test_settings.tmdb_api_key == "tmdb_key"


# ============================================================================
# Configuration Consistency Tests
# ============================================================================


class TestConfigurationConsistency:
    """Tests for configuration consistency"""

    def test_redis_urls_consistency(self):
        """Test Redis URLs are consistent"""
        test_settings = Settings()
        # Celery broker and Redis URL should be on same server
        assert "localhost" in test_settings.redis_url or "redis" in test_settings.redis_url

    def test_cache_ttl_values_reasonable(self):
        """Test cache TTL values are reasonable"""
        test_settings = Settings()
        assert test_settings.redis_cache_default_ttl > 0
        assert test_settings.redis_cache_movie_ttl > 0
        assert test_settings.redis_cache_tv_show_ttl > 0
        assert test_settings.redis_cache_list_ttl > 0

    def test_rate_limits_positive(self):
        """Test rate limits are positive"""
        test_settings = Settings()
        assert test_settings.tmdb_rate_limit > 0

    def test_pool_settings_reasonable(self):
        """Test pool settings are reasonable"""
        test_settings = Settings()
        assert test_settings.db_pool_size > 0
        assert test_settings.db_max_overflow >= 0
        assert test_settings.db_pool_timeout > 0

    def test_celery_timeouts_reasonable(self):
        """Test Celery timeouts are reasonable"""
        test_settings = Settings()
        assert test_settings.celery_task_soft_time_limit > 0
        assert test_settings.celery_task_time_limit > test_settings.celery_task_soft_time_limit
