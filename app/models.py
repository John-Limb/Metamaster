"""SQLAlchemy ORM models for database entities

This module re-exports models from the domain layer to maintain backward compatibility.
The actual model definitions are in app/domain/ subdirectories.
"""

from app.domain.common.models import APICache, BatchOperation, FileQueue, TaskError
from app.domain.files.models import FileItem

# Re-export models from domain layer
from app.domain.movies.models import Movie, MovieFile
from app.domain.tv_shows.models import Episode, EpisodeFile, Season, TVShow

__all__ = [
    "Movie",
    "MovieFile",
    "TVShow",
    "Season",
    "Episode",
    "EpisodeFile",
    "APICache",
    "FileQueue",
    "TaskError",
    "BatchOperation",
    "FileItem",
]
