"""Pydantic models for Plex API responses"""

from typing import List, Optional

from pydantic import BaseModel, Field


class PlexGuid(BaseModel):
    model_config = {"extra": "ignore"}

    id: str  # e.g. "tmdb://603" or "imdb://tt0133093"


class PlexLibrarySection(BaseModel):
    model_config = {"extra": "ignore"}

    key: str
    title: str
    type: str  # "movie" or "show"


class PlexMediaItem(BaseModel):
    model_config = {"populate_by_name": True, "extra": "ignore"}

    rating_key: str = Field(alias="ratingKey")
    title: str
    year: Optional[int] = None
    view_count: int = Field(alias="viewCount", default=0)
    last_viewed_at: Optional[int] = Field(alias="lastViewedAt", default=None)
    guids: List[PlexGuid] = Field(alias="Guid", default_factory=list)

    @property
    def tmdb_id(self) -> Optional[str]:
        for guid in self.guids:
            if guid.id.startswith("tmdb://"):
                return guid.id.removeprefix("tmdb://")
        return None
