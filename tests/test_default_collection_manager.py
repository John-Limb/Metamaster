import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.domain.movies.models import Movie  # noqa: F401 – registers movies table
from app.domain.plex.collection_models import BuilderType, PlexCollection
from app.domain.plex.default_collection_manager import DefaultCollectionManager
from app.domain.plex.models import PlexConnection  # noqa: F401 – registers plex_connections table
from app.domain.tv_shows.models import TVShow  # noqa: F401 – registers tv_shows table


@pytest.fixture
def db_session():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    Session = sessionmaker(bind=eng)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(eng)


@pytest.fixture
def connection(db_session):
    conn = PlexConnection(server_url="http://plex", token="tok", is_active=True)
    db_session.add(conn)
    db_session.commit()
    return conn


@pytest.mark.unit
def test_discover_franchises_creates_collection(db_session, connection):
    movie = Movie(title="Iron Man", tmdb_collection_id=10, tmdb_collection_name="MCU")
    db_session.add(movie)
    db_session.commit()

    manager = DefaultCollectionManager(db_session, connection.id)
    results = manager.discover_franchises()

    assert len(results) == 1
    coll = results[0]
    assert coll.name == "MCU"
    assert coll.builder_type == BuilderType.TMDB_COLLECTION
    assert coll.builder_config == {"tmdb_collection_id": 10}
    assert coll.enabled is False
    assert coll.is_default is True


@pytest.mark.unit
def test_discover_franchises_is_idempotent(db_session, connection):
    movie = Movie(title="Iron Man", tmdb_collection_id=10, tmdb_collection_name="MCU")
    db_session.add(movie)
    db_session.commit()

    manager = DefaultCollectionManager(db_session, connection.id)
    manager.discover_franchises()
    manager.discover_franchises()

    count = (
        db_session.query(PlexCollection).filter_by(connection_id=connection.id, name="MCU").count()
    )
    assert count == 1


@pytest.mark.unit
def test_discover_genres_creates_genre_collections(db_session, connection):
    movie = Movie(title="Die Hard", genres='["Action"]')
    db_session.add(movie)
    db_session.commit()

    manager = DefaultCollectionManager(db_session, connection.id)
    results = manager.discover_genres()

    assert len(results) == 1
    coll = results[0]
    assert coll.name == "Action Films"
    assert coll.builder_type == BuilderType.GENRE
    assert coll.builder_config == {"genre": "Action"}
    assert coll.enabled is False
    assert coll.is_default is True


@pytest.mark.unit
def test_discover_decades_creates_decade_collections(db_session, connection):
    movie = Movie(title="Shrek", year=2005)
    db_session.add(movie)
    db_session.commit()

    manager = DefaultCollectionManager(db_session, connection.id)
    results = manager.discover_decades()

    assert len(results) == 1
    coll = results[0]
    assert coll.name == "2000s"
    assert coll.builder_type == BuilderType.DECADE
    assert coll.builder_config == {"decade": 2000}
    assert coll.enabled is False
    assert coll.is_default is True


@pytest.mark.unit
def test_upsert_does_not_duplicate(db_session, connection):
    movie = Movie(title="Die Hard", genres='["Action"]')
    db_session.add(movie)
    db_session.commit()

    manager = DefaultCollectionManager(db_session, connection.id)
    first = manager.discover_genres()
    second = manager.discover_genres()

    assert len(first) == len(second)
    total = db_session.query(PlexCollection).filter_by(connection_id=connection.id).count()
    assert total == len(first)
