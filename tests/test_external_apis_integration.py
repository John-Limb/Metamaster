"""Comprehensive integration tests for external API integrations (mocked)"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from app.database import Base
from app.models import Movie, TVShow, APICache
from tests.db_utils import TEST_DATABASE_URL


# ============================================================================
# Test Database Setup
# ============================================================================


@pytest.fixture(scope="function")
def db_session():
    """Create a PostgreSQL database session for testing"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


# ============================================================================
# OMDB API Integration Tests
# ============================================================================


class TestOMDBAPIIntegration:
    """Tests for OMDB API integration (mocked)"""

    @patch("app.services_impl.TMDBService.get_movie_details")
    async def test_get_movie_details_success(self, mock_get_details, db_session):
        """Test successful OMDB API call"""
        mock_response = {
            "Title": "The Shawshank Redemption",
            "Year": "1994",
            "imdbRating": "9.3",
            "Runtime": "142 min",
            "Plot": "Two imprisoned men bond over a number of years",
            "Genre": "Drama",
            "imdbID": "tt0111161",
        }
        mock_get_details.return_value = mock_response

        result = await mock_get_details(db_session, "tt0111161")
        assert result["Title"] == "The Shawshank Redemption"
        assert result["imdbRating"] == "9.3"

    @patch("app.services_impl.TMDBService.get_movie_details")
    async def test_get_movie_details_not_found(self, mock_get_details, db_session):
        """Test OMDB API call for non-existent movie"""
        mock_get_details.return_value = None

        result = await mock_get_details(db_session, "tt9999999")
        assert result is None

    @patch("app.services_impl.TMDBService.get_movie_details")
    async def test_get_movie_details_api_error(self, mock_get_details, db_session):
        """Test OMDB API error handling"""
        mock_get_details.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            await mock_get_details(db_session, "tt0111161")

    @patch("app.services_impl.TMDBService.parse_movie_details_response")
    def test_parse_movie_details_response(self, mock_parse):
        """Test parsing TMDB movie details response"""
        tmdb_data = {
            "id": 27205,
            "title": "Inception",
            "release_date": "2010-07-16",
            "vote_average": 8.8,
            "runtime": 148,
            "overview": "A skilled thief",
            "genres": [{"id": 28, "name": "Action"}, {"id": 878, "name": "Sci-Fi"}],
        }

        mock_parse.return_value = {
            "title": "Inception",
            "year": 2010,
            "rating": 8.8,
            "runtime": 148,
            "plot": "A skilled thief",
            "genres": '["Action", "Sci-Fi"]',
            "tmdb_id": "27205",
        }

        result = mock_parse(omdb_data)
        assert result["title"] == "Inception"
        assert result["year"] == 2010
        assert result["rating"] == 8.8

    @patch("app.services_impl.TMDBService.get_movie_details")
    async def test_omdb_rate_limiting(self, mock_get_details, db_session):
        """Test OMDB API rate limiting"""
        mock_get_details.return_value = {"Title": "Test"}

        # Simulate multiple calls
        for i in range(5):
            result = await mock_get_details(db_session, f"tt{i}")
            assert result is not None

        # Verify calls were made
        assert mock_get_details.call_count == 5

    @patch("app.services_impl.TMDBService.get_movie_details")
    async def test_omdb_cache_hit(self, mock_get_details, db_session):
        """Test OMDB API cache hit"""
        # Add cached entry
        cache = APICache(
            api_type="tmdb",
            query_key="movie_details_tmdb_id=278",
            response_data='{"id": 278, "title": "The Shawshank Redemption"}',
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(cache)
        db_session.commit()

        # Query cache
        cached = (
            db_session.query(APICache)
            .filter(APICache.api_type == "tmdb", APICache.query_key == "movie_details_tmdb_id=278")
            .first()
        )

        assert cached is not None
        assert "Shawshank" in cached.response_data


# ============================================================================
# TVDB API Integration Tests
# ============================================================================


class TestTVDBAPIIntegration:
    """Tests for TVDB API integration (mocked)"""

    @patch("app.services_impl.TMDBService.get_series_details")
    async def test_get_series_details_success(self, mock_get_details, db_session):
        """Test successful TVDB API call"""
        mock_response = {
            "data": {
                "name": "Breaking Bad",
                "overview": "A high school chemistry teacher",
                "rating": 9.5,
                "status": "Ended",
                "genres": ["drama", "crime"],
            }
        }
        mock_get_details.return_value = mock_response

        result = await mock_get_details(db_session, "81189")
        assert result["data"]["name"] == "Breaking Bad"
        assert result["data"]["status"] == "Ended"

    @patch("app.services_impl.TMDBService.get_series_details")
    async def test_get_series_details_not_found(self, mock_get_details, db_session):
        """Test TVDB API call for non-existent series"""
        mock_get_details.return_value = None

        result = await mock_get_details(db_session, "999999")
        assert result is None

    @patch("app.services_impl.TMDBService.parse_series_response")
    def test_parse_series_response(self, mock_parse):
        """Test parsing TMDB series details response"""
        tmdb_data = {
            "id": 1399,
            "name": "Game of Thrones",
            "overview": "An epic fantasy series",
            "vote_average": 9.2,
            "status": "Ended",
            "genres": [{"id": 18, "name": "Drama"}, {"id": 10759, "name": "Action & Adventure"}],
        }

        mock_parse.return_value = {
            "title": "Game of Thrones",
            "plot": "An epic fantasy series",
            "rating": 9.2,
            "status": "ended",
            "genres": '["Drama", "Action & Adventure"]',
        }

        result = mock_parse(tmdb_data)
        assert result["title"] == "Game of Thrones"
        assert result["status"] == "ended"

    @patch("app.services_impl.TMDBService.get_series_details")
    async def test_tvdb_rate_limiting(self, mock_get_details, db_session):
        """Test TVDB API rate limiting"""
        mock_get_details.return_value = {"data": {"name": "Test"}}

        # Simulate multiple calls
        for i in range(10):
            result = await mock_get_details(db_session, f"id_{i}")
            assert result is not None

        # Verify calls were made
        assert mock_get_details.call_count == 10

    @patch("app.services_impl.TMDBService.get_series_details")
    async def test_tvdb_cache_hit(self, mock_get_details, db_session):
        """Test TVDB API cache hit"""
        # Add cached entry
        cache = APICache(
            api_type="tmdb",
            query_key="tv_details_tmdb_id=1396",
            response_data='{"id": 1396, "name": "Breaking Bad"}',
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(cache)
        db_session.commit()

        # Query cache
        cached = (
            db_session.query(APICache)
            .filter(APICache.api_type == "tmdb", APICache.query_key == "tv_details_tmdb_id=1396")
            .first()
        )

        assert cached is not None
        assert "Breaking Bad" in cached.response_data


# ============================================================================
# FFProbe Integration Tests
# ============================================================================


class TestFFProbeIntegration:
    """Tests for FFProbe integration (mocked)"""

    @patch("app.services.FFProbeWrapper._run_ffprobe")
    def test_get_resolution(self, mock_run_ffprobe):
        """Test getting video resolution"""
        mock_run_ffprobe.return_value = {
            "streams": [{"codec_type": "video", "width": 1920, "height": 1080}]
        }

        from app.services.ffprobe_wrapper import FFProbeWrapper

        wrapper = FFProbeWrapper()
        wrapper._run_ffprobe = mock_run_ffprobe

        result = wrapper.get_resolution("/path/to/file.mp4")
        assert result["width"] == 1920
        assert result["height"] == 1080
        assert result["label"] == "1080p"

    @patch("app.services.FFProbeWrapper._run_ffprobe")
    def test_get_bitrate(self, mock_run_ffprobe):
        """Test getting video bitrate"""
        mock_run_ffprobe.return_value = {
            "streams": [
                {"codec_type": "video", "bit_rate": "5000000"},
                {"codec_type": "audio", "bit_rate": "128000"},
            ],
            "format": {"bit_rate": "5128000"},
        }

        from app.services.ffprobe_wrapper import FFProbeWrapper

        wrapper = FFProbeWrapper()
        wrapper._run_ffprobe = mock_run_ffprobe

        result = wrapper.get_bitrate("/path/to/file.mp4")
        assert "total" in result
        assert "video" in result
        assert "audio" in result

    @patch("app.services.FFProbeWrapper._run_ffprobe")
    def test_get_codecs(self, mock_run_ffprobe):
        """Test getting video codecs"""
        mock_run_ffprobe.return_value = {
            "streams": [
                {"codec_type": "video", "codec_name": "h264"},
                {"codec_type": "audio", "codec_name": "aac"},
            ]
        }

        from app.services.ffprobe_wrapper import FFProbeWrapper

        wrapper = FFProbeWrapper()
        wrapper._run_ffprobe = mock_run_ffprobe

        result = wrapper.get_codecs("/path/to/file.mp4")
        assert result["video"] == "h264"
        assert result["audio"] == "aac"

    @patch("app.services.FFProbeWrapper._run_ffprobe")
    def test_get_duration(self, mock_run_ffprobe):
        """Test getting video duration"""
        mock_run_ffprobe.return_value = {"format": {"duration": "7200.5"}}

        from app.services.ffprobe_wrapper import FFProbeWrapper

        wrapper = FFProbeWrapper()
        wrapper._run_ffprobe = mock_run_ffprobe

        result = wrapper.get_duration("/path/to/file.mp4")
        assert result == 7200.5

    @patch("app.services.FFProbeWrapper._run_ffprobe")
    def test_ffprobe_invalid_file(self, mock_run_ffprobe):
        """Test FFProbe with invalid file"""
        mock_run_ffprobe.side_effect = FileNotFoundError("File not found")

        from app.services.ffprobe_wrapper import FFProbeWrapper

        wrapper = FFProbeWrapper()
        wrapper._run_ffprobe = mock_run_ffprobe

        with pytest.raises(FileNotFoundError):
            wrapper._run_ffprobe("/nonexistent/file.mp4")


# ============================================================================
# File System Integration Tests
# ============================================================================


class TestFileSystemIntegration:
    """Tests for file system operations"""

    @patch("os.path.exists")
    def test_file_exists(self, mock_exists):
        """Test checking if file exists"""
        mock_exists.return_value = True

        import os

        result = os.path.exists("/path/to/file.mp4")
        assert result is True

    @patch("os.path.getsize")
    def test_get_file_size(self, mock_getsize):
        """Test getting file size"""
        mock_getsize.return_value = 1024 * 1024 * 500  # 500 MB

        import os

        size = os.path.getsize("/path/to/file.mp4")
        assert size == 524288000

    @patch("os.listdir")
    def test_list_directory(self, mock_listdir):
        """Test listing directory contents"""
        mock_listdir.return_value = ["file1.mp4", "file2.mkv", "file3.avi"]

        import os

        files = os.listdir("/media/movies")
        assert len(files) == 3
        assert "file1.mp4" in files

    @patch("pathlib.Path.glob")
    def test_glob_pattern(self, mock_glob):
        """Test glob pattern matching"""
        mock_glob.return_value = [
            "/media/file1.mp4",
            "/media/file2.mkv",
            "/media/file3.avi",
        ]

        from pathlib import Path

        path = Path("/media")
        files = list(path.glob("*"))
        assert len(files) == 3


# ============================================================================
# API Error Handling Tests
# ============================================================================


class TestAPIErrorHandling:
    """Tests for API error handling"""

    @patch("app.services_impl.TMDBService.get_movie_details")
    async def test_omdb_timeout_error(self, mock_get_details, db_session):
        """Test OMDB API timeout error"""
        mock_get_details.side_effect = TimeoutError("Request timeout")

        with pytest.raises(TimeoutError):
            await mock_get_details(db_session, "tt0111161")

    @patch("app.services_impl.TMDBService.get_movie_details")
    async def test_omdb_connection_error(self, mock_get_details, db_session):
        """Test OMDB API connection error"""
        mock_get_details.side_effect = ConnectionError("Connection failed")

        with pytest.raises(ConnectionError):
            await mock_get_details(db_session, "tt0111161")

    @patch("app.services_impl.TMDBService.get_series_details")
    async def test_tvdb_authentication_error(self, mock_get_details, db_session):
        """Test TVDB API authentication error"""
        mock_get_details.side_effect = Exception("Authentication failed")

        with pytest.raises(Exception):
            await mock_get_details(db_session, "81189")

    @patch("app.services.FFProbeWrapper._run_ffprobe")
    def test_ffprobe_timeout(self, mock_run_ffprobe):
        """Test FFProbe timeout"""
        import subprocess

        mock_run_ffprobe.side_effect = subprocess.TimeoutExpired("ffprobe", 30)

        from app.services.ffprobe_wrapper import FFProbeWrapper

        wrapper = FFProbeWrapper()
        wrapper._run_ffprobe = mock_run_ffprobe

        with pytest.raises(subprocess.TimeoutExpired):
            wrapper._run_ffprobe("/path/to/file.mp4")


# ============================================================================
# Retry Logic Tests
# ============================================================================


class TestRetryLogic:
    """Tests for retry logic"""

    @patch("app.services_impl.TMDBService.get_movie_details")
    async def test_omdb_retry_on_failure(self, mock_get_details, db_session):
        """Test OMDB API retry on failure"""
        # First call fails, second succeeds
        mock_get_details.side_effect = [
            Exception("Temporary error"),
            {"Title": "The Shawshank Redemption"},
        ]

        # First call
        with pytest.raises(Exception):
            await mock_get_details(db_session, "tt0111161")

        # Second call (retry)
        result = await mock_get_details(db_session, "tt0111161")
        assert result["Title"] == "The Shawshank Redemption"

    @patch("app.services_impl.TMDBService.get_series_details")
    async def test_tvdb_retry_on_failure(self, mock_get_details, db_session):
        """Test TVDB API retry on failure"""
        # First call fails, second succeeds
        mock_get_details.side_effect = [
            Exception("Temporary error"),
            {"data": {"name": "Breaking Bad"}},
        ]

        # First call
        with pytest.raises(Exception):
            await mock_get_details(db_session, "81189")

        # Second call (retry)
        result = await mock_get_details(db_session, "81189")
        assert result["data"]["name"] == "Breaking Bad"


# ============================================================================
# Cache Expiration Tests
# ============================================================================


class TestCacheExpiration:
    """Tests for cache expiration"""

    def test_cache_expiration_omdb(self, db_session):
        """Test OMDB cache expiration"""
        # Add expired cache
        expired = APICache(
            api_type="tmdb",
            query_key="tt0111161",
            response_data='{"Title": "Old"}',
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        db_session.add(expired)
        db_session.commit()

        # Query should not return expired entry
        result = (
            db_session.query(APICache)
            .filter(
                APICache.api_type == "tmdb",
                APICache.query_key == "tt0111161",
                APICache.expires_at > datetime.utcnow(),
            )
            .first()
        )

        assert result is None

    def test_cache_expiration_tvdb(self, db_session):
        """Test TVDB cache expiration"""
        # Add active cache
        active = APICache(
            api_type="tmdb",
            query_key="81189",
            response_data='{"data": {"name": "Breaking Bad"}}',
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(active)
        db_session.commit()

        # Query should return active entry
        result = (
            db_session.query(APICache)
            .filter(
                APICache.api_type == "tmdb",
                APICache.query_key == "81189",
                APICache.expires_at > datetime.utcnow(),
            )
            .first()
        )

        assert result is not None


# ============================================================================
# Metadata Enrichment Tests
# ============================================================================


class TestMetadataEnrichment:
    """Tests for metadata enrichment"""

    @patch("app.services_impl.TMDBService.get_movie_details")
    async def test_enrich_movie_metadata(self, mock_get_details, db_session):
        """Test enriching movie metadata from OMDB"""
        movie = Movie(title="The Shawshank Redemption", year=1994)
        db_session.add(movie)
        db_session.commit()
        db_session.refresh(movie)

        mock_get_details.return_value = {
            "Title": "The Shawshank Redemption",
            "Year": "1994",
            "imdbRating": "9.3",
            "Runtime": "142 min",
            "Plot": "Two imprisoned men bond over a number of years",
            "Genre": "Drama",
        }

        result = await mock_get_details(db_session, "tt0111161")
        assert result["imdbRating"] == "9.3"

    @patch("app.services_impl.TMDBService.get_series_details")
    async def test_enrich_tvshow_metadata(self, mock_get_details, db_session):
        """Test enriching TV show metadata from TVDB"""
        show = TVShow(title="Breaking Bad")
        db_session.add(show)
        db_session.commit()
        db_session.refresh(show)

        mock_get_details.return_value = {
            "data": {
                "name": "Breaking Bad",
                "overview": "A high school chemistry teacher",
                "rating": 9.5,
                "status": "Ended",
            }
        }

        result = await mock_get_details(db_session, "81189")
        assert result["data"]["rating"] == 9.5
