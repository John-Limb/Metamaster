"""Tests for search and filtering service"""

import json

import pytest
from sqlalchemy.orm import Session

from app.application.search.service import MovieSearchService, SearchFilters, TVShowSearchService
from app.database import Base, engine
from app.models import Movie, TVShow


@pytest.fixture
def db():
    """Create a test database session"""
    Base.metadata.create_all(bind=engine)
    from app.database import SessionLocal

    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_movies(db: Session):
    """Create sample movies for testing"""
    movies = [
        Movie(
            title="The Shawshank Redemption",
            year=1994,
            rating=9.3,
            genres=json.dumps(["Drama"]),
            plot="Two imprisoned men bond over a number of years...",
            tmdb_id="tt0111161",
        ),
        Movie(
            title="The Godfather",
            year=1972,
            rating=9.2,
            genres=json.dumps(["Crime", "Drama"]),
            plot="The aging patriarch of an organized crime dynasty...",
            tmdb_id="tt0068646",
        ),
        Movie(
            title="The Dark Knight",
            year=2008,
            rating=9.0,
            genres=json.dumps(["Action", "Crime", "Drama"]),
            plot="When the menace known as the Joker wreaks havoc...",
            tmdb_id="tt0468569",
        ),
        Movie(
            title="Pulp Fiction",
            year=1994,
            rating=8.9,
            genres=json.dumps(["Crime", "Drama"]),
            plot="The lives of two mob hitmen, a boxer, a gangster...",
            tmdb_id="tt0110912",
        ),
        Movie(
            title="Forrest Gump",
            year=1994,
            rating=8.8,
            genres=json.dumps(["Drama", "Romance"]),
            plot="The presidencies of Kennedy and Johnson unfold...",
            tmdb_id="tt0109830",
        ),
        Movie(
            title="Inception",
            year=2010,
            rating=8.8,
            genres=json.dumps(["Action", "Sci-Fi", "Thriller"]),
            plot="A skilled thief who steals corporate secrets...",
            tmdb_id="tt1375666",
        ),
        Movie(
            title="The Matrix",
            year=1999,
            rating=8.7,
            genres=json.dumps(["Action", "Sci-Fi"]),
            plot="A computer hacker learns from mysterious rebels...",
            tmdb_id="tt0133093",
        ),
        Movie(
            title="Interstellar",
            year=2014,
            rating=8.6,
            genres=json.dumps(["Adventure", "Drama", "Sci-Fi"]),
            plot="A team of explorers travel through a wormhole...",
            tmdb_id="tt0816692",
        ),
        Movie(
            title="The Avengers",
            year=2012,
            rating=8.0,
            genres=json.dumps(["Action", "Adventure", "Sci-Fi"]),
            plot="Earth's mightiest heroes must come together...",
            tmdb_id="tt0848228",
        ),
        Movie(
            title="Avatar",
            year=2009,
            rating=7.8,
            genres=json.dumps(["Action", "Adventure", "Fantasy"]),
            plot="A paraplegic Marine dispatched to the moon Pandora...",
            tmdb_id="tt0499549",
        ),
    ]

    for movie in movies:
        db.add(movie)
    db.commit()

    return movies


