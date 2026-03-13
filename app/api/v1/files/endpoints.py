"""Files API endpoints"""

import logging
import os
import shutil

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.application.pattern_recognition.service import PatternRecognitionService
from app.core.database import get_db
from app.domain.files.models import FileItem
from app.domain.files.schemas import (
    FileBatchDeleteRequest,
    FileBatchMoveRequest,
    FileClassificationResult,
    FileClassifyRequest,
    FileClassifyResponse,
    FileItemCreate,
    FileItemMove,
    FileItemRename,
    FileItemResponse,
    FileItemUpdate,
    FileSearchResponse,
    FileStatsResponse,
    FileUploadResponse,
    PaginatedFileResponse,
)
from app.domain.files.service import FileService
from app.domain.movies.models import MovieFile
from app.domain.plex.models import PlexConnection
from app.domain.plex.service import get_or_cache_library_ids
from app.domain.tv_shows.models import EpisodeFile
from app.tasks.plex import refresh_plex_library

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["Files"])


def get_file_service(db: Session = Depends(get_db)) -> FileService:
    """Dependency to get FileService instance"""
    return FileService(db)


def _sections_for_file(
    db: Session,
    file_id: int,
    conn: "PlexConnection",
) -> set[str]:
    """Return Plex section IDs for a single file based on its media type."""
    file_item = db.query(FileItem).filter(FileItem.id == file_id).first()
    if file_item is None:
        return set()
    path = file_item.path
    is_movie = db.query(MovieFile).filter(MovieFile.file_path == path).first() is not None
    is_tv = db.query(EpisodeFile).filter(EpisodeFile.file_path == path).first() is not None
    if is_movie and conn.movie_library_id:
        return {conn.movie_library_id}
    if is_tv and conn.tv_library_id:
        return {conn.tv_library_id}
    # Unlinked — refresh both sections
    sections = set()
    if conn.movie_library_id:
        sections.add(conn.movie_library_id)
    if conn.tv_library_id:
        sections.add(conn.tv_library_id)
    return sections


def _plex_section_ids_for_files(db: Session, file_ids: list[int]) -> set[str]:
    """Return the set of Plex section IDs that cover the given file IDs.

    Returns an empty set if Plex is not configured or unreachable.
    Never raises — Plex errors must not affect file operations.
    """
    conn = db.query(PlexConnection).filter(PlexConnection.is_active.is_(True)).first()
    if conn is None:
        return set()

    try:
        get_or_cache_library_ids(
            db, conn
        )  # populates conn.movie_library_id / conn.tv_library_id if missing
    except Exception:
        logger.warning("Plex: could not resolve library IDs — skipping refresh")
        return set()

    section_ids: set[str] = set()
    for file_id in file_ids:
        section_ids.update(_sections_for_file(db, file_id, conn))
    return section_ids


@router.get("", response_model=PaginatedFileResponse)
async def list_files(
    path: str = Query("/", description="Directory path to list"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    video_only: bool = Query(True, description="Only show video files (directories always shown)"),
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
    files, total = file_service.list_files(
        path=path, page=page, page_size=page_size, video_only=video_only
    )
    logger.info(
        f"list_files(path={path!r}, page={page}, page_size={page_size})"
        f" returned {total} total, {len(files)} on this page"
    )

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


def _classify_filename(
    classifier: PatternRecognitionService, filename: str
) -> FileClassificationResult:
    """Run pattern classification on a single filename and return the result."""
    classification = classifier.classify_file(filename)
    return FileClassificationResult(
        filename=filename,
        type=classification["type"],
        confidence=classification["confidence"],
        pattern_matched=classification["pattern_matched"],
        title=classification.get("title"),
        show_name=classification.get("show_name"),
        year=classification.get("year"),
        season=classification.get("season"),
        episode=classification.get("episode"),
    )


def _classify_file_by_id(
    classifier: PatternRecognitionService, file_service: FileService, file_id: int
) -> FileClassificationResult:
    """Look up a file by ID, classify it, and return the result.

    Raises HTTPException(404) if the file is not found.
    """
    file_item = file_service.get_file_by_id(file_id)
    if not file_item:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
    return _classify_filename(classifier, file_item.name)


@router.post("/classify", response_model=FileClassifyResponse)
async def classify_files(
    request: FileClassifyRequest,
    db: Session = Depends(get_db),
):
    """
    Classify files as movies or TV shows based on filename patterns.

    Accepts filenames directly and/or file IDs to look up. Returns classification
    results with type, confidence, and extracted metadata for each file.
    """
    if not request.filenames and not request.file_ids:
        raise HTTPException(
            status_code=400,
            detail="At least one of 'filenames' or 'file_ids' must be provided",
        )

    classifier = PatternRecognitionService()
    results = []

    if request.filenames:
        for filename in request.filenames:
            results.append(_classify_filename(classifier, filename))

    if request.file_ids:
        file_service = FileService(db)
        for file_id in request.file_ids:
            results.append(_classify_file_by_id(classifier, file_service, file_id))

    return FileClassifyResponse(results=results, total=len(results))


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

    for section_id in _plex_section_ids_for_files(db, [file_id]):
        refresh_plex_library.delay(section_id)

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

    try:
        file_item = file_service.rename_file(file_id, rename_data.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not file_item:
        raise HTTPException(status_code=404, detail="File not found")

    for section_id in _plex_section_ids_for_files(db, [file_id]):
        refresh_plex_library.delay(section_id)

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

    moved_ids = file_service.batch_move_files(request.ids, request.path)

    for section_id in _plex_section_ids_for_files(db, moved_ids):
        refresh_plex_library.delay(section_id)

    return {
        "success": True,
        "message": f"Moved {len(moved_ids)} file(s)",
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
