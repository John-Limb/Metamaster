# Storage Analytics Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add storage analytics — a live dashboard widget (donut chart + disk bar) and a `/storage` detail page with per-file GB/min efficiency analysis, codec detection, and estimated re-encode savings.

**Architecture:** Extend `FileItem` with four FFprobe-derived columns (`duration_seconds`, `video_codec`, `video_width`, `video_height`) via Alembic migration. A new `StorageService` computes efficiency tiers and savings estimates from these columns. Two new endpoints (`GET /storage/summary`, `GET /storage/files`) feed the dashboard widget and detail page. A Celery task backfills existing files. The frontend adds a `storageService`, wires the existing `StorageChart` component with real data, and introduces a new `StoragePage`.

**Tech Stack:** Python/FastAPI, SQLAlchemy, Alembic, FFProbeWrapper (already at `app/infrastructure/file_system/ffprobe_wrapper.py`), Celery/Redis, React/TypeScript, Tailwind CSS.

---

### Task 1: Alembic migration + FileItem model columns

**Files:**
- Create: `alembic/versions/010_add_file_technical_metadata.py`
- Modify: `app/domain/files/models.py`

**Step 1: Create the migration**

Create `alembic/versions/010_add_file_technical_metadata.py`:

```python
"""Add technical metadata columns to file_items

Revision ID: 010
Revises: 009
Create Date: 2026-02-23
"""
import sqlalchemy as sa
from alembic import op

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('file_items', sa.Column('duration_seconds', sa.Integer(), nullable=True))
    op.add_column('file_items', sa.Column('video_codec', sa.String(20), nullable=True))
    op.add_column('file_items', sa.Column('video_width', sa.Integer(), nullable=True))
    op.add_column('file_items', sa.Column('video_height', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('file_items', 'video_height')
    op.drop_column('file_items', 'video_width')
    op.drop_column('file_items', 'video_codec')
    op.drop_column('file_items', 'duration_seconds')
```

**Step 2: Add columns to FileItem model**

In `app/domain/files/models.py`, after line 22 (`metadata_json`), add:

```python
    duration_seconds = Column(Integer, nullable=True)   # seconds from FFprobe
    video_codec = Column(String(20), nullable=True)     # e.g. 'h264', 'hevc', 'av1'
    video_width = Column(Integer, nullable=True)         # e.g. 1920
    video_height = Column(Integer, nullable=True)        # e.g. 1080
```

Also add `Integer` to the import on line 4:
```python
from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, Boolean, Index
```
(`Integer` is already there — confirm and skip if so.)

**Step 3: Apply migration**

```bash
alembic upgrade head
```
Expected: `Running upgrade 009 -> 010, Add technical metadata columns to file_items`

**Step 4: Verify columns exist**

```bash
python3 -c "
from app.core.database import SessionLocal
from app.domain.files.models import FileItem
db = SessionLocal()
f = db.query(FileItem).first()
print(f.duration_seconds, f.video_codec, f.video_width, f.video_height)
db.close()
"
```
Expected: prints `None None None None` (no data yet, columns exist).

**Step 5: Commit**

```bash
git add alembic/versions/010_add_file_technical_metadata.py app/domain/files/models.py
git commit -m "feat: add duration_seconds, video_codec, video_width, video_height to FileItem"
```

---

### Task 2: StorageService — pure logic helpers (TDD)

**Files:**
- Create: `app/domain/storage/__init__.py`
- Create: `app/domain/storage/service.py`
- Create: `tests/test_storage_service.py`

**Step 1: Create the package**

Create `app/domain/storage/__init__.py` (empty file).

**Step 2: Write failing tests for the pure helper methods**

Create `tests/test_storage_service.py`:

```python
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
    # 10 GB file, 120 min duration → 10*1024 MB / 120 min ≈ 87.4 MB/min
    size = 10 * 1024 * 1024 * 1024
    result = service._calculate_mb_per_min(size, 7200)
    assert result == pytest.approx(87.4, abs=0.1)

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
    # Small file that is already below target size
    savings = service._estimate_savings_bytes(100_000, "h264", 1920, 1080, 7200)
    assert savings == 0
```

**Step 3: Run tests to confirm they fail**

```bash
pytest tests/test_storage_service.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'app.domain.storage'`

**Step 4: Create StorageService with the pure helpers**

Create `app/domain/storage/service.py`:

```python
"""Storage analytics service."""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from app.core.config import MOVIE_DIR, TV_DIR, settings
from app.core.logging_config import get_logger
from app.domain.files.models import FileItem

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
```

