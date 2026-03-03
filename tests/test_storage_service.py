"""Tests for StorageService pure logic helpers."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.domain.storage.service import StorageService


@pytest.fixture
def service():
    return StorageService(db=MagicMock())


# ===========================================================================
# _get_resolution_tier
# ===========================================================================


def test_resolution_tier_4k(service):
    assert service._get_resolution_tier(3840, 2160) == "4k"


def test_resolution_tier_4k_width_only(service):
    assert service._get_resolution_tier(3840, 1080) == "4k"


def test_resolution_tier_1080p(service):
    assert service._get_resolution_tier(1920, 1080) == "1080p"


def test_resolution_tier_720p(service):
    assert service._get_resolution_tier(1280, 720) == "720p"


def test_resolution_tier_sd(service):
    assert service._get_resolution_tier(720, 480) == "sd"


def test_resolution_tier_unknown_when_none(service):
    assert service._get_resolution_tier(None, None) == "unknown"


# ===========================================================================
# _get_efficiency_tier
# ===========================================================================


def test_efficiency_av1_always_efficient(service):
    assert service._get_efficiency_tier("av1", 500.0) == "efficient"


def test_efficiency_hevc_low_bitrate_efficient(service):
    assert service._get_efficiency_tier("hevc", 30.0) == "efficient"


def test_efficiency_hevc_high_bitrate_moderate(service):
    assert service._get_efficiency_tier("hevc", 80.0) == "moderate"


def test_efficiency_h264_low_bitrate_efficient(service):
    assert service._get_efficiency_tier("h264", 20.0) == "efficient"


def test_efficiency_h264_mid_bitrate_moderate(service):
    assert service._get_efficiency_tier("h264", 60.0) == "moderate"


def test_efficiency_h264_high_bitrate_large(service):
    assert service._get_efficiency_tier("h264", 250.0) == "large"


def test_efficiency_mpeg2_always_large(service):
    assert service._get_efficiency_tier("mpeg2video", 20.0) == "large"


def test_efficiency_vc1_always_large(service):
    assert service._get_efficiency_tier("vc1", 20.0) == "large"


def test_efficiency_unknown_when_no_codec(service):
    assert service._get_efficiency_tier(None, None) == "unknown"


def test_efficiency_unknown_when_no_mb_per_min(service):
    assert service._get_efficiency_tier("h264", None) == "unknown"


# ===========================================================================
# _calculate_mb_per_min
# ===========================================================================


def test_mb_per_min_correct_calculation(service):
    # 10 GiB file, 120 min duration → 10*1024 MiB / 120 min = 85.3 MiB/min
    size = 10 * 1024 * 1024 * 1024
    result = service._calculate_mb_per_min(size, 7200)
    assert result == pytest.approx(85.3, abs=0.1)


def test_mb_per_min_returns_none_when_no_size(service):
    assert service._calculate_mb_per_min(None, 7200) is None


def test_mb_per_min_returns_none_when_no_duration(service):
    assert service._calculate_mb_per_min(1000000, None) is None


def test_mb_per_min_returns_none_when_zero_duration(service):
    assert service._calculate_mb_per_min(1000000, 0) is None


# ===========================================================================
# _estimate_savings_bytes
# ===========================================================================


def test_savings_av1_returns_zero(service):
    savings = service._estimate_savings_bytes(30_000_000_000, "av1", 1920, 1080, 7200)
    assert savings == 0


def test_savings_hevc_returns_zero(service):
    savings = service._estimate_savings_bytes(30_000_000_000, "hevc", 1920, 1080, 7200)
    assert savings == 0


def test_savings_h264_1080p_remux_large(service):
    # 30 GB H.264 1080p, 2 hours → target ~3.5 GB → savings ~26.5 GB
    savings = service._estimate_savings_bytes(30_000_000_000, "h264", 1920, 1080, 7200)
    assert savings > 20_000_000_000
    assert savings < 30_000_000_000


def test_savings_returns_zero_when_no_codec(service):
    assert service._estimate_savings_bytes(30_000_000_000, None, 1920, 1080, 7200) == 0


def test_savings_returns_zero_when_no_duration(service):
    assert service._estimate_savings_bytes(30_000_000_000, "h264", 1920, 1080, None) == 0


def test_savings_never_negative(service):
    # Small file already below target size
    savings = service._estimate_savings_bytes(100_000, "h264", 1920, 1080, 7200)
    assert savings == 0


# ===========================================================================
# get_disk_stats
# ===========================================================================


def test_get_disk_stats_returns_correct_values(service):
    mock_stat = MagicMock()
    mock_stat.f_frsize = 4096
    mock_stat.f_blocks = 1000000
    mock_stat.f_bavail = 400000
    with patch("os.statvfs", return_value=mock_stat):
        result = service.get_disk_stats()
    total = 4096 * 1000000
    available = 4096 * 400000
    assert result["total_bytes"] == total
    assert result["available_bytes"] == available
    assert result["used_bytes"] == total - available


def test_get_disk_stats_handles_oserror(service):
    with patch("os.statvfs", side_effect=OSError("no such file")):
        result = service.get_disk_stats()
    assert result == {"total_bytes": 0, "used_bytes": 0, "available_bytes": 0}


# ===========================================================================
# get_summary
# ===========================================================================


def test_get_summary_structure(service):
    service.db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
    with (
        patch("app.domain.storage.service.settings") as mock_settings,
        patch.object(
            service,
            "get_disk_stats",
            return_value={"total_bytes": 1000, "used_bytes": 500, "available_bytes": 500},
        ),
    ):
        mock_settings.watch_extensions = [".mkv", ".mp4"]
        result = service.get_summary()
    assert "disk" in result
    assert "library" in result
    assert "potential_savings_bytes" in result
    assert "files_analyzed" in result
    assert "files_pending_analysis" in result


def test_get_summary_counts_pending(service):
    """Files with null duration count as files_pending_analysis."""
    mock_file = MagicMock()
    mock_file.path = "/media/movies/test.mkv"
    mock_file.size = 1_000_000_000
    mock_file.duration_seconds = None
    mock_file.video_codec = None
    mock_file.video_width = None
    mock_file.video_height = None
    service.db.query.return_value.filter.return_value.filter.return_value.all.return_value = [
        mock_file
    ]
    with (
        patch.object(
            service,
            "get_disk_stats",
            return_value={"total_bytes": 0, "used_bytes": 0, "available_bytes": 0},
        ),
        patch("app.domain.storage.service.settings") as mock_settings,
        patch("app.domain.storage.service.MOVIE_DIR", "/media/movies"),
        patch("app.domain.storage.service.TV_DIR", "/media/tv"),
    ):
        mock_settings.watch_extensions = [".mkv", ".mp4"]
        result = service.get_summary()
    assert result["files_pending_analysis"] == 1
    assert result["files_analyzed"] == 0


# ===========================================================================
# get_files
# ===========================================================================


def _make_mock_file(path, size, codec=None, width=None, height=None, duration=None):
    """Helper to build a mock FileItem."""
    f = MagicMock()
    f.id = 1
    f.name = Path(path).name
    f.path = path
    f.size = size
    f.video_codec = codec
    f.video_width = width
    f.video_height = height
    f.duration_seconds = duration
    f.type = "file"
    return f


def test_get_files_pagination(service):
    """Page 1 of 1 returns correct slice and total."""
    files = [
        _make_mock_file(f"/media/movies/file{i}.mkv", i * 1_000_000_000, "h264", 1920, 1080, 7200)
        for i in range(1, 4)
    ]
    service.db.query.return_value.filter.return_value.filter.return_value.all.return_value = files
    with (
        patch("app.domain.storage.service.settings") as mock_settings,
        patch("app.domain.storage.service.MOVIE_DIR", "/media/movies"),
        patch("app.domain.storage.service.TV_DIR", "/media/tv"),
    ):
        mock_settings.watch_extensions = [".mkv", ".mp4"]
        result = service.get_files(page=1, page_size=10)
    assert result["total"] == 3
    assert len(result["items"]) == 3


def test_get_files_filter_by_media_type(service):
    """media_type filter returns only matching files."""
    files = [
        _make_mock_file("/media/movies/a.mkv", 1_000_000_000, "h264", 1920, 1080, 3600),
        _make_mock_file("/media/tv/b.mkv", 500_000_000, "h264", 1920, 1080, 1800),
    ]
    service.db.query.return_value.filter.return_value.filter.return_value.all.return_value = files
    with (
        patch("app.domain.storage.service.settings") as mock_settings,
        patch("app.domain.storage.service.MOVIE_DIR", "/media/movies"),
        patch("app.domain.storage.service.TV_DIR", "/media/tv"),
    ):
        mock_settings.watch_extensions = [".mkv", ".mp4"]
        result = service.get_files(media_type="movie")
    assert result["total"] == 1
    assert result["items"][0]["media_type"] == "movie"


def test_get_files_sort_none_last_asc(service):
    """Ascending sort: files with null mb_per_min go to the end."""
    files = [
        _make_mock_file("/media/movies/a.mkv", 1_000_000_000, "h264", 1920, 1080, 3600),
        _make_mock_file("/media/movies/b.mkv", 2_000_000_000),  # no duration -> mb_per_min None
        _make_mock_file("/media/movies/c.mkv", 500_000_000, "h264", 1920, 1080, 1800),
    ]
    service.db.query.return_value.filter.return_value.filter.return_value.all.return_value = files
    with (
        patch("app.domain.storage.service.settings") as mock_settings,
        patch("app.domain.storage.service.MOVIE_DIR", "/media/movies"),
        patch("app.domain.storage.service.TV_DIR", "/media/tv"),
    ):
        mock_settings.watch_extensions = [".mkv", ".mp4"]
        result = service.get_files(sort_by="mb_per_min", sort_dir="asc")
    items = result["items"]
    assert items[-1]["mb_per_min"] is None, "None should sort last in asc"


def test_get_files_sort_none_last_desc(service):
    """Descending sort: files with null mb_per_min also go to the end."""
    files = [
        _make_mock_file("/media/movies/a.mkv", 1_000_000_000, "h264", 1920, 1080, 3600),
        _make_mock_file("/media/movies/b.mkv", 2_000_000_000),  # no duration -> mb_per_min None
        _make_mock_file("/media/movies/c.mkv", 500_000_000, "h264", 1920, 1080, 1800),
    ]
    service.db.query.return_value.filter.return_value.filter.return_value.all.return_value = files
    with (
        patch("app.domain.storage.service.settings") as mock_settings,
        patch("app.domain.storage.service.MOVIE_DIR", "/media/movies"),
        patch("app.domain.storage.service.TV_DIR", "/media/tv"),
    ):
        mock_settings.watch_extensions = [".mkv", ".mp4"]
        result = service.get_files(sort_by="mb_per_min", sort_dir="desc")
    items = result["items"]
    assert items[-1]["mb_per_min"] is None, "None should sort last in desc too"
