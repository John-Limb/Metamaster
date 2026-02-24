# Episode Detail Display Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enrich the episode list in TVShowDetailPage to show episode number, name, runtime, quality badge, and a truncated synopsis per row.

**Architecture:** The `EpisodeFile` model already stores `resolution` (→ quality label) and `duration` (→ runtime minutes). We add two optional fields to `EpisodeResponse`, populate them in the API endpoint from the episode's first associated file, update the frontend type, and update the UI component.

**Tech Stack:** Python/FastAPI/SQLAlchemy (backend), TypeScript/React/Tailwind (frontend)

---

### Task 1: Create feature branch

**Files:** none

**Step 1: Create and switch to the branch**

```bash
git checkout -b feat/episode-detail-display
```

Expected: switched to a new branch 'feat/episode-detail-display'

---

### Task 2: Add `quality` and `runtime` to `EpisodeResponse` schema (TDD)

**Files:**
- Modify: `app/schemas.py` — `EpisodeResponse` class (~line 243)
- Modify: `tests/test_schemas_unit.py` — `TestEpisodeResponseSchema` class (~line 241)

**Step 1: Write failing test**

Add to `TestEpisodeResponseSchema` in `tests/test_schemas_unit.py` (after the existing `test_valid_episode_response` test at ~line 261):

```python
def test_episode_response_with_quality_and_runtime(self):
    """Test EpisodeResponse accepts quality and runtime fields"""
    now = datetime.utcnow()
    response = EpisodeResponse(
        id=2,
        episode_number=3,
        title="Full Measure",
        created_at=now,
        updated_at=now,
        quality="1080p",
        runtime=47,
    )
    assert response.quality == "1080p"
    assert response.runtime == 47

def test_episode_response_quality_runtime_optional(self):
    """Test quality and runtime default to None"""
    now = datetime.utcnow()
    response = EpisodeResponse(
        id=3,
        episode_number=1,
        created_at=now,
        updated_at=now,
    )
    assert response.quality is None
    assert response.runtime is None
```

**Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_schemas_unit.py::TestEpisodeResponseSchema -v
```

Expected: FAILED — `EpisodeResponse() got unexpected keyword argument 'quality'`

**Step 3: Add fields to `EpisodeResponse` in `app/schemas.py`**

Find the `EpisodeResponse` class (~line 243). Add two optional fields after `tmdb_id`:

```python
class EpisodeResponse(BaseModel):
    """Schema for episode response"""

    id: int = Field(..., description="Episode ID")
    episode_number: int = Field(..., description="Episode number")
    title: Optional[str] = None
    plot: Optional[str] = None
    air_date: Optional[str] = Field(None, description="Air date in YYYY-MM-DD format")
    rating: Optional[float] = None
    tmdb_id: Optional[str] = None
    quality: Optional[str] = Field(None, description="Quality label derived from file resolution e.g. 1080p, 4K")
    runtime: Optional[int] = Field(None, description="Runtime in minutes derived from file duration")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)
```

**Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_schemas_unit.py::TestEpisodeResponseSchema -v
```

Expected: 3 tests PASSED

**Step 5: Commit**

```bash
git add app/schemas.py tests/test_schemas_unit.py
git commit -m "feat: add quality and runtime fields to EpisodeResponse schema"
```

---

### Task 3: Populate quality/runtime from EpisodeFile in the API endpoint

**Files:**
- Modify: `app/api/v1/tv_shows/endpoints.py` — `get_season_episodes` function (~line 238)

**Context:** The `EpisodeFile` model (in `app/domain/tv_shows/models.py`) has:
- `resolution: str` — e.g. `"1920x1080"`, `"3840x2160"`, `"1280x720"`
- `duration: int` — file duration in seconds

Each `Episode` ORM object has a `.files` relationship (list of `EpisodeFile`). Take the first file if present.

**Step 1: Add a helper function above `get_season_episodes` in `app/api/v1/tv_shows/endpoints.py`**

Add after the imports section, before the router definition or just before the `get_season_episodes` function:

```python
def _resolution_to_quality(resolution: Optional[str]) -> Optional[str]:
    """Convert a resolution string like '1920x1080' to a quality label like '1080p'."""
    if not resolution:
        return None
    try:
        height = int(resolution.split("x")[1])
    except (IndexError, ValueError):
        return None
    if height >= 2160:
        return "4K"
    if height >= 1080:
        return "1080p"
    if height >= 720:
        return "720p"
    if height >= 576:
        return "576p"
    if height >= 480:
        return "480p"
    return f"{height}p"
```

You will need to add `from typing import Optional` if not already imported at the top of `endpoints.py`.
Check the top of the file — if `Optional` is missing, add it to the existing import line or add:
```python
from typing import Optional
```

**Step 2: Update `get_season_episodes` to build episode dicts with quality and runtime**

Replace the return block in `get_season_episodes` (currently ~lines 269-274):

```python
    # Build episode dicts with quality/runtime from first associated file
    episode_items = []
    for ep in episodes:
        first_file = ep.files[0] if ep.files else None
        quality = _resolution_to_quality(first_file.resolution if first_file else None)
        runtime_minutes = round(first_file.duration / 60) if first_file and first_file.duration else None
        episode_items.append({
            "id": ep.id,
            "episode_number": ep.episode_number,
            "title": ep.title,
            "plot": ep.plot,
            "air_date": ep.air_date,
            "rating": ep.rating,
            "tmdb_id": ep.tmdb_id,
            "quality": quality,
            "runtime": runtime_minutes,
            "created_at": ep.created_at,
            "updated_at": ep.updated_at,
        })

    return {
        "items": episode_items,
        "total": total,
        **pagination_metadata(total=total, limit=normalized_limit, skip=normalized_offset),
        "page": current_page,
    }
```

