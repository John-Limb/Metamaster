from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.domain.plex.collection_builder import ResolvedItem
from app.domain.plex.playlist_service import PlexPlaylistService


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
def mock_pc():
    return MagicMock()


@pytest.fixture
def mock_resolver():
    return MagicMock()


@pytest.fixture
def svc(db_session, mock_pc, mock_resolver):
    return PlexPlaylistService(
        db=db_session,
        playlist_client=mock_pc,
        resolver=mock_resolver,
    )


@pytest.mark.unit
def test_push_creates_playlist_when_missing(svc, mock_pc, mock_resolver, db_session):
    from app.domain.plex.collection_models import PlexPlaylist
    from app.domain.plex.models import PlexConnection

    conn = PlexConnection(server_url="http://plex", token="t", is_active=True)
    db_session.add(conn)
    db_session.flush()

    pl = PlexPlaylist(
        connection_id=conn.id,
        name="Weekend",
        builder_config={"items": [{"tmdb_id": "1", "item_type": "movie"}]},
        enabled=True,
    )
    db_session.add(pl)
    db_session.flush()

    mock_resolver.resolve_static_items.return_value = [
        ResolvedItem(plex_rating_key="5", item_type="movie", item_id=1)
    ]
    mock_pc.create_playlist.return_value = "99"

    svc.push_playlist(pl)

    mock_pc.create_playlist.assert_called_once()
    assert pl.plex_rating_key == "99"


@pytest.mark.unit
def test_pull_imports_playlist(svc, mock_pc, db_session):
    from app.domain.plex.collection_models import PlexPlaylist
    from app.domain.plex.models import PlexConnection

    conn = PlexConnection(server_url="http://plex", token="t", is_active=True)
    db_session.add(conn)
    db_session.flush()

    mock_pc.get_playlists.return_value = [
        {"ratingKey": "20", "title": "Weekend", "summary": "Great films"}
    ]

    svc.pull_playlists(connection_id=conn.id)

    pl = db_session.query(PlexPlaylist).filter(PlexPlaylist.plex_rating_key == "20").first()
    assert pl is not None
    assert pl.name == "Weekend"
    assert pl.enabled is False
