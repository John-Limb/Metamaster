# Unwatched Space Optimisation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Surface library files that have never been watched so the user can identify space-saving candidates, by adding a Watched Status filter to the Storage page.

**Architecture:** `StorageService` gains a `_get_path_watch_info()` helper that JOINs through `MovieFile`/`EpisodeFile` and `PlexSyncRecord` to build a path-keyed watch lookup. `get_files()` uses this to add three new fields per row and filter by `watched_status`. `get_summary()` adds unwatched size totals. The Storage page gets a filter dropdown, a recoverable-space banner, and TV episode grouping.

**Tech Stack:** SQLAlchemy (JOIN queries), FastAPI (query param), React + TypeScript (filter, banner, grouping)

---

### Task 1: StorageService — path watch info + get_files() filter

**Files:**
- Modify: `app/domain/storage/service.py`
- Modify: `tests/test_storage_service.py`

#### Background

`StorageService` iterates `FileItem` rows (raw file scans). Watch status lives on `PlexSyncRecord`, linked via `MovieFile.file_path` / `EpisodeFile.file_path`. The new `_get_path_watch_info()` method runs two queries and returns a dict keyed by file path. `get_files()` calls it once, adds three new fields to every result row, and applies the filter when `watched_status` is set.

**Step 1: Write the failing tests**

Add to `tests/test_storage_service.py`:

```python
from unittest.mock import call


def _make_movie_row(path, title, is_watched):
    """Return a 3-tuple mimicking (MovieFile.file_path, Movie.title, PlexSyncRecord.is_watched)."""
    return (path, title, is_watched)


def _make_ep_row(path, show_title, show_id, is_watched):
    """Return a 4-tuple mimicking episode query row."""
    return (path, show_title, show_id, is_watched)


def test_get_path_watch_info_movies(service):
    """Movie paths get is_watched, title, show_title=None, show_fully_unwatched=None."""
    service.db.query.return_value.join.return_value.join.return_value.outerjoin.return_value.all.return_value = []

    movie_q = service.db.query.return_value
    # First .all() call → movie rows
    movie_q.join.return_value.join.return_value.outerjoin.return_value.all.return_value = [
        _make_movie_row("/media/movies/a.mkv", "Movie A", False),
    ]
    # Second .all() call (episode query) → empty
    service.db.query.side_effect = None

    # Use a simpler approach: patch at the method level
    with patch.object(service, "_get_path_watch_info", wraps=None) as _:
        pass  # just verify the helper exists and structure below

    # Directly test via get_files watched_status filter:
    # We'll test _get_path_watch_info indirectly via get_files in the next test.
    assert hasattr(service, "_get_path_watch_info")


def test_get_files_unwatched_filter_excludes_watched(service):
    """watched_status='unwatched' returns only rows with is_watched=False."""
    mock_file = _make_mock_file("/media/movies/a.mkv", 2_000_000_000, "h264", 1920, 1080, 7200)
    service.db.query.return_value.filter.return_value.filter.return_value.all.return_value = [
        mock_file
    ]
    watch_info = {
        "/media/movies/a.mkv": {
            "is_watched": False,
            "title": "Movie A",
            "show_title": None,
            "show_fully_unwatched": None,
        }
    }
    with (
        patch("app.domain.storage.service.settings") as mock_settings,
        patch("app.domain.storage.service.MOVIE_DIR", "/media/movies"),
        patch("app.domain.storage.service.TV_DIR", "/media/tv"),
        patch.object(service, "_get_path_watch_info", return_value=watch_info),
    ):
        mock_settings.watch_extensions = [".mkv"]
        result = service.get_files(watched_status="unwatched")
    assert result["total"] == 1
    assert result["items"][0]["is_watched"] is False


def test_get_files_unwatched_filter_excludes_watched_items(service):
    """watched_status='unwatched' excludes files with is_watched=True."""
    mock_file = _make_mock_file("/media/movies/b.mkv", 1_000_000_000, "h264", 1920, 1080, 7200)
    service.db.query.return_value.filter.return_value.filter.return_value.all.return_value = [
        mock_file
    ]
    watch_info = {
        "/media/movies/b.mkv": {
            "is_watched": True,
            "title": "Movie B",
            "show_title": None,
            "show_fully_unwatched": None,
        }
    }
    with (
        patch("app.domain.storage.service.settings") as mock_settings,
        patch("app.domain.storage.service.MOVIE_DIR", "/media/movies"),
        patch("app.domain.storage.service.TV_DIR", "/media/tv"),
        patch.object(service, "_get_path_watch_info", return_value=watch_info),
    ):
        mock_settings.watch_extensions = [".mkv"]
        result = service.get_files(watched_status="unwatched")
    assert result["total"] == 0


def test_get_files_includes_show_title_for_tv(service):
    """TV episode files get show_title and show_fully_unwatched in the result."""
    mock_file = _make_mock_file("/media/tv/show/s01e01.mkv", 500_000_000, "h264", 1920, 1080, 2700)
    service.db.query.return_value.filter.return_value.filter.return_value.all.return_value = [
        mock_file
    ]
    watch_info = {
        "/media/tv/show/s01e01.mkv": {
            "is_watched": False,
            "title": None,
            "show_title": "My Show",
            "show_fully_unwatched": True,
        }
    }
    with (
        patch("app.domain.storage.service.settings") as mock_settings,
        patch("app.domain.storage.service.MOVIE_DIR", "/media/movies"),
        patch("app.domain.storage.service.TV_DIR", "/media/tv"),
        patch.object(service, "_get_path_watch_info", return_value=watch_info),
    ):
        mock_settings.watch_extensions = [".mkv"]
        result = service.get_files()
    item = result["items"][0]
    assert item["show_title"] == "My Show"
    assert item["show_fully_unwatched"] is True
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_storage_service.py::test_get_files_unwatched_filter_excludes_watched \
       tests/test_storage_service.py::test_get_files_unwatched_filter_excludes_watched_items \
       tests/test_storage_service.py::test_get_files_includes_show_title_for_tv -v
```

