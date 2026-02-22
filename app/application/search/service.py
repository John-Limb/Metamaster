"""Search and filtering service for movies and TV shows"""

import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, func
from app.models import Movie, TVShow

logger = logging.getLogger(__name__)


class SearchFilters:
    """Data class for search filter parameters"""

    def __init__(
        self,
        genre: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        year: Optional[int] = None,
        sort_by: str = "title",
        skip: int = 0,
        limit: int = 10,
        enrichment_statuses: Optional[List[str]] = None,
    ):
        """
        Initialize search filters

        Args:
            genre: Genre to filter by (case-insensitive)
            min_rating: Minimum rating (0-10)
            max_rating: Maximum rating (0-10)
            year: Release/air year to filter by
            sort_by: Field to sort by (title, rating, year, date_added)
            skip: Number of items to skip (pagination)
            limit: Number of items to return (pagination)
            enrichment_statuses: List of enrichment_status values to include
        """
        self.genre = genre.lower() if genre else None
        self.min_rating = min_rating
        self.max_rating = max_rating
        self.year = year
        self.sort_by = sort_by
        self.skip = skip
        self.limit = limit
        self.enrichment_statuses = enrichment_statuses

    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Validate filter parameters

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate ratings
        if self.min_rating is not None:
            if not (0 <= self.min_rating <= 10):
                return False, "min_rating must be between 0 and 10"

        if self.max_rating is not None:
            if not (0 <= self.max_rating <= 10):
                return False, "max_rating must be between 0 and 10"

        # Validate min/max relationship
        if self.min_rating is not None and self.max_rating is not None:
            if self.min_rating > self.max_rating:
                return False, "min_rating cannot be greater than max_rating"

        # Validate year
        if self.year is not None:
            if not (1800 <= self.year <= 2100):
                return False, "year must be between 1800 and 2100"

        # Validate pagination
        if self.skip < 0:
            return False, "skip must be non-negative"

        if not (1 <= self.limit <= 100):
            return False, "limit must be between 1 and 100"

        # Validate sort_by
        valid_sort_fields = ["title", "rating", "year", "date_added"]
        if self.sort_by not in valid_sort_fields:
            return False, f"sort_by must be one of: {', '.join(valid_sort_fields)}"

        return True, None


class MovieSearchService:
    """Service for searching and filtering movies"""

    @staticmethod
    def _parse_genres(genres_str: Optional[str]) -> List[str]:
        """Parse genres from JSON string"""
        if not genres_str:
            return []
        try:
            return json.loads(genres_str)
        except (json.JSONDecodeError, TypeError):
            return []

    @staticmethod
    def _genre_matches(movie_genres: Optional[str], search_genre: str) -> bool:
        """Check if movie genres contain the search genre"""
        genres = MovieSearchService._parse_genres(movie_genres)
        return any(search_genre.lower() in g.lower() for g in genres)

    @staticmethod
    def search(
        db: Session,
        filters: SearchFilters,
    ) -> Tuple[List[Movie], int]:
        """
        Search movies with filters and sorting

        Args:
            db: Database session
            filters: SearchFilters object with filter parameters

        Returns:
            Tuple of (movies, total_count)
        """
        # Validate filters
        is_valid, error_msg = filters.validate()
        if not is_valid:
            logger.warning(f"Invalid search filters: {error_msg}")
            return [], 0

        # Start with base query
        query = db.query(Movie).options(selectinload(Movie.files))

        # Apply genre filter
        if filters.genre:
            # Get all movies and filter in Python (since genres are JSON strings)
            all_movies = query.all()
            filtered_movies = [
                m
                for m in all_movies
                if MovieSearchService._genre_matches(m.genres, filters.genre)
            ]
            # Convert back to query for further filtering
            if filtered_movies:
                movie_ids = [m.id for m in filtered_movies]
                query = db.query(Movie).options(selectinload(Movie.files)).filter(Movie.id.in_(movie_ids))
            else:
                return [], 0

        # Apply rating filters
        if filters.min_rating is not None:
            query = query.filter(Movie.rating >= filters.min_rating)

        if filters.max_rating is not None:
            query = query.filter(Movie.rating <= filters.max_rating)

        # Apply year filter
        if filters.year is not None:
            query = query.filter(Movie.year == filters.year)

        # Apply enrichment status filter
        if filters.enrichment_statuses:
            query = query.filter(Movie.enrichment_status.in_(filters.enrichment_statuses))

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        if filters.sort_by == "title":
            query = query.order_by(Movie.title.asc())
        elif filters.sort_by == "rating":
            query = query.order_by(Movie.rating.desc().nullslast())
        elif filters.sort_by == "year":
            query = query.order_by(Movie.year.desc().nullslast())
        elif filters.sort_by == "date_added":
            query = query.order_by(Movie.created_at.desc())

        # Apply pagination
        movies = query.offset(filters.skip).limit(filters.limit).all()

        logger.info(
            f"Movie search completed: genre={filters.genre}, "
            f"min_rating={filters.min_rating}, max_rating={filters.max_rating}, "
            f"year={filters.year}, sort_by={filters.sort_by}, "
            f"total={total}, returned={len(movies)}"
        )

        return movies, total


