# File Organisation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a manual file organisation feature that renames and moves media files to Plex or Jellyfin naming conventions, with a settings section showing conformance stats and a preview/apply modal.

**Architecture:** New `app_settings` DB table stores the selected preset. A new `OrganisationService` computes target paths from enriched DB metadata, returns dry-run previews and conformance stats, and executes renames via `shutil.move`. Five new API endpoints under `/api/v1/organisation/`. Frontend adds an organisation section to `SettingsPage` and an `OrganisationModal` component.

**Tech Stack:** Python/FastAPI/SQLAlchemy/Alembic (backend), TypeScript/React/Tailwind/Zustand (frontend)

---

### Preset format reference

| | Plex | Jellyfin |
|---|---|---|
| Movie folder | `{Title} ({Year})/` | `{Title} ({Year})/` |
| Movie file | `{Title} ({Year}).ext` | `{Title} ({Year}).ext` |
| TV folder | `{Show Name}/Season {NN}/` | `{Show Name}/Season {NN}/` |
| TV file | `{Show Name} - S{NN}E{NN} - {Episode Title}.ext` | `{Show Name} S{NN}E{NN}.ext` |

Only difference: Plex includes ` - {Episode Title}` in TV episode filenames. Movies are identical across presets.

---

### Task 1: Create feature branch

**Files:** none

**Step 1: Create branch**

```bash
git checkout -b feat/file-organisation
```

---

### Task 2: AppSetting DB model and Alembic migration

**Files:**
- Create: `app/domain/settings/__init__.py`
- Create: `app/domain/settings/models.py`
- Create: `alembic/versions/011_add_app_settings.py`
- Modify: `app/core/init_db.py`

**Step 1: Write the failing test**

Add a new test file `tests/test_app_settings_model.py`:

```python
"""Unit tests for AppSetting model"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.domain.settings.models import AppSetting


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_can_create_app_setting(db):
    setting = AppSetting(key="organisation_preset", value="plex")
    db.add(setting)
    db.commit()
    fetched = db.query(AppSetting).filter_by(key="organisation_preset").first()
    assert fetched is not None
    assert fetched.value == "plex"


def test_app_setting_updated_at_set_automatically(db):
    setting = AppSetting(key="foo", value="bar")
    db.add(setting)
    db.commit()
    assert setting.updated_at is not None
```

**Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_app_settings_model.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.domain.settings'`

**Step 3: Create the model**

Create `app/domain/settings/__init__.py` (empty).

Create `app/domain/settings/models.py`:

```python
"""AppSetting model for server-side key/value settings"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.core.database import Base


class AppSetting(Base):
    """Generic key/value store for server-side application settings."""

    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True, nullable=False)
    value = Column(String(500), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

**Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_app_settings_model.py -v
```

Expected: 2 tests PASS

**Step 5: Create Alembic migration**

Create `alembic/versions/011_add_app_settings.py`:

```python
"""Add app_settings table

Revision ID: 011
Revises: 010
Create Date: 2026-02-24
"""
import sqlalchemy as sa
from alembic import op

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'app_settings',
        sa.Column('key', sa.String(100), primary_key=True, nullable=False),
        sa.Column('value', sa.String(500), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('app_settings')
```

**Step 6: Ensure model is imported at startup**

Open `app/core/init_db.py`. Find where models are imported (look for lines like `from app.domain.movies.models import ...`). Add:

```python
from app.domain.settings.models import AppSetting  # noqa: F401
```

**Step 7: Verify migration runs**

```bash
alembic upgrade head
```

Expected: no errors, migration `011` applied.

---

### Task 3: Organisation service — path builders (TDD)

**Files:**
- Create: `app/domain/organisation/__init__.py`
- Create: `app/domain/organisation/service.py`
- Create: `tests/test_organisation_service.py`

**Step 1: Write failing tests for path builders**

Create `tests/test_organisation_service.py`:

