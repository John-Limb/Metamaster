"""Tests for TVDB Service integration"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services import TVDBService
from app.models import APICache
from app.config import settings


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    db = Mock(spec=Session)
    return db


@pytest.fixture
def sample_search_response():
    """Sample TVDB search response"""
    return {
        "status": "success",
        "data": [
            {
                "id": 121361,
                "name": "Breaking Bad",
                "overview": "A high school chemistry teacher...",
                "status": "Ended",
                "first_air_date": "2008-01-20",
                "image_url": "https://artworks.thetvdb.com/banners/v4/series/81189/posters/5e96d1f89c0a0.jpg",
                "type": "series",
            }
        ],
    }


@pytest.fixture
def sample_series_response():
    """Sample TVDB series details response"""
    return {
        "status": "success",
        "data": {
            "id": 81189,
            "name": "Breaking Bad",
            "overview": "A high school chemistry teacher...",
            "score": 8.9,
            "status": "Ended",
            "first_air_date": "2008-01-20",
            "last_air_date": "2013-09-29",
            "image_url": "https://artworks.thetvdb.com/banners/v4/series/81189/posters/5e96d1f89c0a0.jpg",
            "network": "AMC",
            "country": "United States",
            "genres": ["Drama", "Crime"],
        },
    }


@pytest.fixture
def sample_seasons_response():
    """Sample TVDB seasons response"""
    return {
        "status": "success",
        "data": [
            {"id": 3962, "number": 1, "episodes": 7},
            {"id": 3963, "number": 2, "episodes": 13},
        ],
    }


@pytest.fixture
def sample_episodes_response():
    """Sample TVDB episodes response"""
    return {
        "status": "success",
        "data": [
            {
                "id": 349232,
                "number": 1,
                "name": "Pilot",
                "overview": "A high school chemistry teacher...",
                "aired": "2008-01-20",
                "score": 8.5,
                "runtime": 58,
            },
            {
                "id": 349233,
                "number": 2,
                "name": "Cat's in the Bag...",
                "overview": "Walter and Jesse...",
                "aired": "2008-01-27",
                "score": 8.3,
                "runtime": 58,
            },
        ],
    }


@pytest.fixture
def sample_auth_response():
    """Sample TVDB authentication response"""
    return {"status": "success", "data": {"token": "test_token_12345"}}


@pytest.mark.asyncio
async def test_search_show_with_cache_hit(mock_db, sample_search_response):
    """Test search_show returns cached result"""
    # Setup cache mock
    cache_entry = Mock(spec=APICache)
    cache_entry.response_data = json.dumps(sample_search_response)
    mock_db.query.return_value.filter.return_value.first.return_value = cache_entry

    # Reset auth token to force cache check
    TVDBService._auth_token = "test_token"
    TVDBService._token_expiry = datetime.utcnow() + timedelta(hours=1)

    result = await TVDBService.search_show(mock_db, "Breaking Bad")

    assert result is not None
    assert result["status"] == "success"
    assert len(result["data"]) == 1
    assert result["data"][0]["name"] == "Breaking Bad"


@pytest.mark.asyncio
async def test_search_show_no_auth_token(mock_db):
    """Test search_show fails gracefully without auth token"""
    # Reset auth token to force auth attempt
    TVDBService._auth_token = None
    TVDBService._token_expiry = None

    # Mock db to return None for cache query
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch.object(settings, "tvdb_api_key", None):
        result = await TVDBService.search_show(mock_db, "Breaking Bad")
        assert result is None


@pytest.mark.asyncio
async def test_get_series_details_with_cache_hit(mock_db, sample_series_response):
    """Test get_series_details returns cached result"""
    # Setup cache mock
    cache_entry = Mock(spec=APICache)
    cache_entry.response_data = json.dumps(sample_series_response)
    mock_db.query.return_value.filter.return_value.first.return_value = cache_entry

    # Reset auth token to force cache check
    TVDBService._auth_token = "test_token"
    TVDBService._token_expiry = datetime.utcnow() + timedelta(hours=1)

    result = await TVDBService.get_series_details(mock_db, "81189")

    assert result is not None
    assert result["status"] == "success"
    assert result["data"]["id"] == 81189
    assert result["data"]["name"] == "Breaking Bad"


@pytest.mark.asyncio
async def test_get_series_details_no_auth_token(mock_db):
    """Test get_series_details fails gracefully without auth token"""
    # Reset auth token to force auth attempt
    TVDBService._auth_token = None
    TVDBService._token_expiry = None

    # Mock db to return None for cache query
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch.object(settings, "tvdb_api_key", None):
        result = await TVDBService.get_series_details(mock_db, "81189")
        assert result is None


@pytest.mark.asyncio
async def test_get_seasons_with_cache_hit(mock_db, sample_seasons_response):
    """Test get_seasons returns cached result"""
    # Setup cache mock
    cache_entry = Mock(spec=APICache)
    cache_entry.response_data = json.dumps(sample_seasons_response)
    mock_db.query.return_value.filter.return_value.first.return_value = cache_entry

    # Reset auth token to force cache check
    TVDBService._auth_token = "test_token"
    TVDBService._token_expiry = datetime.utcnow() + timedelta(hours=1)

    result = await TVDBService.get_seasons(mock_db, "81189")

    assert result is not None
    assert result["status"] == "success"
    assert len(result["data"]) == 2
    assert result["data"][0]["number"] == 1


@pytest.mark.asyncio
async def test_get_episodes_with_cache_hit(mock_db, sample_episodes_response):
    """Test get_episodes returns cached result"""
    # Setup cache mock
    cache_entry = Mock(spec=APICache)
    cache_entry.response_data = json.dumps(sample_episodes_response)
    mock_db.query.return_value.filter.return_value.first.return_value = cache_entry

    # Reset auth token to force cache check
    TVDBService._auth_token = "test_token"
    TVDBService._token_expiry = datetime.utcnow() + timedelta(hours=1)

    result = await TVDBService.get_episodes(mock_db, "81189", 1)

    assert result is not None
    assert result["status"] == "success"
    assert len(result["data"]) == 2
    assert result["data"][0]["name"] == "Pilot"


def test_parse_tvdb_search_response(sample_search_response):
    """Test parsing TVDB search response"""
    result = TVDBService.parse_tvdb_search_response(sample_search_response)

    assert result is not None
    assert "search_results" in result
    assert "total_results" in result
    assert len(result["search_results"]) == 1
    assert result["search_results"][0]["title"] == "Breaking Bad"
    assert result["search_results"][0]["tvdb_id"] == "121361"


def test_parse_tvdb_series_response(sample_series_response):
    """Test parsing TVDB series details response"""
    result = TVDBService.parse_tvdb_series_response(sample_series_response)

    assert result is not None
    assert result["title"] == "Breaking Bad"
    assert result["tvdb_id"] == "81189"
    assert result["rating"] == 8.9
    assert result["status"] == "Ended"
    assert result["network"] == "AMC"


def test_parse_tvdb_seasons_response(sample_seasons_response):
    """Test parsing TVDB seasons response"""
    result = TVDBService.parse_tvdb_seasons_response(sample_seasons_response)

    assert result is not None
    assert "seasons" in result
    assert "total_seasons" in result
    assert len(result["seasons"]) == 2
    assert result["seasons"][0]["season_number"] == 1
    assert result["seasons"][0]["episode_count"] == 7


def test_parse_tvdb_episodes_response(sample_episodes_response):
    """Test parsing TVDB episodes response"""
    result = TVDBService.parse_tvdb_episodes_response(sample_episodes_response)

    assert result is not None
    assert "episodes" in result
    assert "total_episodes" in result
    assert len(result["episodes"]) == 2
    assert result["episodes"][0]["title"] == "Pilot"
    assert result["episodes"][0]["episode_number"] == 1
    assert result["episodes"][0]["rating"] == 8.5


def test_parse_tvdb_response_with_invalid_data():
    """Test parsing invalid TVDB response"""
    invalid_response = {"status": "failed", "message": "Not found"}
    result = TVDBService.parse_tvdb_search_response(invalid_response)
    assert result is None


def test_parse_tvdb_response_with_none():
    """Test parsing None response"""
    result = TVDBService.parse_tvdb_search_response(None)
    assert result is None


def test_get_cache_key():
    """Test cache key generation"""
    key1 = TVDBService._get_cache_key("search", {"title": "Breaking Bad"})
    key2 = TVDBService._get_cache_key("search", {"title": "Breaking Bad"})
    key3 = TVDBService._get_cache_key("search", {"title": "Game of Thrones"})

    assert key1 == key2
    assert key1 != key3


def test_get_cache_expired(mock_db):
    """Test cache retrieval with expired entry"""
    # Setup expired cache entry
    cache_entry = Mock(spec=APICache)
    cache_entry.expires_at = datetime.utcnow() - timedelta(hours=1)
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = TVDBService._get_cache(mock_db, "test_key")
    assert result is None


def test_set_cache_new_entry(mock_db):
    """Test setting new cache entry"""
    mock_db.query.return_value.filter.return_value.first.return_value = None

    test_data = {"status": "success", "data": []}
    TVDBService._set_cache(mock_db, "test_key", test_data, 3600)

    # Verify add was called
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_set_cache_update_existing(mock_db):
    """Test updating existing cache entry"""
    existing_entry = Mock(spec=APICache)
    mock_db.query.return_value.filter.return_value.first.return_value = existing_entry

    test_data = {"status": "success", "data": []}
    TVDBService._set_cache(mock_db, "test_key", test_data, 3600)

    # Verify update occurred
    assert existing_entry.response_data == json.dumps(test_data)
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_rate_limit_enforcement():
    """Test rate limiting enforcement (3 requests per second)"""
    # Reset rate limiter
    TVDBService._last_request_time = 0

    start_time = asyncio.get_event_loop().time()
    await TVDBService._rate_limit()
    first_call_time = asyncio.get_event_loop().time() - start_time

    start_time = asyncio.get_event_loop().time()
    await TVDBService._rate_limit()
    second_call_time = asyncio.get_event_loop().time() - start_time

    # Second call should have waited approximately 0.333 seconds (1/3 second for 3 req/sec)
    assert second_call_time >= 0.3  # Allow small timing variance


@pytest.mark.asyncio
async def test_make_request_with_retry_success(sample_series_response):
    """Test successful request with retry logic"""
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value=sample_series_response)
    mock_response.raise_for_status = AsyncMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await TVDBService._make_request_with_retry(
            "http://test.com", {"Authorization": "Bearer test_token"}
        )

        assert result is not None
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_make_request_with_retry_api_error():
    """Test request with API error response"""
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(
        return_value={"status": "failed", "message": "Not found"}
    )
    mock_response.raise_for_status = AsyncMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await TVDBService._make_request_with_retry(
            "http://test.com", {"Authorization": "Bearer test_token"}
        )

        assert result is None


@pytest.mark.asyncio
async def test_make_request_with_retry_http_error():
    """Test request with HTTP error and retry"""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(side_effect=Exception("Connection error"))
        mock_client_class.return_value = mock_client

        result = await TVDBService._make_request_with_retry(
            "http://test.com", {"Authorization": "Bearer test_token"}, max_retries=1
        )

        # Should return None after retries exhausted
        assert result is None


@pytest.mark.asyncio
async def test_get_auth_token_success(sample_auth_response):
    """Test successful authentication token retrieval"""
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value=sample_auth_response)
    mock_response.raise_for_status = AsyncMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        # Reset token state
        TVDBService._auth_token = None
        TVDBService._token_expiry = None

        with patch.object(settings, "tvdb_api_key", "test_key"):
            with patch.object(settings, "tvdb_pin", "test_pin"):
                token = await TVDBService._get_auth_token()

                assert token == "test_token_12345"
                assert TVDBService._auth_token == "test_token_12345"
                assert TVDBService._token_expiry is not None


@pytest.mark.asyncio
async def test_get_auth_token_cached():
    """Test that cached auth token is reused"""
    # Set up cached token
    TVDBService._auth_token = "cached_token"
    TVDBService._token_expiry = datetime.utcnow() + timedelta(hours=1)

    token = await TVDBService._get_auth_token()

    assert token == "cached_token"


@pytest.mark.asyncio
async def test_get_auth_token_no_credentials():
    """Test authentication fails without credentials"""
    # Reset token state
    TVDBService._auth_token = None
    TVDBService._token_expiry = None

    with patch.object(settings, "tvdb_api_key", None):
        with patch.object(settings, "tvdb_pin", None):
            token = await TVDBService._get_auth_token()
            assert token is None
