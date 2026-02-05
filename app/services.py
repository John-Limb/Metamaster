"""Business logic layer for movies and TV shows"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Movie, TVShow, Season, Episode
from app.schemas import MovieCreate, MovieUpdate, TVShowCreate, TVShowUpdate
import logging

logger = logging.getLogger(__name__)


class MovieService:
    """Service class for movie operations"""

    @staticmethod
    def get_all_movies(db: Session, limit: int = 10, offset: int = 0):
        """Get all movies with pagination"""
        query = db.query(Movie)
        total = query.count()
        movies = query.offset(offset).limit(limit).all()
        return movies, total

    @staticmethod
    def get_movie_by_id(db: Session, movie_id: int):
        """Get a specific movie by ID"""
        movie = db.query(Movie).filter(Movie.id == movie_id).first()
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
        search_query = db.query(Movie).filter(
            Movie.title.ilike(f"%{query}%")
        )
        total = search_query.count()
        movies = search_query.offset(offset).limit(limit).all()
        logger.info(f"Searched movies with query: {query}, found: {total}")
        return movies, total


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
    def get_season_episodes(db: Session, show_id: int, season_id: int, limit: int = 10, offset: int = 0):
        """Get all episodes for a season"""
        # Verify show and season exist
        show = db.query(TVShow).filter(TVShow.id == show_id).first()
        if not show:
            return None, 0

        season = db.query(Season).filter(
            Season.id == season_id,
            Season.show_id == show_id
        ).first()
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
