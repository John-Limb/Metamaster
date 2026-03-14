"""Pydantic models for the Kometa-inspired collection/playlist builder DSL."""

from __future__ import annotations

from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class StaticItem(BaseModel):
    tmdb_id: str
    item_type: Literal["movie", "tv_show"] = Field(default="movie", alias="type")

    model_config = {"populate_by_name": True}


class StaticItemsBuilder(BaseModel):
    builder_type: Literal["static_items"] = "static_items"
    items: List[StaticItem] = Field(default_factory=list)


class TmdbCollectionBuilder(BaseModel):
    builder_type: Literal["tmdb_collection"] = "tmdb_collection"
    tmdb_collection_id: str


class GenreBuilder(BaseModel):
    builder_type: Literal["genre"] = "genre"
    genre: str


class DecadeBuilder(BaseModel):
    builder_type: Literal["decade"] = "decade"
    decade: int  # e.g. 2000 means 2000-2009


AnyBuilder = Union[TmdbCollectionBuilder, StaticItemsBuilder, GenreBuilder, DecadeBuilder]


class CollectionDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    sort_title: Optional[str] = None
    builder: AnyBuilder = Field(discriminator="builder_type")


class PlaylistDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    builder: StaticItemsBuilder


class CollectionsYaml(BaseModel):
    """Root of the Kometa-inspired YAML config."""

    collections: Dict[str, CollectionDefinition] = Field(default_factory=dict)
    playlists: Dict[str, PlaylistDefinition] = Field(default_factory=dict)
