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
    MetadataSyncResponse,
)
from app.services import TVShowService, TVDBService
import logging
import json

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


@router.post("/{show_id}/sync-metadata", response_model=MetadataSyncResponse)
async def sync_tv_show_metadata(
    show_id: int,
    db: Session = Depends(get_db),
):
    """
    Fetch TV show metadata from TVDB and update the TV show record.
    
    This endpoint:
    1. Retrieves the TV show from the database
    2. Fetches updated metadata from TVDB using the show's TVDB ID
    3. Updates the TV show record with new metadata
    4. Returns the updated TV show information
    
    Parameters:
    - **show_id**: ID of the TV show to sync
    
    Returns:
    - **success**: Whether sync was successful
    - **message**: Operation message
    - **show_id**: ID of the synced TV show
    - **updated_fields**: List of fields that were updated
    - **metadata**: Updated metadata
    """
    try:
        # Get the TV show
        show = TVShowService.get_tv_show_by_id(db, show_id)
        if not show:
            raise HTTPException(status_code=404, detail="TV show not found")
        
        # Check if show has TVDB ID
        if not show.tvdb_id:
            raise HTTPException(
                status_code=400,
                detail="TV show does not have a TVDB ID. Cannot sync metadata."
            )
        
        logger.info(f"Syncing metadata for TV show {show_id} (TVDB ID: {show.tvdb_id})")
        
        # Fetch metadata from TVDB
        tvdb_data = await TVDBService.get_series_details(db, show.tvdb_id)
        if not tvdb_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch metadata from TVDB. Please try again later."
            )
        
        # Parse TVDB response
        parsed_data = TVDBService.parse_tvdb_series_response(tvdb_data)
        if not parsed_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to parse TVDB response"
            )
        
        # Track which fields were updated
        updated_fields = []
        old_values = {}
        
        # Update TV show fields
        if "title" in parsed_data and parsed_data["title"] != show.title:
            old_values["title"] = show.title
            show.title = parsed_data["title"]
            updated_fields.append("title")
        
        if "plot" in parsed_data and parsed_data["plot"] != show.plot:
            old_values["plot"] = show.plot
            show.plot = parsed_data["plot"]
            updated_fields.append("plot")
        
        if "rating" in parsed_data and parsed_data["rating"] != show.rating:
            old_values["rating"] = show.rating
            show.rating = parsed_data["rating"]
            updated_fields.append("rating")
        
        if "status" in parsed_data and parsed_data["status"] != show.status:
            old_values["status"] = show.status
            show.status = parsed_data["status"]
            updated_fields.append("status")
        
        if "genres" in parsed_data and parsed_data["genres"] != show.genres:
            old_values["genres"] = show.genres
            show.genres = parsed_data["genres"]
            updated_fields.append("genres")
        
        # Commit changes
        db.commit()
        db.refresh(show)
        
        logger.info(
            f"Successfully synced metadata for TV show {show_id}. "
            f"Updated fields: {', '.join(updated_fields) if updated_fields else 'none'}"
        )
        
        # Prepare response metadata
        response_metadata = {
            "title": show.title,
            "plot": show.plot,
            "rating": show.rating,
            "status": show.status,
            "genres": json.loads(show.genres) if show.genres else [],
            "tvdb_id": show.tvdb_id,
        }
        
        return {
            "success": True,
            "message": f"TV show metadata synced successfully. Updated {len(updated_fields)} field(s).",
            "movie_id": None,
            "show_id": show_id,
            "updated_fields": updated_fields,
            "metadata": response_metadata,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing metadata for TV show {show_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while syncing metadata"
        )
