"""Tests for TMDBService — unified movie + TV show metadata service."""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from sqlalchemy.orm import Session

import app.core.database  # noqa: F401 — must be imported before domain models to avoid circular import
from app.models import APICache
from app.services_impl import TMDBService
from app.core.config import settings


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return Mock(spec=Session)


# ---------------------------------------------------------------------------
# Sample TMDB API responses
# ---------------------------------------------------------------------------


@pytest.fixture
def tmdb_movie_search_response():
    """Sample TMDB /search/movie response."""
    return {
        "page": 1,
        "results": [
            {
                "id": 278,
                "title": "The Shawshank Redemption",
                "overview": "Two imprisoned men bond over a number of years.",
                "vote_average": 8.7,
                "poster_path": "/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg",
                "release_date": "1994-09-23",
                "genre_ids": [18],
            }
        ],
        "total_results": 1,
        "total_pages": 1,
    }


@pytest.fixture
def tmdb_movie_details_response():
    """Sample TMDB /movie/{id} response."""
    return {
        "id": 278,
        "title": "The Shawshank Redemption",
        "overview": "Two imprisoned men bond over a number of years.",
        "vote_average": 8.7,
        "poster_path": "/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg",
        "release_date": "1994-09-23",
        "runtime": 142,
        "genres": [{"id": 18, "name": "Drama"}],
        "status": "Released",
    }


@pytest.fixture
def tmdb_tv_search_response():
    """Sample TMDB /search/tv response."""
    return {
        "page": 1,
        "results": [
            {
                "id": 1396,
                "name": "Breaking Bad",
                "overview": "A high school chemistry teacher turns to making meth.",
                "vote_average": 8.9,
                "poster_path": "/ztkUQFLlC19CCMYHW9o1zWhJRNq.jpg",
                "first_air_date": "2008-01-20",
                "status": "Ended",
            }
        ],
        "total_results": 1,
        "total_pages": 1,
    }


@pytest.fixture
def tmdb_series_details_response():
    """Sample TMDB /tv/{id} response."""
    return {
        "id": 1396,
        "name": "Breaking Bad",
        "overview": "A high school chemistry teacher turns to making meth.",
        "vote_average": 8.9,
        "poster_path": "/ztkUQFLlC19CCMYHW9o1zWhJRNq.jpg",
        "first_air_date": "2008-01-20",
        "last_air_date": "2013-09-29",
        "status": "Ended",
        "genres": [{"id": 18, "name": "Drama"}, {"id": 80, "name": "Crime"}],
        "number_of_seasons": 5,
    }


@pytest.fixture
def tmdb_season_response():
    """Sample TMDB /tv/{id}/season/{n} response."""
    return {
        "id": 3572,
        "season_number": 1,
        "episodes": [
            {
                "id": 62085,
                "episode_number": 1,
                "name": "Pilot",
                "overview": "Walter White is diagnosed with cancer.",
                "vote_average": 8.5,
                "air_date": "2008-01-20",
                "runtime": 58,
            },
            {
                "id": 62086,
                "episode_number": 2,
                "name": "Cat's in the Bag...",
                "overview": "Walter and Jesse must dispose of evidence.",
                "vote_average": 8.3,
                "air_date": "2008-01-27",
                "runtime": 48,
            },
        ],
    }


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def make_cache_hit(mock_db, data):
    """Wire mock_db to return a cache entry containing *data*."""
    entry = Mock(spec=APICache)
    entry.response_data = json.dumps(data)
    mock_db.query.return_value.filter.return_value.first.return_value = entry


def make_cache_miss(mock_db):
    """Wire mock_db to return no cache entry."""
    mock_db.query.return_value.filter.return_value.first.return_value = None


# ===========================================================================
# search_movie
# ===========================================================================


@pytest.mark.asyncio
async def test_search_movie_cache_hit(mock_db, tmdb_movie_search_response):
    """search_movie returns a cached result without hitting the network."""
    make_cache_hit(mock_db, tmdb_movie_search_response)

    with patch.object(TMDBService, "_get_auth", return_value=({"Authorization": "Bearer test"}, {})):
        result = await TMDBService.search_movie(mock_db, "The Shawshank Redemption", 1994)

    assert result is not None
    assert result["total_results"] == 1
    assert result["results"][0]["title"] == "The Shawshank Redemption"


