"""Tests for the FileMonitorService"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from app.infrastructure.file_system.monitor import FileMonitorService, MediaFileEventHandler


@pytest.fixture
def temp_media_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def file_monitor(temp_media_dir):
    """Create a FileMonitorService instance for testing"""
    return FileMonitorService(watch_path=temp_media_dir)


@pytest.mark.asyncio
async def test_file_monitor_initialization(file_monitor, temp_media_dir):
    """Test FileMonitorService initialization"""
    assert file_monitor.watch_path == temp_media_dir
    assert file_monitor.is_running is False
    assert file_monitor.file_queue == []


@pytest.mark.asyncio
async def test_file_monitor_start_stop(file_monitor):
    """Test starting and stopping the file monitor"""
    await file_monitor.start()
    assert file_monitor.is_running is True

    await file_monitor.stop()
    assert file_monitor.is_running is False


@pytest.mark.asyncio
async def test_file_monitor_start_creates_directory(temp_media_dir):
    """Test that start() creates the watch directory if it doesn't exist"""
    non_existent_dir = Path(temp_media_dir) / "non_existent"
    assert not non_existent_dir.exists()

    monitor = FileMonitorService(watch_path=str(non_existent_dir))
    await monitor.start()

    assert non_existent_dir.exists()
    await monitor.stop()


@pytest.mark.asyncio
async def test_file_monitor_double_start(file_monitor):
    """Test that starting an already running monitor is safe"""
    await file_monitor.start()
    assert file_monitor.is_running is True

    # Starting again should not raise an error
    await file_monitor.start()
    assert file_monitor.is_running is True

    await file_monitor.stop()


@pytest.mark.asyncio
async def test_file_monitor_stop_when_not_running(file_monitor):
    """Test that stopping a non-running monitor is safe"""
    assert file_monitor.is_running is False

    # Stopping when not running should not raise an error
    await file_monitor.stop()
    assert file_monitor.is_running is False


@pytest.mark.asyncio
async def test_get_queued_files_clears_queue(file_monitor):
    """Test that get_queued_files clears the queue"""
    file_monitor.file_queue = ["/path/to/file1.mp4", "/path/to/file2.mkv"]

    queued = file_monitor.get_queued_files()

    assert len(queued) == 2
    assert "/path/to/file1.mp4" in queued
    assert "/path/to/file2.mkv" in queued
    assert len(file_monitor.file_queue) == 0


@pytest.mark.asyncio
async def test_peek_queued_files_preserves_queue(file_monitor):
    """Test that peek_queued_files doesn't clear the queue"""
    file_monitor.file_queue = ["/path/to/file1.mp4", "/path/to/file2.mkv"]

    peeked = file_monitor.peek_queued_files()

    assert len(peeked) == 2
    assert "/path/to/file1.mp4" in peeked
    assert "/path/to/file2.mkv" in peeked
    assert len(file_monitor.file_queue) == 2


@pytest.mark.asyncio
async def test_clear_queue(file_monitor):
    """Test clearing the queue"""
    file_monitor.file_queue = ["/path/to/file1.mp4", "/path/to/file2.mkv"]

    file_monitor.clear_queue()

    assert len(file_monitor.file_queue) == 0


@pytest.mark.asyncio
async def test_get_status(file_monitor, temp_media_dir):
    """Test getting service status"""
    file_monitor.file_queue = ["/path/to/file1.mp4"]

    status = file_monitor.get_status()

    assert status["is_running"] is False
    assert status["watch_path"] == temp_media_dir
    assert status["queued_files_count"] == 1
    assert "/path/to/file1.mp4" in status["queued_files"]


@pytest.mark.asyncio
async def test_context_manager(file_monitor):
    """Test using FileMonitorService as an async context manager"""
    async with file_monitor:
        assert file_monitor.is_running is True

    assert file_monitor.is_running is False


def test_media_file_event_handler_is_media_file():
    """Test media file detection"""
    handler = MediaFileEventHandler([])

    # Test video formats (from config)
    assert handler._is_media_file("video.mp4") is True
    assert handler._is_media_file("video.mkv") is True
    assert handler._is_media_file("video.avi") is True
    assert handler._is_media_file("video.mov") is True
    assert handler._is_media_file("video.mpg") is True

    # Test non-media files
    assert handler._is_media_file("document.txt") is False
    assert handler._is_media_file("image.jpg") is False
    assert handler._is_media_file("archive.zip") is False
    assert handler._is_media_file("audio.mp3") is False  # mp3 not in config


def test_media_file_event_handler_queue_file():
    """Test file queueing"""
    queue = []
    handler = MediaFileEventHandler(queue)

    handler._queue_file("/path/to/file1.mp4", "created")
    assert len(queue) == 1
    assert "/path/to/file1.mp4" in queue

    # Queueing the same file again should not add a duplicate
    handler._queue_file("/path/to/file1.mp4", "modified")
    assert len(queue) == 1

    # Queueing a different file should add it
    handler._queue_file("/path/to/file2.mkv", "created")
    assert len(queue) == 2


def test_media_file_event_handler_custom_extensions():
    """Test custom extension filtering"""
    queue = []
    custom_extensions = [".mp4", ".avi"]
    handler = MediaFileEventHandler(queue, custom_extensions)

    assert handler._is_media_file("video.mp4") is True
    assert handler._is_media_file("video.avi") is True
    assert handler._is_media_file("video.mkv") is False  # Not in custom list
    assert handler._is_media_file("audio.flac") is False  # Not in custom list
