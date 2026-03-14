import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.domain.movies.models import Movie
from app.domain.plex.collection_builder import BuilderResolver, ResolvedItem
from app.domain.plex.models import PlexConnection, PlexSyncRecord, PlexSyncStatus
from app.domain.tv_shows.models import TVShow


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.mark.unit
def test_resolved_item_dataclass():
    item = ResolvedItem(plex_rating_key="5", item_type="movie", item_id=1)
    assert item.plex_rating_key == "5"
    assert item.item_type == "movie"
    assert item.item_id == 1


@pytest.mark.unit
def test_static_items_resolver_returns_empty_when_no_sync_record(db_session):
    """Items without a SYNCED PlexSyncRecord are skipped."""
    resolver = BuilderResolver(db=db_session, connection_id=1)
    config = {"items": [{"tmdb_id": "99999", "item_type": "movie"}]}
    result = resolver.resolve_static_items(config)
    assert result == []


@pytest.mark.unit
def test_tmdb_collection_resolver_returns_empty_when_no_movies(db_session):
    resolver = BuilderResolver(db=db_session, connection_id=1)
    config = {"tmdb_collection_id": "0000"}
    result = resolver.resolve_tmdb_collection(config)
    assert result == []


@pytest.mark.unit
def test_resolve_genre_returns_empty_when_no_movies(db_session):
    resolver = BuilderResolver(db=db_session, connection_id=1)
    result = resolver.resolve_genre({"genre": "Action"})
    assert result == []


@pytest.mark.unit
def test_resolve_decade_returns_empty_when_no_movies(db_session):
    resolver = BuilderResolver(db=db_session, connection_id=1)
    result = resolver.resolve_decade({"decade": 2000})
    assert result == []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_connection(db_session, connection_id: int = 99) -> PlexConnection:
    conn = PlexConnection(
        id=connection_id,
        server_url="http://localhost:32400",
        token="fake-token",
    )
    db_session.add(conn)
    db_session.flush()
    return conn


def _make_synced_record(
    db_session, connection_id: int, item_type: str, item_id: int, rating_key: str
) -> PlexSyncRecord:
    record = PlexSyncRecord(
        connection_id=connection_id,
        item_type=item_type,
        item_id=item_id,
        plex_rating_key=rating_key,
        sync_status=PlexSyncStatus.SYNCED,
    )
    db_session.add(record)
    db_session.flush()
    return record


# ---------------------------------------------------------------------------
# resolve_genre tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_resolve_genre_matches_movie_with_action_genre(db_session):
    """A movie with genres JSON ["Action"] is returned when genre="Action"."""
    conn = _make_connection(db_session, connection_id=10)
    movie = Movie(title="Die Hard", genres=json.dumps(["Action", "Thriller"]))
    db_session.add(movie)
    db_session.flush()
    _make_synced_record(db_session, conn.id, "movie", movie.id, "rk-action-1")

    resolver = BuilderResolver(db=db_session, connection_id=conn.id)
    result = resolver.resolve_genre({"genre": "Action"})

    assert len(result) == 1
    assert result[0].plex_rating_key == "rk-action-1"
    assert result[0].item_type == "movie"
    assert result[0].item_id == movie.id


@pytest.mark.unit
def test_resolve_genre_excludes_movie_with_wrong_genre(db_session):
    """A movie whose genres do not include the requested genre is not returned."""
    conn = _make_connection(db_session, connection_id=11)
    movie = Movie(title="Shrek", genres=json.dumps(["Animation", "Comedy"]))
    db_session.add(movie)
    db_session.flush()
    _make_synced_record(db_session, conn.id, "movie", movie.id, "rk-comedy-1")

    resolver = BuilderResolver(db=db_session, connection_id=conn.id)
    result = resolver.resolve_genre({"genre": "Action"})

    assert result == []


@pytest.mark.unit
def test_resolve_genre_matches_tv_show(db_session):
    """A TV show with matching genre is included in results."""
    conn = _make_connection(db_session, connection_id=12)
    show = TVShow(title="Breaking Bad", genres=json.dumps(["Drama", "Crime"]))
    db_session.add(show)
    db_session.flush()
    _make_synced_record(db_session, conn.id, "tv_show", show.id, "rk-drama-tv-1")

    resolver = BuilderResolver(db=db_session, connection_id=conn.id)
    result = resolver.resolve_genre({"genre": "Drama"})

    tv_results = [r for r in result if r.item_type == "tv_show"]
    assert len(tv_results) == 1
    assert tv_results[0].plex_rating_key == "rk-drama-tv-1"