@pytest.mark.asyncio
async def test_search_movie_no_api_key(mock_db):
    """search_movie returns None when TMDB_API_KEY is not configured."""
    with patch.object(TMDBService, "_get_auth", return_value=None):
        result = await TMDBService.search_movie(mock_db, "Test Movie")
    assert result is None


@pytest.mark.asyncio
async def test_search_movie_network_call(mock_db, tmdb_movie_search_response):
    """search_movie calls the API when cache misses and stores result."""
    make_cache_miss(mock_db)

    with (
        patch.object(TMDBService, "_get_auth", return_value=({"Authorization": "Bearer test"}, {})),
        patch.object(TMDBService, "_rate_limit", new_callable=AsyncMock),
        patch.object(
            TMDBService,
            "_make_request_with_retry",
            new_callable=AsyncMock,
            return_value=tmdb_movie_search_response,
        ),
        patch.object(TMDBService, "_set_cache"),
    ):
        result = await TMDBService.search_movie(mock_db, "The Shawshank Redemption", 1994)

    assert result == tmdb_movie_search_response


# ===========================================================================
# get_movie_details
# ===========================================================================


@pytest.mark.asyncio
async def test_get_movie_details_cache_hit(mock_db, tmdb_movie_details_response):
    """get_movie_details returns a cached result."""
    make_cache_hit(mock_db, tmdb_movie_details_response)

    with patch.object(TMDBService, "_get_auth", return_value=({"Authorization": "Bearer test"}, {})):
        result = await TMDBService.get_movie_details(mock_db, "278")

    assert result is not None
    assert result["id"] == 278
    assert result["title"] == "The Shawshank Redemption"


@pytest.mark.asyncio
async def test_get_movie_details_no_api_key(mock_db):
    """get_movie_details returns None without an API key."""
    with patch.object(TMDBService, "_get_auth", return_value=None):
        result = await TMDBService.get_movie_details(mock_db, "278")
    assert result is None


# ===========================================================================
# search_show
# ===========================================================================


@pytest.mark.asyncio
async def test_search_show_cache_hit(mock_db, tmdb_tv_search_response):
    """search_show returns a cached result."""
    make_cache_hit(mock_db, tmdb_tv_search_response)

    with patch.object(TMDBService, "_get_auth", return_value=({"Authorization": "Bearer test"}, {})):
        result = await TMDBService.search_show(mock_db, "Breaking Bad")

    assert result is not None
    assert result["results"][0]["name"] == "Breaking Bad"


@pytest.mark.asyncio
async def test_search_show_no_api_key(mock_db):
    """search_show returns None without an API key."""
    with patch.object(TMDBService, "_get_auth", return_value=None):
        result = await TMDBService.search_show(mock_db, "Breaking Bad")
    assert result is None


# ===========================================================================
# get_series_details
# ===========================================================================


@pytest.mark.asyncio
async def test_get_series_details_cache_hit(mock_db, tmdb_series_details_response):
    """get_series_details returns a cached result."""
    make_cache_hit(mock_db, tmdb_series_details_response)

    with patch.object(TMDBService, "_get_auth", return_value=({"Authorization": "Bearer test"}, {})):
        result = await TMDBService.get_series_details(mock_db, "1396")

    assert result is not None
    assert result["id"] == 1396
    assert result["name"] == "Breaking Bad"


@pytest.mark.asyncio
async def test_get_series_details_no_api_key(mock_db):
    """get_series_details returns None without an API key."""
    with patch.object(TMDBService, "_get_auth", return_value=None):
        result = await TMDBService.get_series_details(mock_db, "1396")
    assert result is None


# ===========================================================================
# get_season_details
# ===========================================================================


@pytest.mark.asyncio
async def test_get_season_details_cache_hit(mock_db, tmdb_season_response):
    """get_season_details returns a cached result."""
    make_cache_hit(mock_db, tmdb_season_response)

    with patch.object(TMDBService, "_get_auth", return_value=({"Authorization": "Bearer test"}, {})):
        result = await TMDBService.get_season_details(mock_db, "1396", 1)

    assert result is not None
    assert result["season_number"] == 1
    assert len(result["episodes"]) == 2