@pytest.fixture
def sample_tv_shows(db: Session):
    """Create sample TV shows for testing"""
    shows = [
        TVShow(
            title="Breaking Bad",
            rating=9.5,
            genres=json.dumps(["Crime", "Drama", "Thriller"]),
            plot="A high school chemistry teacher...",
            tmdb_id="81189",
            status="Ended",
        ),
        TVShow(
            title="Game of Thrones",
            rating=9.2,
            genres=json.dumps(["Action", "Adventure", "Drama"]),
            plot="Nine noble families fight for control...",
            tmdb_id="121361",
            status="Ended",
        ),
        TVShow(
            title="The Office",
            rating=9.0,
            genres=json.dumps(["Comedy"]),
            plot="A mockumentary on a group of typical office workers...",
            tmdb_id="6091",
            status="Ended",
        ),
        TVShow(
            title="Stranger Things",
            rating=8.7,
            genres=json.dumps(["Drama", "Fantasy", "Horror"]),
            plot="When a young boy disappears, his friends...",
            tmdb_id="121688",
            status="Continuing",
        ),
        TVShow(
            title="The Crown",
            rating=8.6,
            genres=json.dumps(["Biography", "Drama", "History"]),
            plot="Follows the political rivalries and romance...",
            tmdb_id="270680",
            status="Ended",
        ),
        TVShow(
            title="Friends",
            rating=8.9,
            genres=json.dumps(["Comedy", "Romance"]),
            plot="Follows the personal and professional lives...",
            tmdb_id="1668",
            status="Ended",
        ),
        TVShow(
            title="The Mandalorian",
            rating=8.7,
            genres=json.dumps(["Action", "Adventure", "Sci-Fi"]),
            plot="After the fall of the Empire, a lone gunfighter...",
            tmdb_id="349232",
            status="Continuing",
        ),
        TVShow(
            title="Sherlock",
            rating=9.1,
            genres=json.dumps(["Crime", "Drama", "Mystery"]),
            plot="A modern update finds the famous sleuth...",
            tmdb_id="121362",
            status="Ended",
        ),
    ]

    for show in shows:
        db.add(show)
    db.commit()

    return shows


# ============================================================================
# SearchFilters Validation Tests
# ============================================================================


class TestSearchFiltersValidation:
    """Test SearchFilters validation"""

    def test_valid_filters(self):
        """Test valid filter parameters"""
        filters = SearchFilters(
            genre="Drama",
            min_rating=7.0,
            max_rating=9.0,
            year=2020,
            sort_by="rating",
            skip=0,
            limit=10,
        )
        is_valid, error_msg = filters.validate()
        assert is_valid
        assert error_msg is None

    def test_invalid_min_rating(self):
        """Test invalid minimum rating"""
        filters = SearchFilters(min_rating=-1)
        is_valid, error_msg = filters.validate()
        assert not is_valid
        assert "min_rating" in error_msg

    def test_invalid_max_rating(self):
        """Test invalid maximum rating"""
        filters = SearchFilters(max_rating=11)
        is_valid, error_msg = filters.validate()
        assert not is_valid
        assert "max_rating" in error_msg

    def test_min_greater_than_max_rating(self):
        """Test min_rating greater than max_rating"""
        filters = SearchFilters(min_rating=8.0, max_rating=6.0)
        is_valid, error_msg = filters.validate()
        assert not is_valid
        assert "min_rating" in error_msg and "max_rating" in error_msg

    def test_invalid_year(self):
        """Test invalid year"""
        filters = SearchFilters(year=1700)
        is_valid, error_msg = filters.validate()
        assert not is_valid
        assert "year" in error_msg

    def test_invalid_skip(self):
        """Test invalid skip value"""
        filters = SearchFilters(skip=-1)
        is_valid, error_msg = filters.validate()
        assert not is_valid
        assert "skip" in error_msg

    def test_invalid_limit(self):
        """Test invalid limit value"""
        filters = SearchFilters(limit=0)
        is_valid, error_msg = filters.validate()
        assert not is_valid
        assert "limit" in error_msg

        filters = SearchFilters(limit=101)
        is_valid, error_msg = filters.validate()
        assert not is_valid
        assert "limit" in error_msg

    def test_invalid_sort_by(self):
        """Test invalid sort_by field"""
        filters = SearchFilters(sort_by="invalid_field")
        is_valid, error_msg = filters.validate()
        assert not is_valid
        assert "sort_by" in error_msg


# ============================================================================
# Movie Search Tests
# ============================================================================


