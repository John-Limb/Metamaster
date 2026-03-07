# tests/test_plex_api.py
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.v1.auth.endpoints import get_current_user
from app.core.database import get_db
from app.main import app

_MOCK_USER = MagicMock(id=1)


def _override_current_user():
    return _MOCK_USER


client = TestClient(app, raise_server_exceptions=False)


def auth_headers():
    return {"Authorization": "Bearer test-token"}


@pytest.mark.unit
def test_get_connection_returns_404_when_none():
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None

    def _override_db():
        yield mock_session

    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_db] = _override_db
    try:
        response = client.get("/api/v1/plex/connection", headers=auth_headers())
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.unit
def test_post_connection_creates_record():
    mock_session = MagicMock()
    mock_session.query.return_value.first.return_value = None

    def _fake_refresh(obj):
        obj.id = 99
        obj.created_at = datetime(2026, 1, 1)
        obj.is_active = True
        obj.server_url = "http://plex:32400"
        obj.movie_library_id = None
        obj.tv_library_id = None
        obj.last_connected_at = None

    mock_session.refresh.side_effect = _fake_refresh

    def _override_db():
        yield mock_session

    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_db] = _override_db
    try:
        response = client.post(
            "/api/v1/plex/connection",
            headers=auth_headers(),
            json={"server_url": "http://plex:32400", "token": "my-token"},
        )
        assert response.status_code == 201
        mock_session.add.assert_called_once()
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.unit
@patch("app.api.v1.plex.router.PlexAuth")
def test_oauth_initiate_returns_url_and_pin(mock_auth_cls):
    app.dependency_overrides[get_current_user] = _override_current_user
    try:
        mock_auth = MagicMock()
        mock_auth_cls.return_value = mock_auth
        mock_auth.create_pin.return_value = (42, "ABCD1234")
        mock_auth.build_oauth_url.return_value = "https://app.plex.tv/auth#?code=ABCD1234"

        response = client.get(
            "/api/v1/plex/oauth/initiate",
            headers=auth_headers(),
            params={"redirect_uri": "http://localhost:5173/plex/callback"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pin_id"] == 42
        assert "plex.tv" in data["oauth_url"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.unit
@patch("app.api.v1.plex.router.poll_plex_watched_status")
def test_post_sync_dispatches_celery_task(mock_poll):
    mock_session = MagicMock()
    mock_conn = MagicMock(id=1)
    mock_session.query.return_value.filter.return_value.first.return_value = mock_conn

    def _override_db():
        yield mock_session

    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_db] = _override_db
    try:
        mock_poll.delay.return_value = MagicMock(id="task-abc")

        response = client.post("/api/v1/plex/sync", headers=auth_headers())
        assert response.status_code == 202
        mock_poll.delay.assert_called_once_with(1)
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.unit
def test_plex_health_returns_not_found_count():
    mock_session = MagicMock()
    not_found_records = [
        MagicMock(id=1, item_type="movie", item_id=10, last_error=None),
        MagicMock(id=2, item_type="movie", item_id=11, last_error=None),
    ]
    # First query: PlexSyncRecord NOT_FOUND filter → all()
    mock_session.query.return_value.filter.return_value.all.return_value = not_found_records
    # Second query: PlexConnection active filter → first()
    mock_session.query.return_value.filter.return_value.first.return_value = None

    def _override_db():
        yield mock_session

    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_db] = _override_db
    try:
        response = client.get("/api/v1/plex/health", headers=auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert data["not_found_count"] == 2
        assert len(data["not_found_items"]) == 2
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.unit
@patch("app.api.v1.plex.router.lock_plex_match")
def test_resync_item_dispatches_task(mock_lock):
    mock_session = MagicMock()
    mock_record = MagicMock()
    mock_record.id = 5
    mock_record.item_type = "movie"
    mock_record.item_id = 42
    mock_record.connection_id = 1
    mock_record.sync_status = "not_found"

    # Movie lookup for tmdb_id
    mock_movie = MagicMock()
    mock_movie.tmdb_id = "603"
    mock_session.query.return_value.filter.return_value.first.side_effect = [
        mock_record,  # first: PlexSyncRecord lookup
        mock_movie,  # second: Movie lookup
    ]
    mock_lock.delay.return_value = MagicMock(id="task-xyz")

    def _override_db():
        yield mock_session

    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_db] = _override_db
    try:
        response = client.post("/api/v1/plex/sync/5", headers=auth_headers())
        assert response.status_code == 202
        mock_lock.delay.assert_called_once()
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
