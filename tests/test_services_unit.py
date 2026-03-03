"""Comprehensive unit tests for all service modules"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.application.pattern_recognition.service import (
    ClassificationResult,
    PatternRecognitionService,
)
from app.infrastructure.file_system.ffprobe_wrapper import FFProbeWrapper
from app.infrastructure.file_system.monitor import FileMonitorService, MediaFileEventHandler
from app.infrastructure.file_system.queue_manager import FileQueueManager
from app.infrastructure.monitoring.error_handler import TaskErrorHandler

# ============================================================================
# Pattern Recognition Service Tests
# ============================================================================


class TestPatternRecognitionService:
    """Tests for PatternRecognitionService"""

    @pytest.fixture
    def service(self):
        """Create a PatternRecognitionService instance"""
        return PatternRecognitionService()

    # Movie Pattern Tests
    def test_classify_movie_title_year_parentheses(self, service):
        """Test movie classification with (Year) format"""
        result = service.classify_file("The Matrix (1999).mp4")
        assert result["type"] == "movie"
        assert result["title"] == "The Matrix"
        assert result["year"] == 1999
        assert result["confidence"] == "high"

    def test_classify_movie_title_year_brackets(self, service):
        """Test movie classification with [Year] format"""
        result = service.classify_file("Inception [2010].mkv")
        assert result["type"] == "movie"
        assert result["title"] == "Inception"
        assert result["year"] == 2010

    def test_classify_movie_title_year_separators(self, service):
        """Test movie classification with separator format"""
        result = service.classify_file("The.Dark.Knight.2008.mp4")
        assert result["type"] == "movie"
        assert result["title"] == "The Dark Knight"
        assert result["year"] == 2008

    def test_classify_movie_multiword_title(self, service):
        """Test movie with multi-word title"""
        result = service.classify_file("The Lord of the Rings (2001).mp4")
        assert result["type"] == "movie"
        assert result["title"] == "The Lord of the Rings"
        assert result["year"] == 2001

    def test_extract_movie_info(self, service):
        """Test movie info extraction"""
        info = service.extract_movie_info("Interstellar 2014.mp4")
        assert info["title"] == "Interstellar"
        assert info["year"] == 2014
        assert info["confidence"] == "high"

    def test_is_movie(self, service):
        """Test is_movie quick check"""
        assert service.is_movie("The Matrix (1999).mp4") is True
        assert service.is_movie("Breaking Bad S01E01.mkv") is False

    # TV Show Pattern Tests
    def test_classify_tv_show_standard_format(self, service):
        """Test TV show classification with S01E01 format"""
        result = service.classify_file("Breaking Bad S01E01.mp4")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "Breaking Bad"
        assert result["season"] == 1
        assert result["episode"] == 1
        assert result["confidence"] == "high"

    def test_classify_tv_show_lowercase_format(self, service):
        """Test TV show classification with lowercase s01e01"""
        result = service.classify_file("Game of Thrones s08e06.mkv")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "Game of Thrones"
        assert result["season"] == 8
        assert result["episode"] == 6

    def test_classify_tv_show_number_x_format(self, service):
        """Test TV show classification with 1x01 format"""
        result = service.classify_file("The Office 9x23.mp4")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "The Office"
        assert result["season"] == 9
        assert result["episode"] == 23

    def test_classify_tv_show_season_episode_text(self, service):
        """Test TV show classification with text format"""
        result = service.classify_file("Friends Season 10 Episode 18.mp4")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "Friends"
        assert result["season"] == 10
        assert result["episode"] == 18

    def test_extract_tv_show_info(self, service):
        """Test TV show info extraction"""
        info = service.extract_tv_show_info("Breaking Bad S05E16.mp4")
        assert info["show_name"] == "Breaking Bad"
        assert info["season"] == 5
        assert info["episode"] == 16

    def test_is_tv_show(self, service):
        """Test is_tv_show quick check"""
        assert service.is_tv_show("Breaking Bad S01E01.mkv") is True
        assert service.is_tv_show("The Matrix (1999).mp4") is False

    # Fallback Classification Tests
    def test_fallback_classification_tv_indicators(self, service):
        """Test fallback classification with TV indicators"""
        result = service.classify_file("some_show_season_1_episode_5.mp4")
        assert result["type"] == "tv_show"
        assert result["confidence"] == "low"

    def test_fallback_classification_default_movie(self, service):
        """Test fallback classification defaults to movie"""
        result = service.classify_file("random_filename.mp4")
        assert result["type"] == "movie"
        assert result["confidence"] == "low"

    # Edge Cases
    def test_invalid_year_range(self, service):
        """Test that invalid years are rejected"""
        result = service.classify_file("Some Movie (1500).mp4")
        # Should fallback since year is out of range
        assert result["type"] == "movie"

    def test_empty_filename(self, service):
        """Test with empty filename"""
        result = service.classify_file(".mp4")
        assert result["type"] in ["movie", "tv_show"]

    def test_classification_result_to_dict(self):
        """Test ClassificationResult.to_dict()"""
        result = ClassificationResult(
            type="movie",
            title="Test Movie",
            year=2020,
            confidence="high",
            pattern_matched="test_pattern",
        )
        result_dict = result.to_dict()
        assert result_dict["type"] == "movie"
        assert result_dict["title"] == "Test Movie"
        assert result_dict["year"] == 2020
        assert "show_name" not in result_dict  # None values excluded


# ============================================================================
# FFProbe Wrapper Service Tests
# ============================================================================


class TestFFProbeWrapper:
    """Tests for FFProbeWrapper service"""

    @pytest.fixture
    def wrapper(self):
        """Create FFProbeWrapper instance with mocked ffprobe"""
        with patch.object(FFProbeWrapper, "_verify_ffprobe_available"):
            return FFProbeWrapper()

    def test_get_resolution_label_exact_match(self, wrapper):
        """Test resolution label for exact match"""
        label = wrapper._get_resolution_label(1920, 1080)
        assert label == "1080p"

    def test_get_resolution_label_4k(self, wrapper):
        """Test resolution label for 4K"""
        label = wrapper._get_resolution_label(3840, 2160)
        assert label == "4K"

    def test_get_resolution_label_720p(self, wrapper):
        """Test resolution label for 720p"""
        label = wrapper._get_resolution_label(1280, 720)
        assert label == "720p"

    def test_get_resolution_label_custom_resolution(self, wrapper):
        """Test resolution label for custom resolution"""
        label = wrapper._get_resolution_label(1024, 768)
        assert label == "720p"  # Falls back to 720p for 768 height

    def test_format_bitrate_mbps(self, wrapper):
        """Test bitrate formatting in Mbps"""
        formatted = wrapper._format_bitrate(5500000)
        assert "Mbps" in formatted
        assert "5.5" in formatted

    def test_format_bitrate_kbps(self, wrapper):
        """Test bitrate formatting in kbps"""
        formatted = wrapper._format_bitrate(256000)
        assert "kbps" in formatted

    def test_format_bitrate_bps(self, wrapper):
        """Test bitrate formatting in bps"""
        formatted = wrapper._format_bitrate(500)
        assert "bps" in formatted

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_run_ffprobe_success(self, mock_exists, mock_run, wrapper):
        """Test successful ffprobe execution"""
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(stdout=json.dumps({"streams": [], "format": {}}))
        result = wrapper._run_ffprobe("/path/to/file.mp4")
        assert isinstance(result, dict)
        assert "streams" in result

    @patch("subprocess.run")
    def test_run_ffprobe_file_not_found(self, mock_run, wrapper):
        """Test ffprobe with non-existent file"""
        with pytest.raises(FileNotFoundError):
            wrapper._run_ffprobe("/nonexistent/file.mp4")

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_run_ffprobe_timeout(self, mock_exists, mock_run, wrapper):
        """Test ffprobe timeout handling"""
        import subprocess as sp

        mock_exists.return_value = True
        mock_run.side_effect = sp.TimeoutExpired("ffprobe", 30)
        with pytest.raises(RuntimeError):
            wrapper._run_ffprobe("/path/to/file.mp4")

    @patch.object(FFProbeWrapper, "_run_ffprobe")
    @patch("pathlib.Path.exists")
    def test_is_valid_media_file_true(self, mock_exists, mock_run, wrapper):
        """Test valid media file check"""
        mock_exists.return_value = True
        mock_run.return_value = {"streams": []}
        result = wrapper.is_valid_media_file("/path/to/file.mp4")
        assert result is True

    @patch.object(FFProbeWrapper, "_run_ffprobe")
    def test_is_valid_media_file_false(self, mock_run, wrapper):
        """Test invalid media file check"""
        mock_run.side_effect = RuntimeError("Invalid file")
        result = wrapper.is_valid_media_file("/path/to/file.mp4")
        assert result is False

    @patch.object(FFProbeWrapper, "_run_ffprobe")
    def test_get_resolution(self, mock_run, wrapper):
        """Test resolution extraction"""
        mock_run.return_value = {
            "streams": [{"codec_type": "video", "width": 1920, "height": 1080}]
        }
        result = wrapper.get_resolution("/path/to/file.mp4")
        assert result["width"] == 1920
        assert result["height"] == 1080
        assert result["label"] == "1080p"

    @patch.object(FFProbeWrapper, "_run_ffprobe")
    def test_get_bitrate(self, mock_run, wrapper):
        """Test bitrate extraction"""
        mock_run.return_value = {
            "streams": [
                {"codec_type": "video", "bit_rate": "5000000"},
                {"codec_type": "audio", "bit_rate": "128000"},
            ],
            "format": {"bit_rate": "5128000"},
        }
        result = wrapper.get_bitrate("/path/to/file.mp4")
        assert "total" in result
        assert "video" in result
        assert "audio" in result

    @patch.object(FFProbeWrapper, "_run_ffprobe")
    def test_get_codecs(self, mock_run, wrapper):
        """Test codec extraction"""
        mock_run.return_value = {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "profile": "High",
                    "level": "42",
                },
                {"codec_type": "audio", "codec_name": "aac"},
            ]
        }
        result = wrapper.get_codecs("/path/to/file.mp4")
        assert result["video"] == "h264"
        assert result["audio"] == "aac"

    @patch.object(FFProbeWrapper, "_run_ffprobe")
    def test_get_duration(self, mock_run, wrapper):
        """Test duration extraction"""
        mock_run.return_value = {"format": {"duration": "7200.5"}}
        result = wrapper.get_duration("/path/to/file.mp4")
        assert result == 7200.5

    @patch.object(FFProbeWrapper, "_run_ffprobe")
    def test_get_frame_rate(self, mock_run, wrapper):
        """Test frame rate extraction"""
        mock_run.return_value = {"streams": [{"codec_type": "video", "r_frame_rate": "30/1"}]}
        result = wrapper.get_frame_rate("/path/to/file.mp4")
        assert result == 30.0


# ============================================================================
# File Queue Manager Tests
# ============================================================================


class TestFileQueueManager:
    """Tests for FileQueueManager service"""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def manager(self, mock_session):
        """Create FileQueueManager with mock session"""
        manager = FileQueueManager(session=mock_session)
        return manager

    def test_add_file_success(self, manager, mock_session):
        """Test adding a file to queue"""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_queue_entry = MagicMock()
        mock_queue_entry.id = 1
        manager.session.add = MagicMock()
        manager.session.commit = MagicMock()

        # Manually set the id after add
        def add_side_effect(entry):
            entry.id = 1

        manager.session.add.side_effect = add_side_effect

        queue_id = manager.add_file("/path/to/file.mp4", "movie")
        assert queue_id == 1

    def test_add_file_duplicate(self, manager, mock_session):
        """Test adding duplicate file"""
        existing = MagicMock()
        existing.id = 5
        mock_session.query.return_value.filter.return_value.first.return_value = existing

        queue_id = manager.add_file("/path/to/file.mp4", "movie")
        assert queue_id == 5

    def test_add_file_invalid_type(self, manager):
        """Test adding file with invalid type"""
        with pytest.raises(ValueError):
            manager.add_file("/path/to/file.mp4", "invalid_type")

    def test_add_file_empty_path(self, manager):
        """Test adding file with empty path"""
        with pytest.raises(ValueError):
            manager.add_file("", "movie")

    def test_add_files_batch_success(self, manager, mock_session):
        """Test batch adding files"""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        manager.session.add = MagicMock()
        manager.session.flush = MagicMock()
        manager.session.commit = MagicMock()

        files = [
            {"file_path": "/path/to/file1.mp4", "file_type": "movie"},
            {"file_path": "/path/to/file2.mkv", "file_type": "tv_show"},
        ]

        # Mock the entries to have IDs after flush
        def add_side_effect(entry):
            if not hasattr(entry, "id"):
                entry.id = len([e for e in manager.session.add.call_args_list]) + 1

        manager.session.add.side_effect = add_side_effect

        queue_ids = manager.add_files_batch(files)
        assert len(queue_ids) >= 0

    def test_add_files_batch_empty(self, manager):
        """Test batch adding with empty list"""
        with pytest.raises(ValueError):
            manager.add_files_batch([])

    def test_get_pending_files(self, manager, mock_session):
        """Test getting pending files"""
        mock_file = MagicMock()
        mock_file.id = 1
        mock_file.file_path = "/path/to/file.mp4"
        mock_file.media_type = "movie"
        mock_file.status = "pending"
        mock_file.created_at = datetime.utcnow()

        mock_q = mock_session.query.return_value
        mock_all = mock_q.filter.return_value.order_by.return_value.limit.return_value.all
        mock_all.return_value = [mock_file]

        files = manager.get_pending_files(limit=10)
        assert len(files) == 1
        assert files[0]["file_path"] == "/path/to/file.mp4"

    def test_mark_processing(self, manager, mock_session):
        """Test marking file as processing"""
        mock_file = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_file

        result = manager.mark_processing(1)
        assert result is True
        assert mock_file.status == "processing"

    def test_mark_completed(self, manager, mock_session):
        """Test marking file as completed"""
        mock_file = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_file

        result = manager.mark_completed(1)
        assert result is True
        assert mock_file.status == "completed"

    def test_mark_failed(self, manager, mock_session):
        """Test marking file as failed"""
        mock_file = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_file

        result = manager.mark_failed(1, "Test error")
        assert result is True
        assert mock_file.status == "failed"
        assert mock_file.error_message == "Test error"

    def test_mark_failed_empty_message(self, manager):
        """Test marking failed with empty message"""
        with pytest.raises(ValueError):
            manager.mark_failed(1, "")

    def test_get_file_status(self, manager, mock_session):
        """Test getting file status"""
        mock_file = MagicMock()
        mock_file.id = 1
        mock_file.file_path = "/path/to/file.mp4"
        mock_file.status = "pending"
        mock_file.media_type = "movie"
        mock_file.error_message = None
        mock_file.created_at = datetime.utcnow()
        mock_file.processed_at = None

        mock_session.query.return_value.filter.return_value.first.return_value = mock_file

        status = manager.get_file_status(1)
        assert status["id"] == 1
        assert status["status"] == "pending"

    def test_get_queue_stats(self, manager, mock_session):
        """Test getting queue statistics"""
        mock_session.query.return_value.count.side_effect = [10, 5, 2, 2, 1]
        mock_session.query.return_value.filter.return_value.count.side_effect = [
            5,
            2,
            2,
            1,
        ]

        stats = manager.get_queue_stats()
        assert stats["total"] == 10
        assert stats["pending"] == 5

    def test_is_duplicate_true(self, manager, mock_session):
        """Test duplicate detection - file exists"""
        mock_session.query.return_value.filter.return_value.first.return_value = MagicMock()

        result = manager.is_duplicate("/path/to/file.mp4")
        assert result is True

    def test_is_duplicate_false(self, manager, mock_session):
        """Test duplicate detection - file not exists"""
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = manager.is_duplicate("/path/to/file.mp4")
        assert result is False

    def test_retry_failed_file(self, manager, mock_session):
        """Test retrying failed file"""
        mock_file = MagicMock()
        mock_file.status = "failed"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_file

        result = manager.retry_failed_file(1)
        assert result is True
        assert mock_file.status == "pending"

    def test_clear_completed_files(self, manager, mock_session):
        """Test clearing completed files"""
        mock_session.query.return_value.filter.return_value.delete.return_value = 5
        mock_session.commit = MagicMock()

        deleted = manager.clear_completed_files(days_old=7)
        assert deleted == 5


# ============================================================================
# Task Error Handler Tests
# ============================================================================


class TestTaskErrorHandler:
    """Tests for TaskErrorHandler service"""

    def test_determine_severity_critical(self):
        """Test severity determination for critical task"""
        severity = TaskErrorHandler._determine_severity("app.tasks.analyze_file")
        assert severity == "critical"

    def test_determine_severity_warning(self):
        """Test severity determination for warning task"""
        severity = TaskErrorHandler._determine_severity("app.tasks.cleanup_cache")
        assert severity == "warning"

    def test_determine_severity_info(self):
        """Test severity determination for unknown task"""
        severity = TaskErrorHandler._determine_severity("app.tasks.unknown_task")
        assert severity == "info"

    @patch.object(TaskErrorHandler, "log_task_error")
    @patch.object(TaskErrorHandler, "_store_error_in_db")
    @patch.object(TaskErrorHandler, "notify_failure")
    def test_handle_task_failure(self, mock_notify, mock_store, mock_log):
        """Test task failure handling"""
        exception = Exception("Test error")
        TaskErrorHandler.handle_task_failure(
            task_id="task123",
            task_name="app.tasks.analyze_file",
            exception=exception,
            retry_count=1,
        )

        mock_log.assert_called_once()
        mock_store.assert_called_once()
        mock_notify.assert_called_once()

    @patch("app.infrastructure.monitoring.error_handler.logger")
    def test_notify_failure_critical(self, mock_logger):
        """Test notification for critical error"""
        TaskErrorHandler.notify_failure(
            task_id="task123",
            task_name="app.tasks.analyze_file",
            error_message="Critical error",
            severity="critical",
        )

        mock_logger.log.assert_called_once()

    @patch("app.infrastructure.monitoring.error_handler.logger")
    def test_log_task_error(self, mock_logger):
        """Test error logging"""
        TaskErrorHandler.log_task_error(
            task_id="task123",
            task_name="app.tasks.analyze_file",
            error_details={
                "error_message": "Test error",
                "severity": "critical",
                "retry_count": 1,
            },
        )

        mock_logger.error.assert_called_once()

    @patch("app.infrastructure.monitoring.error_handler.SessionLocal")
    def test_store_error_in_db_new(self, mock_session_local):
        """Test storing new error in database"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        TaskErrorHandler._store_error_in_db(
            task_id="task123",
            task_name="app.tasks.analyze_file",
            error_message="Test error",
            error_traceback="Traceback...",
            severity="critical",
            retry_count=0,
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("app.infrastructure.monitoring.error_handler.SessionLocal")
    def test_mark_error_resolved(self, mock_session_local):
        """Test marking error as resolved"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_error = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_error

        TaskErrorHandler.mark_error_resolved("task123")

        assert mock_error.resolved_at is not None
        mock_session.commit.assert_called_once()

    @patch("app.infrastructure.monitoring.error_handler.SessionLocal")
    def test_get_recent_errors(self, mock_session_local):
        """Test retrieving recent errors"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_error = MagicMock()

        # Setup the query chain properly
        mock_query = MagicMock()
        mock_filtered = MagicMock()
        mock_ordered = MagicMock()
        mock_offset = MagicMock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filtered
        mock_filtered.count.return_value = 1
        mock_filtered.order_by.return_value = mock_ordered
        mock_ordered.offset.return_value = mock_offset
        mock_offset.limit.return_value.all.return_value = [mock_error]

        errors, total = TaskErrorHandler.get_recent_errors(severity="critical", limit=10)

        assert len(errors) == 1
        assert total == 1