```python
"""Unit tests for OrganisationService path builders"""
import pytest
from app.domain.organisation.service import (
    build_movie_target_path,
    build_tv_target_path,
    sanitize_filename,
)


# ---------------------------------------------------------------------------
# sanitize_filename
# ---------------------------------------------------------------------------

def test_sanitize_removes_invalid_chars():
    assert sanitize_filename('Show: Name') == 'Show Name'

def test_sanitize_strips_surrounding_whitespace():
    assert sanitize_filename('  Title  ') == 'Title'

def test_sanitize_collapses_double_spaces():
    assert sanitize_filename('A  B') == 'A B'


# ---------------------------------------------------------------------------
# build_movie_target_path — same for plex and jellyfin
# ---------------------------------------------------------------------------

def test_movie_target_path_plex():
    result = build_movie_target_path(
        base_dir='/media/movies',
        title='The Matrix',
        year=1999,
        ext='.mkv',
        preset='plex',
    )
    assert result == '/media/movies/The Matrix (1999)/The Matrix (1999).mkv'

def test_movie_target_path_jellyfin():
    result = build_movie_target_path(
        base_dir='/media/movies',
        title='The Matrix',
        year=1999,
        ext='.mkv',
        preset='jellyfin',
    )
    assert result == '/media/movies/The Matrix (1999)/The Matrix (1999).mkv'

def test_movie_target_path_no_year():
    result = build_movie_target_path(
        base_dir='/media/movies',
        title='Unknown Film',
        year=None,
        ext='.mp4',
        preset='plex',
    )
    assert result == '/media/movies/Unknown Film/Unknown Film.mp4'

def test_movie_target_path_sanitizes_colon():
    result = build_movie_target_path(
        base_dir='/media/movies',
        title='Batman: Forever',
        year=1995,
        ext='.mkv',
        preset='plex',
    )
    assert result == '/media/movies/Batman Forever (1995)/Batman Forever (1995).mkv'


# ---------------------------------------------------------------------------
# build_tv_target_path
# ---------------------------------------------------------------------------

def test_tv_target_path_plex_includes_title():
    result = build_tv_target_path(
        base_dir='/media/tv',
        show_title='Breaking Bad',
        season_number=1,
        episode_number=6,
        episode_title="Crazy Handful of Nothin'",
        ext='.mkv',
        preset='plex',
    )
    assert result == "/media/tv/Breaking Bad/Season 01/Breaking Bad - S01E06 - Crazy Handful of Nothin'.mkv"

def test_tv_target_path_jellyfin_omits_title():
    result = build_tv_target_path(
        base_dir='/media/tv',
        show_title='Breaking Bad',
        season_number=1,
        episode_number=6,
        episode_title="Crazy Handful of Nothin'",
        ext='.mkv',
        preset='jellyfin',
    )
    assert result == '/media/tv/Breaking Bad/Season 01/Breaking Bad S01E06.mkv'

def test_tv_target_path_plex_no_episode_title():
    """When episode title is None, Plex format omits the title suffix."""
    result = build_tv_target_path(
        base_dir='/media/tv',
        show_title='Some Show',
        season_number=2,
        episode_number=3,
        episode_title=None,
        ext='.mkv',
        preset='plex',
    )
    assert result == '/media/tv/Some Show/Season 02/Some Show - S02E03.mkv'

def test_tv_target_path_pads_numbers():
    result = build_tv_target_path(
        base_dir='/media/tv',
        show_title='Chernobyl',
        season_number=1,
        episode_number=1,
        episode_title='1:23:45',
        ext='.mkv',
        preset='plex',
    )
    # '1:23:45' has colons — they should be sanitized
    assert result == '/media/tv/Chernobyl/Season 01/Chernobyl - S01E01 - 1 23 45.mkv'
```

**Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_organisation_service.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.domain.organisation'`

**Step 3: Create `app/domain/organisation/__init__.py`** (empty)

**Step 4: Implement path builders in `app/domain/organisation/service.py`**

