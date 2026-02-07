"""Tests for OMDB Service integration"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services import OMDBService
from app.models import APICache
from app.config import settings


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    db = Mock(spec=Session)
    return db


@pytest.fixture
def sample_search_response():
    """Sample OMDB search response"""
    return {
        "Search": [
            {
                "Title": "The Shawshank Redemption",
                "Year": "1994",
                "imdbID": "tt0111161",
                "Type": "movie",
                "Poster": "https://m.media-amazon.com/images/M/MV5BMDFkYTc0MGEtZmNhMC00ZDIzLWFmNTEtODM1ZDJkMzQ0MzA1XkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg",
            }
        ],
        "totalResults": "1",
        "Response": "True",
    }


@pytest.fixture
def sample_details_response():
    """Sample OMDB details response"""
    return {
        "Title": "The Shawshank Redemption",
        "Year": "1994",
        "Rated": "R",
        "Released": "14 Oct 1994",
        "Runtime": "142 min",
        "Genre": "Drama",
        "Director": "Frank Darabont",
        "Actors": "Tim Robbins, Morgan Freeman, Bob Gunton",
        "Plot": "Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.",
        "Language": "English",
        "Country": "United States",
        "Awards": "Nominated for 7 Oscars. Another 45 wins & 86 nominations.",
        "Poster": "https://m.media-amazon.com/images/M/MV5BMDFkYTc0MGEtZmNhMC00ZDIzLWFmNTEtODM1ZDJkMzQ0MzA1XkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg",
        "Ratings": [{"Source": "Internet Movie Database", "Value": "9.3/10"}],
        "Metascore": "82",
        "imdbRating": "9.3",
        "imdbVotes": "2,500,000",
        "imdbID": "tt0111161",
        "Type": "movie",
        "DVD": "06 Dec 1999",
        "BoxOffice": "$28,341,469",
        "Production": "Columbia Pictures",
        "Website": "N/A",
        "Response": "True",
    }


@pytest.mark.asyncio
async def test_search_movie_with_cache_hit(mock_db, sample_search_response):
    """Test search_movie returns cached result"""
    # Setup cache mock
    cache_entry = Mock(spec=APICache)
    cache_entry.response_data = json.dumps(sample_search_response)
    mock_db.query.return_value.filter.return_value.first.return_value = cache_entry

    result = await OMDBService.search_movie(mock_db, "The Shawshank Redemption", 1994)

    assert result is not None
    assert result["Response"] == "True"
    assert len(result["Search"]) == 1
    assert result["Search"][0]["Title"] == "The Shawshank Redemption"


@pytest.mark.asyncio
async def test_search_movie_no_api_key(mock_db):
    """Test search_movie fails gracefully without API key"""
    with patch.object(settings, "omdb_api_key", None):
        result = await OMDBService.search_movie(mock_db, "Test Movie")
        assert result is None


@pytest.mark.asyncio
async def test_get_movie_details_with_cache_hit(mock_db, sample_details_response):
    """Test get_movie_details returns cached result"""
    # Setup cache mock
    cache_entry = Mock(spec=APICache)
    cache_entry.response_data = json.dumps(sample_details_response)
    mock_db.query.return_value.filter.return_value.first.return_value = cache_entry

    result = await OMDBService.get_movie_details(mock_db, "tt0111161")

    assert result is not None
    assert result["Response"] == "True"
    assert result["imdbID"] == "tt0111161"
    assert result["Title"] == "The Shawshank Redemption"


@pytest.mark.asyncio
async def test_get_movie_details_no_api_key(mock_db):
    """Test get_movie_details fails gracefully without API key"""
    with patch.object(settings, "omdb_api_key", None):
        result = await OMDBService.get_movie_details(mock_db, "tt0111161")
        assert result is None


def test_parse_omdb_search_response(sample_search_response):
    """Test parsing OMDB search response"""
    result = OMDBService.parse_omdb_response(sample_search_response)

    assert result is not None
    assert "search_results" in result
    assert "total_results" in result
    assert len(result["search_results"]) == 1
    assert result["search_results"][0]["title"] == "The Shawshank Redemption"
    assert result["search_results"][0]["year"] == 1994
    assert result["search_results"][0]["omdb_id"] == "tt0111161"


def test_parse_omdb_details_response(sample_details_response):
    """Test parsing OMDB details response"""
    result = OMDBService.parse_omdb_response(sample_details_response)

    assert result is not None
    assert result["title"] == "The Shawshank Redemption"
    assert result["year"] == 1994
    assert result["omdb_id"] == "tt0111161"
    assert result["rating"] == 9.3
    assert result["runtime"] == 142
    assert result["director"] == "Frank Darabont"
    assert result["actors"] == "Tim Robbins, Morgan Freeman, Bob Gunton"


def test_parse_omdb_response_with_invalid_data():
    """Test parsing invalid OMDB response"""
    invalid_response = {"Response": "False", "Error": "Movie not found!"}
    result = OMDBService.parse_omdb_response(invalid_response)
    assert result is None


def test_parse_omdb_response_with_none():
    """Test parsing None response"""
    result = OMDBService.parse_omdb_response(None)
    assert result is None


def test_get_cache_key():
    """Test cache key generation"""
    key1 = OMDBService._get_cache_key("search", {"title": "Test", "year": 2020})
    key2 = OMDBService._get_cache_key("search", {"title": "Test", "year": 2020})
    key3 = OMDBService._get_cache_key("search", {"title": "Other", "year": 2020})

    assert key1 == key2
    assert key1 != key3


def test_get_cache_expired(mock_db):
    """Test cache retrieval with expired entry"""
    # Setup expired cache entry
    cache_entry = Mock(spec=APICache)
    cache_entry.expires_at = datetime.utcnow() - timedelta(hours=1)
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = OMDBService._get_cache(mock_db, "test_key")
    assert result is None


def test_set_cache_new_entry(mock_db):
    """Test setting new cache entry"""
    mock_db.query.return_value.filter.return_value.first.return_value = None

    test_data = {"title": "Test Movie", "year": 2020}
    OMDBService._set_cache(mock_db, "test_key", test_data, 3600)

    # Verify add was called
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_set_cache_update_existing(mock_db):
    """Test updating existing cache entry"""
    existing_entry = Mock(spec=APICache)
    mock_db.query.return_value.filter.return_value.first.return_value = existing_entry

    test_data = {"title": "Updated Movie", "year": 2021}
    OMDBService._set_cache(mock_db, "test_key", test_data, 3600)

    # Verify update occurred
    assert existing_entry.response_data == json.dumps(test_data)
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_rate_limit_enforcement():
    """Test rate limiting enforcement"""
    # Reset rate limiter
    OMDBService._last_request_time = 0

    start_time = asyncio.get_event_loop().time()
    await OMDBService._rate_limit()
    first_call_time = asyncio.get_event_loop().time() - start_time

    start_time = asyncio.get_event_loop().time()
    await OMDBService._rate_limit()
    second_call_time = asyncio.get_event_loop().time() - start_time

    # Second call should have waited approximately 1 second
    assert second_call_time >= 0.9  # Allow small timing variance


@pytest.mark.asyncio
async def test_make_request_with_retry_success():
    """Test successful request with retry logic"""
    mock_response = AsyncMock()
    mock_response.json.return_value = {"Response": "True", "Title": "Test"}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = await OMDBService._make_request_with_retry("http://test.com")

        assert result is not None
        assert result["Response"] == "True"


@pytest.mark.asyncio
async def test_make_request_with_retry_api_error():
    """Test request with API error response"""
    mock_response = AsyncMock()
    mock_response.json.return_value = {"Response": "False", "Error": "Movie not found!"}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = await OMDBService._make_request_with_retry("http://test.com")

        assert result is None


@pytest.mark.asyncio
async def test_make_request_with_retry_http_error():
    """Test request with HTTP error and retry"""
    mock_response = AsyncMock()
    mock_response.status_code = 500

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.side_effect = Exception("Connection error")
        mock_client_class.return_value = mock_client

        result = await OMDBService._make_request_with_retry(
            "http://test.com", max_retries=1
        )

        # Should return None after retries exhausted
        assert result is None
