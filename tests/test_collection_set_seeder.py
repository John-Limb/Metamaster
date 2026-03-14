import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.domain.plex.collection_models import PlexCollectionSet, SetType
from app.domain.plex.collection_set_seeder import seed_collection_sets
from app.domain.plex.models import PlexConnection  # noqa: F401 – registers plex_connections table


@pytest.fixture
def db_session():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    Session = sessionmaker(bind=eng)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(eng)


@pytest.mark.unit
def test_seed_creates_three_sets(db_session):
    conn = PlexConnection(server_url="http://plex", token="tok", is_active=True)
    db_session.add(conn)
    db_session.commit()

    seed_collection_sets(db_session)

    sets = db_session.query(PlexCollectionSet).filter_by(connection_id=conn.id).all()
    assert len(sets) == 3
    seeded_types = {s.set_type for s in sets}
    assert seeded_types == {SetType.FRANCHISE, SetType.GENRE, SetType.DECADE}
    assert all(s.enabled is False for s in sets)


@pytest.mark.unit
def test_seed_is_idempotent(db_session):
    conn = PlexConnection(server_url="http://plex2", token="tok2", is_active=True)
    db_session.add(conn)
    db_session.commit()

    seed_collection_sets(db_session)
    seed_collection_sets(db_session)

    sets = db_session.query(PlexCollectionSet).filter_by(connection_id=conn.id).all()
    assert len(sets) == 3


@pytest.mark.unit
def test_seed_no_connection_is_noop(db_session):
    before = db_session.query(PlexCollectionSet).count()

    seed_collection_sets(db_session)

    after = db_session.query(PlexCollectionSet).count()
    assert after == before