@pytest.mark.asyncio
async def test_get_season_details_no_api_key(mock_db):
    """get_season_details returns None without an API key."""
    with patch.object(TMDBService, "_get_auth", return_value=None):
        result = await TMDBService.get_season_details(mock_db, "1396", 1)
    assert result is None


# ===========================================================================
# parse_movie_search_response
# ===========================================================================


def test_parse_movie_search_response(tmdb_movie_search_response):
    """parse_movie_search_response extracts search results correctly."""
    result = TMDBService.parse_movie_search_response(tmdb_movie_search_response)

    assert result is not None
    assert "search_results" in result
    assert "total_results" in result
    assert len(result["search_results"]) == 1

    item = result["search_results"][0]
    assert item["tmdb_id"] == "278"
    assert item["title"] == "The Shawshank Redemption"
    assert item["year"] == 1994
    assert item["poster"] == "https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg"


def test_parse_movie_search_response_none():
    """parse_movie_search_response returns None for None input."""
    assert TMDBService.parse_movie_search_response(None) is None


def test_parse_movie_search_response_missing_results():
    """parse_movie_search_response returns None when 'results' key is absent."""
    assert TMDBService.parse_movie_search_response({"page": 1}) is None


def test_parse_movie_search_response_empty_results():
    """parse_movie_search_response handles an empty results list."""
    result = TMDBService.parse_movie_search_response({"results": [], "total_results": 0})
    assert result is not None
    assert result["search_results"] == []
    assert result["total_results"] == 0


# ===========================================================================
# parse_movie_details_response
# ===========================================================================


def test_parse_movie_details_response(tmdb_movie_details_response):
    """parse_movie_details_response extracts all movie fields correctly."""
    result = TMDBService.parse_movie_details_response(tmdb_movie_details_response)

    assert result is not None
    assert result["tmdb_id"] == "278"
    assert result["title"] == "The Shawshank Redemption"
    assert result["year"] == 1994
    assert result["plot"] == "Two imprisoned men bond over a number of years."
    assert result["rating"] == 8.7
    assert result["runtime"] == 142
    assert "Drama" in result["genres"]
    assert result["poster"] == "https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg"


def test_parse_movie_details_response_none():
    """parse_movie_details_response returns None for None input."""
    assert TMDBService.parse_movie_details_response(None) is None


def test_parse_movie_details_response_missing_id():
    """parse_movie_details_response returns None when 'id' is absent."""
    assert TMDBService.parse_movie_details_response({"title": "No ID here"}) is None


def test_parse_movie_details_response_no_poster():
    """parse_movie_details_response handles missing poster gracefully."""
    data = {"id": 278, "title": "Test", "poster_path": None}
    result = TMDBService.parse_movie_details_response(data)
    assert result is not None
    assert result["poster"] is None


# ===========================================================================
# parse_series_search_response
# ===========================================================================


def test_parse_series_search_response(tmdb_tv_search_response):
    """parse_series_search_response extracts search results correctly."""
    result = TMDBService.parse_series_search_response(tmdb_tv_search_response)

    assert result is not None
    assert len(result["search_results"]) == 1

    item = result["search_results"][0]
    assert item["tmdb_id"] == "1396"
    assert item["title"] == "Breaking Bad"


def test_parse_series_search_response_none():
    """parse_series_search_response returns None for None input."""
    assert TMDBService.parse_series_search_response(None) is None


def test_parse_series_search_response_missing_results():
    """parse_series_search_response returns None without 'results'."""
    assert TMDBService.parse_series_search_response({"page": 1}) is None


# ===========================================================================
# parse_series_response
# ===========================================================================


def test_parse_series_response(tmdb_series_details_response):
    """parse_series_response extracts all TV show fields correctly."""
    result = TMDBService.parse_series_response(tmdb_series_details_response)

    assert result is not None
    assert result["tmdb_id"] == "1396"
    assert result["title"] == "Breaking Bad"
    assert result["rating"] == 8.9
    assert result["status"] == "ended"  # normalised from "Ended"
    assert result["number_of_seasons"] == 5
    assert "Drama" in result["genres"]
    assert "Crime" in result["genres"]


