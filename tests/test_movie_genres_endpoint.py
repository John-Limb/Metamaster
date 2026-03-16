"""Tests for the GET /api/v1/movies/genres endpoint."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db

# app.main must be imported before create_all so all ORM models are registered
from app.main import app  # noqa: E402

# ---------------------------------------------------------------------------
# DB setup
# ---------------------------------------------------------------------------

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(_engine)
_SessionLocal = sessionmaker(bind=_engine)


def override_get_db():
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app, raise_server_exceptions=True)


@pytest.fixture(autouse=True)
def _apply_db_override():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def db_session():
    db = _SessionLocal()
    yield db
    db.rollback()
    # Clean up movies table after each test so tests don't bleed into each other
    from app.domain.movies.models import Movie

    db.query(Movie).delete()
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_get_genres_returns_sorted_deduplicated_list(db_session):
    """GET /movies/genres returns sorted, deduplicated genres from movie library."""
    from app.domain.movies.models import Movie

    db_session.add(Movie(title="Film A", genres=json.dumps(["Action", "Thriller"])))
    db_session.add(Movie(title="Film B", genres=json.dumps(["Action", "Comedy"])))
    db_session.add(Movie(title="Film C", genres=None))  # no genres — must be excluded
    db_session.commit()

    response = client.get("/api/v1/movies/genres")
    assert response.status_code == 200
    data = response.json()
    assert data["genres"] == ["Action", "Comedy", "Thriller"]  # sorted, deduped


@pytest.mark.unit
def test_get_genres_empty_library(db_session):
    """GET /movies/genres returns empty list when no movies have genres."""
    response = client.get("/api/v1/movies/genres")
    assert response.status_code == 200
    data = response.json()
    assert data["genres"] == []
