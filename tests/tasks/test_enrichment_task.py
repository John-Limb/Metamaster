"""Tests for external enrichment Celery tasks."""
from unittest.mock import MagicMock, patch
import httpx


def make_movie(id=1, title="Inception", year=2010, enrichment_status="local_only",
               detected_external_id=None, manual_external_id=None):
    m = MagicMock()
    m.id = id
    m.title = title
    m.year = year
    m.enrichment_status = enrichment_status
    m.detected_external_id = detected_external_id
    m.manual_external_id = manual_external_id
    m.tmdb_id = None
    m.plot = None
    m.rating = None
    m.runtime = None
    m.genres = None
    m.poster_url = None
    m.enrichment_error = None
    return m


@patch("app.tasks.enrichment.SessionLocal")
@patch("app.tasks.enrichment.TMDBService")
@patch("app.tasks.enrichment.run_async")
def test_enrich_movie_uses_manual_id_first(mock_run_async, MockTMDB, MockSession):
    """manual_external_id takes priority — goes straight to get_movie_details, no search."""
    movie = make_movie(manual_external_id="tt9999999")
    db = MagicMock()
    MockSession.return_value = db
    db.query.return_value.filter.return_value.first.return_value = movie
    db.query.return_value.filter.return_value.all.return_value = []

    # Return a raw response for get_movie_details
    mock_run_async.return_value = {"id": 27205, "title": "Inception"}
    MockTMDB.parse_movie_details_response.return_value = {
        "tmdb_id": "27205",
        "plot": "A dream heist",
        "rating": 8.8,
    }

    from app.tasks.enrichment import enrich_movie_external
    enrich_movie_external(1)

    # Should NOT call search_movie
    MockTMDB.search_movie.assert_not_called()
    assert movie.enrichment_status == "fully_enriched"


@patch("app.tasks.enrichment.SessionLocal")
@patch("app.tasks.enrichment.TMDBService")
@patch("app.tasks.enrichment.run_async")
def test_enrich_movie_sets_external_failed_on_network_error(mock_run_async, MockTMDB, MockSession):
    """Network error sets status to external_failed."""
    movie = make_movie()
    db = MagicMock()
    MockSession.return_value = db
    db.query.return_value.filter.return_value.first.return_value = movie
    db.query.return_value.filter.return_value.all.return_value = []

    mock_run_async.side_effect = httpx.ConnectError("unreachable")

    from app.tasks.enrichment import enrich_movie_external
    enrich_movie_external(1)

    assert movie.enrichment_status == "external_failed"
    assert movie.enrichment_error is not None


@patch("app.tasks.enrichment.SessionLocal")
@patch("app.tasks.enrichment.TMDBService")
@patch("app.tasks.enrichment.run_async")
def test_enrich_movie_sets_not_found_when_no_results(mock_run_async, MockTMDB, MockSession):
    """Empty API response sets status to not_found."""
    movie = make_movie()
    db = MagicMock()
    MockSession.return_value = db
    db.query.return_value.filter.return_value.first.return_value = movie
    db.query.return_value.filter.return_value.all.return_value = []

    mock_run_async.return_value = None  # API returned nothing

    from app.tasks.enrichment import enrich_movie_external
    enrich_movie_external(1)

    assert movie.enrichment_status == "not_found"
