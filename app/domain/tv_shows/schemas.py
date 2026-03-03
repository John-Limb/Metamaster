"""TV Show domain schemas - re-export from app.schemas"""

from app.schemas import (
    EpisodeResponse,
    MetadataSyncResponse,
    PaginatedEpisodeResponse,
    PaginatedSeasonResponse,
    PaginatedTVShowResponse,
    PaginatedTVShowResponseWithFilters,
    SeasonResponse,
    TVShowCreate,
    TVShowResponse,
    TVShowUpdate,
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