```python
"""Organisation service — file rename/move logic for Plex/Jellyfin standards."""

import logging
import re
import shutil
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import MOVIE_DIR, TV_DIR
from app.domain.movies.models import Movie, MovieFile
from app.domain.tv_shows.models import TVShow, Season, Episode, EpisodeFile

logger = logging.getLogger(__name__)

VALID_PRESETS = ("plex", "jellyfin")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sanitize_filename(name: str) -> str:
    """Remove filesystem-unsafe characters and normalise whitespace."""
    sanitized = re.sub(r'[/\\:*?"<>|]', ' ', name)
    sanitized = re.sub(r'\s+', ' ', sanitized)
    return sanitized.strip()


def build_movie_target_path(
    base_dir: str,
    title: str,
    year: Optional[int],
    ext: str,
    preset: str,
) -> str:
    """Return the target absolute path for a movie file.

    Both Plex and Jellyfin use the same movie format:
        {base_dir}/{Title} ({Year})/{Title} ({Year}).ext
    If year is None the parenthetical is omitted.
    """
    clean_title = sanitize_filename(title)
    folder_name = f"{clean_title} ({year})" if year else clean_title
    filename = f"{folder_name}{ext}"
    return str(Path(base_dir) / folder_name / filename)


def build_tv_target_path(
    base_dir: str,
    show_title: str,
    season_number: int,
    episode_number: int,
    episode_title: Optional[str],
    ext: str,
    preset: str,
) -> str:
    """Return the target absolute path for a TV episode file.

    Plex:     {base_dir}/{Show}/Season NN/{Show} - SNNENN - {Title}.ext
    Jellyfin: {base_dir}/{Show}/Season NN/{Show} SNNENN.ext
    """
    clean_show = sanitize_filename(show_title)
    season_dir = f"Season {season_number:02d}"
    ep_code = f"S{season_number:02d}E{episode_number:02d}"

    if preset == "jellyfin":
        filename = f"{clean_show} {ep_code}{ext}"
    else:  # plex
        if episode_title:
            clean_ep_title = sanitize_filename(episode_title)
            filename = f"{clean_show} - {ep_code} - {clean_ep_title}{ext}"
        else:
            filename = f"{clean_show} - {ep_code}{ext}"

    return str(Path(base_dir) / clean_show / season_dir / filename)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def get_conformance_stats(db: Session, preset: str) -> dict:
    """Return counts of how many files match/need-rename/unenriched per media type.

    Does NOT touch the filesystem — pure DB query.
    """
    movie_match = movie_rename = movie_unenriched = 0
    ep_match = ep_rename = ep_unenriched = 0

    for movie in db.query(Movie).all():
        if not movie.files:
            movie_unenriched += 1
            continue
        if not movie.title:
            movie_unenriched += 1
            continue
        for mf in movie.files:
            ext = Path(mf.file_path).suffix.lower()
            target = build_movie_target_path(MOVIE_DIR, movie.title, movie.year, ext, preset)
            if Path(mf.file_path).resolve() == Path(target).resolve():
                movie_match += 1
            else:
                movie_rename += 1

    for show in db.query(TVShow).all():
        for season in show.seasons:
            for episode in season.episodes:
                if not episode.files:
                    ep_unenriched += 1
                    continue
                for ef in episode.files:
                    ext = Path(ef.file_path).suffix.lower()
                    target = build_tv_target_path(
                        TV_DIR,
                        show.title,
                        season.season_number,
                        episode.episode_number,
                        episode.title,
                        ext,
                        preset,
                    )
                    if Path(ef.file_path).resolve() == Path(target).resolve():
                        ep_match += 1
                    else:
                        ep_rename += 1

    return {
        "movies_match": movie_match,
        "movies_need_rename": movie_rename,
        "movies_unenriched": movie_unenriched,
        "episodes_match": ep_match,
        "episodes_need_rename": ep_rename,
        "episodes_unenriched": ep_unenriched,
    }


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------

def get_preview(db: Session, preset: str) -> dict:
    """Return lists of proposed renames for movies and episodes.

    Only includes files where current path != target path.
    """
    movies = []
    episodes = []

    for movie in db.query(Movie).all():
        if not movie.title or not movie.files:
            continue
        for mf in movie.files:
            ext = Path(mf.file_path).suffix.lower()
            target = build_movie_target_path(MOVIE_DIR, movie.title, movie.year, ext, preset)
            if Path(mf.file_path).resolve() != Path(target).resolve():
                movies.append({
                    "file_id": mf.id,
                    "current_path": mf.file_path,
                    "target_path": target,
                })

    for show in db.query(TVShow).all():
        for season in show.seasons:
            for episode in season.episodes:
                if not episode.files:
                    continue
                for ef in episode.files:
                    ext = Path(ef.file_path).suffix.lower()
                    target = build_tv_target_path(
                        TV_DIR,
                        show.title,
                        season.season_number,
                        episode.episode_number,
                        episode.title,
                        ext,
                        preset,
                    )
                    if Path(ef.file_path).resolve() != Path(target).resolve():
                        episodes.append({
                            "file_id": ef.id,
                            "file_type": "episode",
                            "current_path": ef.file_path,
                            "target_path": target,
                        })

    return {"movies": movies, "episodes": episodes}


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------

def apply_renames(db: Session, items: list[dict]) -> dict:
    """Execute a list of rename operations.

    Each item: {"file_id": int, "file_type": "movie"|"episode", "target_path": str}

    Returns {"success": int, "failed": int, "errors": list[str]}
    """
    success = 0
    failed = 0
    errors = []

    for item in items:
        file_id = item["file_id"]
        file_type = item["file_type"]
        target = item["target_path"]

        try:
            if file_type == "movie":
                record = db.query(MovieFile).filter(MovieFile.id == file_id).first()
            else:
                record = db.query(EpisodeFile).filter(EpisodeFile.id == file_id).first()

            if not record:
                errors.append(f"File record {file_id} not found")
                failed += 1
                continue

            src = Path(record.file_path)
            dst = Path(target)

            if not src.exists():
                errors.append(f"Source file not found: {src}")
                failed += 1
                continue

            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            record.file_path = str(dst)
            success += 1
            logger.info(f"[Organisation] Renamed: {src} → {dst}")

        except Exception as e:
            errors.append(f"Failed to rename file {file_id}: {e}")
            failed += 1
            logger.error(f"[Organisation] Error renaming file {file_id}: {e}")

    if success:
        db.commit()

    return {"success": success, "failed": failed, "errors": errors}
```