class TestMovieSearch:
    """Test movie search and filtering"""

    def test_search_all_movies(self, db: Session, sample_movies):
        """Test retrieving all movies without filters"""
        filters = SearchFilters(skip=0, limit=100)
        movies, total = MovieSearchService.search(db, filters)
        assert len(movies) == 10
        assert total == 10

    def test_search_by_genre(self, db: Session, sample_movies):
        """Test filtering movies by genre"""
        filters = SearchFilters(genre="Drama", skip=0, limit=100)
        movies, total = MovieSearchService.search(db, filters)
        assert total > 0
        # All returned movies should have Drama genre
        for movie in movies:
            genres = json.loads(movie.genres)
            assert "Drama" in genres

    def test_search_by_genre_case_insensitive(self, db: Session, sample_movies):
        """Test genre filtering is case-insensitive"""
        filters_lower = SearchFilters(genre="drama", skip=0, limit=100)
        movies_lower, total_lower = MovieSearchService.search(db, filters_lower)

        filters_upper = SearchFilters(genre="DRAMA", skip=0, limit=100)
        movies_upper, total_upper = MovieSearchService.search(db, filters_upper)

        assert total_lower == total_upper
        assert len(movies_lower) == len(movies_upper)

    def test_search_by_min_rating(self, db: Session, sample_movies):
        """Test filtering movies by minimum rating"""
        filters = SearchFilters(min_rating=9.0, skip=0, limit=100)
        movies, total = MovieSearchService.search(db, filters)
        assert total > 0
        # All returned movies should have rating >= 9.0
        for movie in movies:
            assert movie.rating >= 9.0

    def test_search_by_max_rating(self, db: Session, sample_movies):
        """Test filtering movies by maximum rating"""
        filters = SearchFilters(max_rating=8.0, skip=0, limit=100)
        movies, total = MovieSearchService.search(db, filters)
        assert total > 0
        # All returned movies should have rating <= 8.0
        for movie in movies:
            assert movie.rating <= 8.0

    def test_search_by_rating_range(self, db: Session, sample_movies):
        """Test filtering movies by rating range"""
        filters = SearchFilters(min_rating=8.5, max_rating=9.0, skip=0, limit=100)
        movies, total = MovieSearchService.search(db, filters)
        assert total > 0
        # All returned movies should have rating between 8.5 and 9.0
        for movie in movies:
            assert 8.5 <= movie.rating <= 9.0

    def test_search_by_year(self, db: Session, sample_movies):
        """Test filtering movies by year"""
        filters = SearchFilters(year=1994, skip=0, limit=100)
        movies, total = MovieSearchService.search(db, filters)
        assert total == 3  # Shawshank, Pulp Fiction, Forrest Gump
        # All returned movies should be from 1994
        for movie in movies:
            assert movie.year == 1994

    def test_search_combined_filters(self, db: Session, sample_movies):
        """Test combining multiple filters"""
        filters = SearchFilters(genre="Drama", min_rating=8.5, year=1994, skip=0, limit=100)
        movies, total = MovieSearchService.search(db, filters)
        assert total > 0
        # All returned movies should match all criteria
        for movie in movies:
            genres = json.loads(movie.genres)
            assert "Drama" in genres
            assert movie.rating >= 8.5
            assert movie.year == 1994

    def test_search_sort_by_title(self, db: Session, sample_movies):
        """Test sorting by title"""
        filters = SearchFilters(sort_by="title", skip=0, limit=100)
        movies, total = MovieSearchService.search(db, filters)
        titles = [m.title for m in movies]
        assert titles == sorted(titles)

    def test_search_sort_by_rating(self, db: Session, sample_movies):
        """Test sorting by rating (descending)"""
        filters = SearchFilters(sort_by="rating", skip=0, limit=100)
        movies, total = MovieSearchService.search(db, filters)
        ratings = [m.rating for m in movies if m.rating is not None]
        assert ratings == sorted(ratings, reverse=True)

    def test_search_sort_by_year(self, db: Session, sample_movies):
        """Test sorting by year (descending)"""
        filters = SearchFilters(sort_by="year", skip=0, limit=100)
        movies, total = MovieSearchService.search(db, filters)
        years = [m.year for m in movies if m.year is not None]
        assert years == sorted(years, reverse=True)

    def test_search_sort_by_date_added(self, db: Session, sample_movies):
        """Test sorting by date added (descending)"""
        filters = SearchFilters(sort_by="date_added", skip=0, limit=100)
        movies, total = MovieSearchService.search(db, filters)
        dates = [m.created_at for m in movies]
        assert dates == sorted(dates, reverse=True)

    def test_search_pagination(self, db: Session, sample_movies):
        """Test pagination"""
        # Get first page
        filters_page1 = SearchFilters(skip=0, limit=3)
        movies_page1, total = MovieSearchService.search(db, filters_page1)
        assert len(movies_page1) == 3
        assert total == 10

        # Get second page
        filters_page2 = SearchFilters(skip=3, limit=3)
        movies_page2, total = MovieSearchService.search(db, filters_page2)
        assert len(movies_page2) == 3

        # Ensure pages don't overlap
        ids_page1 = {m.id for m in movies_page1}
        ids_page2 = {m.id for m in movies_page2}
        assert len(ids_page1 & ids_page2) == 0

    def test_search_no_results(self, db: Session, sample_movies):
        """Test search with no results"""
        filters = SearchFilters(genre="NonexistentGenre", skip=0, limit=100)
        movies, total = MovieSearchService.search(db, filters)
        assert len(movies) == 0
        assert total == 0


