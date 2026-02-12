"""TV Show domain schemas - re-export from app.schemas"""

from app.schemas import (
    TVShowCreate,
    TVShowUpdate,
    TVShowResponse,
    PaginatedTVShowResponse,
    PaginatedTVShowResponseWithFilters,
    PaginatedSeasonResponse,
    PaginatedEpisodeResponse,
    SeasonResponse,
    EpisodeResponse,
    MetadataSyncResponse,
)

__all__ = [
    "TVShowCreate",
    "TVShowUpdate",
    "TVShowResponse",
    "PaginatedTVShowResponse",
    "PaginatedTVShowResponseWithFilters",
    "PaginatedSeasonResponse",
    "PaginatedEpisodeResponse",
    "SeasonResponse",
    "EpisodeResponse",
    "MetadataSyncResponse",
]