# ---------------------------------------------------------------------------
# resolve_decade tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_resolve_decade_matches_movie_from_2005(db_session):
    """A movie from 2005 is returned when decade=2000."""
    conn = _make_connection(db_session, connection_id=20)
    movie = Movie(title="Batman Begins", year=2005)
    db_session.add(movie)
    db_session.flush()
    _make_synced_record(db_session, conn.id, "movie", movie.id, "rk-decade-1")

    resolver = BuilderResolver(db=db_session, connection_id=conn.id)
    result = resolver.resolve_decade({"decade": 2000})

    assert len(result) == 1
    assert result[0].plex_rating_key == "rk-decade-1"
    assert result[0].item_id == movie.id


@pytest.mark.unit
def test_resolve_decade_excludes_movie_from_wrong_decade(db_session):
    """A movie from 1999 is not returned when decade=2000."""
    conn = _make_connection(db_session, connection_id=21)
    movie = Movie(title="The Matrix", year=1999)
    db_session.add(movie)
    db_session.flush()
    _make_synced_record(db_session, conn.id, "movie", movie.id, "rk-decade-2")

    resolver = BuilderResolver(db=db_session, connection_id=conn.id)
    result = resolver.resolve_decade({"decade": 2000})

    assert result == []


@pytest.mark.unit
def test_resolve_decade_boundary_year_2009(db_session):
    """A movie from 2009 is returned when decade=2000 (inclusive upper edge)."""
    conn = _make_connection(db_session, connection_id=22)
    movie = Movie(title="Avatar", year=2009)
    db_session.add(movie)
    db_session.flush()
    _make_synced_record(db_session, conn.id, "movie", movie.id, "rk-decade-3")

    resolver = BuilderResolver(db=db_session, connection_id=conn.id)
    result = resolver.resolve_decade({"decade": 2000})

    assert len(result) == 1
    assert result[0].plex_rating_key == "rk-decade-3"


# ---------------------------------------------------------------------------
# resolve_tmdb_collection tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_resolve_tmdb_collection_returns_matched_movies(db_session):
    """Movies with matching tmdb_collection_id are returned (no hasattr guard)."""
    conn = _make_connection(db_session, connection_id=30)
    movie = Movie(title="The Avengers", tmdb_collection_id=86311)
    db_session.add(movie)
    db_session.flush()
    _make_synced_record(db_session, conn.id, "movie", movie.id, "rk-avengers-1")

    resolver = BuilderResolver(db=db_session, connection_id=conn.id)
    result = resolver.resolve_tmdb_collection({"tmdb_collection_id": 86311})

    assert len(result) == 1
    assert result[0].plex_rating_key == "rk-avengers-1"
    assert result[0].item_id == movie.id


@pytest.mark.unit
def test_resolve_tmdb_collection_excludes_different_collection(db_session):
    """Movies belonging to a different collection are not returned."""
    conn = _make_connection(db_session, connection_id=31)
    movie = Movie(title="Iron Man", tmdb_collection_id=131292)
    db_session.add(movie)
    db_session.flush()
    _make_synced_record(db_session, conn.id, "movie", movie.id, "rk-ironman-1")

    resolver = BuilderResolver(db=db_session, connection_id=conn.id)
    result = resolver.resolve_tmdb_collection({"tmdb_collection_id": 86311})

    assert result == []


@pytest.mark.unit
def test_resolve_tmdb_collection_skips_unsynced_movies(db_session):
    """A movie in the collection without a SYNCED record is skipped."""
    conn = _make_connection(db_session, connection_id=32)
    movie = Movie(title="Avengers: Endgame", tmdb_collection_id=86311)
    db_session.add(movie)
    db_session.flush()
    # No PlexSyncRecord added

    resolver = BuilderResolver(db=db_session, connection_id=conn.id)
    result = resolver.resolve_tmdb_collection({"tmdb_collection_id": 86311})

    assert result == []