**Step 5: Run tests — all pass**

```bash
pytest tests/test_storage_service.py -v
```
Expected: all PASS.

**Step 6: Commit**

```bash
git add app/domain/storage/ tests/test_storage_service.py
git commit -m "feat: add StorageService pure helpers with TDD (resolution tier, efficiency tier, MB/min, savings)"
```

---

### Task 3: StorageService — DB-backed methods (TDD)

**Files:**
- Modify: `app/domain/storage/service.py`
- Modify: `tests/test_storage_service.py`

**Step 1: Add DB-backed tests to `tests/test_storage_service.py`**

Add these imports at the top of the test file (after the existing imports):

```python
from unittest.mock import patch, MagicMock, PropertyMock
```

Add the following test section after the existing tests:

```python
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
    service.db.query.return_value.filter.return_value.all.return_value = []
    with patch.object(service, "get_disk_stats", return_value={"total_bytes": 1000, "used_bytes": 500, "available_bytes": 500}):
        result = service.get_summary()
    assert "disk" in result
    assert "library" in result
    assert "potential_savings_bytes" in result
    assert "files_analyzed" in result
    assert "files_pending_analysis" in result

def test_get_summary_counts_pending(service):
    """Files with null duration count as pending_analysis."""
    mock_file = MagicMock()
    mock_file.path = "/media/movies/test.mkv"
    mock_file.size = 1_000_000_000
    mock_file.duration_seconds = None
    mock_file.video_codec = None
    mock_file.video_width = None
    mock_file.video_height = None
    mock_file.type = "file"
    service.db.query.return_value.filter.return_value.all.return_value = [mock_file]
    with patch.object(service, "get_disk_stats", return_value={"total_bytes": 0, "used_bytes": 0, "available_bytes": 0}), \
         patch("app.domain.storage.service.settings") as mock_settings, \
         patch("app.domain.storage.service.MOVIE_DIR", "/media/movies"), \
         patch("app.domain.storage.service.TV_DIR", "/media/tv"):
        mock_settings.watch_extensions = [".mkv", ".mp4"]
        result = service.get_summary()
    assert result["files_pending_analysis"] == 1
    assert result["files_analyzed"] == 0
```

**Step 2: Run new tests to confirm they fail**

```bash
pytest tests/test_storage_service.py::test_get_disk_stats_returns_correct_values tests/test_storage_service.py::test_get_summary_structure -v
```
Expected: FAIL — `NotImplementedError`

**Step 3: Implement `get_disk_stats`, `get_summary`, and `get_files` in `app/domain/storage/service.py`**

Replace the three `raise NotImplementedError` stubs with:

```python
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
        files = (
            self.db.query(FileItem)
            .filter(FileItem.type == "file")
            .all()
        )
        for f in files:
            if Path(f.path).suffix.lower() in video_extensions:
                yield f

    def _media_type_for_path(self, path: str) -> str:
        if path.startswith(str(MOVIE_DIR)):
            return "movie"
        if path.startswith(str(TV_DIR)):
            return "tv"
        return "other"

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
        }

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
    ) -> Dict[str, Any]:
        """Return paginated, sortable file list with efficiency analytics."""
        results = []

        for f in self._iter_video_files():
            size = f.size or 0
            mb_per_min = self._calculate_mb_per_min(size, f.duration_seconds)
            res_tier = self._get_resolution_tier(f.video_width, f.video_height)
            eff_tier = self._get_efficiency_tier(f.video_codec, mb_per_min)
            savings = self._estimate_savings_bytes(
                size, f.video_codec, f.video_width, f.video_height, f.duration_seconds
            )

            results.append({
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
            })

        # Filter
        if media_type:
            results = [r for r in results if r["media_type"] == media_type]
        if codec:
            results = [r for r in results if (r["video_codec"] or "").lower() == codec.lower()]
        if resolution_tier:
            results = [r for r in results if r["resolution_tier"] == resolution_tier]
        if efficiency_tier:
            results = [r for r in results if r["efficiency_tier"] == efficiency_tier]

        # Sort — None values sort to the end
        valid_sort_keys = {"size_bytes", "mb_per_min", "estimated_savings_bytes", "duration_seconds", "name"}
        key = sort_by if sort_by in valid_sort_keys else "size_bytes"
        reverse = sort_dir != "asc"
        results.sort(
            key=lambda x: (x[key] is None, x[key] if x[key] is not None else 0),
            reverse=reverse,
        )

        # Paginate
        total = len(results)
        offset = (page - 1) * page_size
        return {"total": total, "items": results[offset: offset + page_size]}
```

