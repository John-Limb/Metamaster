"""Tests for Plex watch status fields on API schemas and query helpers."""

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.movies.endpoints import _get_movie_watch_status
from app.api.v1.tv_shows.endpoints import _get_show_episode_counts
from app.core.database import Base
from app.domain.plex.models import PlexConnection, PlexSyncRecord
from app.domain.tv_shows.models import Episode, Season, TVShow
from app.schemas import MovieResponse, TVShowResponse


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# --- MovieResponse schema tests ---


def test_movie_response_has_is_watched_field():
    data = {
        "id": 1,
        "title": "Test",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_watched": False,
    }
    m = MovieResponse(**data)
    assert m.is_watched is False


def test_movie_response_is_watched_true():
    data = {
        "id": 1,
        "title": "Test",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_watched": True,
    }
    m = MovieResponse(**data)
    assert m.is_watched is True


def test_movie_response_is_watched_defaults_false():
    data = {
        "id": 1,
        "title": "Test",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    m = MovieResponse(**data)
    assert m.is_watched is False


# --- _get_movie_watch_status helper tests ---


def _make_connection(db):
    """Create a minimal PlexConnection to satisfy FK constraint."""
    conn = PlexConnection(server_url="http://plex.local", token="tok", is_active=True)
    db.add(conn)
    db.flush()
    return conn


def test_get_movie_watch_status_watched(db):
    conn = _make_connection(db)
    record = PlexSyncRecord(
        connection_id=conn.id,
        item_type="movie",
        item_id=42,
        sync_status="synced",
        is_watched=True,
    )
    db.add(record)
    db.flush()
    assert _get_movie_watch_status(db, 42) is True


def test_get_movie_watch_status_unwatched(db):
    assert _get_movie_watch_status(db, 9999) is False


def test_get_movie_watch_status_record_not_watched(db):
    conn = _make_connection(db)
    record = PlexSyncRecord(
        connection_id=conn.id,
        item_type="movie",
        item_id=77,
        sync_status="synced",
        is_watched=False,
    )
    db.add(record)
    db.flush()
    assert _get_movie_watch_status(db, 77) is False


# --- TVShowResponse schema tests ---


def test_tvshow_response_has_watch_count_fields():
    data = {
        "id": 1,
        "title": "Breaking Bad",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "watched_episode_count": 5,
        "total_episode_count": 62,
    }
    s = TVShowResponse(**data)
    assert s.watched_episode_count == 5
    assert s.total_episode_count == 62


def test_tvshow_response_watch_counts_default_zero():
    data = {
        "id": 1,
        "title": "Breaking Bad",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    s = TVShowResponse(**data)
    assert s.watched_episode_count == 0
    assert s.total_episode_count == 0


# --- _get_show_episode_counts helper tests ---


def _make_show_with_episodes(db, num_episodes=3):
    """Create a TVShow with one season and N episodes. Returns show."""
    show = TVShow(title="Test Show", enrichment_status="local_only")
    db.add(show)
    db.flush()
    season = Season(show_id=show.id, season_number=1)
    db.add(season)
    db.flush()
    for i in range(num_episodes):
        ep = Episode(season_id=season.id, episode_number=i + 1)
        db.add(ep)
    db.flush()
    return show


def test_get_show_episode_counts_no_plex(db):
    show = _make_show_with_episodes(db, num_episodes=4)
    watched, total = _get_show_episode_counts(db, show.id)
    assert watched == 0
    assert total == 4


def test_get_show_episode_counts_some_watched(db):
    conn = _make_connection(db)
    show = _make_show_with_episodes(db, num_episodes=3)
    eps = (
        db.query(Episode.id)
        .join(Season, Episode.season_id == Season.id)
        .filter(Season.show_id == show.id)
        .all()
    )
    ep_id = eps[0][0]
    record = PlexSyncRecord(
        connection_id=conn.id,
        item_type="episode",
        item_id=ep_id,
        sync_status="synced",
        is_watched=True,
    )
    db.add(record)
    db.flush()
    watched, total = _get_show_episode_counts(db, show.id)
    assert watched == 1
    assert total == 3