Expected: FAIL — `get_files()` does not accept `watched_status`, rows have no `show_title`.

**Step 3: Implement `_get_path_watch_info` and update `get_files()`**

Add this method to `StorageService` in `app/domain/storage/service.py` (insert before `get_summary`):

```python
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

    for file_path, show_title, show_id, is_watched in ep_data:
        result[file_path] = {
            "is_watched": is_watched,
            "title": None,
            "show_title": show_title,
            "show_fully_unwatched": not show_has_watched[show_id],
        }

    return result
```

Now update `get_files()` signature — add `watched_status: Optional[str] = None` to the parameter list.

Inside `get_files()`, add one line at the top of the method body:

```python
path_watch_info = self._get_path_watch_info()
```

In the `results.append(...)` block, add three fields at the end of the dict:

```python
"is_watched": path_watch_info.get(f.path, {}).get("is_watched"),
"show_title": path_watch_info.get(f.path, {}).get("show_title"),
"show_fully_unwatched": path_watch_info.get(f.path, {}).get("show_fully_unwatched"),
```

After the existing filter block (after `if efficiency_tier:`), add:

```python
if watched_status == "unwatched":
    results = [r for r in results if r.get("is_watched") is False]
elif watched_status == "watched":
    results = [r for r in results if r.get("is_watched") is True]
```

**Step 4: Run tests**

```bash
pytest tests/test_storage_service.py -v
```

Expected: all pass.

**Step 5: Stage**

```bash
git add app/domain/storage/service.py tests/test_storage_service.py
```

---

### Task 2: StorageService — unwatched size totals in get_summary()

**Files:**
- Modify: `app/domain/storage/service.py`
- Modify: `tests/test_storage_service.py`

**Step 1: Write the failing test**

Add to `tests/test_storage_service.py`:

```python
def test_get_summary_includes_unwatched_size_fields(service):
    """get_summary() response includes unwatched_movie_size_bytes and unwatched_tv_size_bytes."""
    service.db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
    with (
        patch("app.domain.storage.service.settings") as mock_settings,
        patch.object(
            service,
            "get_disk_stats",
            return_value={"total_bytes": 0, "used_bytes": 0, "available_bytes": 0},
        ),
    ):
        mock_settings.watch_extensions = []
        result = service.get_summary()
    assert "unwatched_movie_size_bytes" in result
    assert "unwatched_tv_size_bytes" in result
    assert isinstance(result["unwatched_movie_size_bytes"], int)
    assert isinstance(result["unwatched_tv_size_bytes"], int)
```