**Step 4: Run all storage service tests**

```bash
pytest tests/test_storage_service.py -v
```
Expected: all PASS.

**Step 5: Commit**

```bash
git add app/domain/storage/service.py tests/test_storage_service.py
git commit -m "feat: implement StorageService get_disk_stats, get_summary, get_files"
```

---

### Task 4: Storage API endpoints + register router (TDD)

**Files:**
- Create: `app/api/v1/storage/__init__.py`
- Create: `app/api/v1/storage/endpoints.py`
- Create: `tests/test_storage_endpoints.py`
- Modify: `app/main.py`

**Step 1: Write failing endpoint tests**

Create `tests/test_storage_endpoints.py`:

```python
"""Tests for /storage API endpoints."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=False)

SUMMARY_PAYLOAD = {
    "disk": {"total_bytes": 4_000_000_000_000, "used_bytes": 2_000_000_000_000, "available_bytes": 2_000_000_000_000},
    "library": {"movies_bytes": 1_400_000_000_000, "tv_bytes": 600_000_000_000, "other_bytes": 0},
    "potential_savings_bytes": 800_000_000_000,
    "files_analyzed": 100,
    "files_pending_analysis": 5,
}

FILES_PAYLOAD = {
    "total": 1,
    "items": [{
        "id": 1,
        "name": "test.mkv",
        "media_type": "movie",
        "size_bytes": 30_000_000_000,
        "duration_seconds": 7200,
        "video_codec": "h264",
        "video_width": 1920,
        "video_height": 1080,
        "mb_per_min": 254.0,
        "resolution_tier": "1080p",
        "efficiency_tier": "large",
        "estimated_savings_bytes": 26_000_000_000,
    }],
}


def test_get_summary_returns_200():
    with patch("app.api.v1.storage.endpoints.StorageService") as MockService:
        MockService.return_value.get_summary.return_value = SUMMARY_PAYLOAD
        response = client.get("/api/v1/storage/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["disk"]["total_bytes"] == 4_000_000_000_000
    assert data["library"]["movies_bytes"] == 1_400_000_000_000
    assert data["files_analyzed"] == 100


def test_get_files_returns_200():
    with patch("app.api.v1.storage.endpoints.StorageService") as MockService:
        MockService.return_value.get_files.return_value = FILES_PAYLOAD
        response = client.get("/api/v1/storage/files")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "test.mkv"


def test_get_files_passes_query_params():
    with patch("app.api.v1.storage.endpoints.StorageService") as MockService:
        MockService.return_value.get_files.return_value = {"total": 0, "items": []}
        client.get("/api/v1/storage/files?page=2&pageSize=25&sortBy=mb_per_min&sortDir=asc&mediaType=movie")
        MockService.return_value.get_files.assert_called_once_with(
            page=2, page_size=25, sort_by="mb_per_min", sort_dir="asc",
            media_type="movie", codec=None, resolution_tier=None, efficiency_tier=None,
        )


def test_scan_technical_returns_202():
    with patch("app.api.v1.storage.endpoints.enrich_file_technical_metadata") as mock_task:
        response = client.post("/api/v1/storage/scan-technical")
    assert response.status_code == 202
    mock_task.delay.assert_called_once()
```

**Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_storage_endpoints.py -v
```
Expected: FAIL — `404 Not Found` for all routes.

**Step 3: Create the package init**

Create `app/api/v1/storage/__init__.py` (empty).

**Step 4: Create the endpoints**

Create `app/api/v1/storage/endpoints.py`:

```python
"""Storage analytics API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.storage.service import StorageService

router = APIRouter(prefix="/storage", tags=["storage"])


def _get_service(db: Session = Depends(get_db)) -> StorageService:
    return StorageService(db)


@router.get("/summary")
def get_storage_summary(service: StorageService = Depends(_get_service)):
    """Storage summary for dashboard widget — disk stats + library breakdown."""
    return service.get_summary()


@router.get("/files")
def get_storage_files(
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=200, alias="pageSize"),
    sortBy: str = Query("size_bytes", alias="sortBy"),
    sortDir: str = Query("desc", pattern="^(asc|desc)$", alias="sortDir"),
    mediaType: Optional[str] = Query(None, alias="mediaType"),
    codec: Optional[str] = None,
    resolutionTier: Optional[str] = Query(None, alias="resolutionTier"),
    efficiencyTier: Optional[str] = Query(None, alias="efficiencyTier"),
    service: StorageService = Depends(_get_service),
):
    """Paginated, sortable file list with efficiency analytics."""
    return service.get_files(
        page=page,
        page_size=pageSize,
        sort_by=sortBy,
        sort_dir=sortDir,
        media_type=mediaType,
        codec=codec,
        resolution_tier=resolutionTier,
        efficiency_tier=efficiencyTier,
    )


@router.post("/scan-technical", status_code=202)
def trigger_technical_scan():
    """Trigger background FFprobe enrichment for files missing technical metadata."""
    from app.tasks import enrich_file_technical_metadata
    enrich_file_technical_metadata.delay()
    return {"message": "Technical metadata scan queued"}
```

**Step 5: Register the router in `app/main.py`**

Add the import at line 33 (after `enrichment_router`):
```python
from app.api.v1.storage.endpoints import router as storage_router
```

Add the router registration at line 214 (after `enrichment_router`):
```python
app.include_router(storage_router, prefix="/api/v1")
```

**Step 6: Run all endpoint tests**

```bash
pytest tests/test_storage_endpoints.py -v
```
Expected: all PASS.

**Step 7: Commit**

```bash
git add app/api/v1/storage/ tests/test_storage_endpoints.py app/main.py
git commit -m "feat: add /storage/summary, /storage/files, /storage/scan-technical endpoints"
```

---

### Task 5: Celery task for FFprobe batch enrichment (TDD)

**Files:**
- Modify: `app/tasks.py`
- Modify: `tests/test_tasks.py` (create if not exists)

**Step 1: Write a failing test**

If `tests/test_tasks.py` doesn't exist, create it. Otherwise append to it:

```python
"""Tests for Celery tasks."""
import pytest
from unittest.mock import patch, MagicMock, call
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

    with patch("app.tasks.SessionLocal", return_value=__import__("contextlib").nullcontext(mock_db)), \
         patch("app.tasks.FFProbeWrapper", return_value=mock_ffprobe):
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

    with patch("app.tasks.SessionLocal", return_value=__import__("contextlib").nullcontext(mock_db)), \
         patch("app.tasks.FFProbeWrapper", return_value=mock_ffprobe):
        result = enrich_file_technical_metadata.apply(args=[], kwargs={"batch_size": 50}).get()

    # Should still commit (no writes happened, but no crash either)
    assert result["processed"] == 0


def test_enrich_technical_metadata_returns_complete_when_no_files():
    """Returns immediately when no files need enrichment."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []

    with patch("app.tasks.SessionLocal", return_value=__import__("contextlib").nullcontext(mock_db)):
        result = enrich_file_technical_metadata.apply(args=[], kwargs={}).get()

    assert result["status"] == "complete"
    assert result["processed"] == 0
```

**Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_tasks.py::test_enrich_technical_metadata_updates_file_fields tests/test_tasks.py::test_enrich_technical_metadata_returns_complete_when_no_files -v
```
Expected: FAIL — `enrich_file_technical_metadata` not found in `app.tasks`.

**Step 3: Add the Celery task to `app/tasks.py`**

At the top of `app/tasks.py`, add `FileItem` to the models import block:
```python
from app.domain.files.models import FileItem
```

Then add the new task after the existing `enrich_metadata` task (after line ~200):

```python
@celery_app.task(bind=True, max_retries=0)
def enrich_file_technical_metadata(self, batch_size: int = 50):
    """Populate duration_seconds, video_codec, video_width, video_height on FileItems.

    Processes files with null duration_seconds in batches. Chains itself
    if more files remain after this batch.

    Args:
        batch_size: Maximum number of files to process in this invocation.
    """
    with SessionLocal() as db:
        files = (
            db.query(FileItem)
            .filter(
                FileItem.type == "file",
                FileItem.duration_seconds.is_(None),
            )
            .limit(batch_size)
            .all()
        )

        if not files:
            logger.info("enrich_file_technical_metadata: no files pending — done")
            return {"status": "complete", "processed": 0}

        ffprobe = FFProbeWrapper()
        processed = 0

        for file_item in files:
            try:
                duration = ffprobe.get_duration(file_item.path)
                codecs = ffprobe.get_codecs(file_item.path)
                resolution = ffprobe.get_resolution(file_item.path)

                file_item.duration_seconds = int(duration) if duration > 0 else None
                file_item.video_codec = codecs.get("video") if "error" not in codecs else None
                file_item.video_width = resolution.get("width") if "error" not in resolution else None
                file_item.video_height = resolution.get("height") if "error" not in resolution else None
                processed += 1
            except Exception as exc:
                logger.warning(
                    f"enrich_file_technical_metadata: skipping {file_item.path}: {exc}"
                )

        db.commit()

        # Check for remaining files and chain next batch
        remaining = (
            db.query(FileItem)
            .filter(FileItem.type == "file", FileItem.duration_seconds.is_(None))
            .count()
        )

        if remaining > 0:
            logger.info(f"enrich_file_technical_metadata: {remaining} files remain, chaining next batch")
            enrich_file_technical_metadata.delay(batch_size=batch_size)

        return {"status": "success", "processed": processed, "remaining": remaining}
```