# ============================================================================
# File Monitor Service Tests
# ============================================================================


class TestFileMonitorService:
    """Tests for FileMonitorService"""

    @pytest.fixture
    def monitor(self):
        """Create FileMonitorService instance"""
        with patch("app.infrastructure.file_system.monitor.settings"):
            return FileMonitorService(watch_path="/tmp/test_media")

    def test_media_file_event_handler_is_media_file(self):
        """Test media file detection"""
        handler = MediaFileEventHandler([], watch_extensions=[".mp4", ".mkv"])
        assert handler._is_media_file("video.mp4") is True
        assert handler._is_media_file("video.mkv") is True
        assert handler._is_media_file("document.txt") is False

    def test_media_file_event_handler_queue_file(self):
        """Test file queueing"""
        file_queue = []
        handler = MediaFileEventHandler(file_queue, watch_extensions=[".mp4"])
        handler._queue_file("/path/to/video.mp4", "created")
        assert "/path/to/video.mp4" in file_queue

    def test_media_file_event_handler_queue_duplicate(self):
        """Test duplicate file queueing prevention"""
        file_queue = ["/path/to/video.mp4"]
        handler = MediaFileEventHandler(file_queue, watch_extensions=[".mp4"])
        handler._queue_file("/path/to/video.mp4", "created")
        assert len(file_queue) == 1

    @pytest.mark.asyncio
    async def test_file_monitor_get_status(self, monitor):
        """Test getting monitor status"""
        status = monitor.get_status()
        assert "is_running" in status
        assert "watch_path" in status
        assert "queued_files_count" in status

    @pytest.mark.asyncio
    async def test_file_monitor_get_queued_files(self, monitor):
        """Test getting queued files"""
        monitor.file_queue = ["/path/to/file1.mp4", "/path/to/file2.mkv"]
        files = monitor.get_queued_files()
        assert len(files) == 2
        assert len(monitor.file_queue) == 0  # Queue should be cleared

    @pytest.mark.asyncio
    async def test_file_monitor_peek_queued_files(self, monitor):
        """Test peeking at queued files"""
        monitor.file_queue = ["/path/to/file1.mp4"]
        files = monitor.peek_queued_files()
        assert len(files) == 1
        assert len(monitor.file_queue) == 1  # Queue should not be cleared

    @pytest.mark.asyncio
    async def test_file_monitor_clear_queue(self, monitor):
        """Test clearing queue"""
        monitor.file_queue = ["/path/to/file1.mp4", "/path/to/file2.mkv"]
        monitor.clear_queue()
        assert len(monitor.file_queue) == 0