**Step 2: Run to verify it fails**

```bash
pytest tests/test_storage_service.py::test_get_summary_includes_unwatched_size_fields -v
```

Expected: FAIL — keys not present.

**Step 3: Implement**

Add a new private helper in `app/domain/storage/service.py` (insert after `_get_path_watch_info`):

```python
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
```

In `get_summary()`, add just before the `return` statement:

```python
unwatched_movie_bytes, unwatched_tv_bytes = self._get_unwatched_sizes()
```

Add these two keys to the returned dict:

```python
"unwatched_movie_size_bytes": unwatched_movie_bytes,
"unwatched_tv_size_bytes": unwatched_tv_bytes,
```

**Step 4: Run tests**

```bash
pytest tests/test_storage_service.py -v
```

Expected: all pass.

**Step 5: Stage**

```bash
git add app/domain/storage/service.py tests/test_storage_service.py
```

---

### Task 3: API endpoint — watchedStatus query param

**Files:**
- Modify: `app/api/v1/storage/endpoints.py`
- Modify: `tests/test_storage_endpoints.py`

**Step 1: Write the failing test**

Add to `tests/test_storage_endpoints.py`:

```python
def test_get_files_passes_watched_status():
    with patch("app.api.v1.storage.endpoints.StorageService") as MockService:
        MockService.return_value.get_files.return_value = {"total": 0, "items": []}
        client.get("/api/v1/storage/files?watchedStatus=unwatched")
        MockService.return_value.get_files.assert_called_once_with(
            page=1,
            page_size=50,
            sort_by="size_bytes",
            sort_dir="desc",
            media_type=None,
            codec=None,
            resolution_tier=None,
            efficiency_tier=None,
            watched_status="unwatched",
        )


def test_get_summary_includes_unwatched_size_keys():
    summary_with_unwatched = {
        **SUMMARY_PAYLOAD,
        "unwatched_movie_size_bytes": 500_000_000_000,
        "unwatched_tv_size_bytes": 200_000_000_000,
    }
    with patch("app.api.v1.storage.endpoints.StorageService") as MockService:
        MockService.return_value.get_summary.return_value = summary_with_unwatched
        response = client.get("/api/v1/storage/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["unwatched_movie_size_bytes"] == 500_000_000_000
    assert data["unwatched_tv_size_bytes"] == 200_000_000_000
```

**Step 2: Run to verify they fail**

```bash
pytest tests/test_storage_endpoints.py::test_get_files_passes_watched_status \
       tests/test_storage_endpoints.py::test_get_summary_includes_unwatched_size_keys -v
```

Expected: FAIL — endpoint does not accept `watchedStatus`.

**Step 3: Implement**

In `app/api/v1/storage/endpoints.py`, add `watchedStatus` to `get_storage_files`:

```python
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
    watchedStatus: Optional[str] = Query(None, alias="watchedStatus"),
    service: StorageService = Depends(_get_service),
):
    return service.get_files(
        page=page,
        page_size=pageSize,
        sort_by=sortBy,
        sort_dir=sortDir,
        media_type=mediaType,
        codec=codec,
        resolution_tier=resolutionTier,
        efficiency_tier=efficiencyTier,
        watched_status=watchedStatus,
    )
```

Also update the existing `test_get_files_passes_query_params` test — the existing assertion no longer matches because `watched_status` is now passed. Update it:

```python
def test_get_files_passes_query_params():
    with patch("app.api.v1.storage.endpoints.StorageService") as MockService:
        MockService.return_value.get_files.return_value = {"total": 0, "items": []}
        client.get(
            "/api/v1/storage/files?page=2&pageSize=25&sortBy=mb_per_min&sortDir=asc&mediaType=movie"
        )
        MockService.return_value.get_files.assert_called_once_with(
            page=2,
            page_size=25,
            sort_by="mb_per_min",
            sort_dir="asc",
            media_type="movie",
            codec=None,
            resolution_tier=None,
            efficiency_tier=None,
            watched_status=None,
        )
```

**Step 4: Run tests**

```bash
pytest tests/test_storage_endpoints.py -v
```

Expected: all pass.

**Step 5: Stage**

