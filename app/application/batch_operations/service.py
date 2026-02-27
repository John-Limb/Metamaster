"""Batch operations service for large-scale processing with progress tracking"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models import BatchOperation, Movie, TVShow, MovieFile, EpisodeFile
from app.infrastructure.file_system.ffprobe_wrapper import FFProbeWrapper
from app.services_impl import TMDBService
import os

logger = logging.getLogger(__name__)


class BatchOperationService:
    """Service for managing batch operations with progress tracking and cancellation support"""

    # Operation types
    OPERATION_METADATA_SYNC = "metadata_sync"
    OPERATION_FILE_IMPORT = "file_import"

    # Status constants
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    # Resource throttling constants
    DEFAULT_BATCH_SIZE = 10
    DEFAULT_CONCURRENT_WORKERS = 3
    MAX_MEMORY_PERCENT = 80  # Stop processing if memory usage exceeds 80%

    def __init__(self, db: Session):
        """Initialize batch operation service

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.ffprobe = FFProbeWrapper()

    def create_batch_operation(
        self,
        operation_type: str,
        total_items: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BatchOperation:
        """Create a new batch operation

        Args:
            operation_type: Type of operation (metadata_sync, file_import)
            total_items: Total number of items to process
            metadata: Optional operation-specific metadata

        Returns:
            Created BatchOperation instance
        """
        batch_op = BatchOperation(
            operation_type=operation_type,
            status=self.STATUS_PENDING,
            total_items=total_items,
            completed_items=0,
            failed_items=0,
            progress_percentage=0.0,
            metadata=json.dumps(metadata) if metadata else None,
        )
        self.db.add(batch_op)
        self.db.commit()
        self.db.refresh(batch_op)
        logger.info(
            f"Created batch operation {batch_op.id} of type {operation_type} with {total_items} items"
        )
        return batch_op

    def get_batch_operation(self, batch_id: int) -> Optional[BatchOperation]:
        """Get batch operation by ID

        Args:
            batch_id: Batch operation ID

        Returns:
            BatchOperation instance or None if not found
        """
        return self.db.query(BatchOperation).filter(BatchOperation.id == batch_id).first()

    def list_batch_operations(
        self,
        operation_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[BatchOperation], int]:
        """List batch operations with optional filtering

        Args:
            operation_type: Filter by operation type
            status: Filter by status
            limit: Number of items to return
            offset: Offset from start

        Returns:
            Tuple of (list of BatchOperation instances, total count)
        """
        query = self.db.query(BatchOperation)

        if operation_type:
            query = query.filter(BatchOperation.operation_type == operation_type)

        if status:
            query = query.filter(BatchOperation.status == status)

        total = query.count()
        operations = (
            query.order_by(BatchOperation.created_at.desc()).offset(offset).limit(limit).all()
        )

        return operations, total

    def _calculate_eta(
        self, batch_op: BatchOperation, total_processed: int
    ) -> Optional[datetime]:
        """Calculate estimated time of completion for a batch operation."""
        if not batch_op.started_at or total_processed == 0:
            return None
        elapsed = datetime.utcnow() - batch_op.started_at
        rate = total_processed / elapsed.total_seconds()
        if rate <= 0:
            return None
        remaining_seconds = (batch_op.total_items - total_processed) / rate
        return datetime.utcnow() + timedelta(seconds=remaining_seconds)

    def _update_progress_if_due(
        self, batch_id: int, index: int, total: int, completed: int, failed: int
    ) -> None:
        """Update progress every 5 items or on the final item."""
        if (index + 1) % 5 == 0 or (index + 1) == total:
            self.update_batch_progress(batch_id, completed, failed)

    def update_batch_progress(
        self,
        batch_id: int,
        completed_items: int,
        failed_items: int,
        error_message: Optional[str] = None,
    ) -> Optional[BatchOperation]:
        """Update batch operation progress

        Args:
            batch_id: Batch operation ID
            completed_items: Number of completed items
            failed_items: Number of failed items
            error_message: Optional error message

        Returns:
            Updated BatchOperation instance or None if not found
        """
        batch_op = self.get_batch_operation(batch_id)
        if not batch_op:
            return None

        batch_op.completed_items = completed_items
        batch_op.failed_items = failed_items

        total_processed = completed_items + failed_items
        if batch_op.total_items > 0:
            batch_op.progress_percentage = (total_processed / batch_op.total_items) * 100.0

        batch_op.eta = self._calculate_eta(batch_op, total_processed)

        if error_message:
            batch_op.error_message = error_message

        batch_op.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(batch_op)

        logger.info(
            f"Updated batch operation {batch_id}: "
            f"completed={completed_items}, failed={failed_items}, "
            f"progress={batch_op.progress_percentage:.1f}%"
        )

        return batch_op

    def start_batch_operation(self, batch_id: int) -> Optional[BatchOperation]:
        """Mark batch operation as started

        Args:
            batch_id: Batch operation ID

        Returns:
            Updated BatchOperation instance or None if not found
        """
        batch_op = self.get_batch_operation(batch_id)
        if not batch_op:
            return None

        batch_op.status = self.STATUS_RUNNING
        batch_op.started_at = datetime.utcnow()
        batch_op.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(batch_op)

        logger.info(f"Started batch operation {batch_id}")
        return batch_op

    def complete_batch_operation(self, batch_id: int) -> Optional[BatchOperation]:
        """Mark batch operation as completed

        Args:
            batch_id: Batch operation ID

        Returns:
            Updated BatchOperation instance or None if not found
        """
        batch_op = self.get_batch_operation(batch_id)
        if not batch_op:
            return None

        batch_op.status = self.STATUS_COMPLETED
        batch_op.completed_at = datetime.utcnow()
        batch_op.progress_percentage = 100.0
        batch_op.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(batch_op)

        logger.info(f"Completed batch operation {batch_id}")
        return batch_op

    def fail_batch_operation(self, batch_id: int, error_message: str) -> Optional[BatchOperation]:
        """Mark batch operation as failed

        Args:
            batch_id: Batch operation ID
            error_message: Error message

        Returns:
            Updated BatchOperation instance or None if not found
        """
        batch_op = self.get_batch_operation(batch_id)
        if not batch_op:
            return None

        batch_op.status = self.STATUS_FAILED
        batch_op.error_message = error_message
        batch_op.completed_at = datetime.utcnow()
        batch_op.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(batch_op)

        logger.error(f"Failed batch operation {batch_id}: {error_message}")
        return batch_op

    def cancel_batch_operation(self, batch_id: int) -> Optional[BatchOperation]:
        """Cancel batch operation

        Args:
            batch_id: Batch operation ID

        Returns:
            Updated BatchOperation instance or None if not found
        """
        batch_op = self.get_batch_operation(batch_id)
        if not batch_op:
            return None

        batch_op.status = self.STATUS_CANCELLED
        batch_op.completed_at = datetime.utcnow()
        batch_op.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(batch_op)

        logger.info(f"Cancelled batch operation {batch_id}")
        return batch_op

    async def _dispatch_media_sync(self, media_id: int, media_type: str) -> Dict[str, Any]:
        """Dispatch metadata sync to the correct handler for the given media type."""
        if media_type == "movie":
            return await self._sync_movie_metadata(media_id)
        if media_type == "tv_show":
            return await self._sync_tvshow_metadata(media_id)
        raise ValueError(f"Invalid media_type: {media_type}")

    async def bulk_metadata_sync(
        self,
        batch_id: int,
        media_ids: List[int],
        media_type: str,
    ) -> Dict[str, Any]:
        """Perform bulk metadata sync for multiple items

        Args:
            batch_id: Batch operation ID
            media_ids: List of media IDs to sync
            media_type: Type of media ("movie" or "tv_show")

        Returns:
            Dictionary with sync results
        """
        batch_op = self.start_batch_operation(batch_id)
        if not batch_op:
            return {"status": "error", "message": "Batch operation not found"}

        completed = 0
        failed = 0
        errors = []

        try:
            for i, media_id in enumerate(media_ids):
                try:
                    result = await self._dispatch_media_sync(media_id, media_type)
                    if result.get("success"):
                        completed += 1
                    else:
                        failed += 1
                        errors.append(f"Item {media_id}: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    failed += 1
                    error_msg = f"Item {media_id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)

                self._update_progress_if_due(batch_id, i, len(media_ids), completed, failed)

            self.complete_batch_operation(batch_id)

            return {
                "status": "success",
                "batch_id": batch_id,
                "completed": completed,
                "failed": failed,
                "total": len(media_ids),
                "errors": errors if errors else None,
            }

        except Exception as e:
            error_msg = f"Bulk metadata sync failed: {str(e)}"
            self.fail_batch_operation(batch_id, error_msg)
            logger.error(error_msg)
            return {
                "status": "error",
                "batch_id": batch_id,
                "message": error_msg,
            }

    async def _sync_movie_metadata(self, movie_id: int) -> Dict[str, Any]:
        """Sync metadata for a single movie

        Args:
            movie_id: Movie ID

        Returns:
            Dictionary with sync result
        """
        try:
            movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
            if not movie:
                return {"success": False, "error": "Movie not found"}

            if not movie.tmdb_id:
                return {"success": True, "message": "No TMDB ID available"}

            tmdb_data = await TMDBService.get_movie_details(self.db, movie.tmdb_id)
            if tmdb_data:
                parsed = TMDBService.parse_movie_details_response(tmdb_data)
                if parsed:
                    movie.plot = parsed.get("plot", movie.plot)
                    movie.rating = parsed.get("rating", movie.rating)
                    movie.runtime = parsed.get("runtime", movie.runtime)
                    movie.genres = parsed.get("genres", movie.genres)
                    movie.updated_at = datetime.utcnow()
                    self.db.commit()
                    return {"success": True}

            return {"success": True, "message": "No data returned from TMDB"}

        except Exception as e:
            logger.error(f"Error syncing movie {movie_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _sync_tvshow_metadata(self, show_id: int) -> Dict[str, Any]:
        """Sync metadata for a single TV show

        Args:
            show_id: TV show ID

        Returns:
            Dictionary with sync result
        """
        try:
            show = self.db.query(TVShow).filter(TVShow.id == show_id).first()
            if not show:
                return {"success": False, "error": "TV show not found"}

            if not show.tmdb_id:
                return {"success": True, "message": "No TMDB ID available"}

            tmdb_data = await TMDBService.get_series_details(self.db, show.tmdb_id)
            if tmdb_data:
                parsed = TMDBService.parse_series_response(tmdb_data)
                if parsed:
                    show.plot = parsed.get("plot", show.plot)
                    show.rating = parsed.get("rating", show.rating)
                    show.genres = parsed.get("genres", show.genres)
                    show.status = parsed.get("status", show.status)
                    show.updated_at = datetime.utcnow()
                    self.db.commit()
                    return {"success": True}

            return {"success": True, "message": "No data returned from TMDB"}

        except Exception as e:
            logger.error(f"Error syncing TV show {show_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    def _analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single file with ffprobe, returning file info or an error dict."""
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
        metadata = self.ffprobe.get_metadata(file_path)
        if "error" in metadata:
            return {"success": False, "error": f"Failed to analyze {file_path}: {metadata['error']}"}
        resolution = metadata.get("resolution", {})
        return {
            "success": True,
            "path": file_path,
            "size": os.path.getsize(file_path),
            "resolution": f"{resolution.get('width', 0)}x{resolution.get('height', 0)}",
            "codec_video": metadata.get("codecs", {}).get("video", "Unknown"),
            "codec_audio": metadata.get("codecs", {}).get("audio", "Unknown"),
            "duration": metadata.get("duration", -1),
            "bitrate": metadata.get("bitrate", {}).get("total", "Unknown"),
        }

    async def bulk_file_import(
        self,
        batch_id: int,
        file_paths: List[str],
        media_type: str,
    ) -> Dict[str, Any]:
        """Perform bulk file import for multiple files

        Args:
            batch_id: Batch operation ID
            file_paths: List of file paths to import
            media_type: Type of media ("movie" or "tv_show")

        Returns:
            Dictionary with import results
        """
        batch_op = self.start_batch_operation(batch_id)
        if not batch_op:
            return {"status": "error", "message": "Batch operation not found"}

        completed = 0
        failed = 0
        errors = []
        imported_files = []

        try:
            for i, file_path in enumerate(file_paths):
                try:
                    result = self._analyze_file(file_path)
                    if result["success"]:
                        imported_files.append(result)
                        completed += 1
                    else:
                        failed += 1
                        errors.append(result["error"])
                except Exception as e:
                    failed += 1
                    error_msg = f"File {file_path}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)

                self._update_progress_if_due(batch_id, i, len(file_paths), completed, failed)

            self.complete_batch_operation(batch_id)

            return {
                "status": "success",
                "batch_id": batch_id,
                "completed": completed,
                "failed": failed,
                "total": len(file_paths),
                "imported_files": imported_files,
                "errors": errors if errors else None,
            }

        except Exception as e:
            error_msg = f"Bulk file import failed: {str(e)}"
            self.fail_batch_operation(batch_id, error_msg)
            logger.error(error_msg)
            return {
                "status": "error",
                "batch_id": batch_id,
                "message": error_msg,
            }

    def get_batch_metadata(self, batch_id: int) -> Optional[Dict[str, Any]]:
        """Get operation-specific metadata for a batch

        Args:
            batch_id: Batch operation ID

        Returns:
            Dictionary with metadata or None if not found
        """
        batch_op = self.get_batch_operation(batch_id)
        if not batch_op or not batch_op.metadata:
            return None

        try:
            return json.loads(batch_op.metadata)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse metadata for batch {batch_id}")
            return None

    def set_batch_metadata(self, batch_id: int, metadata: Dict[str, Any]) -> bool:
        """Set operation-specific metadata for a batch

        Args:
            batch_id: Batch operation ID
            metadata: Metadata dictionary

        Returns:
            True if successful, False otherwise
        """
        batch_op = self.get_batch_operation(batch_id)
        if not batch_op:
            return False

        try:
            batch_op.metadata = json.dumps(metadata)
            batch_op.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to set metadata for batch {batch_id}: {str(e)}")
            return False