**Step 4: Trigger on startup in `app/main.py`**

In the lifespan function in `app/main.py`, after the media directory sync (around line 80), add:

```python
    # Enrich any files missing technical metadata (duration, codec, resolution)
    logger.info("Triggering technical metadata enrichment for new files...")
    from app.tasks import enrich_file_technical_metadata
    enrich_file_technical_metadata.delay()
```

**Step 5: Run all task tests**

```bash
pytest tests/test_tasks.py -v
```
Expected: PASS.

**Step 6: Commit**

```bash
git add app/tasks.py app/main.py tests/test_tasks.py
git commit -m "feat: add enrich_file_technical_metadata Celery task with FFprobe batch processing"
```

---

### Task 6: Frontend storageService

**Files:**
- Create: `frontend/src/services/storageService.ts`

**Step 1: Create the service**

Create `frontend/src/services/storageService.ts`:

```typescript
import { apiClient } from '@/utils/api'

export interface DiskStats {
  totalBytes: number
  usedBytes: number
  availableBytes: number
}

export interface LibraryBreakdown {
  moviesBytes: number
  tvBytes: number
  otherBytes: number
}

export interface StorageSummary {
  disk: DiskStats
  library: LibraryBreakdown
  potentialSavingsBytes: number
  filesAnalyzed: number
  filesPendingAnalysis: number
}

export interface StorageFileItem {
  id: number
  name: string
  mediaType: 'movie' | 'tv' | 'other'
  sizeBytes: number
  durationSeconds: number | null
  videoCodec: string | null
  videoWidth: number | null
  videoHeight: number | null
  mbPerMin: number | null
  resolutionTier: '4k' | '1080p' | '720p' | 'sd' | 'unknown'
  efficiencyTier: 'efficient' | 'moderate' | 'large' | 'unknown'
  estimatedSavingsBytes: number
}

export interface StorageFilesResponse {
  total: number
  items: StorageFileItem[]
}

export interface StorageFilesParams {
  page?: number
  pageSize?: number
  sortBy?: string
  sortDir?: 'asc' | 'desc'
  mediaType?: string
  codec?: string
  resolutionTier?: string
  efficiencyTier?: string
}

export const storageService = {
  async getSummary(): Promise<StorageSummary> {
    const response = await apiClient.get<StorageSummary>('/storage/summary')
    return response.data
  },

  async getFiles(params: StorageFilesParams = {}): Promise<StorageFilesResponse> {
    const response = await apiClient.get<StorageFilesResponse>('/storage/files', { params })
    return response.data
  },

  async triggerScan(): Promise<void> {
    await apiClient.post('/storage/scan-technical')
  },
}
```

**Step 2: Commit**

```bash
git add frontend/src/services/storageService.ts
git commit -m "feat: add frontend storageService"
```

---

### Task 7: Wire Dashboard StorageChart with real data

**Files:**
- Modify: `frontend/src/components/dashboard/Dashboard/Dashboard.tsx`

**Step 1: Import storageService**

At the top of `Dashboard.tsx`, add after the existing service imports (around line 17):

```typescript
import { storageService, type StorageSummary } from '@/services/storageService'
import { formatFileSize } from '@/utils/helpers'
```

**Step 2: Add storage summary state**

In the `Dashboard` component, after line 140 (`const [configItems, ...`), add:

```typescript
  const [storageSummary, setStorageSummary] = useState<StorageSummary | null>(null)
```

**Step 3: Fetch storage summary in `loadDashboardData`**

In the `Promise.allSettled` array (around line 163), add `storageService.getSummary()` as the 7th item:

```typescript
      const results = await Promise.allSettled([
        healthService.getDetailedHealth(),
        movieService.getMovies(1, 50),
        tvShowService.getTVShows(1, 50),
        queueService.getStats(),
        fileService.getFileStats(),
        movieService.getEnrichmentStats(),
        storageService.getSummary(),           // ← add this
      ])
```

After line 176 (the enrichStats line), add:

```typescript
      const summary = results[6].status === 'fulfilled' ? results[6].value as StorageSummary : null
      setStorageSummary(summary)
```

**Step 4: Replace the storage placeholder with a live widget**

Find the storage section in the return JSX (around line 556):

```tsx
      {/* Storage Chart and Recent Activity - 2 column grid on desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {hasStorageData ? (
          <StorageChart data={storageData} total={totalStorage} />
        ) : (
          <Card variant="elevated">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Storage Usage
            </h3>
            <div className="text-center py-12">
              ...
            </div>
          </Card>
        )}
```

Replace the entire storage branch (from `{hasStorageData ?` through the closing `)}`) with:

```tsx
        {storageSummary ? (
          <div
            className="cursor-pointer"
            onClick={() => navigate('/storage')}
            role="link"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && navigate('/storage')}
          >
            <StorageChart
              data={[
                { label: 'Movies', value: storageSummary.library.moviesBytes, color: '#6366f1' },
                { label: 'TV Shows', value: storageSummary.library.tvBytes, color: '#8b5cf6' },
              ]}
              total={storageSummary.library.moviesBytes + storageSummary.library.tvBytes}
            />
            {storageSummary.disk.totalBytes > 0 && (() => {
              const pct = Math.round(storageSummary.disk.usedBytes / storageSummary.disk.totalBytes * 100)
              return (
                <div className="px-6 pb-4 -mt-2">
                  <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                    <span>{formatFileSize(storageSummary.disk.usedBytes)} used</span>
                    <span>{formatFileSize(storageSummary.disk.totalBytes)} total</span>
                  </div>
                  <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full transition-all ${pct > 90 ? 'bg-red-500' : pct > 70 ? 'bg-amber-400' : 'bg-emerald-500'}`}
                      style={{ width: `${Math.min(pct, 100)}%` }}
                    />
                  </div>
                </div>
              )
            })()}
          </div>
        ) : (
          <Card variant="elevated">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Storage Usage
            </h3>
            <div className="text-center py-12">
              <div className="mx-auto w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                </svg>
              </div>
              <h4 className="text-base font-medium text-slate-900 dark:text-white mb-2">
                Storage analytics loading…
              </h4>
            </div>
          </Card>
        )}
```

Also remove the now-unused `storageData`, `hasStorageData`, and `totalStorage` state and variables (lines ~138–139, 242–245, 470).

**Step 5: Verify in browser**

Open `http://localhost`. The storage widget should show a donut chart (Movies vs TV Shows) and, if disk stats are available, a disk usage bar below it. Clicking navigates to `/storage` (404 until Task 8).

**Step 6: Commit**

```bash
git add frontend/src/components/dashboard/Dashboard/Dashboard.tsx
git commit -m "feat: wire Dashboard StorageChart with live data from /storage/summary"
```

---

### Task 8: StoragePage component, route, and sidebar nav item

**Files:**
- Create: `frontend/src/pages/StoragePage.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/layout/Sidebar/Sidebar.tsx`

**Step 1: Create StoragePage**

Create `frontend/src/pages/StoragePage.tsx`:

```tsx
import React, { useState, useEffect, useCallback } from 'react'
import { Card } from '@/components/common/Card'
import { Skeleton } from '@/components/common/Skeleton'
import { formatFileSize } from '@/utils/helpers'
import { storageService, type StorageFileItem, type StorageSummary } from '@/services/storageService'

// ── Codec display names ────────────────────────────────────────────────────
const CODEC_LABEL: Record<string, string> = {
  h264: 'H.264',
  hevc: 'H.265',
  av1: 'AV1',
  vp9: 'VP9',
  mpeg2video: 'MPEG-2',
  vc1: 'VC-1',
  wmv3: 'WMV',
}

function formatCodec(codec: string | null): string {
  if (!codec) return '—'
  return CODEC_LABEL[codec.toLowerCase()] ?? codec.toUpperCase()
}

function formatDuration(seconds: number | null): string {
  if (!seconds) return '—'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

// ── Efficiency badge ───────────────────────────────────────────────────────
const TIER_CONFIG = {
  efficient: { label: 'Efficient', className: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' },
  moderate: { label: 'Moderate', className: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
  large: { label: 'Large', className: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
  unknown: { label: 'Pending', className: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400' },
} as const

function TierBadge({ tier }: { tier: StorageFileItem['efficiencyTier'] }) {
  const cfg = TIER_CONFIG[tier] ?? TIER_CONFIG.unknown
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${cfg.className}`}>
      {cfg.label}
    </span>
  )
}