**Step 5: Run the tests**

```bash
pytest tests/test_organisation_service.py -v
```

Expected: all PASS

---

### Task 4: Organisation API endpoints

**Files:**
- Create: `app/api/v1/organisation/__init__.py`
- Create: `app/api/v1/organisation/endpoints.py`
- Modify: `app/main.py`

**Step 1: Write a smoke test**

Add to `tests/test_organisation_service.py`:

```python
def test_build_movie_target_path_invalid_preset_still_works():
    """Unknown presets fall back to plex-style."""
    result = build_movie_target_path('/media/movies', 'Alien', 1979, '.mkv', 'unknown')
    assert result == '/media/movies/Alien (1979)/Alien (1979).mkv'
```

```bash
pytest tests/test_organisation_service.py::test_build_movie_target_path_invalid_preset_still_works -v
```

Expected: PASS (the service already handles this since the `else` branch covers all non-jellyfin values)

**Step 2: Create `app/api/v1/organisation/__init__.py`** (empty)

**Step 3: Create `app/api/v1/organisation/endpoints.py`**

```python
"""File Organisation API endpoints"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.organisation.service import (
    get_conformance_stats,
    get_preview,
    apply_renames,
    VALID_PRESETS,
)
from app.domain.settings.models import AppSetting

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organisation", tags=["Organisation"])

DEFAULT_PRESET = "plex"


def _get_preset(db: Session) -> str:
    setting = db.query(AppSetting).filter(AppSetting.key == "organisation_preset").first()
    return setting.value if setting else DEFAULT_PRESET


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class PresetPayload(BaseModel):
    preset: str


@router.get("/settings")
def get_organisation_settings(db: Session = Depends(get_db)):
    return {"preset": _get_preset(db)}


@router.put("/settings")
def update_organisation_settings(payload: PresetPayload, db: Session = Depends(get_db)):
    if payload.preset not in VALID_PRESETS:
        raise HTTPException(status_code=400, detail=f"preset must be one of: {VALID_PRESETS}")
    setting = db.query(AppSetting).filter(AppSetting.key == "organisation_preset").first()
    if setting:
        setting.value = payload.preset
    else:
        setting = AppSetting(key="organisation_preset", value=payload.preset)
        db.add(setting)
    db.commit()
    return {"preset": payload.preset}


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@router.get("/stats")
def get_stats(preset: str = None, db: Session = Depends(get_db)):
    active_preset = preset or _get_preset(db)
    if active_preset not in VALID_PRESETS:
        raise HTTPException(status_code=400, detail=f"preset must be one of: {VALID_PRESETS}")
    return get_conformance_stats(db, active_preset)


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------

@router.get("/preview")
def preview_renames(preset: str = None, db: Session = Depends(get_db)):
    active_preset = preset or _get_preset(db)
    if active_preset not in VALID_PRESETS:
        raise HTTPException(status_code=400, detail=f"preset must be one of: {VALID_PRESETS}")
    return get_preview(db, active_preset)


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------

class RenameItem(BaseModel):
    file_id: int
    file_type: str  # "movie" or "episode"
    target_path: str


class ApplyPayload(BaseModel):
    items: List[RenameItem]


@router.post("/apply")
def apply_organisation(payload: ApplyPayload, db: Session = Depends(get_db)):
    items = [item.model_dump() for item in payload.items]
    result = apply_renames(db, items)
    return result
```

