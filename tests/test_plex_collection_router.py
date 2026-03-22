"""Tests for the Plex collection and playlist API router."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db  # noqa: E402

# app.main must be imported before create_all so all ORM models are registered
# in Base.metadata (app.main transitively imports every model module).
from app.main import app  # noqa: E402 (must come before Base import below)

# ---------------------------------------------------------------------------
# DB / auth overrides
# ---------------------------------------------------------------------------

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    # StaticPool ensures all connections share the same in-memory database.
    poolclass=StaticPool,
)
# All ORM models are now registered because app.main imported them above.
Base.metadata.create_all(_engine)
_SessionLocal = sessionmaker(bind=_engine)


def override_get_db():
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    return {"id": 1, "username": "test"}


from app.api.v1.auth.endpoints import get_current_user  # noqa: E402

# TestClient is created once; overrides are applied per-test via autouse fixture.
client = TestClient(app, raise_server_exceptions=True)


@pytest.fixture(autouse=True)
def _apply_overrides():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_connection():
    from app.domain.plex.models import PlexConnection

    db = _SessionLocal()
    conn = PlexConnection(
        server_url="http://plex-test",
        token="tok",
        is_active=True,
        movie_library_id="1",
        tv_library_id="2",
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    conn_id = conn.id
    db.close()
    return conn_id


def _clear_db():
    db = _SessionLocal()
    from app.domain.movies.models import Movie
    from app.domain.plex.collection_models import (
        PlexCollection,
        PlexCollectionItem,
        PlexCollectionSet,
        PlexPlaylist,
        PlexPlaylistItem,
    )
    from app.domain.plex.models import PlexConnection

    db.query(PlexPlaylistItem).delete()
    db.query(PlexCollectionItem).delete()
    db.query(PlexPlaylist).delete()
    db.query(PlexCollection).delete()
    db.query(PlexCollectionSet).delete()
    db.query(PlexConnection).delete()
    db.query(Movie).delete()
    db.commit()
    db.close()


def _seed_movie(title: str) -> int:
    from app.domain.movies.models import Movie

    db = _SessionLocal()
    movie = Movie(title=title, enrichment_status="local_only")
    db.add(movie)
    db.commit()
    db.refresh(movie)
    mid = movie.id
    db.close()
    return mid


# ---------------------------------------------------------------------------
# Tests: collections
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_list_collections_no_connection():
    """GET /plex/collections returns 404 when no active connection exists."""
    _clear_db()
    resp = client.get("/api/v1/plex/collections")
    assert resp.status_code == 404
    assert "No active Plex connection" in resp.json()["detail"]


@pytest.mark.unit
def test_create_collection_returns_201():
    """POST /plex/collections creates a collection and returns 201."""
    _clear_db()
    _seed_connection()
    payload = {
        "name": "Marvel",
        "builder_type": "static_items",
        "builder_config": {"items": []},
    }
    resp = client.post("/api/v1/plex/collections", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Marvel"
    assert data["enabled"] is False
    assert data["is_default"] is False


@pytest.mark.unit
def test_get_collection_returns_data():
    """GET /plex/collections/{id} returns the collection."""
    _clear_db()
    _seed_connection()
    create_resp = client.post(
        "/api/v1/plex/collections",
        json={"name": "DC", "builder_type": "genre", "builder_config": {"genre": "Action"}},
    )
    assert create_resp.status_code == 201
    coll_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/plex/collections/{coll_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "DC"


@pytest.mark.unit
def test_patch_collection_updates_enabled():
    """PATCH /plex/collections/{id} updates the enabled flag."""
    _clear_db()
    _seed_connection()
    create_resp = client.post(
        "/api/v1/plex/collections",
        json={"name": "Sci-Fi", "builder_type": "decade", "builder_config": {"decade": 1990}},
    )
    coll_id = create_resp.json()["id"]

    resp = client.patch(f"/api/v1/plex/collections/{coll_id}", json={"enabled": True})
    assert resp.status_code == 200
    assert resp.json()["enabled"] is True


@pytest.mark.unit
def test_push_collection_disabled_returns_400():
    """POST /plex/collections/{id}/push returns 400 when collection is disabled."""
    _clear_db()
    _seed_connection()
    create_resp = client.post(
        "/api/v1/plex/collections",
        json={
            "name": "Horror",
            "builder_type": "static_items",
            "builder_config": {"items": []},
        },
    )
    coll_id = create_resp.json()["id"]

    resp = client.post(f"/api/v1/plex/collections/{coll_id}/push")
    assert resp.status_code == 400
    assert "not enabled" in resp.json()["detail"]


@pytest.mark.unit
def test_pull_playlists_calls_service():
    """POST /plex/playlists/pull calls PlexPlaylistService.pull_playlists."""
    _clear_db()
    _seed_connection()

    mock_svc = MagicMock()
    mock_svc.pull_playlists.return_value = None

    with (
        patch(
            "app.api.v1.plex.collection_router._make_clients",
            return_value=(MagicMock(), MagicMock(), MagicMock()),
        ),
        patch(
            "app.api.v1.plex.collection_router._make_services",
            return_value=(MagicMock(), mock_svc),
        ),
    ):
        resp = client.post("/api/v1/plex/playlists/pull")

    assert resp.status_code == 200
    mock_svc.pull_playlists.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: collection sets
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_list_collection_sets_returns_sets():
    """GET /plex/sets returns collection sets for the active connection."""
    from app.domain.plex.collection_models import PlexCollectionSet

    _clear_db()
    conn_id = _seed_connection()
    db = _SessionLocal()
    cs = PlexCollectionSet(connection_id=conn_id, set_type="genre", enabled=False)
    db.add(cs)
    db.commit()
    db.close()

    resp = client.get("/api/v1/plex/sets")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["set_type"] == "genre"
    assert data[0]["enabled"] is False


@pytest.mark.unit
def test_update_collection_set_toggles_enabled():
    """PATCH /plex/sets/genre with enabled=true updates the record."""
    from app.domain.plex.collection_models import PlexCollectionSet

    _clear_db()
    conn_id = _seed_connection()
    db = _SessionLocal()
    cs = PlexCollectionSet(connection_id=conn_id, set_type="genre", enabled=False)
    db.add(cs)
    db.commit()
    db.close()

    resp = client.patch("/api/v1/plex/sets/genre", json={"enabled": True})
    assert resp.status_code == 200
    assert resp.json()["enabled"] is True


@pytest.mark.unit
def test_update_collection_set_404_if_missing():
    """PATCH /plex/sets/genre returns 404 when no matching set exists."""
    _clear_db()
    _seed_connection()

    resp = client.patch("/api/v1/plex/sets/genre", json={"enabled": True})
    assert resp.status_code == 404
    assert "Collection set not found" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Tests: YAML import
# ---------------------------------------------------------------------------

VALID_YAML = """
collections:
  Marvel Cinematic Universe:
    name: Marvel Cinematic Universe
    description: All MCU films
    sort_title: Marvel 01
    builder:
      builder_type: tmdb_collection
      tmdb_collection_id: "86311"
