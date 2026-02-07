"""Pydantic schemas for request/response validation"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ============================================================================
# Movie Schemas
# ============================================================================

class MovieCreate(BaseModel):
    """Schema for creating a new movie"""
    title: str = Field(..., min_length=1, max_length=255,
                       description="Movie title")
    plot: Optional[str] = Field(None, description="Movie plot/description")
    year: Optional[int] = Field(
        None, ge=1800, le=2100, description="Release year")
    rating: Optional[float] = Field(
        None, ge=0, le=10, description="Movie rating (0-10)")
    runtime: Optional[int] = Field(
        None, ge=0, description="Runtime in minutes")
    genres: Optional[str] = Field(
        None, description="Genres as JSON array string")
    omdb_id: Optional[str] = Field(None, description="OMDB ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "The Shawshank Redemption",
                "plot": "Two imprisoned men bond over a number of years...",
                "year": 1994,
                "rating": 9.3,
                "runtime": 142,
                "genres": '["Drama"]',
                "omdb_id": "tt0111161"
            }
        }
    )


class MovieUpdate(BaseModel):
    """Schema for updating a movie"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    plot: Optional[str] = None
    year: Optional[int] = Field(None, ge=1800, le=2100)
    rating: Optional[float] = Field(None, ge=0, le=10)
    runtime: Optional[int] = Field(None, ge=0)
    genres: Optional[str] = None
    omdb_id: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rating": 9.5,
                "runtime": 145
            }
        }
    )


class MovieResponse(BaseModel):
    """Schema for movie response"""
    id: int = Field(..., description="Movie ID")
    title: str = Field(..., description="Movie title")
    plot: Optional[str] = None
    year: Optional[int] = None
    rating: Optional[float] = None
    runtime: Optional[int] = None
    genres: Optional[str] = None
    omdb_id: Optional[str] = None
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TV Show Schemas
# ============================================================================

class TVShowCreate(BaseModel):
    """Schema for creating a new TV show"""
    title: str = Field(..., min_length=1, max_length=255,
                       description="TV show title")
    plot: Optional[str] = Field(None, description="TV show plot/description")
    rating: Optional[float] = Field(
        None, ge=0, le=10, description="TV show rating (0-10)")
    genres: Optional[str] = Field(
        None, description="Genres as JSON array string")
    status: Optional[str] = Field(
        None, description="Status: 'Continuing' or 'Ended'")
    tvdb_id: Optional[str] = Field(None, description="TVDB ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Breaking Bad",
                "plot": "A high school chemistry teacher...",
                "rating": 9.5,
                "genres": '["Drama", "Crime"]',
                "status": "Ended",
                "tvdb_id": "81189"
            }
        }
    )