**Step 4: Register the router in `app/main.py`**

Add the import near the other router imports (~line 34):

```python
from app.api.v1.organisation.endpoints import router as organisation_router
```

Add `app.include_router(...)` near the other router registrations (~line 217):

```python
app.include_router(organisation_router, prefix="/api/v1")
```

**Step 5: Verify import works**

```bash
python -c "from app.api.v1.organisation.endpoints import router; print('OK')"
```

Expected: `OK`

**Step 6: Run schema unit tests to confirm nothing is broken**

```bash
pytest tests/test_schemas_unit.py tests/test_app_settings_model.py tests/test_organisation_service.py -v
```

Expected: all PASS

---

### Task 5: Frontend organisation service

**Files:**
- Create: `frontend/src/services/organisationService.ts`

**Step 1: Create the service**

```typescript
import { apiClient } from '@/utils/api'
import { errorHandler } from '@/utils/errorHandler'

export type OrganisationPreset = 'plex' | 'jellyfin'

export interface OrganisationStats {
  movies_match: number
  movies_need_rename: number
  movies_unenriched: number
  episodes_match: number
  episodes_need_rename: number
  episodes_unenriched: number
}

export interface RenameProposal {
  file_id: number
  file_type: 'movie' | 'episode'
  current_path: string
  target_path: string
}

export interface OrganisationPreview {
  movies: RenameProposal[]
  episodes: RenameProposal[]
}

export interface ApplyResult {
  success: number
  failed: number
  errors: string[]
}

export const organisationService = {
  getSettings: async (): Promise<{ preset: OrganisationPreset }> => {
    try {
      const response = await apiClient.get<{ preset: OrganisationPreset }>('/organisation/settings')
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'getOrganisationSettings')
      throw error
    }
  },

  saveSettings: async (preset: OrganisationPreset): Promise<void> => {
    try {
      await apiClient.put('/organisation/settings', { preset })
    } catch (error: any) {
      errorHandler.handleError(error, 'saveOrganisationSettings')
      throw error
    }
  },

  getStats: async (preset: OrganisationPreset): Promise<OrganisationStats> => {
    try {
      const response = await apiClient.get<OrganisationStats>(`/organisation/stats?preset=${preset}`)
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'getOrganisationStats')
      throw error
    }
  },

  getPreview: async (preset: OrganisationPreset): Promise<OrganisationPreview> => {
    try {
      const response = await apiClient.get<OrganisationPreview>(`/organisation/preview?preset=${preset}`)
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'getOrganisationPreview')
      throw error
    }
  },

  applyRenames: async (items: RenameProposal[]): Promise<ApplyResult> => {
    try {
      const response = await apiClient.post<ApplyResult>('/organisation/apply', { items })
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'applyOrganisationRenames')
      throw error
    }
  },
}
```

