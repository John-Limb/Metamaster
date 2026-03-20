from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.domain.plex.collection_builder import ResolvedItem
from app.domain.plex.collection_service import PlexCollectionService


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


@pytest.fixture
def mock_cc():
    return MagicMock()


@pytest.fixture
def mock_collection_client():
    return MagicMock()


@pytest.fixture
def mock_resolver():
    return MagicMock()


@pytest.fixture
def svc(db_session, mock_cc, mock_resolver):
    return PlexCollectionService(
        db=db_session,
        collection_client=mock_cc,
        resolver=mock_resolver,
        movie_section_id="1",
        tv_section_id="2",
    )


@pytest.mark.unit
def test_push_creates_collection_when_missing(svc, mock_cc, mock_resolver, db_session):
    from app.domain.plex.collection_models import BuilderType, PlexCollection
    from app.domain.plex.models import PlexConnection

    conn = PlexConnection(server_url="http://plex", token="t", is_active=True)
    db_session.add(conn)
    db_session.flush()

    coll = PlexCollection(
        connection_id=conn.id,
        name="MCU",
        builder_type=BuilderType.STATIC_ITEMS,
        builder_config={"items": [{"tmdb_id": "1", "item_type": "movie"}]},
        enabled=True,
        is_default=False,
    )
    db_session.add(coll)
    db_session.flush()

    mock_resolver.resolve_static_items.return_value = [
        ResolvedItem(plex_rating_key="5", item_type="movie", item_id=1)
    ]
    mock_cc.create_collection.return_value = "99"

    svc.push_collection(coll)

    mock_cc.create_collection.assert_called_once()
    assert coll.plex_rating_key == "99"


@pytest.mark.unit
def test_push_reconciles_items(svc, mock_cc, mock_resolver, db_session):
    from app.domain.plex.collection_models import BuilderType, PlexCollection
    from app.domain.plex.models import PlexConnection

    conn = PlexConnection(server_url="http://plex", token="t", is_active=True)
    db_session.add(conn)
    db_session.flush()

    coll = PlexCollection(
        connection_id=conn.id,
        name="MCU",
        builder_type=BuilderType.STATIC_ITEMS,
        builder_config={"items": []},
        plex_rating_key="99",
        enabled=True,
        is_default=False,
    )
    db_session.add(coll)
    db_session.flush()

    mock_resolver.resolve_static_items.return_value = [
        ResolvedItem(plex_rating_key="5", item_type="movie", item_id=1),
    ]
    mock_cc.get_collection_item_keys.return_value = ["6"]

    svc.push_collection(coll)

    mock_cc.add_item_to_collection.assert_called_once_with(collection_key="99", rating_key="5")
    mock_cc.remove_item_from_collection.assert_called_once_with(collection_key="99", item_key="6")


@pytest.mark.unit
def test_upsert_pulled_collection_tags_movie(db_session, mock_collection_client):
    """_upsert_pulled_collection sets content_type='movie' for movie section."""
    from unittest.mock import MagicMock

    from app.domain.plex.collection_builder import BuilderResolver
    from app.domain.plex.collection_models import PlexCollection
    from app.domain.plex.collection_service import PlexCollectionService

    resolver = MagicMock(spec=BuilderResolver)
    mock_collection_client.get_collection_item_keys.return_value = []
    svc = PlexCollectionService(
        db=db_session,
        collection_client=mock_collection_client,
        resolver=resolver,
        movie_section_id="1",
        tv_section_id="2",
    )
    raw = {"ratingKey": "key-movie", "title": "Action Hits", "summary": ""}
    svc._upsert_pulled_collection(raw, connection_id=1, section_id="1")
    db_session.flush()
    coll = db_session.query(PlexCollection).filter_by(plex_rating_key="key-movie").first()
    assert coll is not None
    assert coll.content_type == "movie"


@pytest.mark.unit
def test_upsert_pulled_collection_tags_tv(db_session, mock_collection_client):
    """_upsert_pulled_collection sets content_type='tv_show' for tv section."""
    from unittest.mock import MagicMock

    from app.domain.plex.collection_builder import BuilderResolver
    from app.domain.plex.collection_models import PlexCollection
    from app.domain.plex.collection_service import PlexCollectionService

    resolver = MagicMock(spec=BuilderResolver)
    mock_collection_client.get_collection_item_keys.return_value = []
    svc = PlexCollectionService(
        db=db_session,
        collection_client=mock_collection_client,
        resolver=resolver,
        movie_section_id="1",
        tv_section_id="2",
    )
    raw = {"ratingKey": "key-tv", "title": "Crime Dramas", "summary": ""}
    svc._upsert_pulled_collection(raw, connection_id=1, section_id="2")
    db_session.flush()
    coll = db_session.query(PlexCollection).filter_by(plex_rating_key="key-tv").first()
    assert coll is not None
    assert coll.content_type == "tv_show"