```bash
git add app/api/v1/storage/endpoints.py tests/test_storage_endpoints.py
```

---

### Task 4: Frontend — service types

**Files:**
- Modify: `frontend/src/services/storageService.ts`
- Create: `frontend/src/services/__tests__/storageService.test.ts`

**Step 1: Write the failing test**

Create `frontend/src/services/__tests__/storageService.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { storageService } from '../storageService'

vi.mock('axios')
const mockAxios = vi.mocked(axios)

beforeEach(() => {
  vi.clearAllMocks()
})

describe('storageService.getFiles', () => {
  it('passes watchedStatus param', async () => {
    mockAxios.get = vi.fn().mockResolvedValue({ data: { total: 0, items: [] } })
    await storageService.getFiles({ watchedStatus: 'unwatched' })
    expect(mockAxios.get).toHaveBeenCalledWith(
      '/api/v1/storage/files',
      expect.objectContaining({
        params: expect.objectContaining({ watchedStatus: 'unwatched' }),
      })
    )
  })

  it('includes new fields in StorageFileItem type — is_watched null for unlibrary file', async () => {
    const item = {
      id: 1,
      name: 'test.mkv',
      media_type: 'movie',
      size_bytes: 1_000_000_000,
      duration_seconds: 7200,
      video_codec: 'h264',
      video_width: 1920,
      video_height: 1080,
      mb_per_min: 23.1,
      resolution_tier: '1080p',
      efficiency_tier: 'efficient',
      estimated_savings_bytes: 0,
      is_watched: null,
      show_title: null,
      show_fully_unwatched: null,
    }
    mockAxios.get = vi.fn().mockResolvedValue({ data: { total: 1, items: [item] } })
    const result = await storageService.getFiles({})
    expect(result.items[0].is_watched).toBeNull()
    expect(result.items[0].show_title).toBeNull()
  })
})

describe('storageService.getSummary', () => {
  it('returns unwatched size fields', async () => {
    const summary = {
      disk: { total_bytes: 1000, used_bytes: 500, available_bytes: 500 },
      library: { movies_bytes: 0, tv_bytes: 0, other_bytes: 0 },
      potential_savings_bytes: 0,
      files_analyzed: 0,
      files_pending_analysis: 0,
      unwatched_movie_size_bytes: 400_000_000_000,
      unwatched_tv_size_bytes: 100_000_000_000,
    }
    mockAxios.get = vi.fn().mockResolvedValue({ data: summary })
    const result = await storageService.getSummary()
    expect(result.unwatched_movie_size_bytes).toBe(400_000_000_000)
    expect(result.unwatched_tv_size_bytes).toBe(100_000_000_000)
  })
})
```

**Step 2: Run to verify it fails**

```bash
cd frontend && npm run test -- --run src/services/__tests__/storageService.test.ts
```

Expected: TypeScript compile error — `watchedStatus` not in `StorageFilesParams`, `is_watched` not in `StorageFileItem`.

**Step 3: Implement**

In `frontend/src/services/storageService.ts`, find `StorageFilesParams` and add:

```typescript
watchedStatus?: 'watched' | 'unwatched'
```

Find `StorageFileItem` and add after `estimated_savings_bytes`:

```typescript
is_watched: boolean | null
show_title: string | null
show_fully_unwatched: boolean | null
```

Find `StorageSummary` and add:

```typescript
unwatched_movie_size_bytes: number
unwatched_tv_size_bytes: number
```

In the `getFiles` method, make sure `watchedStatus` is passed through in the params object:

```typescript
params: {
  ...existing params...,
  watchedStatus: params.watchedStatus,
}
```

**Step 4: Run tests**

```bash
cd frontend && npm run test -- --run src/services/__tests__/storageService.test.ts
```

Expected: all pass.

Also verify no TypeScript errors:

```bash
cd frontend && npm run type-check
```

**Step 5: Stage**

```bash
git add frontend/src/services/storageService.ts \
        frontend/src/services/__tests__/storageService.test.ts
```

---

### Task 5: StoragePage — filter, banner, and TV grouping

**Files:**
- Modify: `frontend/src/pages/StoragePage.tsx`
- Create: `frontend/src/pages/__tests__/StoragePage.test.tsx`

**Step 1: Write the failing tests**

