"""Pydantic request/response schemas for Plex collection and playlist API endpoints."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.domain.plex.collection_models import BuilderType, SetType


class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sort_title: Optional[str] = None
    builder_type: BuilderType
    builder_config: dict


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sort_title: Optional[str] = None
    builder_config: Optional[dict] = None
    enabled: Optional[bool] = None


class PlaylistBulkDeleteRequest(BaseModel):
    ids: List[int]


class PlaylistCreate(BaseModel):
    name: str
    description: Optional[str] = None
    builder_config: dict


class PlaylistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    builder_config: Optional[dict] = None
    enabled: Optional[bool] = None


class CollectionItemResponse(BaseModel):
    id: int
    plex_rating_key: str
    item_type: str
    item_id: int
    position: int
    model_config = ConfigDict(from_attributes=True)


class CollectionResponse(BaseModel):
    id: int
    connection_id: int
    name: str
    description: Optional[str]
    sort_title: Optional[str]
    builder_type: BuilderType
    builder_config: dict
    plex_rating_key: Optional[str]
    last_synced_at: Optional[datetime]
    enabled: bool
    is_default: bool
    items: list[CollectionItemResponse] = []
    model_config = ConfigDict(from_attributes=True)


class PlaylistItemResponse(BaseModel):
    id: int
    plex_rating_key: str
    item_type: str
    item_id: int
    position: int
    model_config = ConfigDict(from_attributes=True)


class PlaylistResponse(BaseModel):
    id: int
    connection_id: int
    name: str
    description: Optional[str]
    builder_config: dict
    plex_rating_key: Optional[str]
    last_synced_at: Optional[datetime]
    enabled: bool
    items: list[PlaylistItemResponse] = []
    model_config = ConfigDict(from_attributes=True)


class CollectionSetResponse(BaseModel):
    id: int
    connection_id: int
    set_type: SetType
    enabled: bool
    last_run_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class CollectionSetUpdate(BaseModel):
    enabled: bool


class YamlImportRequest(BaseModel):
    yaml_content: str