def test_parse_series_response_none():
    """parse_series_response returns None for None input."""
    assert TMDBService.parse_series_response(None) is None


def test_parse_series_response_missing_id():
    """parse_series_response returns None when 'id' is absent."""
    assert TMDBService.parse_series_response({"name": "No ID"}) is None


# ===========================================================================
# parse_season_response
# ===========================================================================


def test_parse_season_response(tmdb_season_response):
    """parse_season_response extracts season and episode list correctly."""
    result = TMDBService.parse_season_response(tmdb_season_response)

    assert result is not None
    assert result["season_number"] == 1
    assert len(result["episodes"]) == 2

    pilot = result["episodes"][0]
    assert pilot["tmdb_id"] == "62085"
    assert pilot["episode_number"] == 1
    assert pilot["title"] == "Pilot"
    assert pilot["rating"] == 8.5
    assert pilot["runtime"] == 58


def test_parse_season_response_none():
    """parse_season_response returns None for None input."""
    assert TMDBService.parse_season_response(None) is None


def test_parse_season_response_missing_season_number():
    """parse_season_response returns None when 'season_number' is absent."""
    assert TMDBService.parse_season_response({"id": 123}) is None


def test_parse_season_response_empty_episodes():
    """parse_season_response handles a season with no episodes."""
    data = {"id": 123, "season_number": 1, "episodes": []}
    result = TMDBService.parse_season_response(data)
    assert result is not None
    assert result["episodes"] == []


# ===========================================================================
# _normalize_tv_status
# ===========================================================================


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Returning Series", "continuing"),
        ("In Production", "continuing"),
        ("Pilot", "continuing"),
        ("Ended", "ended"),
        ("Canceled", "ended"),
        ("Cancelled", "ended"),
        ("Planned", "planned"),
        ("", ""),
    ],
)
def test_normalize_tv_status(raw, expected):
    assert TMDBService._normalize_tv_status(raw) == expected


# ===========================================================================
# _poster_url
# ===========================================================================


def test_poster_url_with_path():
    assert TMDBService._poster_url("/abc.jpg") == "https://image.tmdb.org/t/p/w500/abc.jpg"


def test_poster_url_with_none():
    assert TMDBService._poster_url(None) is None


def test_poster_url_with_empty():
    assert TMDBService._poster_url("") is None


# ===========================================================================
# _get_cache_key
# ===========================================================================


def test_get_cache_key_deterministic():
    key1 = TMDBService._get_cache_key("movie_search", {"title": "Inception", "year": 2010})
    key2 = TMDBService._get_cache_key("movie_search", {"title": "Inception", "year": 2010})
    key3 = TMDBService._get_cache_key("movie_search", {"title": "Interstellar", "year": 2014})

    assert key1 == key2
    assert key1 != key3


# ===========================================================================
# _get_auth
# ===========================================================================


def test_get_auth_prefers_read_access_token():
    """_get_auth returns Bearer header when TMDB_READ_ACCESS_TOKEN is set."""
    with patch.object(settings, "tmdb_read_access_token", "my.jwt.token"), \
         patch.object(settings, "tmdb_api_key", "myapikey"):
        result = TMDBService._get_auth()
    assert result is not None
    headers, params = result
    assert headers["Authorization"] == "Bearer my.jwt.token"
    assert params == {}


def test_get_auth_falls_back_to_api_key():
    """_get_auth returns ?api_key= params when only TMDB_API_KEY is set."""
    with patch.object(settings, "tmdb_read_access_token", None), \
         patch.object(settings, "tmdb_api_key", "myapikey"):
        result = TMDBService._get_auth()
    assert result is not None
    headers, params = result
    assert "Authorization" not in headers
    assert params == {"api_key": "myapikey"}


def test_get_auth_returns_none_when_neither_set():
    """_get_auth returns None when no credentials are configured."""
    with patch.object(settings, "tmdb_read_access_token", None), \
         patch.object(settings, "tmdb_api_key", None):
        result = TMDBService._get_auth()
    assert result is None