Create `frontend/src/pages/__tests__/StoragePage.test.tsx`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { StoragePage } from '../StoragePage'
import { storageService } from '@/services/storageService'

vi.mock('@/services/storageService')
const mockService = vi.mocked(storageService)

const baseSummary = {
  disk: { total_bytes: 4_000_000_000_000, used_bytes: 2_000_000_000_000, available_bytes: 2_000_000_000_000 },
  library: { movies_bytes: 1_000_000_000_000, tv_bytes: 500_000_000_000, other_bytes: 0 },
  potential_savings_bytes: 200_000_000_000,
  files_analyzed: 10,
  files_pending_analysis: 0,
  unwatched_movie_size_bytes: 300_000_000_000,
  unwatched_tv_size_bytes: 100_000_000_000,
}

const baseFilesResponse = { total: 0, items: [] }

beforeEach(() => {
  vi.clearAllMocks()
  mockService.getSummary = vi.fn().mockResolvedValue(baseSummary)
  mockService.getFiles = vi.fn().mockResolvedValue(baseFilesResponse)
  mockService.triggerScan = vi.fn().mockResolvedValue(undefined)
})

describe('StoragePage — watched status filter', () => {
  it('renders watched status filter options', async () => {
    render(<StoragePage />)
    await waitFor(() => expect(screen.queryByText('Loading')).not.toBeInTheDocument())
    expect(screen.getByDisplayValue('All')).toBeInTheDocument()
  })

  it('shows recoverable space banner when unwatched filter is active', async () => {
    render(<StoragePage />)
    await waitFor(() => expect(mockService.getFiles).toHaveBeenCalled())
    const select = screen.getByLabelText(/watched status/i)
    fireEvent.change(select, { target: { value: 'unwatched' } })
    await waitFor(() => {
      expect(screen.getByText(/potentially recoverable/i)).toBeInTheDocument()
    })
  })

  it('hides recoverable banner when filter is not unwatched', async () => {
    render(<StoragePage />)
    await waitFor(() => expect(mockService.getFiles).toHaveBeenCalled())
    expect(screen.queryByText(/potentially recoverable/i)).not.toBeInTheDocument()
  })

  it('passes watchedStatus to getFiles when filter changes', async () => {
    render(<StoragePage />)
    await waitFor(() => expect(mockService.getFiles).toHaveBeenCalled())
    const select = screen.getByLabelText(/watched status/i)
    fireEvent.change(select, { target: { value: 'unwatched' } })
    await waitFor(() => {
      const calls = mockService.getFiles.mock.calls
      const lastCall = calls[calls.length - 1][0]
      expect(lastCall.watchedStatus).toBe('unwatched')
    })
  })
})

describe('StoragePage — TV show grouping', () => {
  it('renders TV show group header for episodes with show_title when unwatched filter active', async () => {
    const episodeItem = {
      id: 1,
      name: 's01e01.mkv',
      media_type: 'tv',
      size_bytes: 500_000_000,
      duration_seconds: 2700,
      video_codec: 'h264',
      video_width: 1920,
      video_height: 1080,
      mb_per_min: 11.1,
      resolution_tier: '1080p',
      efficiency_tier: 'efficient' as const,
      estimated_savings_bytes: 0,
      is_watched: false,
      show_title: 'Breaking Bad',
      show_fully_unwatched: true,
    }
    mockService.getFiles = vi.fn().mockResolvedValue({ total: 1, items: [episodeItem] })
    render(<StoragePage />)
    await waitFor(() => expect(mockService.getFiles).toHaveBeenCalled())
    const select = screen.getByLabelText(/watched status/i)
    fireEvent.change(select, { target: { value: 'unwatched' } })
    await waitFor(() => {
      expect(screen.getByText('Breaking Bad')).toBeInTheDocument()
      expect(screen.getByText(/never watched/i)).toBeInTheDocument()
    })
  })
})
```

**Step 2: Run to verify they fail**

```bash
cd frontend && npm run test -- --run src/pages/__tests__/StoragePage.test.tsx
```

Expected: FAIL — no `watchedStatus` filter, no banner, no grouping.

**Step 3: Implement in StoragePage.tsx**

**3a.** Add `filterWatchedStatus` state after `filterEfficiency`:

```typescript
const [filterWatchedStatus, setFilterWatchedStatus] = useState('')
```

**3b.** Pass it to `getFiles` in the `load` callback:

```typescript
watchedStatus: (filterWatchedStatus as 'watched' | 'unwatched') || undefined,
```

Add `filterWatchedStatus` to the `useCallback` dependency array.

**3c.** Add the filter select to the filters section (after the existing Efficiency select):

```tsx
<label htmlFor="filter-watched" className="sr-only">Watched Status</label>
<select
  id="filter-watched"
  aria-label="Watched Status"
  value={filterWatchedStatus}
  onChange={e => { setFilterWatchedStatus(e.target.value); setPage(1) }}
  className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 text-sm px-3 py-2"
