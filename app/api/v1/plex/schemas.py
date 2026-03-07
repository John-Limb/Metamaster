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
