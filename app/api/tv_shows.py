"""TV Show API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    TVShowCreate,
    TVShowUpdate,
    TVShowResponse,
    PaginatedTVShowResponse,
    PaginatedSeasonResponse,
    PaginatedEpisodeResponse,
    SeasonResponse,
    EpisodeResponse,
)
from app.services import TVShowService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tv-shows", tags=["TV Shows"])


@router.get("", response_model=PaginatedTVShowResponse)
async def list_tv_shows(
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset from start"),
    db: Session = Depends(get_db),
):
    """
    List all TV shows with pagination.

    - **limit**: Number of items per page (1-100, default: 10)
    - **offset**: Offset from start (default: 0)
    """
    shows, total = TVShowService.get_all_tv_shows(
        db, limit=limit, offset=offset)
    return {
        "items": shows,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{show_id}", response_model=TVShowResponse)
async def get_tv_show(
    show_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific TV show by ID"""
    show = TVShowService.get_tv_show_by_id(db, show_id)
    if not show:
        raise HTTPException(status_code=404, detail="TV show not found")
    return show


@router.get("/{show_id}/seasons", response_model=PaginatedSeasonResponse)
async def get_tv_show_seasons(
    show_id: int,
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset from start"),
    db: Session = Depends(get_db),
):
    """
    List all seasons for a TV show.

    - **show_id**: TV show ID
    - **limit**: Number of items per page (1-100, default: 10)
    - **offset**: Offset from start (default: 0)
    """
    seasons, total = TVShowService.get_tv_show_seasons(
        db, show_id=show_id, limit=limit, offset=offset
    )
    if seasons is None:
        raise HTTPException(status_code=404, detail="TV show not found")

    # Add episode count to each season
    seasons_with_count = []
    for season in seasons:
        season_dict = {
            "id": season.id,
            "season_number": season.season_number,
            "tvdb_id": season.tvdb_id,
            "episode_count": len(season.episodes),
            "created_at": season.created_at,
        }
        seasons_with_count.append(season_dict)

    return {
        "items": seasons_with_count,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{show_id}/seasons/{season_id}/episodes", response_model=PaginatedEpisodeResponse)
async def get_season_episodes(
    show_id: int,
    season_id: int,
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset from start"),
    db: Session = Depends(get_db),
):
    """
    List all episodes for a season.

    - **show_id**: TV show ID
    - **season_id**: Season ID
    - **limit**: Number of items per page (1-100, default: 10)
    - **offset**: Offset from start (default: 0)
    """
    episodes, total = TVShowService.get_season_episodes(
        db, show_id=show_id, season_id=season_id, limit=limit, offset=offset
    )
    if episodes is None:
        raise HTTPException(
            status_code=404, detail="TV show or season not found")

    return {
        "items": episodes,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("", response_model=TVShowResponse, status_code=201)
async def create_tv_show(
    show_data: TVShowCreate,
    db: Session = Depends(get_db),
):
    """Create a new TV show"""
    show = TVShowService.create_tv_show(db, show_data)
    return show


@router.put("/{show_id}", response_model=TVShowResponse)
async def update_tv_show(
    show_id: int,
    show_data: TVShowUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing TV show"""
    show = TVShowService.update_tv_show(db, show_id, show_data)
    if not show:
        raise HTTPException(status_code=404, detail="TV show not found")
    return show


@router.delete("/{show_id}", status_code=204)
async def delete_tv_show(
    show_id: int,
    db: Session = Depends(get_db),
):
    """Delete a TV show"""
    success = TVShowService.delete_tv_show(db, show_id)
    if not success:
        raise HTTPException(status_code=404, detail="TV show not found")
    return None