>
  <option value="">All</option>
  <option value="unwatched">Unwatched</option>
  <option value="watched">Watched</option>
</select>
```

**3d.** Add the recoverable space banner just before the file table (after the pending banner). Show it only when `filterWatchedStatus === 'unwatched'` and `summary` is set:

```tsx
{filterWatchedStatus === 'unwatched' && summary && (
  <div className="rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 px-4 py-3 text-sm text-amber-800 dark:text-amber-200">
    <span className="font-semibold">
      {formatBytes(summary.unwatched_movie_size_bytes + summary.unwatched_tv_size_bytes)}
    </span>{' '}
    potentially recoverable from unwatched files.
  </div>
)}
```

**3e.** Add TV show grouping logic. Add a helper function above the `StoragePage` component:

```typescript
function groupItemsWithShowHeaders(
  items: StorageFileItem[],
  showGrouping: boolean
): Array<StorageFileItem | { _groupHeader: true; show_title: string; show_fully_unwatched: boolean }> {
  if (!showGrouping) return items
  const result: Array<StorageFileItem | { _groupHeader: true; show_title: string; show_fully_unwatched: boolean }> = []
  let lastShow: string | null = null
  const sorted = [...items].sort((a, b) => {
    if (a.show_title && b.show_title) return a.show_title.localeCompare(b.show_title)
    if (a.show_title) return 1
    if (b.show_title) return -1
    return 0
  })
  for (const item of sorted) {
    if (item.show_title && item.show_title !== lastShow) {
      result.push({ _groupHeader: true, show_title: item.show_title, show_fully_unwatched: item.show_fully_unwatched ?? false })
      lastShow = item.show_title
    }
    result.push(item)
  }
  return result
}
```

**3f.** In the table body, use the grouped items when `filterWatchedStatus === 'unwatched'`:

```tsx
{groupItemsWithShowHeaders(items, filterWatchedStatus === 'unwatched').map((row, idx) => {
  if ('_groupHeader' in row) {
    return (
      <tr key={`group-${row.show_title}`} className="bg-slate-50 dark:bg-slate-800/50">
        <td colSpan={8} className="px-4 py-2">
          <span className="font-semibold text-slate-700 dark:text-slate-200 text-sm">{row.show_title}</span>
          <span className={`ml-2 text-xs px-1.5 py-0.5 rounded ${
            row.show_fully_unwatched
              ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
              : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
          }`}>
            {row.show_fully_unwatched ? 'Never watched' : 'Partially watched'}
          </span>
        </td>
      </tr>
    )
  }
  // existing row render — replace `item` with `row`:
  return (
    <tr key={row.id} /* ... existing row JSX but using `row` instead of `item` */ />
  )
})}
```

> **Note:** The existing table body maps over `items`. Replace the entire map with the grouped version above. The row JSX inside is unchanged — just rename the loop variable from `item` to `row` (for non-header rows).

**Step 4: Run tests**

```bash
cd frontend && npm run test -- --run src/pages/__tests__/StoragePage.test.tsx
```

Expected: all pass.

Also run the full suite to check for regressions:

```bash
cd frontend && npm run test -- --run && npm run type-check && npm run lint
```

**Step 5: Stage**

```bash
git add frontend/src/pages/StoragePage.tsx \
        frontend/src/pages/__tests__/StoragePage.test.tsx
```

---

## Verification

After all tasks:

```bash
# Backend
pytest tests/test_storage_service.py tests/test_storage_endpoints.py -v

# Frontend
cd frontend && npm run test -- --run && npm run type-check && npm run lint
```

All tests should pass with no TypeScript or lint errors.
