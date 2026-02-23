"""Tests for StorageService pure logic helpers."""
import pytest
from unittest.mock import MagicMock
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