# ===========================================================================
# _get_cache / _set_cache
# ===========================================================================


def test_get_cache_hit(mock_db):
    """_get_cache returns parsed data for a valid cache entry."""
    payload = {"results": [{"id": 278}]}
    entry = Mock(spec=APICache)
    entry.response_data = json.dumps(payload)
    mock_db.query.return_value.filter.return_value.first.return_value = entry

    result = TMDBService._get_cache(mock_db, "test_key")
    assert result == payload


def test_get_cache_miss(mock_db):
    """_get_cache returns None when no entry exists."""
    make_cache_miss(mock_db)
    assert TMDBService._get_cache(mock_db, "test_key") is None


def test_set_cache_new_entry(mock_db):
    """_set_cache creates a new APICache entry when one doesn't exist."""
    make_cache_miss(mock_db)

    TMDBService._set_cache(mock_db, "test_key", {"id": 278}, 3600)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_set_cache_updates_existing_entry(mock_db):
    """_set_cache updates response_data on an existing cache entry."""
    existing = Mock(spec=APICache)
    mock_db.query.return_value.filter.return_value.first.return_value = existing

    new_data = {"id": 278, "title": "Updated"}
    TMDBService._set_cache(mock_db, "test_key", new_data, 3600)

    assert existing.response_data == json.dumps(new_data)
    mock_db.commit.assert_called_once()


# ===========================================================================
# _make_request_with_retry
# ===========================================================================


@pytest.mark.asyncio
async def test_make_request_success(tmdb_movie_details_response):
    """_make_request_with_retry returns parsed JSON on a 200 response."""
    mock_response = MagicMock()
    mock_response.json.return_value = tmdb_movie_details_response
    mock_response.raise_for_status = Mock()
    mock_response.status_code = 200
    mock_response.content = b"{}"

    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__.return_value = instance
        instance.__aexit__.return_value = None
        instance.get.return_value = mock_response
        MockClient.return_value = instance

        result = await TMDBService._make_request_with_retry(
            "https://api.themoviedb.org/3/movie/278",
            {"Authorization": "Bearer test"},
        )

    assert result == tmdb_movie_details_response


@pytest.mark.asyncio
async def test_make_request_connection_error():
    """_make_request_with_retry returns None after exhausting retries."""
    import httpx

    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__.return_value = instance
        instance.__aexit__.return_value = None
        instance.get.side_effect = httpx.RequestError("Connection refused")
        MockClient.return_value = instance

        result = await TMDBService._make_request_with_retry(
            "https://api.themoviedb.org/3/movie/278",
            {"Authorization": "Bearer test"},
            max_retries=1,
            base_delay=0,
        )

    assert result is None


@pytest.mark.asyncio
async def test_make_request_401_returns_none():
    """_make_request_with_retry returns None immediately on 401 (bad API key)."""
    import httpx

    mock_response = MagicMock()
    mock_response.status_code = 401

    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__.return_value = instance
        instance.__aexit__.return_value = None
        instance.get.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )
        MockClient.return_value = instance

        result = await TMDBService._make_request_with_retry(
            "https://api.themoviedb.org/3/movie/278",
            {"Authorization": "Bearer bad_key"},
        )

    assert result is None


@pytest.mark.asyncio
async def test_make_request_404_returns_none():
    """_make_request_with_retry returns None on 404."""
    import httpx

    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__.return_value = instance
        instance.__aexit__.return_value = None
        instance.get.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )
        MockClient.return_value = instance

        result = await TMDBService._make_request_with_retry(
            "https://api.themoviedb.org/3/movie/99999999",
            {"Authorization": "Bearer test"},
        )

    assert result is None


# ===========================================================================
# Rate limiting
# ===========================================================================


@pytest.mark.asyncio
async def test_rate_limit_enforced():
    """_rate_limit inserts a delay between rapid calls."""
    TMDBService._last_request_time = 0
    loop = asyncio.get_event_loop()

    await TMDBService._rate_limit()
    t1 = loop.time()
    await TMDBService._rate_limit()
    t2 = loop.time()

    # With default rate_limit=4, min interval is 0.25s
    assert t2 - t1 >= 0.2  # allow small timing variance
