"""Files API endpoints"""

import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.domain.files.service import FileService
from app.domain.files.schemas import (
    FileItemResponse,
    FileItemCreate,
    FileItemUpdate,
    FileItemMove,
    FileItemRename,
    PaginatedFileResponse,
    FileStatsResponse,
    FileUploadResponse,
    FileBatchDeleteRequest,
    FileBatchMoveRequest,
    FileSearchResponse,
    FileOperationResponse,
)
from app.api.utils import pagination_metadata, resolve_pagination
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["Files"])


def get_file_service(db: Session = Depends(get_db)) -> FileService:
    """Dependency to get FileService instance"""
    return FileService(db)


@router.get("", response_model=PaginatedFileResponse)
async def list_files(
    path: str = Query("/", description="Directory path to list"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    List files in a directory with pagination.

    - **path**: Directory path to list (default: root of media directory)
    - **page**: Page number (1-indexed, default: 1)
    - **page_size**: Number of items per page (1-100, default: 20)
    """
    file_service = FileService(db)

    # Handle root path
    if path == "/" or not path:
        path = "/"

    # Get files and total count
    files, total = file_service.list_files(path=path, page=page, page_size=page_size)

    # Convert to response format
    items = [file_service.file_to_response(f) for f in files]

    # Calculate pagination metadata
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return {
        "items": items,
        "total": total,
        "limit": page_size,
        "offset": (page - 1) * page_size,
        "page": page,
        "pageSize": page_size,
        "totalPages": total_pages,
    }


@router.get("/stats", response_model=FileStatsResponse)
async def get_file_stats(
    db: Session = Depends(get_db),
):
    """
    Get file statistics including total files, total size, and files by type.
    """
    file_service = FileService(db)
    return file_service.get_file_stats()


@router.get("/search", response_model=FileSearchResponse)
async def search_files(
    query: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Search files by name or path.

    - **query**: Search query string
    - **page**: Page number (1-indexed, default: 1)
    - **page_size**: Number of items per page (1-100, default: 20)
    """
    file_service = FileService(db)

    files, total = file_service.search_files(query=query, page=page, page_size=page_size)

    items = [file_service.file_to_response(f) for f in files]
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return {
        "items": items,
        "total": total,
        "limit": page_size,
        "offset": (page - 1) * page_size,
        "page": page,
        "pageSize": page_size,
        "totalPages": total_pages,
    }


@router.get("/{file_id}", response_model=FileItemResponse)
async def get_file_details(
    file_id: int,
    db: Session = Depends(get_db),
):
    """
    Get details of a specific file by ID.

    - **file_id**: The ID of the file to retrieve
    """
    file_service = FileService(db)
    file_item = file_service.get_file_by_id(file_id)

    if not file_item:
        raise HTTPException(status_code=404, detail="File not found")

    return file_service.file_to_response(file_item)


@router.put("/{file_id}", response_model=FileItemResponse)
async def update_file_metadata(
    file_id: int,
    file_data: FileItemUpdate,
    db: Session = Depends(get_db),
):
    """
    Update file metadata.

    - **file_id**: The ID of the file to update
    - **name**: New name (optional)
    - **path**: New path (optional)
    - **is_indexed**: Whether file is indexed (optional)
    - **metadata**: Additional metadata (optional)
    """
    file_service = FileService(db)
    file_item = file_service.update_file(file_id, file_data)

    if not file_item:
        raise HTTPException(status_code=404, detail="File not found")

    return file_service.file_to_response(file_item)


@router.patch("/{file_id}/move", response_model=FileItemResponse)
async def move_file(
    file_id: int,
    move_data: FileItemMove,
    db: Session = Depends(get_db),
):
    """
    Move a file to a new path.

    - **file_id**: The ID of the file to move
    - **path**: New path for the file
    """
    file_service = FileService(db)

    try:
        file_item = file_service.move_file(file_id, move_data.path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not file_item:
        raise HTTPException(status_code=404, detail="File not found")

    return file_service.file_to_response(file_item)


@router.patch("/{file_id}/rename", response_model=FileItemResponse)
async def rename_file(
    file_id: int,
    rename_data: FileItemRename,
    db: Session = Depends(get_db),
):
    """
    Rename a file.

    - **file_id**: The ID of the file to rename
    - **name**: New name for the file
    """
    file_service = FileService(db)
    file_item = file_service.rename_file(file_id, rename_data.name)

    if not file_item:
        raise HTTPException(status_code=404, detail="File not found")

    return file_service.file_to_response(file_item)


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: int,
    delete_from_disk: bool = Query(False, description="Also delete from disk"),
    db: Session = Depends(get_db),
):
    """
    Delete a file.

    - **file_id**: The ID of the file to delete
    - **delete_from_disk**: Also delete from filesystem (default: False)
    """
    file_service = FileService(db)
    success = file_service.delete_file(file_id, delete_from_disk=delete_from_disk)

    if not success:
        raise HTTPException(status_code=404, detail="File not found")

    return None


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    path: str = Form("/", description="Upload path"),
    db: Session = Depends(get_db),
):
    """
    Upload a file to the specified path.

    - **file**: The file to upload
    - **path**: Target directory path (default: root)
    """
    file_service = FileService(db)

    # Ensure path is within media directories
    if not file_service._ensure_within_media_dirs(path):
        raise HTTPException(
            status_code=400,
            detail=f"Path must be within media directories: {file_service.media_dirs}",
        )

    # Create destination path
    filename = file.filename or "unknown"
    destination_path = os.path.join(path, filename)

    # Save file to disk
    try:
        with open(destination_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    finally:
        await file.close()

    # Get file info
    file_size = os.path.getsize(destination_path) if os.path.exists(destination_path) else 0
    file_type = file_service._get_file_type(destination_path)
    mime_type = file_service._get_mime_type(destination_path)

    # Create file record
    file_data = FileItemCreate(
        name=filename,
        path=destination_path,
        type=file_type,
        size=file_size,
        mime_type=mime_type,
    )

    file_item = file_service.create_file(file_data)

    return {
        "success": True,
        "message": "File uploaded successfully",
        "data": file_service.file_to_response(file_item),
    }


@router.post("/batch-delete")
async def batch_delete_files(
    request: FileBatchDeleteRequest,
    delete_from_disk: bool = Query(False, description="Also delete from disk"),
    db: Session = Depends(get_db),
):
    """
    Delete multiple files.

    - **ids**: List of file IDs to delete
    - **delete_from_disk**: Also delete from filesystem (default: False)
    """
    file_service = FileService(db)
    deleted_count = file_service.batch_delete_files(request.ids, delete_from_disk=delete_from_disk)

    return {
        "success": True,
        "message": f"Deleted {deleted_count} file(s)",
    }


@router.post("/batch-move")
async def batch_move_files(
    request: FileBatchMoveRequest,
    db: Session = Depends(get_db),
):
    """
    Move multiple files to a new path.

    - **ids**: List of file IDs to move
    - **path**: New path for the files
    """
    file_service = FileService(db)

    # Validate target path
    if not file_service._ensure_within_media_dirs(request.path):
        raise HTTPException(
            status_code=400,
            detail=f"Path must be within media directories: {file_service.media_dirs}",
        )

    moved_count = file_service.batch_move_files(request.ids, request.path)

    return {
        "success": True,
        "message": f"Moved {moved_count} file(s)",
    }


@router.post("/sync")
async def sync_directory(
    path: str = Query(..., description="Directory path to sync"),
    db: Session = Depends(get_db),
):
    """
    Sync a directory to the database.

    - **path**: Directory path to sync
    """
    file_service = FileService(db)

    try:
        synced_count = file_service.sync_directory(path)
        return {
            "success": True,
            "message": f"Synced {synced_count} item(s) from directory",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
