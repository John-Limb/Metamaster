"""Pydantic schemas for File operations"""

from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional, List, Dict, Any
from datetime import datetime


class FileItemBase(BaseModel):
    """Base schema for file items"""

    name: str = Field(..., description="File or directory name")
    path: str = Field(..., description="Full path to the file or directory")
    type: str = Field(..., description="Type: 'file' or 'directory'")
    size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type of the file")


class FileItemResponse(FileItemBase):
    """Schema for file item response"""

    id: str = Field(..., description="File ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_indexed: bool = Field(default=False, description="Whether file is indexed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class FileItemCreate(BaseModel):
    """Schema for creating a file item"""

    name: str = Field(..., min_length=1, max_length=500)
    path: str = Field(..., min_length=1, max_length=1000)
    type: str = Field(..., pattern="^(file|directory)$")
    size: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "movie.mp4",
                "path": "/media/movies/movie.mp4",
                "type": "file",
                "size": 1073741824,
                "mime_type": "video/mp4",
            }
        }
    )


class FileItemUpdate(BaseModel):
    """Schema for updating a file item"""

    name: Optional[str] = Field(None, min_length=1, max_length=500)
    path: Optional[str] = Field(None, min_length=1, max_length=1000)
    is_indexed: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(json_schema_extra={"example": {"name": "new_name.mp4"}})


class FileItemMove(BaseModel):
    """Schema for moving a file item"""

    path: str = Field(..., description="New path for the file")

    model_config = ConfigDict(json_schema_extra={"path": "/media/movies/new_folder/"})


class FileItemRename(BaseModel):
    """Schema for renaming a file item"""

    name: str = Field(..., min_length=1, max_length=500, description="New name for the file")

    model_config = ConfigDict(json_schema_extra={"name": "new_name.mp4"})


class FileUploadResponse(BaseModel):
    """Schema for file upload response"""

    success: bool = Field(default=True)
    message: str = Field(default="File uploaded successfully")
    data: FileItemResponse


class FileStatsResponse(BaseModel):
    """Schema for file statistics response"""

    totalFiles: int = Field(..., description="Total number of files")
    totalSize: int = Field(..., description="Total size in bytes")
    filesByType: Dict[str, int] = Field(..., description="File count by type")
    lastUpdated: datetime = Field(..., description="Last update timestamp")
    movieCount: int = Field(0, description="Number of video files in movie directory")
    tvShowCount: int = Field(0, description="Number of video files in TV directory")


class PaginatedFileResponse(BaseModel):
    """Schema for paginated file list response"""

    items: List[FileItemResponse]
    total: int
    limit: int
    offset: int
    page: int
    pageSize: int
    totalPages: int


class FileBatchDeleteRequest(BaseModel):
    """Schema for batch delete request"""

    ids: List[int] = Field(..., description="List of file IDs to delete")

    model_config = ConfigDict(json_schema_extra={"ids": [1, 2, 3]})


class FileBatchMoveRequest(BaseModel):
    """Schema for batch move request"""

    ids: List[int] = Field(..., description="List of file IDs to move")
    path: str = Field(..., description="New path for the files")

    model_config = ConfigDict(json_schema_extra={"ids": [1, 2, 3], "path": "/media/movies/new_folder/"})


class FileSearchResponse(BaseModel):
    """Schema for file search response"""

    items: List[FileItemResponse]
    total: int
    limit: int
    offset: int
    page: int
    pageSize: int
    totalPages: int


class FileOperationResponse(BaseModel):
    """Generic file operation response"""

    success: bool
    message: str
    data: Optional[FileItemResponse] = None


class FileClassifyRequest(BaseModel):
    """Schema for file classification request"""

    filenames: Optional[List[str]] = Field(None, description="List of filenames to classify")
    file_ids: Optional[List[int]] = Field(None, description="List of file IDs to classify")


class FileClassificationResult(BaseModel):
    """Schema for a single file classification result"""

    filename: str = Field(..., description="The filename that was classified")
    type: str = Field(..., description="Classified type: 'movie' or 'tv_show'")
    confidence: str = Field(..., description="Classification confidence: 'high', 'medium', or 'low'")
    pattern_matched: str = Field(..., description="Which pattern was matched")
    title: Optional[str] = Field(None, description="Extracted movie title")
    show_name: Optional[str] = Field(None, description="Extracted TV show name")
    year: Optional[int] = Field(None, description="Extracted year")
    season: Optional[int] = Field(None, description="Extracted season number")
    episode: Optional[int] = Field(None, description="Extracted episode number")


class FileClassifyResponse(BaseModel):
    """Schema for file classification response"""

    results: List[FileClassificationResult]
    total: int
