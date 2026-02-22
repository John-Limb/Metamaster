"""Unit tests for enrichment_status on Movie and TVShow models."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Movie, TVShow
from app.database import Base


@pytest.fixture(scope="module")
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_movie_default_enrichment_status(db_session):
    movie = Movie(title="Test", year=2020)
    db_session.add(movie)
    db_session.flush()
    assert movie.enrichment_status == "pending_local"


def test_movie_enrichment_status_assignment(db_session):
    movie = Movie(title="Test", year=2020)
    db_session.add(movie)
    db_session.flush()
    movie.enrichment_status = "local_only"
    db_session.flush()
    assert movie.enrichment_status == "local_only"


def test_movie_detected_external_id_defaults_none(db_session):
    movie = Movie(title="Test", year=2020)
    db_session.add(movie)
    db_session.flush()
    assert movie.detected_external_id is None


def test_movie_manual_external_id_defaults_none(db_session):
    movie = Movie(title="Test", year=2020)
    db_session.add(movie)
    db_session.flush()
    assert movie.manual_external_id is None


def test_tvshow_default_enrichment_status(db_session):
    show = TVShow(title="Test Show")
    db_session.add(show)
    db_session.flush()
    assert show.enrichment_status == "pending_local"


def test_tvshow_detected_external_id_defaults_none(db_session):
    show = TVShow(title="Test Show")
    db_session.add(show)
    db_session.flush()
    assert show.detected_external_id is None
