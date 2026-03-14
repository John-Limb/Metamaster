"""Business logic layer for movies and TV shows"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models import APICache, Episode, Movie, Season, TVShow
from app.schemas import MovieCreate, MovieUpdate, TVShowCreate, TVShowUpdate

logger = logging.getLogger(__name__)
external_api_logger = logging.getLogger("external_api")


def _mask_url(url: str) -> str:
    """Mask API keys in URLs for safe logging."""
    import re

    return re.sub(r"(apikey=)[^&]+", r"\1***", url)


class MovieService:
    """Service class for movie operations"""

    @staticmethod
    def get_all_movies(db: Session, limit: int = 10, offset: int = 0):
        """Get all movies with pagination"""
        query = db.query(Movie).options(selectinload(Movie.files))
        total = query.count()
        movies = query.offset(offset).limit(limit).all()
        return movies, total

    @staticmethod
    def get_popular_movies(db: Session, limit: int = 10, offset: int = 0):
        """Return movies ordered by descending rating then recency."""
        query = (
            db.query(Movie)
            .options(selectinload(Movie.files))
            .order_by(Movie.rating.desc().nullslast(), Movie.created_at.desc())
        )
        total = query.count()
        movies = query.offset(offset).limit(limit).all()
        return movies, total

    @staticmethod
    def get_top_rated_movies(db: Session, limit: int = 10, offset: int = 0):
        """Return top-rated movies prioritizing highest rating and longest runtime."""
        query = (
            db.query(Movie)
            .options(selectinload(Movie.files))
            .order_by(Movie.rating.desc().nullslast(), Movie.runtime.desc().nullslast())
        )
        total = query.count()
        movies = query.offset(offset).limit(limit).all()
        return movies, total

    @staticmethod
    def get_movie_by_id(db: Session, movie_id: int):
        """Get a specific movie by ID"""
        movie = (
            db.query(Movie).options(selectinload(Movie.files)).filter(Movie.id == movie_id).first()
        )
        return movie

    @staticmethod
    def create_movie(db: Session, movie_data: MovieCreate):
        """Create a new movie"""
        db_movie = Movie(
            title=movie_data.title,
            plot=movie_data.plot,
            year=movie_data.year,
            rating=movie_data.rating,
            runtime=movie_data.runtime,
            genres=movie_data.genres,
            tmdb_id=movie_data.tmdb_id,
        )
        db.add(db_movie)
        db.commit()
        db.refresh(db_movie)
        logger.info(f"Created movie: {db_movie.id} - {db_movie.title}")
        return db_movie

    @staticmethod
    def update_movie(db: Session, movie_id: int, movie_data: MovieUpdate):
        """Update an existing movie"""
        db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if not db_movie:
            return None

        update_data = movie_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_movie, field, value)

        db.commit()
        db.refresh(db_movie)
        logger.info(f"Updated movie: {db_movie.id} - {db_movie.title}")
        return db_movie

    @staticmethod
    def delete_movie(db: Session, movie_id: int):
        """Delete a movie"""
        db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if not db_movie:
            return False

        db.delete(db_movie)
        db.commit()
        logger.info(f"Deleted movie: {movie_id}")
        return True

    @staticmethod
    def search_movies(db: Session, query: str, limit: int = 10, offset: int = 0):
        """Search movies by title"""
        search_query = (
            db.query(Movie)
            .options(selectinload(Movie.files))
            .filter(Movie.title.ilike(f"%{query}%"))
        )
        total = search_query.count()
        movies = search_query.offset(offset).limit(limit).all()
        logger.info(f"Searched movies with query: {query}, found: {total}")
        return movies, total


class TMDBService:
    """Service class for TMDB API integration with rate limiting and caching.

    Covers both movies (replacing OMDB) and TV shows (replacing TVDB).
    API docs: https://developer.themoviedb.org/reference/intro/getting-started
    """

    TMDB_BASE_URL = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

    # Class-level rate limiter
    _last_request_time: float = 0
    _rate_limit_lock = asyncio.Lock()

    @classmethod
    async def _rate_limit(cls) -> None:
        """Enforce rate limiting (~4 requests per second)."""
        async with cls._rate_limit_lock:
            elapsed = time.time() - cls._last_request_time
            min_interval = 1.0 / settings.tmdb_rate_limit
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            cls._last_request_time = time.time()

    @staticmethod
    def _get_cache_key(endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key from endpoint and parameters."""
        param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{endpoint}_{param_str}"

    @staticmethod
    def _get_cache(db: Session, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached API response if not expired."""
        cache_entry = (
            db.query(APICache)
            .filter(
                APICache.api_type == "tmdb",
                APICache.query_key == cache_key,
                APICache.expires_at > datetime.utcnow(),
            )
            .first()
        )

        if cache_entry:
            external_api_logger.debug(
                f"TMDB cache HIT: {cache_key}",
                extra={"api_service": "tmdb", "cache_key": cache_key, "cache_hit": True},
            )
            return json.loads(cache_entry.response_data)
        external_api_logger.debug(
            f"TMDB cache MISS: {cache_key}",
            extra={"api_service": "tmdb", "cache_key": cache_key, "cache_hit": False},
        )
        return None

    @staticmethod
    def _set_cache(
        db: Session, cache_key: str, response_data: Dict[str, Any], ttl_seconds: int
    ) -> None:
        """Store API response in cache with TTL."""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

        existing = (
            db.query(APICache)
            .filter(APICache.api_type == "tmdb", APICache.query_key == cache_key)
            .first()
        )

        if existing:
            existing.response_data = json.dumps(response_data)
            existing.expires_at = expires_at
        else:
            cache_entry = APICache(
                api_type="tmdb",
                query_key=cache_key,
                response_data=json.dumps(response_data),
                expires_at=expires_at,
            )
            db.add(cache_entry)

        db.commit()
        logger.info(f"Cached TMDB response for: {cache_key}")

    @staticmethod
    async def _make_request_with_retry(
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request with exponential backoff retry logic."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            for attempt in range(max_retries):
                start_time = time.time()
                try:
                    external_api_logger.info(
                        f"TMDB >> GET {url} (attempt {attempt + 1}/{max_retries})",
                        extra={"api_service": "tmdb", "api_url": url, "attempt": attempt + 1},
                    )

                    response = await client.get(url, headers=headers, params=params or {})
                    elapsed_ms = (time.time() - start_time) * 1000

                    external_api_logger.info(
                        f"TMDB << {response.status_code} in {elapsed_ms:.0f}ms "
                        f"({len(response.content)} bytes) {url}",
                        extra={
                            "api_service": "tmdb",
                            "api_url": url,
                            "response_status": response.status_code,
                            "duration": elapsed_ms,
                            "response_size": len(response.content),
                        },
                    )

                    response.raise_for_status()
                    return response.json()

                except httpx.HTTPStatusError as e:
                    elapsed_ms = (time.time() - start_time) * 1000
                    if e.response.status_code == 429:
                        delay = base_delay * (2**attempt)
                        external_api_logger.warning(
                            f"TMDB rate limited (429). Retrying in {delay}s",
                            extra={
                                "api_service": "tmdb",
                                "api_url": url,
                                "response_status": 429,
                                "duration": elapsed_ms,
                            },
                        )
                        await asyncio.sleep(delay)
                    elif e.response.status_code == 401:
                        external_api_logger.error(
                            "TMDB authentication failed (401) — check TMDB_API_KEY",
                            extra={
                                "api_service": "tmdb",
                                "api_url": url,
                                "response_status": 401,
                                "duration": elapsed_ms,
                            },
                        )
                        return None
                    elif e.response.status_code == 404:
                        external_api_logger.warning(
                            f"TMDB resource not found (404): {url}",
                            extra={
                                "api_service": "tmdb",
                                "api_url": url,
                                "response_status": 404,
                                "duration": elapsed_ms,
                            },
                        )
                        return None
                    elif e.response.status_code >= 500:
                        delay = base_delay * (2**attempt)
                        external_api_logger.warning(
                            f"TMDB server error ({e.response.status_code}). Retrying in {delay}s",
                            extra={
                                "api_service": "tmdb",
                                "api_url": url,
                                "response_status": e.response.status_code,
                                "duration": elapsed_ms,
                            },
                        )
                        await asyncio.sleep(delay)
                    else:
                        external_api_logger.error(
                            f"TMDB HTTP error {e.response.status_code}: {url}",
                            extra={
                                "api_service": "tmdb",
                                "api_url": url,
                                "response_status": e.response.status_code,
                                "duration": elapsed_ms,
                            },
                        )
                        return None

                except httpx.RequestError as e:
                    elapsed_ms = (time.time() - start_time) * 1000
                    delay = base_delay * (2**attempt)
                    external_api_logger.warning(
                        f"TMDB request error: {e}. Retrying in {delay}s",
                        extra={"api_service": "tmdb", "api_url": url, "duration": elapsed_ms},
                    )
                    await asyncio.sleep(delay)

                except json.JSONDecodeError as e:
                    external_api_logger.error(
                        f"Failed to parse TMDB response: {e}",
                        extra={"api_service": "tmdb", "api_url": url},
                    )
                    return None

            external_api_logger.error(
                f"TMDB request failed after {max_retries} attempts: {url}",
                extra={"api_service": "tmdb", "api_url": url},
            )
            return None

    @classmethod
    def _get_auth(cls) -> tuple:
        """Return (headers, query_params) for TMDB authentication.

        Priority: TMDB_READ_ACCESS_TOKEN (Bearer) > TMDB_API_KEY (?api_key=).
        Raises RuntimeError if neither is configured so callers surface this as
        external_failed (retryable) rather than silently marking items not_found.
        """
        if settings.tmdb_read_access_token:
            return (
                {
                    "Authorization": f"Bearer {settings.tmdb_read_access_token}",
                    "accept": "application/json",
                },
                {},
            )
        if settings.tmdb_api_key:
            return (
                {"accept": "application/json"},
                {"api_key": settings.tmdb_api_key},
            )
        raise RuntimeError(
            "No TMDB credentials configured — set TMDB_READ_ACCESS_TOKEN or TMDB_API_KEY"
        )

    @staticmethod
    def _normalize_tv_status(status: str) -> str:
        """Normalise TMDB TV show status strings to internal values."""
        s = (status or "").lower()
        if s in ("returning series", "in production", "pilot"):
            return "continuing"
        if s in ("ended", "canceled", "cancelled"):
            return "ended"
        return s

    @staticmethod
    def _poster_url(poster_path: Optional[str]) -> Optional[str]:
        """Build a full poster URL from a TMDB poster_path."""
        if not poster_path:
            return None
        return f"https://image.tmdb.org/t/p/w500{poster_path}"

    # ------------------------------------------------------------------ #
    # Movie methods
    # ------------------------------------------------------------------ #

    @classmethod
    async def search_movie(
        cls, db: Session, title: str, year: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Search TMDB for a movie by title and optional year."""
        headers, params = cls._get_auth()

        cache_params: Dict[str, Any] = {"title": title}
        if year:
            cache_params["year"] = year
        cache_key = cls._get_cache_key("movie_search", cache_params)

        cached = cls._get_cache(db, cache_key)
        if cached:
            return cached

        await cls._rate_limit()

        query_str = f"query={title}"
        if year:
            query_str += f"&year={year}"
        url = f"{cls.TMDB_BASE_URL}/search/movie?{query_str}"

        logger.info(f"Searching TMDB for movie: {title} (year: {year})")
        result = await cls._make_request_with_retry(url, headers, params)

        if result:
            cls._set_cache(db, cache_key, result, settings.tmdb_cache_ttl)
        return result

    @classmethod
    async def get_movie_details(cls, db: Session, tmdb_id: str) -> Optional[Dict[str, Any]]:
        """Fetch full movie details from TMDB by TMDB ID."""
        headers, params = cls._get_auth()

        cache_key = cls._get_cache_key("movie_details", {"tmdb_id": tmdb_id})
        cached = cls._get_cache(db, cache_key)
        if cached:
            return cached

        await cls._rate_limit()

        url = f"{cls.TMDB_BASE_URL}/movie/{tmdb_id}"
        logger.info(f"Fetching TMDB movie details for ID: {tmdb_id}")
        result = await cls._make_request_with_retry(url, headers, params)

        if result:
            cls._set_cache(db, cache_key, result, settings.tmdb_cache_ttl)
        return result

    @staticmethod
    def parse_movie_search_response(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse TMDB movie search response into internal format."""
        if not data or "results" not in data:
            return None
        try:
            results = []
            for item in data.get("results", []):
                release_year = None
                release_date = item.get("release_date", "")
                if release_date and len(release_date) >= 4:
                    try:
                        release_year = int(release_date[:4])
                    except ValueError:
                        pass
                results.append(
                    {
                        "tmdb_id": str(item.get("id")),
                        "title": item.get("title"),
                        "year": release_year,
                        "poster": TMDBService._poster_url(item.get("poster_path")),
                    }
                )
            return {"search_results": results, "total_results": data.get("total_results", 0)}
        except (ValueError, KeyError, AttributeError) as e:
            logger.error(f"Error parsing TMDB movie search response: {e}")
            return None

    @staticmethod
    def parse_movie_details_response(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse TMDB movie details response into Movie model compatible format."""
        if not data or "id" not in data:
            return None
        try:
            genres = [g["name"] for g in data.get("genres", []) if g.get("name")]
            release_year = None
            release_date = data.get("release_date", "")
            if release_date and len(release_date) >= 4:
                try:
                    release_year = int(release_date[:4])
                except ValueError:
                    pass
            rating = data.get("vote_average")
            if rating is not None:
                rating = round(float(rating), 1)
            collection_data = data.get("belongs_to_collection") or {}
            return {
                "tmdb_id": str(data.get("id")),
                "title": data.get("title"),
                "year": release_year,
                "plot": data.get("overview"),
                "rating": rating,
                "runtime": data.get("runtime"),
                "genres": json.dumps(genres),
                "poster": TMDBService._poster_url(data.get("poster_path")),
                "tmdb_collection_id": collection_data.get("id"),
                "tmdb_collection_name": collection_data.get("name"),
            }
        except (ValueError, KeyError, AttributeError) as e:
            logger.error(f"Error parsing TMDB movie details response: {e}")
            return None

    # ------------------------------------------------------------------ #
    # TV show methods
    # ------------------------------------------------------------------ #

    @classmethod
    async def search_show(cls, db: Session, title: str) -> Optional[Dict[str, Any]]:
        """Search TMDB for a TV show by title."""
        headers, params = cls._get_auth()

        cache_key = cls._get_cache_key("tv_search", {"title": title})
        cached = cls._get_cache(db, cache_key)
        if cached:
            return cached

        await cls._rate_limit()

        url = f"{cls.TMDB_BASE_URL}/search/tv?query={title}"
        logger.info(f"Searching TMDB for TV show: {title}")
        result = await cls._make_request_with_retry(url, headers, params)

        if result:
            cls._set_cache(db, cache_key, result, settings.tmdb_cache_ttl)
        return result

    @classmethod
    async def get_series_details(cls, db: Session, tmdb_id: str) -> Optional[Dict[str, Any]]:
        """Fetch full TV series details from TMDB by TMDB ID."""
        headers, params = cls._get_auth()

        cache_key = cls._get_cache_key("tv_details", {"tmdb_id": tmdb_id})
        cached = cls._get_cache(db, cache_key)
        if cached:
            return cached

        await cls._rate_limit()

        url = f"{cls.TMDB_BASE_URL}/tv/{tmdb_id}"
        logger.info(f"Fetching TMDB series details for ID: {tmdb_id}")
        result = await cls._make_request_with_retry(url, headers, params)

        if result:
            cls._set_cache(db, cache_key, result, settings.tmdb_cache_ttl)
        return result

    @classmethod
    async def get_season_details(
        cls, db: Session, tmdb_id: str, season_number: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch season details (including episode list) from TMDB."""
        headers, params = cls._get_auth()

        cache_key = cls._get_cache_key("tv_season", {"tmdb_id": tmdb_id, "season": season_number})
        cached = cls._get_cache(db, cache_key)
        if cached:
            return cached

        await cls._rate_limit()

        url = f"{cls.TMDB_BASE_URL}/tv/{tmdb_id}/season/{season_number}"
        logger.info(f"Fetching TMDB season {season_number} for series ID: {tmdb_id}")
        result = await cls._make_request_with_retry(url, headers, params)

        if result:
            cls._set_cache(db, cache_key, result, settings.tmdb_cache_ttl)
        return result

    @staticmethod
    def parse_series_search_response(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse TMDB TV search response into internal format."""
        if not data or "results" not in data:
            return None
        try:
            results = []
            for item in data.get("results", []):
                results.append(
                    {
                        "tmdb_id": str(item.get("id")),
                        "title": item.get("name"),
                        "plot": item.get("overview"),
                        "status": item.get("status"),
                        "first_air_date": item.get("first_air_date"),
                        "poster": TMDBService._poster_url(item.get("poster_path")),
                    }
                )
            return {"search_results": results, "total_results": data.get("total_results", 0)}
        except (ValueError, KeyError, AttributeError) as e:
            logger.error(f"Error parsing TMDB series search response: {e}")
            return None

    @staticmethod
    def parse_series_response(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse TMDB TV series details response into TVShow model compatible format."""
        if not data or "id" not in data:
            return None
        try:
            genres = [g["name"] for g in data.get("genres", []) if g.get("name")]
            rating = data.get("vote_average")
            if rating is not None:
                rating = round(float(rating), 1)
            return {
                "tmdb_id": str(data.get("id")),
                "title": data.get("name"),
                "plot": data.get("overview"),
                "rating": rating,
                "status": TMDBService._normalize_tv_status(data.get("status", "")),
                "genres": json.dumps(genres),
                "first_air_date": data.get("first_air_date"),
                "last_air_date": data.get("last_air_date"),
                "poster": TMDBService._poster_url(data.get("poster_path")),
                "number_of_seasons": data.get("number_of_seasons"),
            }
        except (ValueError, KeyError, AttributeError) as e:
            logger.error(f"Error parsing TMDB series response: {e}")
            return None

    @staticmethod
    def parse_season_response(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse TMDB season response (includes episode list) into internal format."""
        if not data or "season_number" not in data:
            return None
        try:
            episodes = []
            for ep in data.get("episodes", []):
                rating = ep.get("vote_average")
                if rating is not None:
                    rating = round(float(rating), 1)
                episodes.append(
                    {
                        "tmdb_id": str(ep.get("id")),
                        "episode_number": ep.get("episode_number"),
                        "title": ep.get("name"),
                        "plot": ep.get("overview"),
                        "air_date": ep.get("air_date"),
                        "rating": rating,
                        "runtime": ep.get("runtime"),
                    }
                )
            return {
                "tmdb_id": str(data.get("id")),
                "season_number": data.get("season_number"),
                "episodes": episodes,
            }
        except (ValueError, KeyError, AttributeError) as e:
            logger.error(f"Error parsing TMDB season response: {e}")
            return None


class CacheService:
    """Service class for cache operations with TTL support and statistics tracking"""

    @staticmethod
    def generate_cache_key(api_type: str, endpoint: str, params: Dict[str, Any]) -> str:
        """
        Generate a unique cache key from API type, endpoint, and parameters.

        Args:
            api_type: Type of API ("omdb", "tvdb", etc.)
            endpoint: API endpoint name
            params: Query parameters dictionary

        Returns:
            Generated cache key string
        """
        param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{api_type}:{endpoint}:{param_str}"

    @staticmethod
    def get_cache(db: Session, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached API response if not expired.

        Args:
            db: Database session
            cache_key: Cache key to retrieve

        Returns:
            Cached response data or None if not found or expired
        """
        cache_entry = (
            db.query(APICache)
            .filter(APICache.query_key == cache_key, APICache.expires_at > datetime.utcnow())
            .first()
        )

        if cache_entry:
            logger.info(f"Cache hit for key: {cache_key}")
            return json.loads(cache_entry.response_data)

        logger.debug(f"Cache miss for key: {cache_key}")
        return None

    @staticmethod
    def set_cache(
        db: Session,
        cache_key: str,
        response_data: Dict[str, Any],
        api_type: str = "generic",
        ttl_seconds: int = 2592000,
    ) -> bool:
        """
        Store API response in cache with TTL.

        Args:
            db: Database session
            cache_key: Cache key to store
            response_data: Response data to cache
            api_type: Type of API ("omdb", "tvdb", etc.)
            ttl_seconds: Time to live in seconds (default: 30 days)

        Returns:
            True if successful, False otherwise
        """
        try:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

            # Check if cache entry already exists
            existing = db.query(APICache).filter(APICache.query_key == cache_key).first()

            if existing:
                existing.response_data = json.dumps(response_data)
                existing.expires_at = expires_at
                logger.info(f"Updated cache for key: {cache_key}")
            else:
                cache_entry = APICache(
                    api_type=api_type,
                    query_key=cache_key,
                    response_data=json.dumps(response_data),
                    expires_at=expires_at,
                )
                db.add(cache_entry)
                logger.info(f"Created cache for key: {cache_key}")

            db.commit()
            return True

        except Exception as e:
            logger.error(f"Error setting cache for key {cache_key}: {e}")
            db.rollback()
            return False

    @staticmethod
    def delete_cache(db: Session, cache_key: str) -> bool:
        """
        Delete a specific cache entry.

        Args:
            db: Database session
            cache_key: Cache key to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            cache_entry = db.query(APICache).filter(APICache.query_key == cache_key).first()

            if not cache_entry:
                logger.warning(f"Cache entry not found for key: {cache_key}")
                return False

            db.delete(cache_entry)
            db.commit()
            logger.info(f"Deleted cache for key: {cache_key}")
            return True

        except Exception as e:
            logger.error(f"Error deleting cache for key {cache_key}: {e}")
            db.rollback()
            return False

    @staticmethod
    def clear_expired_cache(db: Session) -> int:
        """
        Delete all expired cache entries.

        Args:
            db: Database session

        Returns:
            Number of entries deleted
        """
        try:
            expired_entries = (
                db.query(APICache).filter(APICache.expires_at <= datetime.utcnow()).all()
            )

            count = len(expired_entries)
            for entry in expired_entries:
                db.delete(entry)

            db.commit()
            logger.info(f"Cleared {count} expired cache entries")
            return count

        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
            db.rollback()
            return 0

    @staticmethod
    def invalidate_by_type(db: Session, api_type: str) -> int:
        """
        Invalidate all cache entries for a specific API type.

        Args:
            db: Database session
            api_type: API type to invalidate ("omdb", "tvdb", etc.)

        Returns:
            Number of entries invalidated
        """
        try:
            entries = db.query(APICache).filter(APICache.api_type == api_type).all()

            count = len(entries)
            for entry in entries:
                db.delete(entry)

            db.commit()
            logger.info(f"Invalidated {count} cache entries for API type: {api_type}")
            return count

        except Exception as e:
            logger.error(f"Error invalidating cache by type {api_type}: {e}")
            db.rollback()
            return 0

    @staticmethod
    def invalidate_by_pattern(db: Session, pattern: str) -> int:
        """
        Invalidate cache entries matching a key pattern.

        Args:
            db: Database session
            pattern: Pattern to match (supports wildcards like "omdb:*")

        Returns:
            Number of entries invalidated
        """
        try:
            # Convert wildcard pattern to SQL LIKE pattern
            sql_pattern = pattern.replace("*", "%")

            entries = db.query(APICache).filter(APICache.query_key.like(sql_pattern)).all()

            count = len(entries)
            for entry in entries:
                db.delete(entry)

            db.commit()
            logger.info(f"Invalidated {count} cache entries matching pattern: {pattern}")
            return count

        except Exception as e:
            logger.error(f"Error invalidating cache by pattern {pattern}: {e}")
            db.rollback()
            return 0

    @staticmethod
    def get_cache_stats(db: Session) -> Dict[str, Any]:
        """
        Get cache statistics including size, count, and breakdown by API type.

        Args:
            db: Database session

        Returns:
            Dictionary containing cache statistics
        """
        try:
            total_entries = db.query(func.count(APICache.id)).scalar() or 0
            expired_entries = (
                db.query(func.count(APICache.id))
                .filter(APICache.expires_at <= datetime.utcnow())
                .scalar()
                or 0
            )
            active_entries = total_entries - expired_entries

            # Get breakdown by API type
            type_breakdown = (
                db.query(APICache.api_type, func.count(APICache.id).label("count"))
                .group_by(APICache.api_type)
                .all()
            )

            type_stats = {api_type: count for api_type, count in type_breakdown}

            # Calculate total cache size in bytes
            total_size = db.query(func.sum(func.length(APICache.response_data))).scalar() or 0

            stats = {
                "total_entries": total_entries,
                "active_entries": active_entries,
                "expired_entries": expired_entries,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "by_api_type": type_stats,
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Cache stats: {total_entries} total, {active_entries} active, {total_size} bytes"
            )
            return stats

        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}")
            return {
                "error": str(e),
                "total_entries": 0,
                "active_entries": 0,
                "expired_entries": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "by_api_type": {},
            }

    @staticmethod
    def bulk_delete_cache(db: Session, cache_keys: list) -> int:
        """
        Delete multiple cache entries at once.

        Args:
            db: Database session
            cache_keys: List of cache keys to delete

        Returns:
            Number of entries deleted
        """
        try:
            entries = db.query(APICache).filter(APICache.query_key.in_(cache_keys)).all()

            count = len(entries)
            for entry in entries:
                db.delete(entry)

            db.commit()
            logger.info(f"Bulk deleted {count} cache entries")
            return count

        except Exception as e:
            logger.error(f"Error bulk deleting cache: {e}")
            db.rollback()
            return 0

    @staticmethod
    def clear_all_cache(db: Session) -> int:
        """
        Clear all cache entries (use with caution).

        Args:
            db: Database session

        Returns:
            Number of entries deleted
        """
        try:
            entries = db.query(APICache).all()
            count = len(entries)

            for entry in entries:
                db.delete(entry)

            db.commit()
            logger.warning(f"Cleared all {count} cache entries")
            return count

        except Exception as e:
            logger.error(f"Error clearing all cache: {e}")
            db.rollback()
            return 0

    @staticmethod
    def get_cache_by_type(db: Session, api_type: str, limit: int = 100, offset: int = 0):
        """
        Retrieve cache entries for a specific API type with pagination.

        Args:
            db: Database session
            api_type: API type to retrieve
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            Tuple of (entries list, total count)
        """
        try:
            query = db.query(APICache).filter(APICache.api_type == api_type)
            total = query.count()
            entries = query.offset(offset).limit(limit).all()

            return entries, total

        except Exception as e:
            logger.error(f"Error retrieving cache by type {api_type}: {e}")
            return [], 0


class TVShowService:
    """Service class for TV show operations"""

    @staticmethod
    def get_all_tv_shows(db: Session, limit: int = 10, offset: int = 0):
        """Get all TV shows with pagination"""
        query = db.query(TVShow)
        total = query.count()
        shows = query.offset(offset).limit(limit).all()
        return shows, total

    @staticmethod
    def get_tv_show_by_id(db: Session, show_id: int):
        """Get a specific TV show by ID"""
        show = db.query(TVShow).filter(TVShow.id == show_id).first()
        return show

    @staticmethod
    def get_tv_show_seasons(db: Session, show_id: int, limit: int = 10, offset: int = 0):
        """Get all seasons for a TV show"""
        # Verify show exists
        show = db.query(TVShow).filter(TVShow.id == show_id).first()
        if not show:
            return None, 0

        query = db.query(Season).filter(Season.show_id == show_id)
        total = query.count()
        seasons = query.offset(offset).limit(limit).all()
        return seasons, total

    @staticmethod
    def get_season_episodes(
        db: Session, show_id: int, season_id: int, limit: int = 10, offset: int = 0
    ):
        """Get all episodes for a season"""
        # Verify show and season exist
        show = db.query(TVShow).filter(TVShow.id == show_id).first()
        if not show:
            return None, 0

        season = db.query(Season).filter(Season.id == season_id, Season.show_id == show_id).first()
        if not season:
            return None, 0

        query = db.query(Episode).filter(Episode.season_id == season_id)
        total = query.count()
        episodes = query.offset(offset).limit(limit).all()
        return episodes, total

    @staticmethod
    def create_tv_show(db: Session, show_data: TVShowCreate):
        """Create a new TV show"""
        db_show = TVShow(
            title=show_data.title,
            plot=show_data.plot,
            rating=show_data.rating,
            genres=show_data.genres,
            status=show_data.status,
            tmdb_id=show_data.tmdb_id,
        )
        db.add(db_show)
        db.commit()
        db.refresh(db_show)
        logger.info(f"Created TV show: {db_show.id} - {db_show.title}")
        return db_show

    @staticmethod
    def update_tv_show(db: Session, show_id: int, show_data: TVShowUpdate):
        """Update an existing TV show"""
        db_show = db.query(TVShow).filter(TVShow.id == show_id).first()
        if not db_show:
            return None

        update_data = show_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_show, field, value)

        db.commit()
        db.refresh(db_show)
        logger.info(f"Updated TV show: {db_show.id} - {db_show.title}")
        return db_show

    @staticmethod
    def delete_tv_show(db: Session, show_id: int):
        """Delete a TV show"""
        db_show = db.query(TVShow).filter(TVShow.id == show_id).first()
        if not db_show:
            return False

        db.delete(db_show)
        db.commit()
        logger.info(f"Deleted TV show: {show_id}")
        return True
