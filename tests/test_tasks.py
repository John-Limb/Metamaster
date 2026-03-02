"""Tests for Celery tasks — technical metadata enrichment."""
import pytest
from unittest.mock import patch, MagicMock
from app.tasks import enrich_file_technical_metadata


def test_enrich_technical_metadata_updates_file_fields():
    """Task reads FFprobe data and writes it to FileItem columns."""
    mock_file = MagicMock()
    mock_file.path = "/media/movies/test.mkv"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [mock_file]
    mock_db.query.return_value.filter.return_value.count.return_value = 0

    mock_ffprobe = MagicMock()
    mock_ffprobe.get_duration.return_value = 7200.0
    mock_ffprobe.get_codecs.return_value = {"video": "h264", "audio": "aac"}
    mock_ffprobe.get_resolution.return_value = {"width": 1920, "height": 1080, "label": "1080p"}

    with patch("app.tasks.SessionLocal") as MockSession, patch(
        "app.tasks.FFProbeWrapper", return_value=mock_ffprobe
    ):
        MockSession.return_value = mock_db
        result = enrich_file_technical_metadata.apply(args=[], kwargs={"batch_size": 50}).get()

    assert mock_file.duration_seconds == 7200
    assert mock_file.video_codec == "h264"
    assert mock_file.video_width == 1920
    assert mock_file.video_height == 1080
    mock_db.commit.assert_called_once()
    assert result["processed"] == 1


def test_enrich_technical_metadata_skips_failed_files():
    """If FFprobe fails for a file, it is skipped and processing continues."""
    mock_file = MagicMock()
    mock_file.path = "/media/movies/broken.mkv"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [mock_file]
    mock_db.query.return_value.filter.return_value.count.return_value = 0

    mock_ffprobe = MagicMock()
    mock_ffprobe.get_duration.side_effect = RuntimeError("ffprobe failed")

    with patch("app.tasks.SessionLocal") as MockSession, patch(
        "app.tasks.FFProbeWrapper", return_value=mock_ffprobe
    ):
        MockSession.return_value = mock_db
        result = enrich_file_technical_metadata.apply(args=[], kwargs={"batch_size": 50}).get()

    assert result["processed"] == 0


def test_enrich_technical_metadata_returns_complete_when_no_files():
    """Returns immediately when no files need enrichment."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []

    with patch("app.tasks.SessionLocal") as MockSession:
        MockSession.return_value = mock_db
        result = enrich_file_technical_metadata.apply(args=[], kwargs={}).get()

    assert result["status"] == "complete"
    assert result["processed"] == 0
