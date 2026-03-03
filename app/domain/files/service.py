"""File domain service for business logic"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import MEDIA_DIRECTORIES, MOVIE_DIR, TV_DIR, settings
from app.domain.files.models import FileItem
from app.domain.files.schemas import FileItemCreate, FileItemUpdate, FileStatsResponse


class FileService:
    """Service for file operations"""

    def __init__(self, db: Session):
        self.db = db
        self.media_dirs = MEDIA_DIRECTORIES

    def _normalize_path(self, path: str) -> str:
        """Normalize a path to be relative to media directories"""
        normalized = Path(path).resolve()
        normalized_str = str(normalized)

        # Check if path is within media directories
        for media_dir in self.media_dirs:
            media_path = Path(media_dir).resolve()
            if str(normalized).startswith(str(media_path)):
                return normalized_str

        # If not within media directories, return as-is
        return normalized_str

    def _get_file_type(self, path: str) -> str:
        """Determine if path is a file or directory"""
        p = Path(path)
        return "directory" if p.is_dir() else "file"

    def _get_mime_type(self, path: str) -> Optional[str]:
        """Get MIME type for a file"""
        import mimetypes

        mime_type, _ = mimetypes.guess_type(path)
        return mime_type

    def _ensure_within_media_dirs(self, path: str) -> bool:
        """Check if path is within allowed media directories"""
        path_obj = Path(path).resolve()
        for media_dir in self.media_dirs:
            media_path = Path(media_dir).resolve()
            if str(path_obj).startswith(str(media_path)):
                return True
        return False

    def list_files(
        self,
        path: str = "/",
        page: int = 1,
        page_size: int = 20,
        video_only: bool = True,
    ) -> Tuple[List[FileItem], int]:
        """
        List files in a directory.

        Args:
            path: Directory path to list
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (file items, total count)
        """
        # Normalize and validate path
        if path == "/" or not path:
            # Query all media directories (resolve to match stored paths)
            path_filters = [
                FileItem.path.startswith(str(Path(media_dir).resolve()))
                for media_dir in self.media_dirs
            ]
        else:
            query_path = self._normalize_path(path)
            path_filters = [FileItem.path.startswith(query_path)]

        # Calculate offset
        offset = (page - 1) * page_size

        # Query database for files in this directory
        files_query = self.db.query(FileItem).filter(
            or_(*path_filters) if len(path_filters) > 1 else path_filters[0]
        )

        # Filter to video files only (keep directories for navigation)
        if video_only:
            video_extensions = {ext.lower() for ext in settings.watch_extensions}
            video_patterns = [FileItem.path.like(f"%{ext}") for ext in video_extensions]
            files_query = files_query.filter(
                or_(
                    FileItem.type == "directory",
                    *video_patterns,
                )
            )

        # Count total
        total = files_query.count()

        # Get paginated results
        files = (
            files_query.order_by(FileItem.type.desc(), FileItem.name)
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return files, total

    def get_file_by_id(self, file_id: int) -> Optional[FileItem]:
        """Get a file by ID"""
        return self.db.query(FileItem).filter(FileItem.id == file_id).first()

    def get_file_by_path(self, path: str) -> Optional[FileItem]:
        """Get a file by path"""
        normalized = self._normalize_path(path)
        return self.db.query(FileItem).filter(FileItem.path == normalized).first()

    def create_file(self, file_data: FileItemCreate) -> FileItem:
        """Create a new file record"""
        # Normalize path
        normalized_path = self._normalize_path(file_data.path)

        # Check if file already exists
        existing = self.get_file_by_path(normalized_path)
        if existing:
            return existing

        # Determine type and mime type
        file_type = file_data.type or self._get_file_type(normalized_path)
        mime_type = file_data.mime_type or self._get_mime_type(normalized_path)

        # Create metadata JSON
        metadata_json = None
        if file_data.metadata:
            metadata_json = json.dumps(file_data.metadata)

        # Create file item
        file_item = FileItem(
            name=file_data.name,
            path=normalized_path,
            type=file_type,
            size=file_data.size,
            mime_type=mime_type,
            metadata_json=metadata_json,
        )

        self.db.add(file_item)
        self.db.commit()
        self.db.refresh(file_item)

        return file_item

    def update_file(self, file_id: int, file_data: FileItemUpdate) -> Optional[FileItem]:
        """Update a file record"""
        file_item = self.get_file_by_id(file_id)
        if not file_item:
            return None

        update_data = file_data.model_dump(exclude_unset=True)

        if "name" in update_data:
            file_item.name = update_data["name"]

        if "path" in update_data:
            new_path = self._normalize_path(update_data["path"])
            file_item.path = new_path

        if "is_indexed" in update_data:
            file_item.is_indexed = update_data["is_indexed"]

        if "metadata" in update_data:
            file_item.metadata_json = (
                json.dumps(update_data["metadata"]) if update_data["metadata"] else None
            )

        file_item.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(file_item)

        return file_item

    def move_file(self, file_id: int, new_path: str) -> Optional[FileItem]:
        """Move a file to a new path"""
        file_item = self.get_file_by_id(file_id)
        if not file_item:
            return None

        # Validate new path is within media directories
        if not self._ensure_within_media_dirs(new_path):
            raise ValueError(f"Path must be within media directories: {self.media_dirs}")

        # Get new name from path
        new_name = Path(new_path).name

        # Move the file on disk
        old_path = file_item.path
        try:
            if Path(old_path).exists():
                shutil.move(old_path, new_path)
            file_item.path = new_path
            file_item.name = new_name
            file_item.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(file_item)
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to move file: {str(e)}")

        return file_item

    def rename_file(self, file_id: int, new_name: str) -> Optional[FileItem]:
        """Rename a file"""
        file_item = self.get_file_by_id(file_id)
        if not file_item:
            return None

        # Get current directory
        current_path = Path(file_item.path)
        new_path = current_path.parent / new_name

        return self.move_file(file_id, str(new_path))

    def delete_file(self, file_id: int, delete_from_disk: bool = False) -> bool:
        """Delete a file record and optionally from disk"""
        file_item = self.get_file_by_id(file_id)
        if not file_item:
            return False

        # Delete from disk if requested
        if delete_from_disk:
            try:
                if file_item.type == "directory":
                    shutil.rmtree(file_item.path)
                else:
                    os.remove(file_item.path)
            except Exception as e:
                raise ValueError(f"Failed to delete file from disk: {str(e)}")

        # Delete from database
        self.db.delete(file_item)
        self.db.commit()

        return True

    def batch_delete_files(self, file_ids: List[int], delete_from_disk: bool = False) -> int:
        """Delete multiple files"""
        deleted_count = 0
        for file_id in file_ids:
            if self.delete_file(file_id, delete_from_disk):
                deleted_count += 1
        return deleted_count

    def batch_move_files(self, file_ids: List[int], new_path: str) -> int:
        """Move multiple files to a new path"""
        moved_count = 0
        for file_id in file_ids:
            try:
                if self.move_file(file_id, new_path):
                    moved_count += 1
            except ValueError:
                continue
        return moved_count

    def search_files(
        self, query: str, page: int = 1, page_size: int = 20
    ) -> Tuple[List[FileItem], int]:
        """Search files by name"""
        offset = (page - 1) * page_size

        # Search in database
        files_query = self.db.query(FileItem).filter(
            or_(
                FileItem.name.ilike(f"%{query}%"),
                FileItem.path.ilike(f"%{query}%"),
            )
        )

        total = files_query.count()

        files = files_query.order_by(FileItem.name).offset(offset).limit(page_size).all()

        return files, total

    def get_file_stats(self) -> FileStatsResponse:
        """Get file statistics (video files only)"""
        video_extensions = {ext.lower() for ext in settings.watch_extensions}
        movie_dir_resolved = str(Path(MOVIE_DIR).resolve())
        tv_dir_resolved = str(Path(TV_DIR).resolve())

        # Get all file paths and sizes in one query
        files = self.db.query(FileItem.path, FileItem.size).filter(FileItem.type == "file").all()

        # Filter to video files and categorize
        total_files = 0
        total_size = 0
        movie_count = 0
        tv_show_count = 0
        files_by_type = {}

        for path, size in files:
            ext = Path(path).suffix.lower()
            if ext not in video_extensions:
                continue

            total_files += 1
            total_size += size or 0
            files_by_type[ext] = files_by_type.get(ext, 0) + 1

            if path.startswith(movie_dir_resolved):
                movie_count += 1
            elif path.startswith(tv_dir_resolved):
                tv_show_count += 1

        # Get last updated
        last_updated = self.db.query(FileItem).order_by(FileItem.updated_at.desc()).first()
        last_updated_time = last_updated.updated_at if last_updated else datetime.utcnow()

        return FileStatsResponse(
            totalFiles=total_files,
            totalSize=total_size,
            filesByType=files_by_type,
            lastUpdated=last_updated_time,
            movieCount=movie_count,
            tvShowCount=tv_show_count,
        )

    def sync_directory(self, path: str) -> int:
        """Sync a directory to the database"""
        if not self._ensure_within_media_dirs(path):
            raise ValueError(f"Path must be within media directories: {self.media_dirs}")

        synced_count = 0

        for root, dirs, files in os.walk(path):
            # Process directories
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                file_data = FileItemCreate(
                    name=dir_name,
                    path=str(dir_path),
                    type="directory",
                )
                self.create_file(file_data)
                synced_count += 1

            # Process files (video files only)
            video_extensions = {ext.lower() for ext in settings.watch_extensions}
            for file_name in files:
                file_path = Path(root) / file_name
                if file_path.suffix.lower() not in video_extensions:
                    continue

                file_type = self._get_file_type(str(file_path))
                mime_type = self._get_mime_type(str(file_path))
                file_size = file_path.stat().st_size if file_path.exists() else None

                file_data = FileItemCreate(
                    name=file_name,
                    path=str(file_path),
                    type=file_type,
                    size=file_size,
                    mime_type=mime_type,
                )
                self.create_file(file_data)
                synced_count += 1

        return synced_count

    def file_to_response(self, file_item: FileItem) -> dict:
        """Convert a FileItem to a response dictionary"""
        metadata = None
        if file_item.metadata_json:
            try:
                metadata = json.loads(file_item.metadata_json)
            except json.JSONDecodeError:
                metadata = None

        return {
            "id": str(file_item.id),
            "name": file_item.name,
            "path": file_item.path,
            "type": file_item.type,
            "size": file_item.size,
            "mime_type": file_item.mime_type,
            "created_at": file_item.created_at.isoformat(),
            "updated_at": file_item.updated_at.isoformat(),
            "is_indexed": file_item.is_indexed,
            "metadata": metadata,
        }
