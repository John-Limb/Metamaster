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

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

# TestClient must be created AFTER dependency overrides are applied.
client = TestClient(app, raise_server_exceptions=True)


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
    from app.domain.plex.collection_models import PlexCollection, PlexCollectionSet, PlexPlaylist
    from app.domain.plex.models import PlexConnection

    db.query(PlexPlaylist).delete()
    db.query(PlexCollection).delete()
    db.query(PlexCollectionSet).delete()
    db.query(PlexConnection).delete()
    db.commit()
    db.close()


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
