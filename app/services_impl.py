"""Business logic layer for movies and TV shows"""

from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
from app.models import Movie, TVShow, Season, Episode, APICache
from app.schemas import MovieCreate, MovieUpdate, TVShowCreate, TVShowUpdate
from app.core.config import settings
import logging
import httpx
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)
external_api_logger = logging.getLogger("external_api")


def _mask_url(url: str) -> str:
    """Mask API keys in URLs for safe logging."""
    import re
    return re.sub(r'(apikey=)[^&]+', r'\1***', url)


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
        query = db.query(Movie).options(selectinload(Movie.files)).order_by(Movie.rating.desc().nullslast(), Movie.created_at.desc())
        total = query.count()
        movies = query.offset(offset).limit(limit).all()
        return movies, total

    @staticmethod
    def get_top_rated_movies(db: Session, limit: int = 10, offset: int = 0):
        """Return top-rated movies prioritizing highest rating and longest runtime."""
        query = db.query(Movie).options(selectinload(Movie.files)).order_by(
            Movie.rating.desc().nullslast(), Movie.runtime.desc().nullslast()
        )
        total = query.count()
        movies = query.offset(offset).limit(limit).all()
        return movies, total

    @staticmethod
    def get_movie_by_id(db: Session, movie_id: int):
        """Get a specific movie by ID"""
        movie = db.query(Movie).options(selectinload(Movie.files)).filter(Movie.id == movie_id).first()
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
            omdb_id=movie_data.omdb_id,
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
        search_query = db.query(Movie).options(selectinload(Movie.files)).filter(Movie.title.ilike(f"%{query}%"))
        total = search_query.count()
        movies = search_query.offset(offset).limit(limit).all()
        logger.info(f"Searched movies with query: {query}, found: {total}")
        return movies, total