# ============================================================================
# TV Show Search Tests
# ============================================================================


class TestTVShowSearch:
    """Test TV show search and filtering"""

    def test_search_all_shows(self, db: Session, sample_tv_shows):
        """Test retrieving all TV shows without filters"""
        filters = SearchFilters(skip=0, limit=100)
        shows, total = TVShowSearchService.search(db, filters)
        assert len(shows) == 8
        assert total == 8

    def test_search_by_genre(self, db: Session, sample_tv_shows):
        """Test filtering TV shows by genre"""
        filters = SearchFilters(genre="Drama", skip=0, limit=100)
        shows, total = TVShowSearchService.search(db, filters)
        assert total > 0
        # All returned shows should have Drama genre
        for show in shows:
            genres = json.loads(show.genres)
            assert "Drama" in genres

    def test_search_by_min_rating(self, db: Session, sample_tv_shows):
        """Test filtering TV shows by minimum rating"""
        filters = SearchFilters(min_rating=9.0, skip=0, limit=100)
        shows, total = TVShowSearchService.search(db, filters)
        assert total > 0
        # All returned shows should have rating >= 9.0
        for show in shows:
            assert show.rating >= 9.0

    def test_search_by_max_rating(self, db: Session, sample_tv_shows):
        """Test filtering TV shows by maximum rating"""
        filters = SearchFilters(max_rating=8.7, skip=0, limit=100)
        shows, total = TVShowSearchService.search(db, filters)
        assert total > 0
        # All returned shows should have rating <= 8.7
        for show in shows:
            assert show.rating <= 8.7

    def test_search_by_rating_range(self, db: Session, sample_tv_shows):
        """Test filtering TV shows by rating range"""
        filters = SearchFilters(min_rating=8.5, max_rating=9.0, skip=0, limit=100)
        shows, total = TVShowSearchService.search(db, filters)
        assert total > 0
        # All returned shows should have rating between 8.5 and 9.0
        for show in shows:
            assert 8.5 <= show.rating <= 9.0

    def test_search_combined_filters(self, db: Session, sample_tv_shows):
        """Test combining multiple filters"""
        filters = SearchFilters(genre="Drama", min_rating=8.5, skip=0, limit=100)
        shows, total = TVShowSearchService.search(db, filters)
        assert total > 0
        # All returned shows should match all criteria
        for show in shows:
            genres = json.loads(show.genres)
            assert "Drama" in genres
            assert show.rating >= 8.5

    def test_search_sort_by_title(self, db: Session, sample_tv_shows):
        """Test sorting by title"""
        filters = SearchFilters(sort_by="title", skip=0, limit=100)
        shows, total = TVShowSearchService.search(db, filters)
        titles = [s.title for s in shows]
        assert titles == sorted(titles)

    def test_search_sort_by_rating(self, db: Session, sample_tv_shows):
        """Test sorting by rating (descending)"""
        filters = SearchFilters(sort_by="rating", skip=0, limit=100)
        shows, total = TVShowSearchService.search(db, filters)
        ratings = [s.rating for s in shows if s.rating is not None]
        assert ratings == sorted(ratings, reverse=True)

    def test_search_sort_by_date_added(self, db: Session, sample_tv_shows):
        """Test sorting by date added (descending)"""
        filters = SearchFilters(sort_by="date_added", skip=0, limit=100)
        shows, total = TVShowSearchService.search(db, filters)
        dates = [s.created_at for s in shows]
        assert dates == sorted(dates, reverse=True)

    def test_search_pagination(self, db: Session, sample_tv_shows):
        """Test pagination"""
        # Get first page
        filters_page1 = SearchFilters(skip=0, limit=3)
        shows_page1, total = TVShowSearchService.search(db, filters_page1)
        assert len(shows_page1) == 3
        assert total == 8

        # Get second page
        filters_page2 = SearchFilters(skip=3, limit=3)
        shows_page2, total = TVShowSearchService.search(db, filters_page2)
        assert len(shows_page2) == 3

        # Ensure pages don't overlap
        ids_page1 = {s.id for s in shows_page1}
        ids_page2 = {s.id for s in shows_page2}
        assert len(ids_page1 & ids_page2) == 0

    def test_search_no_results(self, db: Session, sample_tv_shows):
        """Test search with no results"""
        filters = SearchFilters(genre="NonexistentGenre", skip=0, limit=100)
        shows, total = TVShowSearchService.search(db, filters)
        assert len(shows) == 0
        assert total == 0

    def test_search_year_filter_ignored(self, db: Session, sample_tv_shows):
        """Test that year filter is ignored for TV shows"""
        # TV shows don't have year field, so this should return all shows
        filters = SearchFilters(year=2020, skip=0, limit=100)
        shows, total = TVShowSearchService.search(db, filters)
        # Should return all shows since year filter is ignored
        assert total == 8


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_database(self, db: Session):
        """Test search on empty database"""
        filters = SearchFilters(skip=0, limit=100)
        movies, total = MovieSearchService.search(db, filters)
        assert len(movies) == 0
        assert total == 0

    def test_null_ratings(self, db: Session):
        """Test filtering with null ratings"""
        # Add movie with null rating
        movie = Movie(
            title="Test Movie",
            year=2020,
            rating=None,
            genres=json.dumps(["Drama"]),
        )
        db.add(movie)
        db.commit()

        # Search with min_rating should exclude null ratings
        filters = SearchFilters(min_rating=5.0, skip=0, limit=100)
        movies, total = MovieSearchService.search(db, filters)
        assert all(m.rating is not None for m in movies)

    def test_null_genres(self, db: Session):
        """Test filtering with null genres"""
        # Add movie with null genres
        movie = Movie(
            title="Test Movie",
            year=2020,
            rating=8.0,
            genres=None,
        )
        db.add(movie)
        db.commit()

        # Search by genre should not return movie with null genres
        filters = SearchFilters(genre="Drama", skip=0, limit=100)
        movies, total = MovieSearchService.search(db, filters)
        assert all(m.genres is not None for m in movies)

    def test_invalid_json_genres(self, db: Session):
        """Test handling of invalid JSON in genres field"""
        # Add movie with invalid JSON genres
        movie = Movie(
            title="Test Movie",
            year=2020,
            rating=8.0,
            genres="invalid json",
        )
        db.add(movie)
        db.commit()

        # Search should handle gracefully
        filters = SearchFilters(genre="Drama", skip=0, limit=100)
        movies, total = MovieSearchService.search(db, filters)
        # Should not crash, just not match the invalid genre
        assert True
