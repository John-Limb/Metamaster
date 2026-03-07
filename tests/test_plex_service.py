from unittest.mock import MagicMock

import pytest

from app.domain.plex.models import PlexItemType, PlexSyncRecord, PlexSyncStatus
from app.domain.plex.service import PlexSyncService
from app.infrastructure.external_apis.plex.schemas import PlexLibrarySection, PlexMediaItem


def make_service(movie_lib="Movies", tv_lib="TV Shows"):
    mock_db = MagicMock()
    mock_client = MagicMock()
    mock_client.get_library_sections.return_value = [
        PlexLibrarySection(key="1", title="Movies", type="movie"),
        PlexLibrarySection(key="2", title="TV Shows", type="show"),
    ]
    return PlexSyncService(
        db=mock_db,
        client=mock_client,
        movie_library_name=movie_lib,
        tv_library_name=tv_lib,
    )


@pytest.mark.unit
def test_resolve_library_ids_success():
    svc = make_service()
    movie_id, tv_id = svc.resolve_library_ids()
    assert movie_id == "1"
    assert tv_id == "2"


@pytest.mark.unit
def test_resolve_library_ids_movie_name_mismatch_raises():
    svc = make_service(movie_lib="Films")
    with pytest.raises(ValueError, match="Library 'Films' not found"):
        svc.resolve_library_ids()


@pytest.mark.unit
def test_resolve_library_ids_tv_name_mismatch_raises():
    svc = make_service(tv_lib="Series")
    with pytest.raises(ValueError, match="Library 'Series' not found"):
        svc.resolve_library_ids()


@pytest.mark.unit
def test_resolve_library_ids_error_includes_available_names():
    svc = make_service(movie_lib="Films")
    with pytest.raises(ValueError) as exc_info:
        svc.resolve_library_ids()
    assert "Movies" in str(exc_info.value)
    assert "TV Shows" in str(exc_info.value)


@pytest.mark.unit
def test_lock_match_creates_sync_record_on_success():
    mock_db = MagicMock()
    mock_client = MagicMock()
    mock_client.find_rating_key_by_tmdb_id.return_value = "99"
    mock_db.query.return_value.filter.return_value.first.return_value = None

    svc = PlexSyncService(
        db=mock_db,
        client=mock_client,
        movie_library_name="Movies",
        tv_library_name="TV Shows",
    )
    svc.lock_match(
        section_id="1",
        item_type=PlexItemType.MOVIE,
        item_id=42,
        tmdb_id="603",
        connection_id=1,
    )

    mock_db.add.assert_called_once()
    record = mock_db.add.call_args[0][0]
    assert record.plex_rating_key == "99"
    assert record.sync_status == PlexSyncStatus.SYNCED


@pytest.mark.unit
def test_lock_match_marks_not_found_when_no_plex_item():
    mock_db = MagicMock()
    mock_client = MagicMock()
    mock_client.find_rating_key_by_tmdb_id.return_value = None
    mock_db.query.return_value.filter.return_value.first.return_value = None

    svc = PlexSyncService(
        db=mock_db,
        client=mock_client,
        movie_library_name="Movies",
        tv_library_name="TV Shows",
    )
    svc.lock_match(
        section_id="1",
        item_type=PlexItemType.MOVIE,
        item_id=42,
        tmdb_id="999",
        connection_id=1,
    )

    record = mock_db.add.call_args[0][0]
    assert record.sync_status == PlexSyncStatus.NOT_FOUND
    assert record.plex_rating_key is None


@pytest.mark.unit
def test_lock_match_does_not_raise_on_not_found():
    """not_found items must never block processing — no exception raised."""
    mock_db = MagicMock()
    mock_client = MagicMock()
    mock_client.find_rating_key_by_tmdb_id.return_value = None
    mock_db.query.return_value.filter.return_value.first.return_value = None

    svc = PlexSyncService(
        db=mock_db,
        client=mock_client,
        movie_library_name="Movies",
        tv_library_name="TV Shows",
    )
    # Must not raise
    svc.lock_match(
        section_id="1",
        item_type=PlexItemType.MOVIE,
        item_id=99,
        tmdb_id="000",
        connection_id=1,
    )


@pytest.mark.unit
def test_pull_watched_status_updates_existing_record():
    mock_db = MagicMock()
    mock_client = MagicMock()
    plex_item = PlexMediaItem(
        **{
            "ratingKey": "99",
            "title": "The Matrix",
            "viewCount": 5,
            "lastViewedAt": 1700000000,
            "Guid": [{"id": "tmdb://603"}],
        }
    )
    mock_client.get_all_items.return_value = [plex_item]
    existing_record = MagicMock(spec=PlexSyncRecord)
    mock_db.query.return_value.filter.return_value.first.return_value = existing_record

    svc = PlexSyncService(
        db=mock_db,
        client=mock_client,
        movie_library_name="Movies",
        tv_library_name="TV Shows",
    )
    svc.pull_watched_status(section_id="1", media_type=1, connection_id=1)

    assert existing_record.watch_count == 5
    assert existing_record.is_watched is True
    mock_db.commit.assert_called()


@pytest.mark.unit
def test_pull_watched_status_skips_items_with_no_tmdb_id():
    mock_db = MagicMock()
    mock_client = MagicMock()
    plex_item = PlexMediaItem(**{"ratingKey": "99", "title": "Unknown", "Guid": []})
    mock_client.get_all_items.return_value = [plex_item]

    svc = PlexSyncService(
        db=mock_db,
        client=mock_client,
        movie_library_name="Movies",
        tv_library_name="TV Shows",
    )
    svc.pull_watched_status(section_id="1", media_type=1, connection_id=1)

    mock_db.add.assert_not_called()


@pytest.mark.unit
def test_pull_watched_status_continues_after_unmatched_record():
    """If a Plex item has no sync record, processing must continue for others."""
    mock_db = MagicMock()
    mock_client = MagicMock()
    items = [
        PlexMediaItem(
            **{
                "ratingKey": "1",
                "title": "A",
                "viewCount": 1,
                "Guid": [{"id": "tmdb://100"}],
            }
        ),
        PlexMediaItem(
            **{
                "ratingKey": "2",
                "title": "B",
                "viewCount": 2,
                "Guid": [{"id": "tmdb://200"}],
            }
        ),
    ]
    mock_client.get_all_items.return_value = items
    # First query returns None (no record), second returns a mock record
    no_record = None
    mock_record = MagicMock(spec=PlexSyncRecord)
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        no_record,
        mock_record,
    ]

    svc = PlexSyncService(
        db=mock_db,
        client=mock_client,
        movie_library_name="Movies",
        tv_library_name="TV Shows",
    )
    svc.pull_watched_status(section_id="1", media_type=1, connection_id=1)

    # Second item should still be updated despite first having no record
    assert mock_record.watch_count == 2