**Step 2: Type-check**

```bash
cd /Users/john/Code/Metamaster/frontend && npm run type-check
```

Expected: no errors

---

### Task 6: Settings page — File Organisation section

**Files:**
- Modify: `frontend/src/pages/SettingsPage.tsx`

**Context:** The page already has a `SettingsSection` component. We are adding a new section below the existing ones, before the action buttons.

**Step 1: Add imports at the top of `SettingsPage.tsx`**

Add to the existing imports:

```typescript
import { FaFolder } from 'react-icons/fa'
import { organisationService, type OrganisationPreset, type OrganisationStats } from '@/services/organisationService'
import { OrganisationModal } from '@/components/features/organisation/OrganisationModal'
```

**Step 2: Add state inside the `SettingsPage` component**

Add after the existing `useState` declarations:

```typescript
const [orgPreset, setOrgPreset] = useState<OrganisationPreset>('plex')
const [orgStats, setOrgStats] = useState<OrganisationStats | null>(null)
const [orgStatsLoading, setOrgStatsLoading] = useState(false)
const [orgModalOpen, setOrgModalOpen] = useState(false)
```

**Step 3: Load saved preset and initial stats on mount**

Add a new `useEffect` after the existing scan schedule `useEffect`:

```typescript
useEffect(() => {
  organisationService.getSettings()
    .then(({ preset }) => {
      setOrgPreset(preset)
      return organisationService.getStats(preset)
    })
    .then(setOrgStats)
    .catch(() => {})
}, [])
```

**Step 4: Add a preset change handler**

Add after the existing `handleSaveScanSchedule` function:

```typescript
const handleOrgPresetChange = async (preset: OrganisationPreset) => {
  setOrgPreset(preset)
  setOrgStatsLoading(true)
  try {
    await organisationService.saveSettings(preset)
    const stats = await organisationService.getStats(preset)
    setOrgStats(stats)
  } catch {
    // non-fatal
  } finally {
    setOrgStatsLoading(false)
  }
}
```

**Step 5: Add the File Organisation section to the JSX**

Add this section just before the `{/* Action Buttons */}` div:

```tsx
{/* File Organisation */}
<SettingsSection
  icon={<FaFolder />}
  title="File Organisation"
  description="Rename and move media files to match your media server's naming convention"
>
  <div className="space-y-4">
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Naming Preset
      </label>
      <select
        value={orgPreset}
        onChange={(e) => handleOrgPresetChange(e.target.value as OrganisationPreset)}
        className="w-full sm:w-48 px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
      >
        <option value="plex">Plex</option>
        <option value="jellyfin">Jellyfin</option>
      </select>
    </div>

    {/* Conformance stats */}
    {orgStats && (
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
          <p className="font-medium text-gray-700 dark:text-gray-300 mb-1">Movies</p>
          <p className="text-green-600 dark:text-green-400">✓ {orgStats.movies_match} match</p>
          {orgStats.movies_need_rename > 0 && (
            <p className="text-amber-600 dark:text-amber-400">⚠ {orgStats.movies_need_rename} need renaming</p>
          )}
          {orgStats.movies_unenriched > 0 && (
            <p className="text-gray-400 dark:text-gray-500">– {orgStats.movies_unenriched} unenriched</p>
          )}
        </div>
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
          <p className="font-medium text-gray-700 dark:text-gray-300 mb-1">TV Episodes</p>
          <p className="text-green-600 dark:text-green-400">✓ {orgStats.episodes_match} match</p>
          {orgStats.episodes_need_rename > 0 && (
            <p className="text-amber-600 dark:text-amber-400">⚠ {orgStats.episodes_need_rename} need renaming</p>
          )}
          {orgStats.episodes_unenriched > 0 && (
            <p className="text-gray-400 dark:text-gray-500">– {orgStats.episodes_unenriched} unenriched</p>
          )}
        </div>
      </div>
    )}
    {orgStatsLoading && (
      <p className="text-sm text-gray-400 dark:text-gray-500">Loading stats…</p>
    )}

    <button
      onClick={() => setOrgModalOpen(true)}
      disabled={!orgStats || (orgStats.movies_need_rename === 0 && orgStats.episodes_need_rename === 0)}
      className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
    >
      Preview & Apply Changes
    </button>
  </div>
</SettingsSection>

<OrganisationModal
  isOpen={orgModalOpen}
  preset={orgPreset}
  onClose={() => {
    setOrgModalOpen(false)
    // Refresh stats after modal closes
    organisationService.getStats(orgPreset).then(setOrgStats).catch(() => {})
  }}
/>
```

