"""File monitoring service using Watchdog for cross-platform file system event monitoring"""

import logging
import asyncio
from pathlib import Path
from typing import List, Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
from app.core.config import settings, MOVIE_DIR, TV_DIR

logger = logging.getLogger(__name__)


class MediaFileEventHandler(FileSystemEventHandler):
    """Event handler for media file system events"""

    # Comprehensive list of supported media extensions
    MEDIA_EXTENSIONS: Set[str] = {
        # Video formats
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".flv",
        ".wmv",
        ".webm",
        ".m4v",
        ".ts",
        ".m2ts",
        ".mts",
        ".3gp",
        ".3g2",
        ".ogv",
        ".f4v",
        ".asf",
        ".rm",
        ".rmvb",
        ".vob",
        ".divx",
        ".dv",
        ".m2v",
        ".mxf",
        ".mpeg",
        ".mpg",
        ".m1v",
        ".m2p",
        # Audio formats
        ".ogg",
        ".ogm",
        ".m4a",
        ".aac",
        ".flac",
        ".wma",
        ".wav",
        ".alac",
        ".ape",
        ".opus",
        ".wv",
        ".tta",
        ".dsf",
        ".dff",
        ".dsd",
        ".mp2",
        ".mpa",
        # Subtitle formats
        ".srt",
        ".ass",
        ".ssa",
        ".sub",
        ".vtt",
        # Container formats
        ".iso",
    }

    def __init__(self, file_queue: List[str], watch_extensions: Optional[List[str]] = None):
        """
        Initialize the event handler.

        Args:
            file_queue: List to store detected file paths
            watch_extensions: Optional list of extensions to watch (overrides defaults)
        """
        super().__init__()
        self.file_queue = file_queue

        # Use provided extensions or fall back to config, then to defaults
        if watch_extensions:
            self.extensions = set(ext.lower() for ext in watch_extensions)
        elif hasattr(settings, "watch_extensions") and settings.watch_extensions:
            self.extensions = set(ext.lower() for ext in settings.watch_extensions)
        else:
            self.extensions = self.MEDIA_EXTENSIONS

    def _is_media_file(self, file_path: str) -> bool:
        """
        Check if a file has a supported media extension.

        Args:
            file_path: Path to the file

        Returns:
            True if file has a supported media extension, False otherwise
        """
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.extensions

    def _queue_file(self, file_path: str, event_type: str) -> None:
        """
        Add a file to the processing queue.

        Args:
            file_path: Path to the file
            event_type: Type of event (created, modified, etc.)
        """
        if file_path not in self.file_queue:
            self.file_queue.append(file_path)
            logger.info(f"Queued file for processing ({event_type}): {file_path}")
        else:
            logger.debug(f"File already in queue: {file_path}")

    def on_created(self, event: FileCreatedEvent) -> None:
        """
        Handle file creation events.

        Args:
            event: FileCreatedEvent from Watchdog
        """
        if event.is_directory:
            logger.debug(f"Directory created: {event.src_path}")
            return

        if self._is_media_file(event.src_path):
            logger.info(f"Media file created: {event.src_path}")
            self._queue_file(event.src_path, "created")
        else:
            logger.debug(f"Non-media file created (ignored): {event.src_path}")

    def on_modified(self, event: FileModifiedEvent) -> None:
        """
        Handle file modification events.

        Args:
            event: FileModifiedEvent from Watchdog
        """
        if event.is_directory:
            logger.debug(f"Directory modified: {event.src_path}")
            return

        if self._is_media_file(event.src_path):
            logger.info(f"Media file modified: {event.src_path}")
            self._queue_file(event.src_path, "modified")
        else:
            logger.debug(f"Non-media file modified (ignored): {event.src_path}")


class FileMonitorService:
    """Service for monitoring media directories using Watchdog"""

    def __init__(
        self,
        watch_paths: Optional[List[str]] = None,
        watch_extensions: Optional[List[str]] = None,
    ):
        """
        Initialize the file monitor service.

        Args:
            watch_paths: List of directory paths to monitor (defaults to settings.media_directories)
            watch_extensions: Optional list of extensions to watch
        """
        self.watch_paths = watch_paths or [MOVIE_DIR, TV_DIR]
        self.watch_extensions = watch_extensions
        self.observers: List[Observer] = []
        self.file_queue: List[str] = []
        self.is_running = False
        self._lock = asyncio.Lock()

        logger.info(f"FileMonitorService initialized for paths: {self.watch_paths}")

    async def start(self) -> None:
        """
        Start the file monitoring service.

        Raises:
            RuntimeError: If the service is already running or watch paths don't exist
        """
        async with self._lock:
            if self.is_running:
                logger.warning("FileMonitorService is already running")
                return

            try:
                # Create event handler
                event_handler = MediaFileEventHandler(self.file_queue, self.watch_extensions)

                # Validate and monitor each watch path
                for watch_path in self.watch_paths:
                    watch_path_obj = Path(watch_path)
                    if not watch_path_obj.exists():
                        logger.warning(f"Watch path does not exist, creating: {watch_path}")
                        watch_path_obj.mkdir(parents=True, exist_ok=True)

                    # Create and configure observer for each path
                    observer = Observer()
                    observer.schedule(event_handler, path=watch_path, recursive=True)
                    self.observers.append(observer)

                # Start all observers in separate threads
                for observer in self.observers:
                    observer.start()

                self.is_running = True

                logger.info(
                    f"FileMonitorService started - watching: {self.watch_paths} "
                    f"(recursive: True)"
                )

            except Exception as e:
                logger.error(f"Failed to start FileMonitorService: {e}", exc_info=True)
                self.is_running = False
                raise

    async def stop(self) -> None:
        """
        Stop the file monitoring service.

        Gracefully shuts down all observers and cleans up resources.
        """
        async with self._lock:
            if not self.is_running:
                logger.warning("FileMonitorService is not running")
                return

            try:
                for observer in self.observers:
                    observer.stop()
                    observer.join(timeout=5)

                self.observers.clear()
                self.is_running = False
                logger.info("FileMonitorService stopped")

            except Exception as e:
                logger.error(f"Error stopping FileMonitorService: {e}", exc_info=True)
                self.is_running = False

    def get_queued_files(self) -> List[str]:
        """
        Get all queued files and clear the queue.

        Returns:
            List of file paths that were queued
        """
        queued = self.file_queue.copy()
        self.file_queue.clear()

        if queued:
            logger.info(f"Retrieved {len(queued)} queued files")

        return queued

    def peek_queued_files(self) -> List[str]:
        """
        Peek at queued files without clearing the queue.

        Returns:
            List of file paths currently in the queue
        """
        return self.file_queue.copy()

    def clear_queue(self) -> None:
        """Clear all queued files."""
        count = len(self.file_queue)
        self.file_queue.clear()
        logger.info(f"Cleared {count} files from queue")

    def get_status(self) -> dict:
        """
        Get the current status of the file monitor service.

        Returns:
            Dictionary containing service status information
        """
        return {
            "is_running": self.is_running,
            "watch_paths": self.watch_paths,
            "queued_files_count": len(self.file_queue),
            "queued_files": self.file_queue.copy(),
        }

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