"""


@pytest.mark.unit
def test_import_yaml_creates_collections():
    """POST /plex/collections/import with valid YAML creates a collection."""
    _clear_db()
    _seed_connection()

    resp = client.post(
        "/api/v1/plex/collections/import",
        json={"yaml_content": VALID_YAML},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "Marvel Cinematic Universe" in data["collections_created"]
    assert data["playlists_created"] == []

    list_resp = client.get("/api/v1/plex/collections")
    names = [c["name"] for c in list_resp.json()]
    assert "Marvel Cinematic Universe" in names


@pytest.mark.unit
def test_import_yaml_invalid_yaml_returns_422():
    """POST /plex/collections/import with invalid YAML returns 422."""
    _clear_db()
    _seed_connection()

    resp = client.post(
        "/api/v1/plex/collections/import",
        json={"yaml_content": ":\tinvalid: [yaml"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Tests: local TMDB collections
# ---------------------------------------------------------------------------


@pytest.fixture()
def db():
    """Provide a DB session and clean up Movie rows after each test."""
    from app.domain.movies.models import Movie

    session = _SessionLocal()
    yield session
    session.query(Movie).delete()
    session.commit()
    session.close()


@pytest.mark.unit
def test_get_local_tmdb_collections_groups_by_collection(db):
    """Returns movies grouped by tmdb_collection_id, sorted by count desc."""
    from app.domain.movies.models import Movie

    db.add(
        Movie(
            title="Batman Begins",
            tmdb_collection_id=263,
            tmdb_collection_name="The Dark Knight Collection",
        )
    )
    db.add(
        Movie(
            title="The Dark Knight",
            tmdb_collection_id=263,
            tmdb_collection_name="The Dark Knight Collection",
        )
    )
    db.add(
        Movie(
            title="Inception",
            tmdb_collection_id=536,
            tmdb_collection_name="Inception Collection",
        )
    )
    db.add(Movie(title="No Collection"))
    db.commit()

    response = client.get("/api/v1/plex/tmdb-collections/local")
    assert response.status_code == 200
    data = response.json()
    # sorted by movie_count desc: 263 (2) before 536 (1)
    assert len(data) == 2
    assert data[0]["tmdb_collection_id"] == 263
    assert data[0]["movie_count"] == 2
    assert data[0]["name"] == "The Dark Knight Collection"
    assert data[1]["tmdb_collection_id"] == 536
    assert data[1]["movie_count"] == 1


@pytest.mark.unit
def test_get_local_tmdb_collections_fallback_name(db):
    """Falls back to 'Collection {id}' when tmdb_collection_name is None."""
    from app.domain.movies.models import Movie

    db.add(
        Movie(
            title="Mystery Film",
            tmdb_collection_id=999,
            tmdb_collection_name=None,
        )
    )
    db.commit()

    response = client.get("/api/v1/plex/tmdb-collections/local")
    assert response.status_code == 200
    names = [item["name"] for item in response.json()]
    assert "Collection 999" in names


# ---------------------------------------------------------------------------
# Tests: TMDB collection search proxy
# ---------------------------------------------------------------------------


def test_search_tmdb_collections_returns_results(monkeypatch):
    """Proxies to TMDB and returns id + name list."""
    from unittest.mock import MagicMock, patch

    import httpx

    fake_response_data = {
        "results": [
            {"id": 9485, "name": "Christopher Nolan Collection"},
            {"id": 948, "name": "Batman Collection"},
        ]
    }

    async def mock_get(self, url, **kwargs):
        mock = MagicMock()
        mock.raise_for_status = MagicMock()
        mock.json.return_value = fake_response_data
        return mock

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    with patch("app.api.v1.plex.collection_router.settings") as mock_settings:
        mock_settings.tmdb_read_access_token = "fake-token"
        mock_settings.tmdb_api_key = None
        response = client.get("/api/v1/plex/tmdb-collections/search?q=nolan")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0] == {"id": 9485, "name": "Christopher Nolan Collection"}


def test_search_tmdb_collections_returns_503_when_no_credentials():
    """Returns 503 when no TMDB credentials are configured."""
    from unittest.mock import patch

    with patch("app.api.v1.plex.collection_router.settings") as mock_settings:
        mock_settings.tmdb_read_access_token = None
        mock_settings.tmdb_api_key = None
        response = client.get("/api/v1/plex/tmdb-collections/search?q=batman")

    assert response.status_code == 503


@pytest.mark.unit
def test_push_all_collections_queues_task():
    """POST /plex/collections/push-all returns 202 and queues Celery task with connection id."""
    _clear_db()
    conn_id = _seed_connection()
    with patch("app.api.v1.plex.collection_router.push_all_collections") as mock_task:
        resp = client.post("/api/v1/plex/collections/push-all")
    assert resp.status_code == 202
    assert resp.json() == {"status": "queued"}
    mock_task.delay.assert_called_once_with(conn_id)


@pytest.mark.unit
def test_delete_collection_without_plex_flag():
    """DELETE /plex/collections/{id} without flag just deletes from DB (no Plex call)."""
    _clear_db()
    _seed_connection()
    payload = {
        "name": "To Delete",
        "builder_type": "static_items",
        "builder_config": {"items": []},
    }
    create_resp = client.post("/api/v1/plex/collections", json=payload)
    coll_id = create_resp.json()["id"]

    with patch("app.api.v1.plex.collection_router._make_clients") as mock_clients:
        resp = client.delete(f"/api/v1/plex/collections/{coll_id}")

    assert resp.status_code == 204
    mock_clients.assert_not_called()


@pytest.mark.unit
def test_delete_collection_with_plex_flag_calls_client():
    """DELETE with ?delete_from_plex=true calls PlexCollectionClient.delete_collection."""
    _clear_db()
    _seed_connection()
    payload = {
        "name": "Plex Delete Test",
        "builder_type": "static_items",
        "builder_config": {"items": []},
    }
    create_resp = client.post("/api/v1/plex/collections", json=payload)
    coll_id = create_resp.json()["id"]

    # Manually set plex_rating_key so the branch is exercised
    db = _SessionLocal()
    from app.domain.plex.collection_models import PlexCollection

    coll = db.query(PlexCollection).filter_by(id=coll_id).first()
    coll.plex_rating_key = "plex-key-999"
    db.commit()
    db.close()

    mock_cc = MagicMock()
    with patch(
        "app.api.v1.plex.collection_router.PlexCollectionClient",
        return_value=mock_cc,
    ):
        resp = client.delete(f"/api/v1/plex/collections/{coll_id}?delete_from_plex=true")

    assert resp.status_code == 204
    mock_cc.delete_collection.assert_called_once_with("plex-key-999")


@pytest.mark.unit
def test_delete_collection_plex_failure_still_deletes_db_row():
    """If Plex delete_collection raises, endpoint still returns 204 and removes DB row."""
    _clear_db()
    _seed_connection()
    payload = {
        "name": "Plex Fail Test",
        "builder_type": "static_items",
        "builder_config": {"items": []},
    }
    create_resp = client.post("/api/v1/plex/collections", json=payload)
    coll_id = create_resp.json()["id"]

    db = _SessionLocal()
    from app.domain.plex.collection_models import PlexCollection

    coll = db.query(PlexCollection).filter_by(id=coll_id).first()
    coll.plex_rating_key = "plex-key-fail"
    db.commit()
    db.close()

    mock_cc = MagicMock()
    mock_cc.return_value.delete_collection.side_effect = Exception("Plex unavailable")
    with patch(
        "app.api.v1.plex.collection_router.PlexCollectionClient",
        mock_cc,
    ):
        resp = client.delete(f"/api/v1/plex/collections/{coll_id}?delete_from_plex=true")

    assert resp.status_code == 204
    # Row must be gone from the DB
    db = _SessionLocal()
    assert db.query(PlexCollection).filter_by(id=coll_id).first() is None
    db.close()


@pytest.mark.unit
def test_get_collection_items_have_movie_title_field():
    """GET /plex/collections/{id} returns items list (movie_title tested in enrichment tests)."""
    _clear_db()
    _seed_connection()
    create_resp = client.post(
        "/api/v1/plex/collections",
        json={"name": "T", "builder_type": "static_items", "builder_config": {"items": []}},
    )
    coll_id = create_resp.json()["id"]
    resp = client.get(f"/api/v1/plex/collections/{coll_id}")
    assert resp.status_code == 200
    assert "items" in resp.json()


@pytest.mark.unit
def test_get_playlist_items_have_movie_title_field():
    """GET /plex/playlists/{id} returns items list (movie_title tested in enrichment tests)."""
    _clear_db()
    _seed_connection()
    pl_resp = client.post(
        "/api/v1/plex/playlists",
        json={"name": "P", "builder_config": {}},
    )
    pl_id = pl_resp.json()["id"]
    resp = client.get(f"/api/v1/plex/playlists/{pl_id}")
    assert resp.status_code == 200
    assert "items" in resp.json()


@pytest.mark.unit
def test_get_collection_items_resolved_with_movie_title():
    """Items matched in the local movie DB include their title."""
    _clear_db()
    _seed_connection()
    movie_id = _seed_movie("The Dark Knight")

    create_resp = client.post(
        "/api/v1/plex/collections",
        json={"name": "Heroes", "builder_type": "static_items", "builder_config": {}},
    )
    coll_id = create_resp.json()["id"]

    from app.domain.plex.collection_models import PlexCollectionItem

    db = _SessionLocal()
    db.add(
        PlexCollectionItem(
            collection_id=coll_id,
            plex_rating_key="key-1",
            item_type="movie",
            item_id=movie_id,
            position=0,
        )
    )
    db.commit()
    db.close()

    resp = client.get(f"/api/v1/plex/collections/{coll_id}")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["movie_title"] == "The Dark Knight"


@pytest.mark.unit
def test_get_collection_item_unmatched_has_null_title():
    """Items with item_type=tv_show get movie_title=null."""
    _clear_db()
    _seed_connection()
    create_resp = client.post(
        "/api/v1/plex/collections",
        json={"name": "TV", "builder_type": "static_items", "builder_config": {}},
    )
    coll_id = create_resp.json()["id"]

    from app.domain.plex.collection_models import PlexCollectionItem

    db = _SessionLocal()
    db.add(
        PlexCollectionItem(
            collection_id=coll_id,
            plex_rating_key="key-tv",
            item_type="tv_show",
            item_id=999,
            position=0,
        )
    )
    db.commit()
    db.close()

    resp = client.get(f"/api/v1/plex/collections/{coll_id}")
    items = resp.json()["items"]
    assert items[0]["movie_title"] is None


@pytest.mark.unit
def test_get_playlist_items_resolved_with_movie_title():
    """Playlist items matched in the local movie DB include their title."""
    _clear_db()
    _seed_connection()
    movie_id = _seed_movie("Mad Max")

    pl_resp = client.post("/api/v1/plex/playlists", json={"name": "P", "builder_config": {}})
    pl_id = pl_resp.json()["id"]

    from app.domain.plex.collection_models import PlexPlaylistItem

    db = _SessionLocal()
    db.add(
        PlexPlaylistItem(
            playlist_id=pl_id,
            plex_rating_key="key-2",
            item_type="movie",
            item_id=movie_id,
            position=0,
        )
    )
    db.commit()
    db.close()

    resp = client.get(f"/api/v1/plex/playlists/{pl_id}")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items[0]["movie_title"] == "Mad Max"


@pytest.mark.unit
def test_collection_artwork_returns_404_when_no_plex_key():
    """GET /plex/collections/{id}/artwork returns 404 when not synced to Plex."""
    _clear_db()
    _seed_connection()
    create_resp = client.post(
        "/api/v1/plex/collections",
        json={"name": "Art", "builder_type": "static_items", "builder_config": {}},
    )
    coll_id = create_resp.json()["id"]
    resp = client.get(f"/api/v1/plex/collections/{coll_id}/artwork")
    assert resp.status_code == 404


@pytest.mark.unit
def test_collection_artwork_proxies_plex_image():
    """GET /plex/collections/{id}/artwork returns proxied image from Plex."""
    _clear_db()
    _seed_connection()
    create_resp = client.post(
        "/api/v1/plex/collections",
        json={"name": "Art", "builder_type": "static_items", "builder_config": {}},
    )
    coll_id = create_resp.json()["id"]

    from app.domain.plex.collection_models import PlexCollection

    db = _SessionLocal()
    coll = db.query(PlexCollection).filter_by(id=coll_id).first()
    coll.plex_rating_key = "rk-art"
    db.commit()
    db.close()

    mock_response = MagicMock()
    mock_response.content = b"fake-image-bytes"
    mock_response.headers = {"content-type": "image/jpeg"}
    mock_response.raise_for_status = MagicMock()

    with patch("app.api.v1.plex.collection_router.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        resp = client.get(f"/api/v1/plex/collections/{coll_id}/artwork")

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"
    assert resp.content == b"fake-image-bytes"


@pytest.mark.unit
def test_collection_artwork_returns_502_on_plex_error():
    """GET /plex/collections/{id}/artwork returns 502 when Plex is unreachable."""
    _clear_db()
    _seed_connection()
    create_resp = client.post(
        "/api/v1/plex/collections",
        json={"name": "Art", "builder_type": "static_items", "builder_config": {}},
    )
    coll_id = create_resp.json()["id"]

    from app.domain.plex.collection_models import PlexCollection

    db = _SessionLocal()
    coll = db.query(PlexCollection).filter_by(id=coll_id).first()
    coll.plex_rating_key = "rk-err"
    db.commit()
    db.close()

    with patch("app.api.v1.plex.collection_router.httpx.Client") as mock_client:
        import httpx as httpx_lib

        mock_client.return_value.__enter__.return_value.get.side_effect = httpx_lib.RequestError(
            "timeout"
        )
        resp = client.get(f"/api/v1/plex/collections/{coll_id}/artwork")

    assert resp.status_code == 502


@pytest.mark.unit
def test_playlist_artwork_returns_404_when_no_plex_key():
    """GET /plex/playlists/{id}/artwork returns 404 when not synced to Plex."""
    _clear_db()
    _seed_connection()
    pl_resp = client.post("/api/v1/plex/playlists", json={"name": "P", "builder_config": {}})
    pl_id = pl_resp.json()["id"]
    resp = client.get(f"/api/v1/plex/playlists/{pl_id}/artwork")
    assert resp.status_code == 404


@pytest.mark.unit
def test_playlist_artwork_proxies_plex_image():
    """GET /plex/playlists/{id}/artwork returns proxied image from Plex."""
    _clear_db()
    _seed_connection()
    pl_resp = client.post("/api/v1/plex/playlists", json={"name": "P", "builder_config": {}})
    pl_id = pl_resp.json()["id"]

    from app.domain.plex.collection_models import PlexPlaylist

    db = _SessionLocal()
    pl = db.query(PlexPlaylist).filter_by(id=pl_id).first()
    pl.plex_rating_key = "rk-pl"
    db.commit()
    db.close()

    mock_response = MagicMock()
    mock_response.content = b"playlist-image"
    mock_response.headers = {"content-type": "image/png"}
    mock_response.raise_for_status = MagicMock()

    with patch("app.api.v1.plex.collection_router.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        resp = client.get(f"/api/v1/plex/playlists/{pl_id}/artwork")

    assert resp.status_code == 200
    assert resp.content == b"playlist-image"


@pytest.mark.unit
def test_playlist_artwork_returns_502_on_plex_error():
    """GET /plex/playlists/{id}/artwork returns 502 when Plex is unreachable."""
    _clear_db()
    _seed_connection()
    pl_resp = client.post("/api/v1/plex/playlists", json={"name": "P", "builder_config": {}})
    pl_id = pl_resp.json()["id"]

    from app.domain.plex.collection_models import PlexPlaylist

    db = _SessionLocal()
    pl = db.query(PlexPlaylist).filter_by(id=pl_id).first()
    pl.plex_rating_key = "rk-pl-err"
    db.commit()
    db.close()

    with patch("app.api.v1.plex.collection_router.httpx.Client") as mock_client:
        import httpx as httpx_lib

        mock_client.return_value.__enter__.return_value.get.side_effect = httpx_lib.RequestError(
            "timeout"
        )
        resp = client.get(f"/api/v1/plex/playlists/{pl_id}/artwork")

    assert resp.status_code == 502
