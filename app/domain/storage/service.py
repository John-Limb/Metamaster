"""Storage analytics service."""
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Target MB/min per resolution tier, assuming H.265 re-encode
TARGET_MB_PER_MIN: Dict[str, float] = {
    "4k": 90.0,    # ~12 Mbps
    "1080p": 30.0,  # ~4 Mbps
    "720p": 15.0,   # ~2 Mbps
    "sd": 7.5,      # ~1 Mbps
}

# Codecs already efficient — no savings estimate made
EFFICIENT_CODECS = {"av1", "hevc"}

# Legacy / lossless codecs always flagged as large regardless of bitrate
LEGACY_CODECS = {"mpeg2video", "vc1", "wmv3", "mpeg1video"}


class StorageService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Pure helpers (no DB access)
    # ------------------------------------------------------------------

    def _get_resolution_tier(self, width: Optional[int], height: Optional[int]) -> str:
        """Classify resolution as 4k / 1080p / 720p / sd / unknown."""
        if not width or not height:
            return "unknown"
        if width >= 3840 or height >= 2160:
            return "4k"
        if width >= 1920 or height >= 1080:
            return "1080p"
        if width >= 1280 or height >= 720:
            return "720p"
        return "sd"

    def _get_efficiency_tier(
        self, codec: Optional[str], mb_per_min: Optional[float]
    ) -> str:
        """Classify file efficiency as efficient / moderate / large / unknown."""
        if codec is None or mb_per_min is None:
            return "unknown"
        codec_lower = codec.lower()
        if codec_lower == "av1":
            return "efficient"
        if codec_lower in LEGACY_CODECS:
            return "large"
        if mb_per_min > 100:
            return "large"
        if codec_lower == "hevc":
            return "efficient" if mb_per_min < 50 else "moderate"
        if codec_lower == "h264":
            if mb_per_min < 30:
                return "efficient"
            return "moderate"
        # Unknown codec with moderate bitrate
        return "moderate"

    def _calculate_mb_per_min(
        self, size_bytes: Optional[int], duration_seconds: Optional[int]
    ) -> Optional[float]:
        """Return MB/min or None if data is missing."""
        if not size_bytes or not duration_seconds or duration_seconds <= 0:
            return None
        duration_minutes = duration_seconds / 60
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb / duration_minutes, 1)

    def _estimate_savings_bytes(
        self,
        size_bytes: int,
        codec: Optional[str],
        width: Optional[int],
        height: Optional[int],
        duration_seconds: Optional[int],
    ) -> int:
        """Estimate bytes saved if re-encoded to H.265 at a target bitrate."""
        if not codec or not duration_seconds or duration_seconds <= 0:
            return 0
        if codec.lower() in EFFICIENT_CODECS:
            return 0
        resolution_tier = self._get_resolution_tier(width, height)
        if resolution_tier == "unknown":
            return 0
        target_mb_per_min = TARGET_MB_PER_MIN[resolution_tier]
        duration_minutes = duration_seconds / 60
        estimated_target = duration_minutes * target_mb_per_min * 1024 * 1024
        return max(0, int(size_bytes - estimated_target))

    # ------------------------------------------------------------------
    # DB-backed methods (implemented in Task 3)
    # ------------------------------------------------------------------

    def get_disk_stats(self) -> Dict[str, int]:
        raise NotImplementedError

    def get_summary(self) -> Dict[str, Any]:
        raise NotImplementedError

    def get_files(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError
