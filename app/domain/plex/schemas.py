"""Pydantic schemas for Plex domain API responses"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PlexConnectionResponse(BaseModel):
    model_config = {"from_attributes": True, "extra": "ignore"}

    id: int
    server_url: str
    is_active: bool
    movie_library_id: Optional[str] = None
    tv_library_id: Optional[str] = None
    created_at: datetime
    last_connected_at: Optional[datetime] = None


class PlexSyncRecordResponse(BaseModel):
    model_config = {"from_attributes": True, "extra": "ignore"}

    id: int
    connection_id: int
    item_type: str
    item_id: int
    plex_rating_key: Optional[str] = None
    plex_tmdb_id: Optional[str] = None
    sync_status: str
    watch_count: int = 0
    is_watched: bool = False
    last_matched_at: Optional[datetime] = None
    last_pulled_at: Optional[datetime] = None
    last_watched_at: Optional[datetime] = None
    last_error: Optional[str] = None
