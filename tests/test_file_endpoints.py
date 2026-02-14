"""Tests for file API endpoints and config check logic"""

import os

# Override database URL before any app imports to avoid psycopg2 dependency
os.environ["DATABASE_URL"] = "sqlite:///test_file_endpoints.db"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.main import app
from app.core.database import Base, get_db
from app.domain.files.models import FileItem


@pytest.fixture(scope="function")
def test_db():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal()
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def seeded_db(test_db):
    """Seed DB with sample file items including non-video files for filtering tests"""
    files = [
        FileItem(
            name="movie.mp4",
            path="/media/movies/movie.mp4",
            type="file",
            size=1_000_000,
            mime_type="video/mp4",
        ),
        FileItem(
            name="show.mkv",
            path="/media/tv/show.mkv",
            type="file",
            size=2_000_000,
            mime_type="video/x-matroska",
        ),
        FileItem(
            name="another_movie.avi",
            path="/media/movies/another_movie.avi",
            type="file",
            size=500_000,
            mime_type="video/x-msvideo",
        ),
        FileItem(
            name="poster.jpg",
            path="/media/movies/poster.jpg",
            type="file",
            size=50_000,
            mime_type="image/jpeg",
        ),
        FileItem(
            name="info.nfo",
            path="/media/tv/info.nfo",
            type="file",
            size=1_000,
            mime_type=None,
        ),
        FileItem(
            name="movies",
            path="/media/movies",
            type="directory",
            size=None,
            mime_type=None,
        ),
    ]
    for f in files:
        test_db.add(f)
    test_db.commit()
    return test_db


# ============================================================================
# File List Endpoint Tests
# ============================================================================


class TestFileListEndpoint:
    """Tests for GET /api/v1/files"""

    def test_list_files_empty(self, client):
        """Returns empty list when no files exist"""
        response = client.get("/api/v1/files")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert "page" in data
        assert "totalPages" in data

    def test_list_files_returns_items(self, client, seeded_db):
        """Returns only video files and directories (not .jpg/.nfo) by default"""
        response = client.get("/api/v1/files?path=/&page=1&pageSize=20")
        assert response.status_code == 200
        data = response.json()
        # 3 video files + 1 directory = 4 (poster.jpg and info.nfo filtered out)
        assert data["total"] == 4
        assert len(data["items"]) == 4
        assert data["page"] == 1

    def test_list_files_video_only_false(self, client, seeded_db):
        """Returns all files when video_only=false"""
        response = client.get("/api/v1/files?path=/&page=1&pageSize=20&video_only=false")
        assert response.status_code == 200
        data = response.json()
        # All 5 files + 1 directory = 6
        assert data["total"] == 6

    def test_list_files_camelcase_fields(self, client, seeded_db):
        """Response items use camelCase field names"""
        response = client.get("/api/v1/files?path=/")
        data = response.json()
        item = data["items"][0]
        assert "mime_type" in item or "mimeType" in item
        assert "created_at" in item or "createdAt" in item
        assert "is_indexed" in item or "isIndexed" in item


# ============================================================================
# File Stats Endpoint Tests
# ============================================================================


class TestFileStatsEndpoint:
    """Tests for GET /api/v1/files/stats"""

    def test_stats_empty(self, client):
        """Returns zero stats when no files exist"""
        response = client.get("/api/v1/files/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["totalFiles"] == 0
        assert data["totalSize"] == 0
        assert data["filesByType"] == {}

    def test_stats_with_files(self, client, seeded_db):
        """Returns correct stats for video files only, with category counts"""
        response = client.get("/api/v1/files/stats")
        assert response.status_code == 200
        data = response.json()
        # 3 video files (mp4, mkv, avi) — not poster.jpg or info.nfo
        assert data["totalFiles"] == 3
        assert data["totalSize"] == 3_500_000
        assert data["movieCount"] == 2  # movie.mp4 + another_movie.avi
        assert data["tvShowCount"] == 1  # show.mkv

    def test_stats_files_by_type_uses_extension(self, client, seeded_db):
        """filesByType keys are video file extensions only"""
        response = client.get("/api/v1/files/stats")
        data = response.json()
        by_type = data["filesByType"]
        assert ".mp4" in by_type
        assert ".mkv" in by_type
        assert ".avi" in by_type
        # Non-video extensions should NOT appear
        assert ".jpg" not in by_type
        assert ".nfo" not in by_type


# ============================================================================
# Config Check Endpoint Tests
# ============================================================================


class TestConfigCheckEndpoint:
    """Tests for GET /api/v1/config/check"""

    @patch("app.api.v1.config.endpoints.check_path_exists", return_value=True)
    @patch("app.api.v1.config.endpoints.settings")
    def test_config_complete_without_api_keys(self, mock_settings, mock_path, client):
        """Config is complete when paths + db configured, even without API keys"""
        mock_settings.omdb_api_key = "your_omdb_api_key_here"  # placeholder
        mock_settings.tvdb_api_key = "your_tvdb_api_key_here"  # placeholder
        mock_settings.database_url = "postgresql://localhost/metamaster"
        response = client.get("/api/v1/config/check")
        assert response.status_code == 200
        data = response.json()
        assert data["isComplete"] is True

    @patch("app.api.v1.config.endpoints.check_path_exists", return_value=True)
    @patch("app.api.v1.config.endpoints.settings")
    def test_api_keys_severity_is_important(self, mock_settings, mock_path, client):
        """OMDB and TVDB API keys should have severity 'important', not 'critical'"""
        mock_settings.omdb_api_key = ""
        mock_settings.tvdb_api_key = ""
        mock_settings.database_url = "postgresql://localhost/metamaster"
        response = client.get("/api/v1/config/check")
        data = response.json()
        omdb_item = next(i for i in data["items"] if i["id"] == "api-keys-omdb")
        tvdb_item = next(i for i in data["items"] if i["id"] == "api-keys-tvdb")
        assert omdb_item["severity"] == "important"
        assert tvdb_item["severity"] == "important"