class OMDBService:
    """Service class for OMDB API integration with rate limiting and caching"""

    # Class-level rate limiter
    _last_request_time: float = 0
    _rate_limit_lock = asyncio.Lock()

    OMDB_BASE_URL = "https://www.omdbapi.com/"
    SEARCH_ENDPOINT = "?s={title}&y={year}&type=movie&apikey={api_key}"
    DETAILS_ENDPOINT = "?i={omdb_id}&apikey={api_key}"

    @classmethod
    async def _rate_limit(cls) -> None:
        """Enforce rate limiting (1 request per second)"""
        async with cls._rate_limit_lock:
            elapsed = time.time() - cls._last_request_time
            if elapsed < 1.0:
                await asyncio.sleep(1.0 - elapsed)
            cls._last_request_time = time.time()

    @staticmethod
    def _get_cache_key(endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key from endpoint and parameters"""
        param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{endpoint}_{param_str}"

    @staticmethod
    def _get_cache(db: Session, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached API response if not expired"""
        cache_entry = (
            db.query(APICache)
            .filter(
                APICache.api_type == "omdb",
                APICache.query_key == cache_key,
                APICache.expires_at > datetime.utcnow(),
            )
            .first()
        )

        if cache_entry:
            external_api_logger.debug(
                f"OMDB cache HIT: {cache_key}",
                extra={"api_service": "omdb", "cache_key": cache_key, "cache_hit": True},
            )
            return json.loads(cache_entry.response_data)
        external_api_logger.debug(
            f"OMDB cache MISS: {cache_key}",
            extra={"api_service": "omdb", "cache_key": cache_key, "cache_hit": False},
        )
        return None

    @staticmethod
    def _set_cache(
        db: Session, cache_key: str, response_data: Dict[str, Any], ttl_seconds: int
    ) -> None:
        """Store API response in cache with TTL"""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

        # Check if cache entry already exists
        existing = (
            db.query(APICache)
            .filter(APICache.api_type == "omdb", APICache.query_key == cache_key)
            .first()
        )

        if existing:
            existing.response_data = json.dumps(response_data)
            existing.expires_at = expires_at
        else:
            cache_entry = APICache(
                api_type="omdb",
                query_key=cache_key,
                response_data=json.dumps(response_data),
                expires_at=expires_at,
            )
            db.add(cache_entry)

        db.commit()
        logger.info(f"Cached OMDB response for: {cache_key}")

    @staticmethod
    async def _make_request_with_retry(
        url: str, max_retries: int = 3, base_delay: float = 1.0
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request with exponential backoff retry logic"""
        masked_url = _mask_url(url)
        async with httpx.AsyncClient(timeout=10.0) as client:
            for attempt in range(max_retries):
                start_time = time.time()
                try:
                    external_api_logger.info(
                        f"OMDB >> GET {masked_url} (attempt {attempt + 1}/{max_retries})",
                        extra={"api_service": "omdb", "api_url": masked_url, "attempt": attempt + 1},
                    )

                    response = await client.get(url)
                    elapsed_ms = (time.time() - start_time) * 1000

                    external_api_logger.info(
                        f"OMDB << {response.status_code} in {elapsed_ms:.0f}ms "
                        f"({len(response.content)} bytes) {masked_url}",
                        extra={
                            "api_service": "omdb",
                            "api_url": masked_url,
                            "response_status": response.status_code,
                            "duration": elapsed_ms,
                            "response_size": len(response.content),
                        },
                    )

                    response.raise_for_status()
                    data = response.json()

                    # Check for OMDB API error response
                    if data.get("Response") == "False":
                        error_msg = data.get("Error", "Unknown error")
                        external_api_logger.warning(
                            f"OMDB API returned error: {error_msg}",
                            extra={"api_service": "omdb", "api_url": masked_url},
                        )
                        return None

                    return data

                except httpx.HTTPStatusError as e:
                    elapsed_ms = (time.time() - start_time) * 1000
                    if e.response.status_code == 429:  # Rate limited
                        delay = base_delay * (2**attempt)
                        external_api_logger.warning(
                            f"OMDB rate limited (429). Retrying in {delay}s (attempt {attempt + 1}/{max_retries})",
                            extra={"api_service": "omdb", "api_url": masked_url, "response_status": 429, "duration": elapsed_ms},
                        )
                        await asyncio.sleep(delay)
                    elif e.response.status_code >= 500:  # Server error
                        delay = base_delay * (2**attempt)
                        external_api_logger.warning(
                            f"OMDB server error ({e.response.status_code}). Retrying in {delay}s (attempt {attempt + 1}/{max_retries})",
                            extra={"api_service": "omdb", "api_url": masked_url, "response_status": e.response.status_code, "duration": elapsed_ms},
                        )
                        await asyncio.sleep(delay)
                    else:
                        external_api_logger.error(
                            f"OMDB HTTP error: {e.response.status_code} for {masked_url}",
                            extra={"api_service": "omdb", "api_url": masked_url, "response_status": e.response.status_code, "duration": elapsed_ms},
                        )
                        return None

                except httpx.RequestError as e:
                    elapsed_ms = (time.time() - start_time) * 1000
                    delay = base_delay * (2**attempt)
                    external_api_logger.warning(
                        f"OMDB request error: {e}. Retrying in {delay}s (attempt {attempt + 1}/{max_retries})",
                        extra={"api_service": "omdb", "api_url": masked_url, "duration": elapsed_ms},
                    )
                    await asyncio.sleep(delay)

                except json.JSONDecodeError as e:
                    external_api_logger.error(
                        f"Failed to parse OMDB response: {e}",
                        extra={"api_service": "omdb", "api_url": masked_url},
                    )
                    return None

            external_api_logger.error(
                f"OMDB request failed after {max_retries} attempts: {masked_url}",
                extra={"api_service": "omdb", "api_url": masked_url},
            )
            return None

    @classmethod
    async def search_movie(
        cls, db: Session, title: str, year: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Search for a movie by title and optional year.

        Args:
            db: Database session
            title: Movie title to search for
            year: Optional release year

        Returns:
            Search results or None if not found
        """
        if not settings.omdb_api_key:
            logger.error("OMDB_API_KEY not configured")
            return None

        # Generate cache key
        cache_params = {"title": title}
        if year:
            cache_params["year"] = year
        cache_key = cls._get_cache_key("search", cache_params)

        # Check cache first
        cached_result = cls._get_cache(db, cache_key)
        if cached_result:
            return cached_result

        # Apply rate limiting
        await cls._rate_limit()

        # Build URL
        url = cls.OMDB_BASE_URL + cls.SEARCH_ENDPOINT.format(
            title=title, year=year or "", api_key=settings.omdb_api_key
        )

        logger.info(f"Searching OMDB for movie: {title} (year: {year})")

        # Make request with retry logic
        result = await cls._make_request_with_retry(url)

        if result:
            # Cache the result
            cls._set_cache(db, cache_key, result, settings.omdb_cache_ttl)
            return result

        return None

    @classmethod
    async def get_movie_details(cls, db: Session, omdb_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a movie by OMDB ID.

        Args:
            db: Database session
            omdb_id: OMDB movie ID (e.g., "tt0111161")

        Returns:
            Movie details or None if not found
        """
        if not settings.omdb_api_key:
            logger.error("OMDB_API_KEY not configured")
            return None

        # Generate cache key
        cache_key = cls._get_cache_key("details", {"omdb_id": omdb_id})

        # Check cache first
        cached_result = cls._get_cache(db, cache_key)
        if cached_result:
            return cached_result

        # Apply rate limiting
        await cls._rate_limit()

        # Build URL
        url = cls.OMDB_BASE_URL + cls.DETAILS_ENDPOINT.format(
            omdb_id=omdb_id, api_key=settings.omdb_api_key
        )

        logger.info(f"Fetching OMDB details for: {omdb_id}")

        # Make request with retry logic
        result = await cls._make_request_with_retry(url)

        if result:
            # Cache the result
            cls._set_cache(db, cache_key, result, settings.omdb_cache_ttl)
            return result

        return None

    @staticmethod
    def parse_omdb_response(omdb_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse OMDB response into Movie model compatible format.

        Args:
            omdb_data: Raw OMDB API response

        Returns:
            Structured data compatible with Movie model
        """
        if not omdb_data or omdb_data.get("Response") == "False":
            return None

        try:
            # Handle search results
            if "Search" in omdb_data:
                results = []
                for item in omdb_data.get("Search", []):
                    results.append(
                        {
                            "title": item.get("Title"),
                            "year": (
                                int(item.get("Year", 0)) if item.get("Year", "").isdigit() else None
                            ),
                            "omdb_id": item.get("imdbID"),
                            "type": item.get("Type"),
                            "poster": item.get("Poster"),
                        }
                    )
                return {
                    "search_results": results,
                    "total_results": int(omdb_data.get("totalResults", 0)),
                }

            # Handle detailed response
            if "imdbID" in omdb_data:
                runtime_str = omdb_data.get("Runtime", "0 min")
                runtime_minutes = int(runtime_str.split()[0]) if runtime_str else 0

                rating_str = omdb_data.get("imdbRating", "N/A")
                rating = float(rating_str) if rating_str != "N/A" else None

                genres = omdb_data.get("Genre", "").split(", ") if omdb_data.get("Genre") else []

                return {
                    "title": omdb_data.get("Title"),
                    "year": (
                        int(omdb_data.get("Year", 0))
                        if omdb_data.get("Year", "").isdigit()
                        else None
                    ),
                    "omdb_id": omdb_data.get("imdbID"),
                    "plot": omdb_data.get("Plot"),
                    "rating": rating,
                    "runtime": runtime_minutes,
                    "genres": json.dumps(genres),
                    "director": omdb_data.get("Director"),
                    "actors": omdb_data.get("Actors"),
                    "type": omdb_data.get("Type"),
                    "poster": omdb_data.get("Poster"),
                }

            return None

        except (ValueError, KeyError, AttributeError) as e:
            logger.error(f"Error parsing OMDB response: {e}")
            return None


class TVDBService:
    """Service class for TVDB API integration with rate limiting and caching"""

    # Class-level rate limiter (3 requests per second)
    _last_request_time: float = 0
    _rate_limit_lock = asyncio.Lock()
    _auth_token: Optional[str] = None
    _token_expiry: Optional[datetime] = None

    TVDB_BASE_URL = "https://api4.thetvdb.com/v4"
    LOGIN_ENDPOINT = "/login"
    SEARCH_ENDPOINT = "/search?query={query}&type=series"
    SERIES_ENDPOINT = "/series/{tvdb_id}"
    SERIES_SEASONS_ENDPOINT = "/series/{tvdb_id}/seasons"
    SERIES_EPISODES_ENDPOINT = "/series/{tvdb_id}/episodes"

    @classmethod
    async def _rate_limit(cls) -> None:
        """Enforce rate limiting (3 requests per second)"""
        async with cls._rate_limit_lock:
            elapsed = time.time() - cls._last_request_time
            min_interval = 1.0 / settings.tvdb_rate_limit  # ~0.333 seconds for 3 req/sec
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            cls._last_request_time = time.time()

    @classmethod
    async def _get_auth_token(cls) -> Optional[str]:
        """Get or refresh TVDB authentication token"""
        if cls._auth_token and cls._token_expiry and datetime.utcnow() < cls._token_expiry:
            return cls._auth_token

        if not settings.tvdb_api_key or not settings.tvdb_pin:
            logger.error("TVDB_API_KEY or TVDB_PIN not configured")
            return None

        login_url = f"{cls.TVDB_BASE_URL}{cls.LOGIN_ENDPOINT}"
        try:
            start_time = time.time()
            external_api_logger.info(
                f"TVDB >> POST {login_url} (auth login)",
                extra={"api_service": "tvdb", "api_url": login_url},
            )

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    login_url,
                    json={"apikey": settings.tvdb_api_key, "pin": settings.tvdb_pin},
                )
                elapsed_ms = (time.time() - start_time) * 1000

                external_api_logger.info(
                    f"TVDB << {response.status_code} in {elapsed_ms:.0f}ms (auth login)",
                    extra={
                        "api_service": "tvdb",
                        "api_url": login_url,
                        "response_status": response.status_code,
                        "duration": elapsed_ms,
                    },
                )

                response.raise_for_status()
                data = response.json()

                if data.get("status") == "success" and "data" in data:
                    cls._auth_token = data["data"].get("token")
                    # Token typically valid for 24 hours, refresh after 23 hours
                    cls._token_expiry = datetime.utcnow() + timedelta(hours=23)
                    external_api_logger.info(
                        "TVDB auth token obtained successfully",
                        extra={"api_service": "tvdb"},
                    )
                    return cls._auth_token
                else:
                    external_api_logger.error(
                        f"TVDB authentication failed: {data.get('message', 'Unknown error')}",
                        extra={"api_service": "tvdb", "api_url": login_url},
                    )
                    return None

        except Exception as e:
            external_api_logger.error(
                f"TVDB authentication error: {e}",
                extra={"api_service": "tvdb", "api_url": login_url},
            )
            return None

    @staticmethod
    def _get_cache_key(endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key from endpoint and parameters"""
        param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{endpoint}_{param_str}"

    @staticmethod
    def _get_cache(db: Session, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached API response if not expired"""
        cache_entry = (
            db.query(APICache)
            .filter(
                APICache.api_type == "tvdb",
                APICache.query_key == cache_key,
                APICache.expires_at > datetime.utcnow(),
            )
            .first()
        )

        if cache_entry:
            external_api_logger.debug(
                f"TVDB cache HIT: {cache_key}",
                extra={"api_service": "tvdb", "cache_key": cache_key, "cache_hit": True},
            )
            return json.loads(cache_entry.response_data)
        external_api_logger.debug(
            f"TVDB cache MISS: {cache_key}",
            extra={"api_service": "tvdb", "cache_key": cache_key, "cache_hit": False},
        )
        return None

    @staticmethod
    def _set_cache(
        db: Session, cache_key: str, response_data: Dict[str, Any], ttl_seconds: int
    ) -> None:
        """Store API response in cache with TTL"""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

        # Check if cache entry already exists
        existing = (
            db.query(APICache)
            .filter(APICache.api_type == "tvdb", APICache.query_key == cache_key)
            .first()
        )

        if existing:
            existing.response_data = json.dumps(response_data)
            existing.expires_at = expires_at
        else:
            cache_entry = APICache(
                api_type="tvdb",
                query_key=cache_key,
                response_data=json.dumps(response_data),
                expires_at=expires_at,
            )
            db.add(cache_entry)

        db.commit()
        logger.info(f"Cached TVDB response for: {cache_key}")

    @staticmethod
    async def _make_request_with_retry(
        url: str, headers: Dict[str, str], max_retries: int = 3, base_delay: float = 1.0
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request with exponential backoff retry logic"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            for attempt in range(max_retries):
                start_time = time.time()
                try:
                    external_api_logger.info(
                        f"TVDB >> GET {url} (attempt {attempt + 1}/{max_retries})",
                        extra={"api_service": "tvdb", "api_url": url, "attempt": attempt + 1},
                    )

                    response = await client.get(url, headers=headers)
                    elapsed_ms = (time.time() - start_time) * 1000

                    external_api_logger.info(
                        f"TVDB << {response.status_code} in {elapsed_ms:.0f}ms "
                        f"({len(response.content)} bytes) {url}",
                        extra={
                            "api_service": "tvdb",
                            "api_url": url,
                            "response_status": response.status_code,
                            "duration": elapsed_ms,
                            "response_size": len(response.content),
                        },
                    )

                    response.raise_for_status()
                    data = response.json()

                    # Check for TVDB API error response
                    if data.get("status") != "success":
                        error_msg = data.get("message", "Unknown error")
                        external_api_logger.warning(
                            f"TVDB API returned error: {error_msg}",
                            extra={"api_service": "tvdb", "api_url": url},
                        )
                        return None

                    return data

                except httpx.HTTPStatusError as e:
                    elapsed_ms = (time.time() - start_time) * 1000
                    if e.response.status_code == 429:  # Rate limited
                        delay = base_delay * (2**attempt)
                        external_api_logger.warning(
                            f"TVDB rate limited (429). Retrying in {delay}s (attempt {attempt + 1}/{max_retries})",
                            extra={"api_service": "tvdb", "api_url": url, "response_status": 429, "duration": elapsed_ms},
                        )
                        await asyncio.sleep(delay)
                    elif e.response.status_code == 401:  # Unauthorized
                        external_api_logger.error(
                            "TVDB authentication failed (401)",
                            extra={"api_service": "tvdb", "api_url": url, "response_status": 401, "duration": elapsed_ms},
                        )
                        return None
                    elif e.response.status_code >= 500:  # Server error
                        delay = base_delay * (2**attempt)
                        external_api_logger.warning(
                            f"TVDB server error ({e.response.status_code}). Retrying in {delay}s (attempt {attempt + 1}/{max_retries})",
                            extra={"api_service": "tvdb", "api_url": url, "response_status": e.response.status_code, "duration": elapsed_ms},
                        )
                        await asyncio.sleep(delay)
                    else:
                        external_api_logger.error(
                            f"TVDB HTTP error: {e.response.status_code} for {url}",
                            extra={"api_service": "tvdb", "api_url": url, "response_status": e.response.status_code, "duration": elapsed_ms},
                        )
                        return None

                except httpx.RequestError as e:
                    elapsed_ms = (time.time() - start_time) * 1000
                    delay = base_delay * (2**attempt)
                    external_api_logger.warning(
                        f"TVDB request error: {e}. Retrying in {delay}s (attempt {attempt + 1}/{max_retries})",
                        extra={"api_service": "tvdb", "api_url": url, "duration": elapsed_ms},
                    )
                    await asyncio.sleep(delay)

                except json.JSONDecodeError as e:
                    external_api_logger.error(
                        f"Failed to parse TVDB response: {e}",
                        extra={"api_service": "tvdb", "api_url": url},
                    )
                    return None

            external_api_logger.error(
                f"TVDB request failed after {max_retries} attempts: {url}",
                extra={"api_service": "tvdb", "api_url": url},
            )
            return None

    @classmethod
    async def search_show(cls, db: Session, title: str) -> Optional[Dict[str, Any]]:
        """
        Search for a TV show by title.

        Args:
            db: Database session
            title: TV show title to search for

        Returns:
            Search results or None if not found
        """
        # Get authentication token
        token = await cls._get_auth_token()
        if not token:
            return None

        # Generate cache key
        cache_key = cls._get_cache_key("search", {"title": title})

        # Check cache first
        cached_result = cls._get_cache(db, cache_key)
        if cached_result:
            return cached_result

        # Apply rate limiting
        await cls._rate_limit()

        # Build URL
        url = cls.TVDB_BASE_URL + cls.SEARCH_ENDPOINT.format(query=title)
        headers = {"Authorization": f"Bearer {token}"}

        logger.info(f"Searching TVDB for show: {title}")

        # Make request with retry logic
        result = await cls._make_request_with_retry(url, headers)

        if result:
            # Cache the result
            cls._set_cache(db, cache_key, result, settings.tvdb_cache_ttl)
            return result

        return None

    @classmethod
    async def get_series_details(cls, db: Session, tvdb_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a TV series by TVDB ID.

        Args:
            db: Database session
            tvdb_id: TVDB series ID

        Returns:
            Series details or None if not found
        """
        # Get authentication token
        token = await cls._get_auth_token()
        if not token:
            return None

        # Generate cache key
        cache_key = cls._get_cache_key("series_details", {"tvdb_id": tvdb_id})

        # Check cache first
        cached_result = cls._get_cache(db, cache_key)
        if cached_result:
            return cached_result

        # Apply rate limiting
        await cls._rate_limit()

        # Build URL
        url = cls.TVDB_BASE_URL + cls.SERIES_ENDPOINT.format(tvdb_id=tvdb_id)
        headers = {"Authorization": f"Bearer {token}"}

        logger.info(f"Fetching TVDB series details for: {tvdb_id}")

        # Make request with retry logic
        result = await cls._make_request_with_retry(url, headers)

        if result:
            # Cache the result
            cls._set_cache(db, cache_key, result, settings.tvdb_cache_ttl)
            return result

        return None

    @classmethod
    async def get_seasons(cls, db: Session, tvdb_id: str) -> Optional[Dict[str, Any]]:
        """
        Get all seasons for a TV series.

        Args:
            db: Database session
            tvdb_id: TVDB series ID

        Returns:
            Seasons data or None if not found
        """
        # Get authentication token
        token = await cls._get_auth_token()
        if not token:
            return None

        # Generate cache key
        cache_key = cls._get_cache_key("seasons", {"tvdb_id": tvdb_id})

        # Check cache first
        cached_result = cls._get_cache(db, cache_key)
        if cached_result:
            return cached_result

        # Apply rate limiting
        await cls._rate_limit()

        # Build URL
        url = cls.TVDB_BASE_URL + cls.SERIES_SEASONS_ENDPOINT.format(tvdb_id=tvdb_id)
        headers = {"Authorization": f"Bearer {token}"}

        logger.info(f"Fetching TVDB seasons for series: {tvdb_id}")

        # Make request with retry logic
        result = await cls._make_request_with_retry(url, headers)

        if result:
            # Cache the result
            cls._set_cache(db, cache_key, result, settings.tvdb_cache_ttl)
            return result

        return None

    @classmethod
    async def get_episodes(
        cls, db: Session, tvdb_id: str, season_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get all episodes for a specific season.

        Args:
            db: Database session
            tvdb_id: TVDB series ID
            season_number: Season number

        Returns:
            Episodes data or None if not found
        """
        # Get authentication token
        token = await cls._get_auth_token()
        if not token:
            return None

        # Generate cache key
        cache_key = cls._get_cache_key("episodes", {"tvdb_id": tvdb_id, "season": season_number})

        # Check cache first
        cached_result = cls._get_cache(db, cache_key)
        if cached_result:
            return cached_result

        # Apply rate limiting
        await cls._rate_limit()

        # Build URL - TVDB v4 API uses query parameter for season filtering
        url = cls.TVDB_BASE_URL + cls.SERIES_EPISODES_ENDPOINT.format(tvdb_id=tvdb_id)
        url += f"?season={season_number}"
        headers = {"Authorization": f"Bearer {token}"}

        logger.info(f"Fetching TVDB episodes for series {tvdb_id}, season {season_number}")

        # Make request with retry logic
        result = await cls._make_request_with_retry(url, headers)

        if result:
            # Cache the result
            cls._set_cache(db, cache_key, result, settings.tvdb_cache_ttl)
            return result

        return None

    @staticmethod
    def parse_tvdb_search_response(
        tvdb_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Parse TVDB search response into structured format.

        Args:
            tvdb_data: Raw TVDB API response

        Returns:
            Structured data compatible with TVShow model
        """
        if not tvdb_data or tvdb_data.get("status") != "success":
            return None

        try:
            results = []
            for item in tvdb_data.get("data", []):
                results.append(
                    {
                        "tvdb_id": str(item.get("id")),
                        "title": item.get("name"),
                        "plot": item.get("overview"),
                        "status": item.get("status"),
                        "first_air_date": item.get("first_air_date"),
                        "poster": item.get("image_url"),
                        "type": item.get("type"),
                    }
                )
            return {"search_results": results, "total_results": len(results)}

        except (ValueError, KeyError, AttributeError) as e:
            logger.error(f"Error parsing TVDB search response: {e}")
            return None

    @staticmethod
    def parse_tvdb_series_response(
        tvdb_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Parse TVDB series details response into TVShow model compatible format.

        Args:
            tvdb_data: Raw TVDB API response

        Returns:
            Structured data compatible with TVShow model
        """
        if not tvdb_data or tvdb_data.get("status") != "success":
            return None

        try:
            series = tvdb_data.get("data", {})
            rating = float(series.get("score", 0)) if series.get("score") else None
            genres = series.get("genres", []) if isinstance(series.get("genres"), list) else []

            return {
                "tvdb_id": str(series.get("id")),
                "title": series.get("name"),
                "plot": series.get("overview"),
                "rating": rating,
                "status": series.get("status"),
                "genres": json.dumps(genres),
                "first_air_date": series.get("first_air_date"),
                "last_air_date": series.get("last_air_date"),
                "poster": series.get("image_url"),
                "network": series.get("network"),
                "country": series.get("country"),
            }

        except (ValueError, KeyError, AttributeError) as e:
            logger.error(f"Error parsing TVDB series response: {e}")
            return None

    @staticmethod
    def parse_tvdb_seasons_response(
        tvdb_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Parse TVDB seasons response into structured format.

        Args:
            tvdb_data: Raw TVDB API response

        Returns:
            Structured seasons data
        """
        if not tvdb_data or tvdb_data.get("status") != "success":
            return None

        try:
            seasons = []
            for item in tvdb_data.get("data", []):
                seasons.append(
                    {
                        "tvdb_id": str(item.get("id")),
                        "season_number": item.get("number"),
                        "episode_count": item.get("episodes", 0),
                    }
                )
            return {"seasons": seasons, "total_seasons": len(seasons)}

        except (ValueError, KeyError, AttributeError) as e:
            logger.error(f"Error parsing TVDB seasons response: {e}")
            return None

    @staticmethod
    def parse_tvdb_episodes_response(
        tvdb_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Parse TVDB episodes response into structured format.

        Args:
            tvdb_data: Raw TVDB API response

        Returns:
            Structured episodes data
        """
        if not tvdb_data or tvdb_data.get("status") != "success":
            return None

        try:
            episodes = []
            for item in tvdb_data.get("data", []):
                rating = float(item.get("score", 0)) if item.get("score") else None
                episodes.append(
                    {
                        "tvdb_id": str(item.get("id")),
                        "episode_number": item.get("number"),
                        "title": item.get("name"),
                        "plot": item.get("overview"),
                        "air_date": item.get("aired"),
                        "rating": rating,
                        "runtime": item.get("runtime"),
                    }
                )
            return {"episodes": episodes, "total_episodes": len(episodes)}

        except (ValueError, KeyError, AttributeError) as e:
            logger.error(f"Error parsing TVDB episodes response: {e}")
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
            tvdb_id=show_data.tvdb_id,
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