**Step 6: Type-check**

```bash
cd /Users/john/Code/Metamaster/frontend && npm run type-check
```

Expected: errors about `OrganisationModal` not existing yet — that's fine, we build it next.

---

### Task 7: OrganisationModal component

**Files:**
- Create: `frontend/src/components/features/organisation/OrganisationModal.tsx`

**Step 1: Create the component**

```tsx
import React, { useEffect, useState } from 'react'
import {
  organisationService,
  type OrganisationPreset,
  type OrganisationPreview,
  type RenameProposal,
} from '@/services/organisationService'

interface OrganisationModalProps {
  isOpen: boolean
  preset: OrganisationPreset
  onClose: () => void
}

type Tab = 'movies' | 'episodes'

export const OrganisationModal: React.FC<OrganisationModalProps> = ({ isOpen, preset, onClose }) => {
  const [preview, setPreview] = useState<OrganisationPreview | null>(null)
  const [loading, setLoading] = useState(false)
  const [applying, setApplying] = useState(false)
  const [result, setResult] = useState<{ success: number; failed: number; errors: string[] } | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [activeTab, setActiveTab] = useState<Tab>('movies')

  useEffect(() => {
    if (!isOpen) return
    setPreview(null)
    setResult(null)
    setLoading(true)
    organisationService.getPreview(preset)
      .then((data) => {
        setPreview(data)
        // Pre-select all items
        const allKeys = new Set<string>([
          ...data.movies.map((m) => `movie-${m.file_id}`),
          ...data.episodes.map((e) => `episode-${e.file_id}`),
        ])
        setSelected(allKeys)
        setActiveTab(data.movies.length > 0 ? 'movies' : 'episodes')
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [isOpen, preset])

  const toggleItem = (key: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const toggleAll = (items: RenameProposal[], type: 'movie' | 'episode') => {
    const keys = items.map((i) => `${type}-${i.file_id}`)
    const allSelected = keys.every((k) => selected.has(k))
    setSelected((prev) => {
      const next = new Set(prev)
      if (allSelected) keys.forEach((k) => next.delete(k))
      else keys.forEach((k) => next.add(k))
      return next
    })
  }

  const handleApply = async () => {
    if (!preview) return
    setApplying(true)
    setResult(null)

    const items: RenameProposal[] = [
      ...preview.movies
        .filter((m) => selected.has(`movie-${m.file_id}`))
        .map((m) => ({ ...m, file_type: 'movie' as const })),
      ...preview.episodes
        .filter((e) => selected.has(`episode-${e.file_id}`))
        .map((e) => ({ ...e, file_type: 'episode' as const })),
    ]

    try {
      const res = await organisationService.applyRenames(items)
      setResult(res)
      // Remove applied items from preview
      setPreview((prev) => prev ? {
        movies: prev.movies.filter((m) => !selected.has(`movie-${m.file_id}`)),
        episodes: prev.episodes.filter((e) => !selected.has(`episode-${e.file_id}`)),
      } : null)
      setSelected(new Set())
    } catch {
      setResult({ success: 0, failed: items.length, errors: ['Request failed'] })
    } finally {
      setApplying(false)
    }
  }

  const selectedCount = selected.size
  const shorten = (path: string) => path.split('/').slice(-3).join('/')

  if (!isOpen) return null

  const movies = preview?.movies ?? []
  const episodes = preview?.episodes ?? []

  return (
    <div
      className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"
      onClick={onClose}
      aria-hidden="true"
    >
      <div
        className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="File Organisation Preview"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Preview & Apply Changes</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5 capitalize">{preset} format</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-200 dark:border-slate-700 px-6">
          {(['movies', 'episodes'] as Tab[]).map((tab) => {
            const count = tab === 'movies' ? movies.length : episodes.length
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-3 px-4 text-sm font-medium border-b-2 -mb-px transition capitalize ${
                  activeTab === tab
                    ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                    : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
              >
                {tab} <span className="ml-1 text-xs text-slate-400">({count})</span>
              </button>
            )
          })}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            (() => {
              const items = activeTab === 'movies' ? movies : episodes
              const type = activeTab === 'movies' ? 'movie' : 'episode'
              if (items.length === 0) {
                return (
                  <p className="text-center py-12 text-slate-400 dark:text-slate-500 text-sm">
                    All {activeTab} already match the {preset} format.
                  </p>
                )
              }
              return (
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-left text-slate-400 dark:text-slate-500">
                      <th className="pb-2 pr-3 w-8">
                        <input
                          type="checkbox"
                          checked={items.every((i) => selected.has(`${type}-${i.file_id}`))}
                          onChange={() => toggleAll(items, type)}
                          className="w-3.5 h-3.5 text-indigo-600 rounded"
                        />
                      </th>
                      <th className="pb-2 pr-4">Current path</th>
                      <th className="pb-2">Proposed path</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
                    {items.map((item) => {
                      const key = `${type}-${item.file_id}`
                      return (
                        <tr key={key} className="hover:bg-slate-50 dark:hover:bg-slate-700/30">
                          <td className="py-2 pr-3">
                            <input
                              type="checkbox"
                              checked={selected.has(key)}
                              onChange={() => toggleItem(key)}
                              className="w-3.5 h-3.5 text-indigo-600 rounded"
                            />
                          </td>
                          <td className="py-2 pr-4 font-mono text-slate-500 dark:text-slate-400">
                            …/{shorten(item.current_path)}
                          </td>
                          <td className="py-2 font-mono text-slate-800 dark:text-slate-200">
                            …/{shorten(item.target_path)}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )
            })()
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between gap-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">
            {selectedCount > 0 ? `${selectedCount} file${selectedCount !== 1 ? 's' : ''} selected` : 'No files selected'}
            {result && (
              <span className="ml-3">
                {result.success > 0 && <span className="text-green-600 dark:text-green-400">✓ {result.success} renamed</span>}
                {result.failed > 0 && <span className="ml-2 text-red-500 dark:text-red-400">✗ {result.failed} failed</span>}
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition"
            >
              Close
            </button>
            <button
              onClick={handleApply}
              disabled={applying || selectedCount === 0}
              className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {applying ? 'Applying…' : `Apply ${selectedCount > 0 ? selectedCount : ''} change${selectedCount !== 1 ? 's' : ''}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
```

**Step 2: Type-check and lint**

```bash
cd /Users/john/Code/Metamaster/frontend && npm run type-check
```

Expected: no errors

---

### Task 8: End-to-end verification

**Step 1: Backend tests**

```bash
pytest tests/test_app_settings_model.py tests/test_organisation_service.py tests/test_schemas_unit.py -v
```

Expected: all PASS

**Step 2: Frontend build**

```bash
cd /Users/john/Code/Metamaster/frontend && npm run build
```

Expected: clean build, no TypeScript errors

**Step 3: Confirm branch is clean and all changes staged**

```bash
git status
git log --oneline -8
```

Expected: all files either committed or staged for your manual commit