**Step 3: Verify the backend runs without import errors**

```bash
python -c "from app.api.v1.tv_shows.endpoints import router; print('OK')"
```

Expected: `OK`

**Step 4: Run the full schema unit test suite**

```bash
pytest tests/test_schemas_unit.py -v
```

Expected: all tests PASSED

**Step 5: Commit**

```bash
git add app/api/v1/tv_shows/endpoints.py
git commit -m "feat: populate quality and runtime from EpisodeFile in episodes endpoint"
```

---

### Task 4: Update the frontend `Episode` type

**Files:**
- Modify: `frontend/src/types/index.ts` — `Episode` interface (~line 131)

**Step 1: Add `quality` and `runtime` fields to the `Episode` interface**

Locate the `Episode` interface in `frontend/src/types/index.ts` (around line 131). It currently looks like:

```typescript
export interface Episode {
  id: number
  episode_number: number
  title?: string | null
  plot?: string | null
  air_date?: string | null
  rating?: number | null
  tmdb_id?: string | null
  created_at: string
  updated_at: string
}
```

Add the two new fields after `tmdb_id`:

```typescript
export interface Episode {
  id: number
  episode_number: number
  title?: string | null
  plot?: string | null
  air_date?: string | null
  rating?: number | null
  tmdb_id?: string | null
  quality?: string | null
  runtime?: number | null
  created_at: string
  updated_at: string
}
```

**Step 2: Run TypeScript type check**

```bash
cd frontend && npm run type-check
```

Expected: no errors

**Step 3: Commit**

```bash
git add frontend/src/types/index.ts
git commit -m "feat: add quality and runtime to Episode type"
```

---

### Task 5: Update the episode row in TVShowDetailPage

**Files:**
- Modify: `frontend/src/components/features/tvshows/TVShowDetailPage/TVShowDetailPage.tsx`

**Context:** The episode row rendering is in the `.map((ep) => ...)` block starting around line 246. The current row layout is:
- Left: episode number (monospace), then title + plot
- Right: air date + rating

The new layout will be:
- Left: episode number + title (with quality badge + runtime inline in the title line)
- Below title: synopsis (2-line clamp, same as now)
- Right: air date + rating (unchanged)

**Step 1: Add a `formatRuntime` helper near the top of the file**

Add this helper alongside the existing `formatAirDate` helper (~line 71):

```typescript
const formatRuntime = (minutes: number) => {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}
```

**Step 2: Replace the episode row JSX**

Find the episode row JSX block (the `<div key={ep.id} className="flex items-start gap-4 px-6 py-3">` block, roughly lines 247-281) and replace the entire `<div key={ep.id} ...>` element with:

```tsx
<div
  key={ep.id}
  className="flex items-start gap-4 px-6 py-3"
>
  {/* Episode number */}
  <span className="flex-shrink-0 w-8 text-sm font-mono text-slate-400 dark:text-slate-500 pt-0.5">
    {String(ep.episode_number).padStart(2, '0')}
  </span>

  {/* Title row + synopsis */}
  <div className="flex-1 min-w-0">
    <div className="flex items-center gap-2 flex-wrap">
      <p className="text-sm font-medium text-slate-900 dark:text-white">
        {ep.title ?? `Episode ${ep.episode_number}`}
      </p>
      {ep.quality && (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300">
          {ep.quality}
        </span>
      )}
      {ep.runtime != null && (
        <span className="text-xs text-slate-400 dark:text-slate-500">
          {formatRuntime(ep.runtime)}
        </span>
      )}
    </div>
    {ep.plot && (
      <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2">
        {ep.plot}
      </p>
    )}
  </div>

  {/* Meta: air date + rating */}
  <div className="flex-shrink-0 text-right space-y-0.5">
    {ep.air_date && (
      <p className="text-xs text-slate-400 dark:text-slate-500">
        {formatAirDate(ep.air_date)}
      </p>
    )}
    {ep.rating != null && (
      <p className="text-xs text-amber-500 font-medium">
        ★ {ep.rating.toFixed(1)}
      </p>
    )}
  </div>
</div>
```

**Step 3: Run type check**

```bash
cd frontend && npm run type-check
```

Expected: no errors

**Step 4: Run the frontend linter**

```bash
cd frontend && npm run lint
```

Expected: no errors

**Step 5: Commit**

```bash
git add frontend/src/components/features/tvshows/TVShowDetailPage/TVShowDetailPage.tsx
git commit -m "feat: show episode name, quality badge, runtime, and synopsis in season episode list"
```

---

### Task 6: Verify everything end-to-end

**Step 1: Run backend tests**

```bash
pytest tests/test_schemas_unit.py -v
```

Expected: all PASSED

**Step 2: Run frontend build to catch any compilation errors**

```bash
cd frontend && npm run build
```

Expected: build succeeds with no TypeScript errors

**Step 3: Final commit / push**

All individual changes are already committed. Confirm branch is clean:

```bash
git status
git log --oneline -5
```

Expected: clean working tree, 4 feature commits on `feat/episode-detail-display`
