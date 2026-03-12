"""Storage analytics service."""

import math
import os
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.config import MOVIE_DIR, TV_DIR, settings
from app.core.logging_config import get_logger
from app.domain.files.models import FileItem

logger = get_logger(__name__)

# Target MB/min per resolution tier, assuming H.265 re-encode
TARGET_MB_PER_MIN: Dict[str, float] = {
    "4k": 90.0,  # ~12 Mbps
    "1080p": 30.0,  # ~4 Mbps
    "720p": 15.0,  # ~2 Mbps
    "sd": 7.5,  # ~1 Mbps
}

# Codecs already efficient — no savings estimate made
EFFICIENT_CODECS = {"av1", "hevc"}

# Legacy / lossless codecs always flagged as large regardless of bitrate
LEGACY_CODECS = {"mpeg2video", "vc1", "wmv3", "mpeg1video"}

# MB/min threshold below which a codec is considered "efficient".
# float("inf") means always efficient regardless of bitrate (e.g. AV1).
_EFFICIENT_THRESHOLD: dict[str, float] = {
    "av1": float("inf"),
    "hevc": 50.0,
    "h264": 30.0,
}


def _sort_key_none_last(value, reverse: bool):
    """Return sort key placing None at the end in both asc and desc."""
    if value is None:
        return math.inf if not reverse else -math.inf
    return value


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

    def _get_efficiency_tier(self, codec: Optional[str], mb_per_min: Optional[float]) -> str:
        """Classify file efficiency as efficient / moderate / large / unknown."""
        if codec is None or mb_per_min is None:
            return "unknown"
        codec_lower = codec.lower()
        if codec_lower in LEGACY_CODECS:
            return "large"
        if mb_per_min > 100:
            return "large"
        threshold = _EFFICIENT_THRESHOLD.get(codec_lower)
        if threshold is None:
            return "moderate"
        return "efficient" if mb_per_min < threshold else "moderate"

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
    # DB-backed methods
    # ------------------------------------------------------------------

    def _get_unwatched_sizes(self) -> tuple:
        """Return (unwatched_movie_bytes, unwatched_tv_bytes) for the space banner."""
        from app.domain.movies.models import Movie, MovieFile
        from app.domain.plex.models import PlexItemType, PlexSyncRecord
        from app.domain.tv_shows.models import Episode, EpisodeFile, Season
        from sqlalchemy import func as sa_func

        movie_bytes = (
            self.db.query(sa_func.coalesce(sa_func.sum(MovieFile.file_size), 0))
            .join(Movie, MovieFile.movie_id == Movie.id)
            .join(
                PlexSyncRecord,
                (PlexSyncRecord.item_id == Movie.id)
                & (PlexSyncRecord.item_type == PlexItemType.MOVIE),
            )
            .filter(PlexSyncRecord.is_watched.is_(False))
            .scalar()
        ) or 0

        tv_bytes = (
            self.db.query(sa_func.coalesce(sa_func.sum(EpisodeFile.file_size), 0))
            .join(Episode, EpisodeFile.episode_id == Episode.id)
            .join(Season, Episode.season_id == Season.id)
            .join(
                PlexSyncRecord,
                (PlexSyncRecord.item_id == Episode.id)
                & (PlexSyncRecord.item_type == PlexItemType.EPISODE),
            )
            .filter(PlexSyncRecord.is_watched.is_(False))
            .scalar()
        ) or 0

        return int(movie_bytes), int(tv_bytes)

    def get_disk_stats(self) -> Dict[str, int]:
        """Get filesystem disk usage via os.statvfs on the movie media directory."""
        try:
            stat = os.statvfs(MOVIE_DIR)
            total = stat.f_frsize * stat.f_blocks
            available = stat.f_frsize * stat.f_bavail
            return {
                "total_bytes": total,
                "used_bytes": total - available,
                "available_bytes": available,
            }
        except OSError as e:
            logger.warning(f"Could not get disk stats from {MOVIE_DIR}: {e}")
            return {"total_bytes": 0, "used_bytes": 0, "available_bytes": 0}

    def _iter_video_files(self):
        """Yield FileItem rows that are video files (type='file')."""
        video_extensions = {ext.lower() for ext in settings.watch_extensions}
        if not video_extensions:
            return
        ext_filters = [func.lower(FileItem.path).like(f"%{ext}") for ext in video_extensions]
        files = (
            self.db.query(FileItem).filter(FileItem.type == "file").filter(or_(*ext_filters)).all()
        )
        yield from files

    def _media_type_for_path(self, path: str) -> str:
        p = Path(path)
        if p.is_relative_to(Path(MOVIE_DIR)):
            return "movie"
        if p.is_relative_to(Path(TV_DIR)):
            return "tv"
        return "other"

    def _get_path_watch_info(self) -> dict:
        """Return {file_path: {is_watched, title, show_title, show_fully_unwatched}}
        for every file that is matched in the library."""
        from app.domain.movies.models import Movie, MovieFile
        from app.domain.plex.models import PlexItemType, PlexSyncRecord
        from app.domain.tv_shows.models import Episode, EpisodeFile, Season, TVShow

        result: dict = {}

        movie_rows = (
            self.db.query(MovieFile.file_path, Movie.title, PlexSyncRecord.is_watched)
            .join(Movie, MovieFile.movie_id == Movie.id)
            .outerjoin(
                PlexSyncRecord,
                (PlexSyncRecord.item_id == Movie.id)
                & (PlexSyncRecord.item_type == PlexItemType.MOVIE),
            )
            .all()
        )
        for file_path, title, is_watched in movie_rows:
            result[file_path] = {
                "is_watched": is_watched,
                "title": title,
                "show_title": None,
                "show_fully_unwatched": None,
            }

        ep_rows = (
            self.db.query(
                EpisodeFile.file_path,
                TVShow.title,
                TVShow.id,
                PlexSyncRecord.is_watched,
            )
            .join(Episode, EpisodeFile.episode_id == Episode.id)
            .join(Season, Episode.season_id == Season.id)
            .join(TVShow, Season.show_id == TVShow.id)
            .outerjoin(
                PlexSyncRecord,
                (PlexSyncRecord.item_id == Episode.id)
                & (PlexSyncRecord.item_type == PlexItemType.EPISODE),
            )
            .all()
        )
        show_has_watched: dict = {}
        ep_data = []
        for file_path, show_title, show_id, is_watched in ep_rows:
            ep_data.append((file_path, show_title, show_id, is_watched))
            if show_id not in show_has_watched:
                show_has_watched[show_id] = False
            if is_watched:
                show_has_watched[show_id] = True

        # Both loops iterate ep_data, so show_id is always present in show_has_watched.
        for file_path, show_title, show_id, is_watched in ep_data:
            result[file_path] = {
                "is_watched": is_watched,
                "title": None,
                "show_title": show_title,
                "show_fully_unwatched": not show_has_watched[show_id],
            }

        return result

    def get_summary(self) -> Dict[str, Any]:
        """Aggregate storage summary for dashboard widget."""
        movies_bytes = 0
        tv_bytes = 0
        other_bytes = 0
        files_analyzed = 0
        files_pending = 0
        potential_savings = 0

        for f in self._iter_video_files():
            size = f.size or 0
            media_type = self._media_type_for_path(f.path)
            if media_type == "movie":
                movies_bytes += size
            elif media_type == "tv":
                tv_bytes += size
            else:
                other_bytes += size

            if f.duration_seconds is not None and f.video_codec is not None:
                files_analyzed += 1
                savings = self._estimate_savings_bytes(
                    size, f.video_codec, f.video_width, f.video_height, f.duration_seconds
                )
                potential_savings += savings
            else:
                files_pending += 1

        unwatched_movie_bytes, unwatched_tv_bytes = self._get_unwatched_sizes()
        return {
            "disk": self.get_disk_stats(),
            "library": {
                "movies_bytes": movies_bytes,
                "tv_bytes": tv_bytes,
                "other_bytes": other_bytes,
            },
            "potential_savings_bytes": potential_savings,
            "files_analyzed": files_analyzed,
            "files_pending_analysis": files_pending,
            "unwatched_movie_size_bytes": unwatched_movie_bytes,
            "unwatched_tv_size_bytes": unwatched_tv_bytes,
        }

    def _apply_watched_filter(self, results: list, watched_status: Optional[str]) -> list:
        """Filter file list by Plex watch status.

        Files with is_watched=None (not yet synced to Plex) are excluded
        from both 'watched' and 'unwatched' results.
        """
        if watched_status == "unwatched":
            return [r for r in results if r.get("is_watched") is False]
        if watched_status == "watched":
            return [r for r in results if r.get("is_watched") is True]
        return results

    def get_files(
        self,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "size_bytes",
        sort_dir: str = "desc",
        media_type: Optional[str] = None,
        codec: Optional[str] = None,
        resolution_tier: Optional[str] = None,
        efficiency_tier: Optional[str] = None,
        watched_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return paginated, sortable file list with efficiency analytics."""
        path_watch_info = self._get_path_watch_info()
        results = []

        for f in self._iter_video_files():
            size = f.size or 0
            mb_per_min = self._calculate_mb_per_min(size, f.duration_seconds)
            res_tier = self._get_resolution_tier(f.video_width, f.video_height)
            eff_tier = self._get_efficiency_tier(f.video_codec, mb_per_min)
            savings = self._estimate_savings_bytes(
                size, f.video_codec, f.video_width, f.video_height, f.duration_seconds
            )

            results.append(
                {
                    "id": f.id,
                    "name": f.name,
                    "media_type": self._media_type_for_path(f.path),
                    "size_bytes": size,
                    "duration_seconds": f.duration_seconds,
                    "video_codec": f.video_codec,
                    "video_width": f.video_width,
                    "video_height": f.video_height,
                    "mb_per_min": mb_per_min,
                    "resolution_tier": res_tier,
                    "efficiency_tier": eff_tier,
                    "estimated_savings_bytes": savings,
                    "is_watched": path_watch_info.get(f.path, {}).get("is_watched"),
                    "show_title": path_watch_info.get(f.path, {}).get("show_title"),
                    "show_fully_unwatched": path_watch_info.get(f.path, {}).get(
                        "show_fully_unwatched"
                    ),
                }
            )

        # Filter
        if media_type:
            results = [r for r in results if r["media_type"] == media_type]
        if codec:
            results = [r for r in results if (r["video_codec"] or "").lower() == codec.lower()]
        if resolution_tier:
            results = [r for r in results if r["resolution_tier"] == resolution_tier]
        if efficiency_tier:
            results = [r for r in results if r["efficiency_tier"] == efficiency_tier]
        results = self._apply_watched_filter(results, watched_status)

        # Sort — None values sort to the end
        valid_sort_keys = {
            "size_bytes",
            "mb_per_min",
            "estimated_savings_bytes",
            "duration_seconds",
            "name",
        }
        key = sort_by if sort_by in valid_sort_keys else "size_bytes"
        reverse = sort_dir != "asc"
        results.sort(
            key=lambda x: _sort_key_none_last(x[key], reverse),
            reverse=reverse,
        )

        # Paginate
        total = len(results)
        offset = (page - 1) * page_size
        return {"total": total, "items": results[offset : offset + page_size]}
