"""File Queue Management System

This module provides a FileQueueManager class for handling persistent storage
and processing of detected media files with support for status tracking,
duplicate detection, error logging, and retry logic.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.application.pattern_recognition.service import PatternRecognitionService
from app.core.database import SessionLocal
from app.models import FileQueue

logger = logging.getLogger(__name__)


class FileQueueManager:
    """Manages file queue operations with persistent storage and processing tracking."""

    # Queue status constants
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    VALID_STATUSES = {
        STATUS_PENDING,
        STATUS_PROCESSING,
        STATUS_COMPLETED,
        STATUS_FAILED,
    }

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize FileQueueManager.

        Args:
            session: SQLAlchemy session. If None, creates a new session.
        """
        self.session = session or SessionLocal()
        self._owns_session = session is None
        self._classifier = PatternRecognitionService()

    def __del__(self):
        """Clean up session if manager owns it."""
        if self._owns_session and self.session:
            self.session.close()

    def add_file(
        self,
        file_path: str,
        file_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Add a file to the queue.

        Args:
            file_path: Path to the file
            file_type: Type of media ("movie" or "tv_show"). If None, auto-classified from filename.
            metadata: Optional metadata dictionary (currently unused but reserved for future use)

        Returns:
            Queue ID of the added file

        Raises:
            ValueError: If file_path is empty or file_type is invalid
            RuntimeError: If database operation fails
        """
        if not file_path or not file_path.strip():
            raise ValueError("file_path cannot be empty")

        if file_type is None:
            result = self._classifier.classify_file(file_path)
            file_type = result["type"]
            logger.info(
                f"Auto-classified '{file_path}' as '{file_type}' "
                f"(confidence: {result.get('confidence', 'unknown')})"
            )

        if file_type not in ("movie", "tv_show"):
            raise ValueError(f"file_type must be 'movie' or 'tv_show', got '{file_type}'")

        try:
            # Check for duplicate
            existing = (
                self.session.query(FileQueue).filter(FileQueue.file_path == file_path).first()
            )

            if existing:
                logger.warning(f"File already in queue: {file_path}")
                return existing.id

            # Create new queue entry
            queue_entry = FileQueue(
                file_path=file_path,
                media_type=file_type,
                status=self.STATUS_PENDING,
                created_at=datetime.utcnow(),
            )

            self.session.add(queue_entry)
            self.session.commit()

            logger.info(f"Added file to queue: {file_path} (ID: {queue_entry.id})")
            return queue_entry.id

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to add file to queue: {str(e)}")
            raise RuntimeError(f"Failed to add file to queue: {str(e)}")

    def add_files_batch(self, files: List[Dict[str, Any]]) -> List[int]:
        """
        Add multiple files to the queue in a batch operation.

        Args:
            files: List of dictionaries with keys 'file_path', 'file_type', and optional 'metadata'

        Returns:
            List of queue IDs for added files

        Raises:
            ValueError: If files list is empty or contains invalid entries
            RuntimeError: If database operation fails
        """
        if not files:
            raise ValueError("files list cannot be empty")

        queue_ids = []
        entries_to_add = []
        seen_paths = set()

        try:
            for file_entry in files:
                if not isinstance(file_entry, dict):
                    logger.warning("Skipping entry that is not a dictionary")
                    continue

                file_path = file_entry.get("file_path")
                file_type = file_entry.get("file_type")

                if not file_path or not file_path.strip():
                    logger.warning("Skipping entry with empty file_path")
                    continue

                if file_type is None:
                    result = self._classifier.classify_file(file_path)
                    file_type = result["type"]
                    logger.info(
                        f"Auto-classified '{file_path}' as '{file_type}' "
                        f"(confidence: {result.get('confidence', 'unknown')})"
                    )

                if file_type not in ("movie", "tv_show"):
                    logger.warning(f"Skipping entry with invalid file_type: {file_type}")
                    continue

                # Check for duplicate within this batch
                if file_path in seen_paths:
                    logger.warning(f"Duplicate within batch, skipping: {file_path}")
                    continue

                # Check for duplicate in database
                existing = (
                    self.session.query(FileQueue).filter(FileQueue.file_path == file_path).first()
                )

                if existing:
                    logger.warning(f"File already in queue, skipping: {file_path}")
                    queue_ids.append(existing.id)
                    seen_paths.add(file_path)
                    continue

                # Create new queue entry
                queue_entry = FileQueue(
                    file_path=file_path,
                    media_type=file_type,
                    status=self.STATUS_PENDING,
                    created_at=datetime.utcnow(),
                )

                entries_to_add.append(queue_entry)
                seen_paths.add(file_path)

            # Add all new entries and flush to get IDs
            for entry in entries_to_add:
                self.session.add(entry)

            self.session.flush()

            # Collect IDs from newly added entries
            for entry in entries_to_add:
                queue_ids.append(entry.id)

            self.session.commit()
            logger.info(f"Added {len(queue_ids)} files to queue in batch operation")
            return queue_ids

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to add files batch to queue: {str(e)}")
            raise RuntimeError(f"Failed to add files batch to queue: {str(e)}")

    def get_pending_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get pending files for processing.

        Args:
            limit: Maximum number of files to return

        Returns:
            List of pending file entries with their queue information

        Raises:
            ValueError: If limit is not positive
            RuntimeError: If database operation fails
        """
        if limit <= 0:
            raise ValueError("limit must be positive")

        try:
            pending_files = (
                self.session.query(FileQueue)
                .filter(FileQueue.status == self.STATUS_PENDING)
                .order_by(FileQueue.created_at)
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": f.id,
                    "file_path": f.file_path,
                    "media_type": f.media_type,
                    "status": f.status,
                    "created_at": f.created_at,
                }
                for f in pending_files
            ]

        except Exception as e:
            logger.error(f"Failed to get pending files: {str(e)}")
            raise RuntimeError(f"Failed to get pending files: {str(e)}")

    def mark_processing(self, queue_id: int) -> bool:
        """
        Mark a file as being processed.

        Args:
            queue_id: ID of the queue entry

        Returns:
            True if successful, False if entry not found

        Raises:
            RuntimeError: If database operation fails
        """
        try:
            queue_entry = self.session.query(FileQueue).filter(FileQueue.id == queue_id).first()

            if not queue_entry:
                logger.warning(f"Queue entry not found: {queue_id}")
                return False

            queue_entry.status = self.STATUS_PROCESSING
            self.session.commit()

            logger.info(f"Marked queue entry as processing: {queue_id}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to mark file as processing: {str(e)}")
            raise RuntimeError(f"Failed to mark file as processing: {str(e)}")

    def mark_completed(self, queue_id: int, result_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Mark a file as completed.

        Args:
            queue_id: ID of the queue entry
            result_data: Optional result data (currently unused but reserved for future use)

        Returns:
            True if successful, False if entry not found

        Raises:
            RuntimeError: If database operation fails
        """
        try:
            queue_entry = self.session.query(FileQueue).filter(FileQueue.id == queue_id).first()

            if not queue_entry:
                logger.warning(f"Queue entry not found: {queue_id}")
                return False

            queue_entry.status = self.STATUS_COMPLETED
            queue_entry.processed_at = datetime.utcnow()
            queue_entry.error_message = None
            self.session.commit()

            logger.info(f"Marked queue entry as completed: {queue_id}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to mark file as completed: {str(e)}")
            raise RuntimeError(f"Failed to mark file as completed: {str(e)}")

    def mark_failed(self, queue_id: int, error_message: str) -> bool:
        """
        Mark a file as failed.

        Args:
            queue_id: ID of the queue entry
            error_message: Error message describing the failure

        Returns:
            True if successful, False if entry not found

        Raises:
            ValueError: If error_message is empty
            RuntimeError: If database operation fails
        """
        if not error_message or not error_message.strip():
            raise ValueError("error_message cannot be empty")

        try:
            queue_entry = self.session.query(FileQueue).filter(FileQueue.id == queue_id).first()

            if not queue_entry:
                logger.warning(f"Queue entry not found: {queue_id}")
                return False

            queue_entry.status = self.STATUS_FAILED
            queue_entry.error_message = error_message
            queue_entry.processed_at = datetime.utcnow()
            self.session.commit()

            logger.warning(f"Marked queue entry as failed: {queue_id} - {error_message}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to mark file as failed: {str(e)}")
            raise RuntimeError(f"Failed to mark file as failed: {str(e)}")

    def get_file_status(self, queue_id: int) -> Dict[str, Any]:
        """
        Get current status of a queued file.

        Args:
            queue_id: ID of the queue entry

        Returns:
            Dictionary with file status information

        Raises:
            RuntimeError: If database operation fails or entry not found
        """
        try:
            queue_entry = self.session.query(FileQueue).filter(FileQueue.id == queue_id).first()

            if not queue_entry:
                raise RuntimeError(f"Queue entry not found: {queue_id}")

            return {
                "id": queue_entry.id,
                "file_path": queue_entry.file_path,
                "status": queue_entry.status,
                "media_type": queue_entry.media_type,
                "error_message": queue_entry.error_message,
                "created_at": queue_entry.created_at,
                "processed_at": queue_entry.processed_at,
            }

        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"Failed to get file status: {str(e)}")
            raise RuntimeError(f"Failed to get file status: {str(e)}")

    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get overall queue statistics.

        Returns:
            Dictionary with queue statistics including counts by status

        Raises:
            RuntimeError: If database operation fails
        """
        try:
            total = self.session.query(FileQueue).count()
            pending = (
                self.session.query(FileQueue)
                .filter(FileQueue.status == self.STATUS_PENDING)
                .count()
            )
            processing = (
                self.session.query(FileQueue)
                .filter(FileQueue.status == self.STATUS_PROCESSING)
                .count()
            )
            completed = (
                self.session.query(FileQueue)
                .filter(FileQueue.status == self.STATUS_COMPLETED)
                .count()
            )
            failed = (
                self.session.query(FileQueue).filter(FileQueue.status == self.STATUS_FAILED).count()
            )

            return {
                "total": total,
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
            }

        except Exception as e:
            logger.error(f"Failed to get queue statistics: {str(e)}")
            raise RuntimeError(f"Failed to get queue statistics: {str(e)}")

    def is_duplicate(self, file_path: str) -> bool:
        """
        Check if a file already exists in the queue.

        Args:
            file_path: Path to the file

        Returns:
            True if file is already in queue, False otherwise

        Raises:
            ValueError: If file_path is empty
            RuntimeError: If database operation fails
        """
        if not file_path or not file_path.strip():
            raise ValueError("file_path cannot be empty")

        try:
            existing = (
                self.session.query(FileQueue).filter(FileQueue.file_path == file_path).first()
            )

            return existing is not None

        except Exception as e:
            logger.error(f"Failed to check for duplicate: {str(e)}")
            raise RuntimeError(f"Failed to check for duplicate: {str(e)}")

    def retry_failed_file(self, queue_id: int) -> bool:
        """
        Retry a failed file by resetting its status to pending.

        Args:
            queue_id: ID of the queue entry

        Returns:
            True if successful, False if entry not found or not in failed status

        Raises:
            RuntimeError: If database operation fails
        """
        try:
            queue_entry = self.session.query(FileQueue).filter(FileQueue.id == queue_id).first()

            if not queue_entry:
                logger.warning(f"Queue entry not found: {queue_id}")
                return False

            if queue_entry.status != self.STATUS_FAILED:
                logger.warning(
                    f"Cannot retry file not in failed status: {queue_id}"
                    f" (status: {queue_entry.status})"
                )
                return False

            queue_entry.status = self.STATUS_PENDING
            queue_entry.error_message = None
            queue_entry.processed_at = None
            self.session.commit()

            logger.info(f"Retried failed file: {queue_id}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to retry file: {str(e)}")
            raise RuntimeError(f"Failed to retry file: {str(e)}")

    def clear_completed_files(self, days_old: int = 7) -> int:
        """
        Clean up old completed files from the queue.

        Args:
            days_old: Delete completed files older than this many days

        Returns:
            Number of files deleted

        Raises:
            ValueError: If days_old is not positive
            RuntimeError: If database operation fails
        """
        if days_old <= 0:
            raise ValueError("days_old must be positive")

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            deleted_count = (
                self.session.query(FileQueue)
                .filter(
                    and_(
                        FileQueue.status == self.STATUS_COMPLETED,
                        FileQueue.processed_at < cutoff_date,
                    )
                )
                .delete()
            )

            self.session.commit()

            logger.info(f"Cleared {deleted_count} completed files older than {days_old} days")
            return deleted_count

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to clear completed files: {str(e)}")
            raise RuntimeError(f"Failed to clear completed files: {str(e)}")
