"""Request/response schemas for Plex API endpoints"""

from pydantic import BaseModel


class PlexConnectionCreate(BaseModel):
    server_url: str
    token: str


class PlexSyncTriggerResponse(BaseModel):
    task_id: str
    message: str


class PlexOAuthInitResponse(BaseModel):
    oauth_url: str
    pin_id: int


class PlexMismatchItem(BaseModel):
    id: int
    item_type: str
    item_id: int
    plex_rating_key: str
    plex_tmdb_id: str


class PlexResolveRequest(BaseModel):
    trust: str  # "metamaster" or "plex"
