"""Movie API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import MovieCreate, MovieUpdate, MovieResponse, PaginatedMovieResponse
from app.services import MovieService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("", response_model=PaginatedMovieResponse)
async def list_movies(
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset from start"),
    db: Session = Depends(get_db),
):
    """
    List all movies with pagination.

    - **limit**: Number of items per page (1-100, default: 10)
    - **offset**: Offset from start (default: 0)
    """
    movies, total = MovieService.get_all_movies(db, limit=limit, offset=offset)
    return {
        "items": movies,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/search", response_model=PaginatedMovieResponse)
async def search_movies(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset from start"),
    db: Session = Depends(get_db),
):
    """
    Search movies by title.

    - **q**: Search query (required)
    - **limit**: Number of items per page (1-100, default: 10)
    - **offset**: Offset from start (default: 0)
    """
    movies, total = MovieService.search_movies(
        db, query=q, limit=limit, offset=offset)
    return {
        "items": movies,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(
    movie_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific movie by ID"""
    movie = MovieService.get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.post("", response_model=MovieResponse, status_code=201)
async def create_movie(
    movie_data: MovieCreate,
    db: Session = Depends(get_db),
):
    """Create a new movie"""
    movie = MovieService.create_movie(db, movie_data)
    return movie


@router.put("/{movie_id}", response_model=MovieResponse)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing movie"""
    movie = MovieService.update_movie(db, movie_id, movie_data)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.delete("/{movie_id}", status_code=204)
async def delete_movie(
    movie_id: int,
    db: Session = Depends(get_db),
):
    """Delete a movie"""
    success = MovieService.delete_movie(db, movie_id)
    if not success:
        raise HTTPException(status_code=404, detail="Movie not found")
    return None
