import pytest

from app.domain.plex.models import PlexConnection, PlexItemType, PlexSyncRecord, PlexSyncStatus
from app.domain.plex.schemas import PlexConnectionResponse, PlexSyncRecordResponse


@pytest.mark.unit
def test_plex_connection_tablename():
    assert PlexConnection.__tablename__ == "plex_connections"


@pytest.mark.unit
def test_plex_sync_record_tablename():
    assert PlexSyncRecord.__tablename__ == "plex_sync_records"


@pytest.mark.unit
def test_plex_sync_status_values():
    assert PlexSyncStatus.PENDING == "pending"
    assert PlexSyncStatus.SYNCED == "synced"
    assert PlexSyncStatus.FAILED == "failed"
    assert PlexSyncStatus.NOT_FOUND == "not_found"
    assert PlexSyncStatus.MISMATCH == "mismatch"


@pytest.mark.unit
def test_plex_item_type_values():
    assert PlexItemType.MOVIE == "movie"
    assert PlexItemType.TV_SHOW == "tv_show"
    assert PlexItemType.EPISODE == "episode"


@pytest.mark.unit
def test_plex_sync_record_has_required_columns():
    cols = {c.name for c in PlexSyncRecord.__table__.columns}
    required = {
        "id",
        "connection_id",
        "item_type",
        "item_id",
        "plex_rating_key",
        "plex_tmdb_id",
        "last_matched_at",
        "last_pulled_at",
        "watch_count",
        "last_watched_at",
        "is_watched",
        "sync_status",
        "last_error",
    }
    assert required.issubset(cols)


@pytest.mark.unit
def test_plex_connection_has_required_columns():
    cols = {c.name for c in PlexConnection.__table__.columns}
    required = {
        "id",
        "server_url",
        "token",
        "movie_library_id",
        "tv_library_id",
        "is_active",
        "created_at",
        "last_connected_at",
    }
    assert required.issubset(cols)


@pytest.mark.unit
def test_plex_connection_response_schema():
    data = {
        "id": 1,
        "server_url": "http://plex:32400",
        "is_active": True,
        "movie_library_id": "1",
        "tv_library_id": "2",
        "created_at": "2026-03-05T00:00:00",
        "last_connected_at": None,
    }
    schema = PlexConnectionResponse(**data)
    assert schema.server_url == "http://plex:32400"
    assert schema.is_active is True
    assert schema.movie_library_id == "1"


@pytest.mark.unit
def test_plex_sync_record_response_schema():
    data = {
        "id": 1,
        "connection_id": 1,
        "item_type": "movie",
        "item_id": 42,
        "plex_rating_key": "99",
        "sync_status": "synced",
        "watch_count": 3,
        "is_watched": True,
        "last_matched_at": None,
        "last_pulled_at": None,
        "last_watched_at": None,
        "last_error": None,
    }
    schema = PlexSyncRecordResponse(**data)
    assert schema.sync_status == "synced"
    assert schema.watch_count == 3
    assert schema.item_id == 42


@pytest.mark.unit
def test_plex_connection_response_optional_fields_default_none():
    data = {
        "id": 2,
        "server_url": "http://plex:32400",
        "is_active": False,
        "movie_library_id": None,
        "tv_library_id": None,
        "created_at": "2026-03-05T00:00:00",
        "last_connected_at": None,
    }
    schema = PlexConnectionResponse(**data)
    assert schema.movie_library_id is None
    assert schema.is_active is False


@pytest.mark.unit
def test_plex_sync_status_has_mismatch_value():
    assert PlexSyncStatus.MISMATCH == "mismatch"


@pytest.mark.unit
def test_plex_sync_record_has_plex_tmdb_id_column():
    cols = {c.name for c in PlexSyncRecord.__table__.columns}
    assert "plex_tmdb_id" in cols
