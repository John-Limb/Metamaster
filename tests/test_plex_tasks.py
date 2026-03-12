"""Tests for Celery tasks in app.tasks.plex"""

from unittest.mock import MagicMock, patch

import pytest

from app.domain.plex.models import PlexItemType
from app.tasks.plex import lock_plex_match, poll_plex_watched_status, refresh_plex_library


@pytest.mark.unit
@patch("app.tasks.plex.PlexClient")
@patch("app.tasks.plex.get_db")
@patch("app.tasks.plex.settings")
def test_refresh_plex_library_calls_client(mock_settings, mock_get_db, mock_client_cls):
    mock_settings.plex_server_url = "http://plex:32400"
    mock_settings.plex_token = "token"
    mock_settings.plex_library_movies = "Movies"
    mock_settings.plex_library_tv = "TV Shows"

    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])

    refresh_plex_library.apply(args=["1"]).get()

    mock_client.refresh_library_section.assert_called_once_with(section_id="1")


@pytest.mark.unit
@patch("app.tasks.plex.settings")
def test_refresh_plex_library_skips_when_no_server_url(mock_settings):
    mock_settings.plex_server_url = None
    result = refresh_plex_library.apply(args=["1"]).get()
    assert result is None


@pytest.mark.unit
@patch("app.tasks.plex.PlexSyncService")
@patch("app.tasks.plex.PlexClient")
@patch("app.tasks.plex.get_db")
@patch("app.tasks.plex.settings")
def test_lock_plex_match_delegates_to_service(
    mock_settings, mock_get_db, mock_client_cls, mock_service_cls
):
    mock_settings.plex_server_url = "http://plex:32400"
    mock_settings.plex_token = "token"
    mock_settings.plex_library_movies = "Movies"
    mock_settings.plex_library_tv = "TV Shows"

    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])
    mock_service = MagicMock()
    mock_service_cls.return_value = mock_service
    mock_service.resolve_library_ids.return_value = ("1", "2")

    lock_plex_match.apply(args=["movie", 42, "603", 1]).get()

    call_kwargs = mock_service.lock_match.call_args[1]
    assert call_kwargs["section_id"] == "1"
    assert call_kwargs["item_type"] == PlexItemType.MOVIE
    assert call_kwargs["item_id"] == 42
    assert call_kwargs["tmdb_id"] == "603"
    assert call_kwargs["connection_id"] == 1
    assert "title" in call_kwargs
    assert "year" in call_kwargs


@pytest.mark.unit
@patch("app.tasks.plex.PlexSyncService")
@patch("app.tasks.plex.get_db")
@patch("app.tasks.plex._make_client")
def test_lock_plex_match_passes_title_and_year(mock_make_client, mock_get_db, mock_svc_cls):
    mock_client = MagicMock()
    mock_make_client.return_value = mock_client

    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])

    mock_movie = MagicMock()
    mock_movie.title = "The Matrix"
    mock_movie.year = 1999
    mock_db.query.return_value.filter.return_value.first.return_value = mock_movie

    mock_svc = MagicMock()
    mock_svc.resolve_library_ids.return_value = ("1", "2")
    mock_svc_cls.return_value = mock_svc

    lock_plex_match("movie", 42, "603", 1)

    call_kwargs = mock_svc.lock_match.call_args[1]
    assert call_kwargs["title"] == "The Matrix"
    assert call_kwargs["year"] == 1999


@pytest.mark.unit
@patch("app.tasks.plex.PlexSyncService")
@patch("app.tasks.plex.PlexClient")
@patch("app.tasks.plex.get_db")
@patch("app.tasks.plex.settings")
def test_poll_plex_watched_status_calls_pull_for_movies_and_tv(
    mock_settings, mock_get_db, mock_client_cls, mock_service_cls
):
    mock_settings.plex_server_url = "http://plex:32400"
    mock_settings.plex_token = "token"
    mock_settings.plex_library_movies = "Movies"
    mock_settings.plex_library_tv = "TV Shows"

    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])
    mock_service = MagicMock()
    mock_service_cls.return_value = mock_service
    mock_service.resolve_library_ids.return_value = ("1", "2")

    poll_plex_watched_status.apply(args=[1]).get()

    calls = mock_service.pull_watched_status.call_args_list
    assert any(c.kwargs.get("media_type") == 1 or (c.args and c.args[1] == 1) for c in calls)
    assert any(c.kwargs.get("media_type") == 4 or (c.args and c.args[1] == 4) for c in calls)
