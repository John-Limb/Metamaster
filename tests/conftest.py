"""Shared test configuration and fixtures for pytest"""

import sys
import os
from pathlib import Path

# Add the project root to sys.path to ensure app module is importable
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(scope="session")
def app_root():
    """Provide the application root directory"""
    return project_root


@pytest.fixture
def mock_redis():
    """Provide a mock Redis client for testing"""
    with patch("redis.from_url") as mock_redis_client:
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_client.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_db_session():
    """Provide a mock database session for testing"""
    mock_session = MagicMock()
    yield mock_session


@pytest.fixture
def mock_settings():
    """Provide mock settings for testing"""
    with patch("app.config.settings") as mock_settings_obj:
        mock_settings_obj.redis_url = "redis://localhost:6379/0"
        mock_settings_obj.database_url = (
            "postgresql+psycopg2://test:test@localhost:5432/metamaster_test"
        )
        mock_settings_obj.debug = True
        yield mock_settings_obj


@pytest.fixture
def mock_logger():
    """Provide a mock logger for testing"""
    with patch("logging.getLogger") as mock_get_logger:
        mock_log = MagicMock()
        mock_get_logger.return_value = mock_log
        yield mock_log


def pytest_configure(config):
    """Configure pytest with custom settings"""
    # Register custom markers
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "database: mark test as requiring database")
    config.addinivalue_line("markers", "redis: mark test as requiring Redis")
    config.addinivalue_line("markers", "external_api: mark test as calling external APIs")
    config.addinivalue_line("markers", "docker: mark test as requiring Docker")