// ── Summary cards ──────────────────────────────────────────────────────────
function SummaryCards({ summary }: { summary: StorageSummary }) {
  const libraryTotal = summary.library.moviesBytes + summary.library.tvBytes + summary.library.otherBytes
  const diskPct = summary.disk.totalBytes > 0
    ? Math.round(summary.disk.usedBytes / summary.disk.totalBytes * 100)
    : 0
  const totalFiles = summary.filesAnalyzed + summary.filesPendingAnalysis

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <Card variant="elevated" className="p-4">
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Total Library</p>
        <p className="text-2xl font-bold text-slate-900 dark:text-white">{formatFileSize(libraryTotal)}</p>
      </Card>
      <Card variant="elevated" className="p-4">
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Disk Available</p>
        <p className="text-2xl font-bold text-slate-900 dark:text-white">{formatFileSize(summary.disk.availableBytes)}</p>
        <p className="text-xs text-slate-400 mt-1">{diskPct}% used of {formatFileSize(summary.disk.totalBytes)}</p>
      </Card>
      <Card variant="elevated" className="p-4">
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Potential Savings</p>
        <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
          ~{formatFileSize(summary.potentialSavingsBytes)}
        </p>
        <p className="text-xs text-slate-400 mt-1">if re-encoded to H.265</p>
      </Card>
      <Card variant="elevated" className="p-4">
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Files Analyzed</p>
        <p className="text-2xl font-bold text-slate-900 dark:text-white">
          {summary.filesAnalyzed} <span className="text-base font-normal text-slate-400">/ {totalFiles}</span>
        </p>
      </Card>
    </div>
  )
}