class TVShowSearchService:
    """Service for searching and filtering TV shows"""

    @staticmethod
    def _parse_genres(genres_str: Optional[str]) -> List[str]:
        """Parse genres from JSON string"""
        if not genres_str:
            return []
        try:
            return json.loads(genres_str)
        except (json.JSONDecodeError, TypeError):
            return []

    @staticmethod
    def _genre_matches(show_genres: Optional[str], search_genre: str) -> bool:
        """Check if show genres contain the search genre"""
        genres = TVShowSearchService._parse_genres(show_genres)
        return any(search_genre.lower() in g.lower() for g in genres)

    @staticmethod
    def search(
        db: Session,
        filters: SearchFilters,
    ) -> Tuple[List[TVShow], int]:
        """
        Search TV shows with filters and sorting

        Args:
            db: Database session
            filters: SearchFilters object with filter parameters

        Returns:
            Tuple of (tv_shows, total_count)
        """
        # Validate filters
        is_valid, error_msg = filters.validate()
        if not is_valid:
            logger.warning(f"Invalid search filters: {error_msg}")
            return [], 0

        # Start with base query
        query = db.query(TVShow)

        # Apply genre filter
        if filters.genre:
            # Get all shows and filter in Python (since genres are JSON strings)
            all_shows = query.all()
            filtered_shows = [
                s
                for s in all_shows
                if TVShowSearchService._genre_matches(s.genres, filters.genre)
            ]
            # Convert back to query for further filtering
            if filtered_shows:
                show_ids = [s.id for s in filtered_shows]
                query = db.query(TVShow).filter(TVShow.id.in_(show_ids))
            else:
                return [], 0

        # Apply rating filters
        if filters.min_rating is not None:
            query = query.filter(TVShow.rating >= filters.min_rating)

        if filters.max_rating is not None:
            query = query.filter(TVShow.rating <= filters.max_rating)

        # Note: TVShow doesn't have a year field, so year filter is skipped
        # (year filtering is only for movies)

        # Apply enrichment status filter
        if filters.enrichment_statuses:
            query = query.filter(TVShow.enrichment_status.in_(filters.enrichment_statuses))

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        if filters.sort_by == "title":
            query = query.order_by(TVShow.title.asc())
        elif filters.sort_by == "rating":
            query = query.order_by(TVShow.rating.desc().nullslast())
        elif filters.sort_by == "year":
            # TV shows don't have year, so fall back to title
            query = query.order_by(TVShow.title.asc())
        elif filters.sort_by == "date_added":
            query = query.order_by(TVShow.created_at.desc())

        # Apply pagination
        shows = query.offset(filters.skip).limit(filters.limit).all()

        logger.info(
            f"TV show search completed: genre={filters.genre}, "
            f"min_rating={filters.min_rating}, max_rating={filters.max_rating}, "
            f"sort_by={filters.sort_by}, "
            f"total={total}, returned={len(shows)}"
        )

        return shows, total
