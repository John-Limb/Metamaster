"""Tests for file API endpoints and config check logic"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.domain.files.models import FileItem
from app.domain.files.service import FileService
from app.main import app
from tests.db_utils import TEST_DATABASE_URL


@pytest.fixture(scope="function")
def test_db():
    """Create a PostgreSQL database session for testing"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    session = TestingSessionLocal()
    yield session
    session.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


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
        mock_settings.tmdb_api_key = "your_tmdb_api_key_here"  # placeholder
        mock_settings.database_url = "postgresql://localhost/metamaster"
        response = client.get("/api/v1/config/check")
        assert response.status_code == 200
        data = response.json()
        assert data["isComplete"] is True

    @patch("app.api.v1.config.endpoints.check_path_exists", return_value=True)
    @patch("app.api.v1.config.endpoints.settings")
    def test_api_keys_severity_is_important(self, mock_settings, mock_path, client):
        """TMDB API key should have severity 'important', not 'critical'"""
        mock_settings.tmdb_api_key = ""
        mock_settings.database_url = "postgresql://localhost/metamaster"
        response = client.get("/api/v1/config/check")
        data = response.json()
        tmdb_item = next(i for i in data["items"] if i["id"] == "api-keys-tmdb")
        assert tmdb_item["severity"] == "important"


# ============================================================================
# FileService Unit Tests
# ============================================================================


@pytest.mark.unit
def test_batch_move_files_returns_list_of_moved_ids():
    """batch_move_files returns list of IDs that succeeded, not a count."""
    db = MagicMock()
    svc = FileService(db)

    def fake_move(file_id, path):
        if file_id == 99:
            raise ValueError("not found")
        mock_file = MagicMock()
        mock_file.id = file_id
        return mock_file

    svc.move_file = fake_move
    result = svc.batch_move_files([1, 2, 99], "/media/movies")
    assert result == [1, 2]
    assert 99 not in result


@pytest.mark.unit
@patch("app.api.v1.files.endpoints.get_or_cache_library_ids")
def test_plex_section_ids_for_files_returns_movie_section(mock_cache):
    from app.api.v1.files.endpoints import _plex_section_ids_for_files

    mock_conn = MagicMock()
    mock_conn.movie_library_id = "1"
    mock_conn.tv_library_id = "2"
    mock_cache.return_value = ("1", "2")

    mock_file_item = MagicMock()
    mock_file_item.path = "/media/movies/foo.mkv"

    db = MagicMock()

    def query_side_effect(model):
        m = MagicMock()
        if model.__name__ == "PlexConnection":
            m.filter.return_value.first.return_value = mock_conn
        elif model.__name__ == "FileItem":
            m.filter.return_value.first.return_value = mock_file_item
        elif model.__name__ == "MovieFile":
            m.filter.return_value.first.return_value = MagicMock()  # found
        else:
            m.filter.return_value.first.return_value = None  # no EpisodeFile
        return m

    db.query.side_effect = query_side_effect

    result = _plex_section_ids_for_files(db, [1])
    assert result == {"1"}


@pytest.mark.unit
def test_plex_section_ids_for_files_returns_empty_when_no_connection():
    from app.api.v1.files.endpoints import _plex_section_ids_for_files

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    result = _plex_section_ids_for_files(db, [1])
    assert result == set()


@pytest.mark.unit
@patch("app.api.v1.files.endpoints.get_or_cache_library_ids")
def test_plex_section_ids_for_files_returns_empty_when_plex_unreachable(mock_cache):
    from app.api.v1.files.endpoints import _plex_section_ids_for_files

    mock_conn = MagicMock()
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_conn
    mock_cache.side_effect = ValueError("unreachable")

    result = _plex_section_ids_for_files(db, [1])
    assert result == set()


@pytest.mark.unit
@patch("app.api.v1.files.endpoints.get_or_cache_library_ids")
def test_plex_section_ids_for_files_returns_both_for_unlinked_file(mock_cache):
    from app.api.v1.files.endpoints import _plex_section_ids_for_files

    mock_conn = MagicMock()
    mock_conn.movie_library_id = "1"
    mock_conn.tv_library_id = "2"
    mock_cache.return_value = ("1", "2")

    db = MagicMock()

    def query_side_effect(model):
        m = MagicMock()
        if model.__name__ == "PlexConnection":
            m.filter.return_value.first.return_value = mock_conn
        elif model.__name__ == "FileItem":
            m.filter.return_value.first.return_value = MagicMock(path="/foo.mkv")
        else:
            m.filter.return_value.first.return_value = None  # no MovieFile or EpisodeFile
        return m

    db.query.side_effect = query_side_effect

    result = _plex_section_ids_for_files(db, [1])
    assert result == {"1", "2"}


@pytest.mark.unit
@patch("app.api.v1.files.endpoints._plex_section_ids_for_files", return_value={"1"})
@patch("app.api.v1.files.endpoints.refresh_plex_library")
def test_move_endpoint_dispatches_plex_refresh(mock_refresh, mock_sections, client, test_db):
    """Move endpoint dispatches one refresh per section ID returned by helper."""
    mock_refresh.delay = MagicMock()
    file = FileItem(
        name="foo.mkv",
        path="/media/movies/foo.mkv",
        type="file",
        size=1000,
        mime_type="video/x-matroska",
    )
    test_db.add(file)
    test_db.commit()
    test_db.refresh(file)

    response = client.patch(f"/api/v1/files/{file.id}/move", json={"path": "/media/movies/subdir"})
    assert response.status_code == 200
    mock_refresh.delay.assert_called_once_with("1")


@pytest.mark.unit
@patch("app.api.v1.files.endpoints._plex_section_ids_for_files", return_value=set())
@patch("app.api.v1.files.endpoints.refresh_plex_library")
def test_move_endpoint_no_refresh_when_no_connection(mock_refresh, mock_sections, client, test_db):
    """No refresh dispatched when _plex_section_ids_for_files returns empty set."""
    mock_refresh.delay = MagicMock()
    file = FileItem(
        name="foo.mkv",
        path="/media/movies/foo.mkv",
        type="file",
        size=1000,
        mime_type="video/x-matroska",
    )
    test_db.add(file)
    test_db.commit()
    test_db.refresh(file)

    client.patch(f"/api/v1/files/{file.id}/move", json={"path": "/media/movies/subdir"})
    mock_refresh.delay.assert_not_called()


@pytest.mark.unit
@patch("app.api.v1.files.endpoints._plex_section_ids_for_files", return_value={"1"})
@patch("app.api.v1.files.endpoints.refresh_plex_library")
def test_batch_move_dispatches_one_refresh_per_section(
    mock_refresh, mock_sections, client, test_db
):
    """Batch move dispatches exactly one task per unique section, not one per file."""
    mock_refresh.delay = MagicMock()
    files = [
        FileItem(
            name=f"f{i}.mkv",
            path=f"/media/movies/f{i}.mkv",
            type="file",
            size=1000,
            mime_type="video/x-matroska",
        )
        for i in range(3)
    ]
    for f in files:
        test_db.add(f)
    test_db.commit()
    for f in files:
        test_db.refresh(f)

    ids = [f.id for f in files]
    client.post("/api/v1/files/batch-move", json={"ids": ids, "path": "/media/movies/subdir"})
    assert mock_refresh.delay.call_count == 1