class TVShowUpdate(BaseModel):
    """Schema for updating a TV show"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    plot: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=10)
    genres: Optional[str] = None
    status: Optional[str] = None
    tvdb_id: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rating": 9.6,
                "status": "Ended"
            }
        }
    )


class TVShowResponse(BaseModel):
    """Schema for TV show response"""
    id: int = Field(..., description="TV show ID")
    title: str = Field(..., description="TV show title")
    plot: Optional[str] = None
    rating: Optional[float] = None
    genres: Optional[str] = None
    status: Optional[str] = None
    tvdb_id: Optional[str] = None
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Season and Episode Schemas
# ============================================================================

class SeasonResponse(BaseModel):
    """Schema for season response"""
    id: int = Field(..., description="Season ID")
    season_number: int = Field(..., description="Season number")
    tvdb_id: Optional[str] = None
    episode_count: Optional[int] = Field(
        None, description="Number of episodes in season")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class EpisodeResponse(BaseModel):
    """Schema for episode response"""
    id: int = Field(..., description="Episode ID")
    episode_number: int = Field(..., description="Episode number")
    title: Optional[str] = None
    plot: Optional[str] = None
    air_date: Optional[str] = Field(
        None, description="Air date in YYYY-MM-DD format")
    rating: Optional[float] = None
    tvdb_id: Optional[str] = None
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Pagination Schemas
# ============================================================================

class PaginatedResponse(BaseModel):
    """Generic pagination wrapper"""
    items: List[dict] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Offset from start")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 100,
                "limit": 10,
                "offset": 0
            }
        }
    )


class PaginatedMovieResponse(BaseModel):
    """Paginated response for movies"""
    items: List[MovieResponse] = Field(..., description="List of movies")
    total: int = Field(..., description="Total number of movies")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Offset from start")


class PaginatedTVShowResponse(BaseModel):
    """Paginated response for TV shows"""
    items: List[TVShowResponse] = Field(..., description="List of TV shows")
    total: int = Field(..., description="Total number of TV shows")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Offset from start")


class PaginatedSeasonResponse(BaseModel):
    """Paginated response for seasons"""
    items: List[SeasonResponse] = Field(..., description="List of seasons")
    total: int = Field(..., description="Total number of seasons")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Offset from start")


class PaginatedEpisodeResponse(BaseModel):
    """Paginated response for episodes"""
    items: List[EpisodeResponse] = Field(..., description="List of episodes")
    total: int = Field(..., description="Total number of episodes")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Offset from start")


# ============================================================================
# Cache Schemas
# ============================================================================

class CacheStatsResponse(BaseModel):
    """Schema for cache statistics response"""
    total_entries: int = Field(..., description="Total number of cache entries")
    active_entries: int = Field(..., description="Number of active (non-expired) entries")
    expired_entries: int = Field(..., description="Number of expired entries")
    total_size_bytes: int = Field(..., description="Total cache size in bytes")
    total_size_mb: float = Field(..., description="Total cache size in megabytes")
    by_api_type: dict = Field(..., description="Breakdown of entries by API type")
    timestamp: str = Field(..., description="Timestamp of statistics generation")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_entries": 150,
                "active_entries": 120,
                "expired_entries": 30,
                "total_size_bytes": 5242880,
                "total_size_mb": 5.0,
                "by_api_type": {"omdb": 80, "tvdb": 70},
                "timestamp": "2026-02-06T12:34:23.380Z"
            }
        }
    )


class CacheEntryResponse(BaseModel):
    """Schema for individual cache entry"""
    id: int = Field(..., description="Cache entry ID")
    api_type: str = Field(..., description="API type (omdb, tvdb, etc.)")
    query_key: str = Field(..., description="Cache query key")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class PaginatedCacheResponse(BaseModel):
    """Paginated response for cache entries"""
    items: List[CacheEntryResponse] = Field(..., description="List of cache entries")
    total: int = Field(..., description="Total number of cache entries")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Offset from start")


class CacheOperationResponse(BaseModel):
    """Schema for cache operation responses"""
    success: bool = Field(..., description="Whether operation was successful")
    message: str = Field(..., description="Operation message")
    affected_entries: int = Field(..., description="Number of entries affected")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Expired cache entries cleared",
                "affected_entries": 25
            }
        }
    )


class MetadataSyncResponse(BaseModel):
    """Schema for metadata sync operation response"""
    success: bool = Field(..., description="Whether sync was successful")
    message: str = Field(..., description="Operation message")
    movie_id: Optional[int] = Field(None, description="Movie ID (for movie sync)")
    show_id: Optional[int] = Field(None, description="TV show ID (for show sync)")
    updated_fields: List[str] = Field(..., description="List of fields that were updated")
    metadata: dict = Field(..., description="Updated metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Movie metadata synced successfully",
                "movie_id": 1,
                "show_id": None,
                "updated_fields": ["rating", "plot", "runtime"],
                "metadata": {
                    "title": "The Shawshank Redemption",
                    "rating": 9.3,
                    "plot": "Two imprisoned men bond...",
                    "runtime": 142
                }
            }
        }
    )


# ============================================================================
# Task Monitoring Schemas
# ============================================================================

class TaskStatusResponse(BaseModel):
    """Schema for task status response"""
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Task status (pending/started/success/failure/retry)")
    result: Optional[dict] = Field(None, description="Task result if completed")
    error: Optional[str] = Field(None, description="Error message if task failed")
    created_at: Optional[datetime] = Field(None, description="Task creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Task last update timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "abc123def456",
                "status": "success",
                "result": {"processed_items": 42},
                "error": None,
                "created_at": "2026-02-07T10:00:00Z",
                "updated_at": "2026-02-07T10:05:00Z"
            }
        }
    )


class TaskRetryResponse(BaseModel):
    """Schema for task retry response"""
    success: bool = Field(..., description="Whether retry was successful")
    message: str = Field(..., description="Operation message")
    original_task_id: str = Field(..., description="Original task ID")
    new_task_id: str = Field(..., description="New task ID for retry attempt")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Task retry initiated successfully",
                "original_task_id": "abc123def456",
                "new_task_id": "xyz789uvw012"
            }
        }
    )


class TaskListItemResponse(BaseModel):
    """Schema for individual task in list"""
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Task status")
    created_at: Optional[datetime] = Field(None, description="Task creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Task last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """Schema for paginated task list response"""
    items: List[TaskListItemResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Offset from start")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "task_id": "abc123def456",
                        "status": "success",
                        "created_at": "2026-02-07T10:00:00Z",
                        "updated_at": "2026-02-07T10:05:00Z"
                    }
                ],
                "total": 100,
                "limit": 50,
                "offset": 0
            }
        }
    )


class TaskCancelResponse(BaseModel):
     """Schema for task cancellation response"""
     success: bool = Field(..., description="Whether cancellation was successful")
     message: str = Field(..., description="Operation message")
     task_id: str = Field(..., description="Task ID that was cancelled")

     model_config = ConfigDict(
         json_schema_extra={
             "example": {
                 "success": True,
                 "message": "Task cancelled successfully",
                 "task_id": "abc123def456"
             }
         }
     )


# ============================================================================
# Task Error Schemas
# ============================================================================

class TaskErrorResponse(BaseModel):
     """Schema for individual task error"""
     id: int = Field(..., description="Task error ID")
     task_id: str = Field(..., description="Celery task ID")
     task_name: str = Field(..., description="Name of the task")
     error_message: str = Field(..., description="Error message")
     error_traceback: Optional[str] = Field(None, description="Full error traceback")
     severity: str = Field(..., description="Error severity (critical/warning/info)")
     retry_count: int = Field(..., description="Number of retries attempted")
     created_at: datetime = Field(..., description="Error creation timestamp")
     resolved_at: Optional[datetime] = Field(None, description="Error resolution timestamp")

     model_config = ConfigDict(
         from_attributes=True,
         json_schema_extra={
             "example": {
                 "id": 1,
                 "task_id": "abc123def456",
                 "task_name": "app.tasks.analyze_file",
                 "error_message": "File not found: /path/to/file.mp4",
                 "error_traceback": "Traceback (most recent call last):\n  ...",
                 "severity": "critical",
                 "retry_count": 3,
                 "created_at": "2026-02-07T10:00:00Z",
                 "resolved_at": None
             }
         }
     )


class PaginatedTaskErrorResponse(BaseModel):
     """Paginated response for task errors"""
     items: List[TaskErrorResponse] = Field(..., description="List of task errors")
     total: int = Field(..., description="Total number of task errors")
     limit: int = Field(..., description="Items per page")
     offset: int = Field(..., description="Offset from start")

     model_config = ConfigDict(
         json_schema_extra={
             "example": {
                 "items": [
                     {
                         "id": 1,
                         "task_id": "abc123def456",
                         "task_name": "app.tasks.analyze_file",
                         "error_message": "File not found: /path/to/file.mp4",
                         "error_traceback": "Traceback (most recent call last):\n  ...",
                         "severity": "critical",
                         "retry_count": 3,
                         "created_at": "2026-02-07T10:00:00Z",
                         "resolved_at": None
                     }
                 ],
                 "total": 10,
                 "limit": 50,
                 "offset": 0
             }
         }
     )