// ── Column header with sort ────────────────────────────────────────────────
function SortHeader({
  label, field, sortBy, sortDir, onSort,
}: {
  label: string
  field: string
  sortBy: string
  sortDir: 'asc' | 'desc'
  onSort: (field: string) => void
}) {
  const active = sortBy === field
  return (
    <th
      className="px-4 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide cursor-pointer hover:text-slate-900 dark:hover:text-white select-none whitespace-nowrap"
      onClick={() => onSort(field)}
    >
      {label}
      {active && <span className="ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span>}
    </th>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────
export function StoragePage() {
  const [summary, setSummary] = useState<StorageSummary | null>(null)
  const [items, setItems] = useState<StorageFileItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState('size_bytes')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [filterMediaType, setFilterMediaType] = useState('')
  const [filterEfficiency, setFilterEfficiency] = useState('')

  const PAGE_SIZE = 50

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [summaryData, filesData] = await Promise.all([
        storageService.getSummary(),
        storageService.getFiles({
          page,
          pageSize: PAGE_SIZE,
          sortBy,
          sortDir,
          mediaType: filterMediaType || undefined,
          efficiencyTier: filterEfficiency || undefined,
        }),
      ])
      setSummary(summaryData)
      setItems(filesData.items)
      setTotal(filesData.total)
    } catch (err) {
      console.error('StoragePage: failed to load', err)
    } finally {
      setLoading(false)
    }
  }, [page, sortBy, sortDir, filterMediaType, filterEfficiency])

  useEffect(() => { load() }, [load])

  const handleSort = (field: string) => {
    if (field === sortBy) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortDir('desc')
    }
    setPage(1)
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Storage Analytics</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            File efficiency analysis — MB/min, codec, and estimated re-encode savings.
          </p>
        </div>
      </div>

      {/* Summary cards */}
      {loading && !summary ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)}
        </div>
      ) : summary ? (
        <SummaryCards summary={summary} />
      ) : null}

      {/* Pending banner */}
      {summary && summary.filesPendingAnalysis > 0 && (
        <div className="rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 px-4 py-3 text-sm text-amber-800 dark:text-amber-300">
          Technical metadata is being gathered for <strong>{summary.filesPendingAnalysis}</strong> files — refresh to update.
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <select
          value={filterMediaType}
          onChange={e => { setFilterMediaType(e.target.value); setPage(1) }}
          className="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-1.5"
        >
          <option value="">All Types</option>
          <option value="movie">Movies</option>
          <option value="tv">TV Shows</option>
        </select>
        <select
          value={filterEfficiency}
          onChange={e => { setFilterEfficiency(e.target.value); setPage(1) }}
          className="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-1.5"
        >
          <option value="">All Tiers</option>
          <option value="large">Large</option>
          <option value="moderate">Moderate</option>
          <option value="efficient">Efficient</option>
          <option value="unknown">Pending</option>
        </select>
        <span className="text-sm text-slate-500 dark:text-slate-400 self-center">
          {total} file{total !== 1 ? 's' : ''}
        </span>
      </div>

      {/* File table */}
      <Card variant="elevated" className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-200 dark:border-slate-700">
              <tr>
                <SortHeader label="File" field="name" sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Type</th>
                <SortHeader label="Size" field="size_bytes" sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
                <SortHeader label="Duration" field="duration_seconds" sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
                <SortHeader label="MB/min" field="mb_per_min" sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Codec</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Resolution</th>
                <SortHeader label="Est. Savings" field="estimated_savings_bytes" sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Tier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {loading ? (
                [...Array(10)].map((_, i) => (
                  <tr key={i}>
                    {[...Array(9)].map((_, j) => (
                      <td key={j} className="px-4 py-3"><Skeleton className="h-4 rounded" /></td>
                    ))}
                  </tr>
                ))
              ) : items.map(item => (
                <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                  <td className="px-4 py-3 max-w-xs truncate font-medium text-slate-900 dark:text-white" title={item.name}>
                    {item.name}
                  </td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400 capitalize">{item.mediaType}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300 whitespace-nowrap">{formatFileSize(item.sizeBytes)}</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400 whitespace-nowrap">{formatDuration(item.durationSeconds)}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{item.mbPerMin != null ? item.mbPerMin.toFixed(1) : '—'}</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{formatCodec(item.videoCodec)}</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400 uppercase text-xs">{item.resolutionTier === 'unknown' ? '—' : item.resolutionTier}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300 whitespace-nowrap">
                    {item.estimatedSavingsBytes > 0 ? `~${formatFileSize(item.estimatedSavingsBytes)}` : '—'}
                  </td>
                  <td className="px-4 py-3"><TierBadge tier={item.efficiencyTier} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200 dark:border-slate-700">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="text-sm px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-50 dark:hover:bg-slate-800"
            >
              Previous
            </button>
            <span className="text-sm text-slate-500 dark:text-slate-400">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="text-sm px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-50 dark:hover:bg-slate-800"
            >
              Next
            </button>
          </div>
        )}
      </Card>
    </div>
  )
}

export default StoragePage
```

**Step 2: Add the route to `frontend/src/App.tsx`**

Add the lazy import after line 22 (`EnrichmentPage`):
```typescript
const StoragePage = lazy(() => import('./pages/StoragePage').then(m => ({ default: m.StoragePage })))
```

Add the route after the `/enrichment` route block (after line 153):
```tsx
        <Route
          path="/storage"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<LoadingFallback />}>
                  <StoragePage />
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        />
```

**Step 3: Add Storage to the sidebar nav in `frontend/src/components/layout/Sidebar/Sidebar.tsx`**

Add `FaDatabase` to the react-icons import at line 3:
```typescript
import {
  FaHome, FaFolder, FaSearch, FaFilm, FaTv, FaCog, FaChevronLeft,
  FaChevronRight, FaInfoCircle, FaDatabase,
} from 'react-icons/fa'
```

Add the Storage nav item to `navItems` after the TV Shows entry (line 33):
```typescript
  { label: 'Storage', path: '/storage', icon: <FaDatabase className="w-5 h-5" /> },
```

**Step 4: Verify in browser**

- Open `http://localhost` — dashboard storage widget shows real data
- Click widget → navigates to `/storage`
- Click Storage in sidebar → navigates to `/storage`
- Storage page shows summary cards, filter dropdowns, sortable table
- Files with `null` codec show `—` in MB/min, Resolution, Est. Savings columns; Tier shows "Pending"

**Step 5: Commit**

```bash
git add frontend/src/pages/StoragePage.tsx frontend/src/App.tsx frontend/src/components/layout/Sidebar/Sidebar.tsx
git commit -m "feat: add StoragePage with file efficiency table, route, and sidebar nav item"
```
