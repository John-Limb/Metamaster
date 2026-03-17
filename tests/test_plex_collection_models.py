import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.domain.plex.collection_models import (
    BuilderType,
    PlexCollection,
    PlexCollectionItem,
    PlexCollectionSet,
    PlexPlaylist,
    PlexPlaylistItem,
    SetType,
)
from app.domain.plex.models import PlexConnection  # noqa: F401 – registers plex_connections table


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
def test_builder_type_enum_values():
    assert BuilderType.TMDB_COLLECTION == "tmdb_collection"
    assert BuilderType.STATIC_ITEMS == "static_items"
    assert BuilderType.GENRE == "genre"
    assert BuilderType.DECADE == "decade"


@pytest.mark.unit
def test_set_type_enum_values():
    assert SetType.FRANCHISE == "franchise"
    assert SetType.GENRE == "genre"
    assert SetType.DECADE == "decade"


@pytest.mark.unit
def test_plex_collection_has_required_columns():
    cols = {c.name for c in PlexCollection.__table__.columns}
    assert {
        "id",
        "connection_id",
        "name",
        "builder_type",
        "builder_config",
        "plex_rating_key",
        "last_synced_at",
        "enabled",
        "is_default",
    }.issubset(cols)


@pytest.mark.unit
def test_plex_collection_enabled_defaults_false():
    col = PlexCollection.__table__.columns["enabled"]
    assert col.default.arg is False


@pytest.mark.unit
def test_plex_playlist_has_required_columns():
    cols = {c.name for c in PlexPlaylist.__table__.columns}
    assert {
        "id",
        "connection_id",
        "name",
        "builder_config",
        "plex_rating_key",
        "last_synced_at",
        "enabled",
    }.issubset(cols)


@pytest.mark.unit
def test_plex_collection_item_has_position():
    cols = {c.name for c in PlexCollectionItem.__table__.columns}
    assert "position" in cols


@pytest.mark.unit
def test_plex_playlist_item_has_position():
    cols = {c.name for c in PlexPlaylistItem.__table__.columns}
    assert "position" in cols


@pytest.mark.unit
def test_plex_collection_set_has_enabled_false_default():
    col = PlexCollectionSet.__table__.columns["enabled"]
    assert col.default.arg is False


@pytest.mark.unit
def test_plex_collection_has_content_type_column():
    """PlexCollection must have a nullable content_type column."""
    from app.domain.plex.collection_models import PlexCollection

    col = PlexCollection.__table__.c.get("content_type")
    assert col is not None, "content_type column missing from PlexCollection"
    assert col.nullable is True


@pytest.mark.unit
def test_collection_set_defaults(db_session):
    conn = PlexConnection(server_url="http://x", token="t", is_active=True)
    db_session.add(conn)
    db_session.flush()
    cs = PlexCollectionSet(connection_id=conn.id, set_type=SetType.GENRE)
    db_session.add(cs)
    db_session.flush()
    assert cs.enabled is False
    assert cs.last_run_at is None
