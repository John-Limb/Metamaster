# Plex Now Playing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a "Now Playing" panel that polls Plex's active sessions endpoint every 30 s (via Celery), caches results in Redis, and surfaces them on the System Health page with a live-updating frontend panel.

**Architecture:** A new Celery Beat task calls `GET /status/sessions` on the Plex server every 30 s and stores the result in Redis under key `plex:sessions:live` with a 60 s TTL. A new FastAPI endpoint reads that key and returns the list. The frontend polls the endpoint every 15 s via TanStack Query and renders a `NowPlayingPanel` component.

**Tech Stack:** Python/Pydantic (schemas), httpx (PlexClient), Celery Beat (task scheduling), RedisCacheService (ephemeral storage), FastAPI (endpoint), React + TanStack Query (frontend).

---

### Task 1: PlexSession schema + PlexClient.get_sessions()

**Files:**
- Modify: `app/infrastructure/external_apis/plex/schemas.py`
- Modify: `app/infrastructure/external_apis/plex/client.py`
- Test: `tests/test_plex_client.py`

**Context:** Plex `/status/sessions` returns a `MediaContainer.Metadata` list. Each item has a nested `Player` object (`title`, `state`) and `User` object (`title`). When no sessions are active the key `Metadata` is absent entirely. For episodes `type` = `"episode"`, `grandparentTitle` = show name, `parentIndex` = season, `index` = episode number.

**Step 1: Write failing tests**

Add to the bottom of `tests/test_plex_client.py`:

```python
@pytest.mark.unit
def test_plex_session_parses_movie():
    from app.infrastructure.external_apis.plex.schemas import PlexSession
    data = {
        "ratingKey": "42",
        "title": "Inception",
        "type": "movie",
        "grandparentTitle": None,
        "parentIndex": None,
        "index": None,
        "duration": 7200000,
        "viewOffset": 3600000,
        "Player": {"title": "Chrome", "state": "playing"},
        "User": {"title": "john"},
    }
    session = PlexSession(**data)
    assert session.rating_key == "42"
    assert session.title == "Inception"
    assert session.type == "movie"
    assert session.view_offset == 3600000
    assert session.player.state == "playing"
    assert session.player.title == "Chrome"
    assert session.user.title == "john"
    assert session.grandparent_title is None


@pytest.mark.unit
def test_plex_session_parses_episode():
    from app.infrastructure.external_apis.plex.schemas import PlexSession
    data = {
        "ratingKey": "99",
        "title": "Pilot",
        "type": "episode",
        "grandparentTitle": "Breaking Bad",
        "parentIndex": 1,
        "index": 1,
        "duration": 3000000,
        "viewOffset": 1000000,
        "Player": {"title": "Apple TV", "state": "paused"},
        "User": {"title": "jane"},
    }
    session = PlexSession(**data)
    assert session.grandparent_title == "Breaking Bad"
    assert session.parent_index == 1
    assert session.index == 1
    assert session.player.state == "paused"


@pytest.mark.unit
@respx.mock
def test_get_sessions_returns_active_sessions():
    from app.infrastructure.external_apis.plex.schemas import PlexSession
    respx.get("http://plex:32400/status/sessions").mock(
        return_value=httpx.Response(
            200,
            json={
                "MediaContainer": {
                    "size": 1,
                    "Metadata": [
                        {
                            "ratingKey": "42",
                            "title": "Inception",
                            "type": "movie",
                            "duration": 7200000,
                            "viewOffset": 3600000,
                            "Player": {"title": "Chrome", "state": "playing"},
                            "User": {"title": "john"},
                        }
                    ],
                }
            },
        )
    )
    client = PlexClient(server_url="http://plex:32400", token="tok123")
    sessions = client.get_sessions()
    assert len(sessions) == 1
    assert isinstance(sessions[0], PlexSession)
    assert sessions[0].title == "Inception"


@pytest.mark.unit
@respx.mock
def test_get_sessions_returns_empty_when_nothing_playing():
    respx.get("http://plex:32400/status/sessions").mock(
        return_value=httpx.Response(
            200,
            json={"MediaContainer": {"size": 0}},
        )
    )
    client = PlexClient(server_url="http://plex:32400", token="tok123")
    sessions = client.get_sessions()
    assert sessions == []
```

**Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_plex_client.py -k "session" -v -m unit
```

Expected: `ImportError` or `AttributeError` — `PlexSession` and `get_sessions` don't exist yet.

**Step 3: Add `PlexSessionPlayer`, `PlexSessionUser`, `PlexSession` to schemas**

In `app/infrastructure/external_apis/plex/schemas.py`, append after `PlexMediaItem`:

```python
class PlexSessionPlayer(BaseModel):
    model_config = {"extra": "ignore"}

    title: str = "Unknown"
    state: str = "playing"  # "playing", "paused", "buffering"


class PlexSessionUser(BaseModel):
    model_config = {"extra": "ignore"}

    title: str = "Unknown"


class PlexSession(BaseModel):
    model_config = {"populate_by_name": True, "extra": "ignore"}

    rating_key: str = Field(alias="ratingKey")
    title: str
    type: str  # "movie" or "episode"
    grandparent_title: Optional[str] = Field(alias="grandparentTitle", default=None)
    parent_index: Optional[int] = Field(alias="parentIndex", default=None)
    index: Optional[int] = Field(alias="index", default=None)
    duration: int = 0  # milliseconds
    view_offset: int = Field(alias="viewOffset", default=0)  # milliseconds
    player: PlexSessionPlayer = Field(alias="Player", default_factory=PlexSessionPlayer)
    user: PlexSessionUser = Field(alias="User", default_factory=PlexSessionUser)
```

**Step 4: Add `get_sessions()` to PlexClient**

In `app/infrastructure/external_apis/plex/client.py`, add this import at the top:

```python
from app.infrastructure.external_apis.plex.schemas import PlexLibrarySection, PlexMediaItem, PlexSession
```

Then append the method to the `PlexClient` class:

```python
    def get_sessions(self) -> List[PlexSession]:
        data = self._get("/status/sessions")
        metadata = data.get("MediaContainer", {}).get("Metadata") or []
        return [PlexSession(**m) for m in metadata]
```

**Step 5: Run tests — expect PASS**

```bash
pytest tests/test_plex_client.py -k "session" -v -m unit
```

Expected: 4 tests passing.

**Step 6: Run full unit suite to confirm no regressions**

```bash
pytest -m unit -q
```

Expected: 43 passed, 0 failed.

**Step 7: Commit**

```bash
git add app/infrastructure/external_apis/plex/schemas.py \
        app/infrastructure/external_apis/plex/client.py \
        tests/test_plex_client.py
git commit -m "feat(plex): add PlexSession schema and get_sessions() client method"
```

---

### Task 2: Celery task poll_plex_sessions + Redis storage

**Files:**
- Modify: `app/tasks/plex.py`
- Modify: `app/tasks/celery_beat.py`
- Test: `tests/test_plex_tasks.py`

**Context:** `_make_client()` already handles missing config. Use `get_cache_service()` from `app/infrastructure/cache/redis_cache.py` — its `set(key, value, ttl)` handles JSON serialisation. Store sessions as a list of dicts with `model_dump()`. Use TTL 60 s (two poll intervals) so stale data expires if the task stops running.

**Step 1: Write failing tests**

Add to the bottom of `tests/test_plex_tasks.py`:

```python
@pytest.mark.unit
@patch("app.tasks.plex._make_client")
@patch("app.tasks.plex.get_cache_service")
def test_poll_plex_sessions_stores_to_redis(mock_cache_svc, mock_make_client):
    from app.infrastructure.external_apis.plex.schemas import (
        PlexSession,
        PlexSessionPlayer,
        PlexSessionUser,
    )
    from app.tasks.plex import poll_plex_sessions

    mock_session = PlexSession(
        ratingKey="1",
        title="Inception",
        type="movie",
        duration=7200000,
        viewOffset=1800000,
        Player=PlexSessionPlayer(title="Chrome", state="playing"),
        User=PlexSessionUser(title="john"),
    )
    mock_client = MagicMock()
    mock_client.get_sessions.return_value = [mock_session]
    mock_make_client.return_value = mock_client

    mock_cache = MagicMock()
    mock_cache_svc.return_value = mock_cache

    poll_plex_sessions()

    mock_client.get_sessions.assert_called_once()
    mock_cache.set.assert_called_once()
    call_args = mock_cache.set.call_args
    assert call_args[0][0] == "plex:sessions:live"
    stored = call_args[0][1]
    assert isinstance(stored, list)
    assert stored[0]["title"] == "Inception"
    assert call_args[1]["ttl"] == 60


@pytest.mark.unit
@patch("app.tasks.plex._make_client")
def test_poll_plex_sessions_skips_when_not_configured(mock_make_client):
    from app.tasks.plex import poll_plex_sessions

    mock_make_client.return_value = None
    result = poll_plex_sessions()
    assert result is None
```

**Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_plex_tasks.py -k "session" -v -m unit
```

Expected: `ImportError` — `poll_plex_sessions` doesn't exist yet.

**Step 3: Add task to `app/tasks/plex.py`**

Add this import at the top of `app/tasks/plex.py` (after existing imports):

```python
from app.infrastructure.cache.redis_cache import get_cache_service
```

Then append the new task:

```python
@celery_app.task(
    name="app.tasks.plex.poll_plex_sessions",
    queue="external_api",
)
def poll_plex_sessions() -> None:
    """Poll Plex active sessions and cache them in Redis."""
    client = _make_client()
    if client is None:
        return None

    sessions = client.get_sessions()
    payload = [s.model_dump() for s in sessions]
    get_cache_service().set("plex:sessions:live", payload, ttl=60)
    logger.info("Plex: cached %d active sessions", len(sessions))
```

**Step 4: Add to Celery Beat schedule in `app/tasks/celery_beat.py`**

Append inside the `beat_schedule` dict:

```python
    "poll_plex_sessions": {
        "task": "app.tasks.plex.poll_plex_sessions",
        "schedule": 30.0,  # every 30 seconds
        "options": {
            "queue": "external_api",
        },
    },
```

**Step 5: Run tests — expect PASS**

```bash
pytest tests/test_plex_tasks.py -k "session" -v -m unit
```

Expected: 2 tests passing.

**Step 6: Run full unit suite**

```bash
pytest -m unit -q
```

Expected: 45 passed, 0 failed.

**Step 7: Commit**

```bash
git add app/tasks/plex.py app/tasks/celery_beat.py tests/test_plex_tasks.py
git commit -m "feat(plex): add poll_plex_sessions task with Redis caching"
```

---

### Task 3: Backend API endpoint GET /api/v1/plex/sessions

**Files:**
- Modify: `app/api/v1/plex/router.py`
- Test: `tests/test_plex_api.py`

**Context:** The endpoint reads from Redis. If Redis is unavailable or the key has expired (no active sessions), return `[]`. No auth required — consistent with the existing `/health` endpoint on this router. The `get_current_user` dependency is used on connection-management endpoints only; sessions are read-only telemetry.

**Step 1: Write failing test**

Add to the bottom of `tests/test_plex_api.py`:

```python
@pytest.mark.unit
@patch("app.api.v1.plex.router.get_cache_service")
def test_get_plex_sessions_returns_cached_data(mock_cache_svc, client):
    mock_cache = MagicMock()
    mock_cache.get.return_value = [
        {
            "rating_key": "42",
            "title": "Inception",
            "type": "movie",
            "grandparent_title": None,
            "parent_index": None,
            "index": None,
            "duration": 7200000,
            "view_offset": 3600000,
            "player": {"title": "Chrome", "state": "playing"},
            "user": {"title": "john"},
        }
    ]
    mock_cache_svc.return_value = mock_cache

    response = client.get("/api/v1/plex/sessions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Inception"


@pytest.mark.unit
@patch("app.api.v1.plex.router.get_cache_service")
def test_get_plex_sessions_returns_empty_when_no_cache(mock_cache_svc, client):
    mock_cache = MagicMock()
    mock_cache.get.return_value = None
    mock_cache_svc.return_value = mock_cache

    response = client.get("/api/v1/plex/sessions")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.unit
@patch("app.api.v1.plex.router.get_cache_service")
def test_get_plex_sessions_returns_empty_on_redis_error(mock_cache_svc, client):
    mock_cache_svc.side_effect = Exception("Redis down")

    response = client.get("/api/v1/plex/sessions")
    assert response.status_code == 200
    assert response.json() == []
```

**Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_plex_api.py -k "sessions" -v -m unit
```

Expected: 404 or `AttributeError` — endpoint doesn't exist yet.

**Step 3: Add import and endpoint to `app/api/v1/plex/router.py`**

Add to the imports block at the top:

```python
from app.infrastructure.cache.redis_cache import get_cache_service
```

Then append the endpoint (before the final closing of the file):

```python
@router.get("/sessions")
async def get_plex_sessions() -> list:
    """Return currently active Plex playback sessions from Redis cache.

    Returns an empty list if Plex is not configured, nothing is playing,
    or Redis is unavailable.
    """
    try:
        data = get_cache_service().get("plex:sessions:live")
        return data or []
    except Exception:
        return []
```

**Step 4: Run tests — expect PASS**

```bash
pytest tests/test_plex_api.py -k "sessions" -v -m unit
```

Expected: 3 tests passing.

**Step 5: Run full unit suite**

```bash
pytest -m unit -q
```

Expected: 48 passed, 0 failed.

**Step 6: Lint**

```bash
black app/api/v1/plex/router.py && isort app/api/v1/plex/router.py && flake8 app/api/v1/plex/router.py
```

Expected: Clean.

**Step 7: Commit**

```bash
git add app/api/v1/plex/router.py tests/test_plex_api.py
git commit -m "feat(plex): add GET /api/v1/plex/sessions endpoint"
```

---

### Task 4: Frontend service — getPlexSessions()

**Files:**
- Modify: `frontend/src/services/plexService.ts`
- Test: `frontend/src/services/__tests__/plexService.test.ts` (create if absent, else append)

**Context:** Follow the existing pattern in `plexService.ts` — use `apiClient.get<T>()` from `@/utils/api`. The `PlexSession` interface mirrors the snake_case fields the backend returns from `model_dump()`.

**Step 1: Write failing test**

Create `frontend/src/services/__tests__/plexService.test.ts` (or append if it exists):

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getPlexSessions } from '../plexService'

vi.mock('@/utils/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

import { apiClient } from '@/utils/api'

describe('getPlexSessions', () => {
  beforeEach(() => vi.clearAllMocks())

  it('returns session list from API', async () => {
    const sessions = [
      {
        rating_key: '42',
        title: 'Inception',
        type: 'movie',
        grandparent_title: null,
        parent_index: null,
        index: null,
        duration: 7200000,
        view_offset: 3600000,
        player: { title: 'Chrome', state: 'playing' },
        user: { title: 'john' },
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: sessions })

    const result = await getPlexSessions()
    expect(result).toEqual(sessions)
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/plex/sessions')
  })

  it('returns empty array when nothing is playing', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: [] })
    const result = await getPlexSessions()
    expect(result).toEqual([])
  })
})
```

**Step 2: Run test — expect FAIL**

```bash
cd frontend && npm run test -- --run plexService
```

Expected: `getPlexSessions is not a function` or export not found.

**Step 3: Add types and function to `frontend/src/services/plexService.ts`**

Append before the closing of the file:

```typescript
export interface PlexSessionPlayer {
  title: string
  state: 'playing' | 'paused' | 'buffering'
}

export interface PlexSessionUser {
  title: string
}

export interface PlexSession {
  rating_key: string
  title: string
  type: 'movie' | 'episode' | string
  grandparent_title: string | null
  parent_index: number | null
  index: number | null
  duration: number
  view_offset: number
  player: PlexSessionPlayer
  user: PlexSessionUser
}

export const getPlexSessions = async (): Promise<PlexSession[]> => {
  const response = await apiClient.get<PlexSession[]>('/api/v1/plex/sessions')
  return response.data
}
```

**Step 4: Run test — expect PASS**

```bash
cd frontend && npm run test -- --run plexService
```

Expected: 2 tests passing.

**Step 5: Run full frontend test suite**

```bash
cd frontend && npm run test -- --run
```

Expected: All existing tests still pass + 2 new.

**Step 6: TypeScript check**

```bash
cd frontend && npm run type-check
```

Expected: No errors.

**Step 7: Commit**

```bash
git add frontend/src/services/plexService.ts \
        frontend/src/services/__tests__/plexService.test.ts
git commit -m "feat(plex): add PlexSession types and getPlexSessions() service function"
```

---

### Task 5: NowPlayingPanel component + wire into SystemHealthPage

**Files:**
- Create: `frontend/src/components/features/plex/NowPlayingPanel.tsx`
- Modify: `frontend/src/pages/SystemHealthPage.tsx`
- Test: `frontend/src/components/features/plex/__tests__/NowPlayingPanel.test.tsx` (create)

**Context:** Uses TanStack Query (`useQuery`) — `QueryClientProvider` is already present in `main.tsx`. Poll every 15 s (`refetchInterval: 15_000`). For episodes, show `"Show · S1E2 · Episode Title"`. For movies, show title only. Progress bar uses `view_offset / duration * 100`. State dot: green = playing, amber = paused/buffering.

**Step 1: Write failing test**

Create `frontend/src/components/features/plex/__tests__/NowPlayingPanel.test.tsx`:

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { NowPlayingPanel } from '../NowPlayingPanel'

vi.mock('@/services/plexService', () => ({
  getPlexSessions: vi.fn(),
}))

import { getPlexSessions } from '@/services/plexService'

function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      {children}
    </QueryClientProvider>
  )
}

describe('NowPlayingPanel', () => {
  it('shows empty state when nothing is playing', async () => {
    vi.mocked(getPlexSessions).mockResolvedValue([])
    render(<NowPlayingPanel />, { wrapper })
    expect(await screen.findByText(/nothing playing/i)).toBeInTheDocument()
  })

  it('renders a movie session', async () => {
    vi.mocked(getPlexSessions).mockResolvedValue([
      {
        rating_key: '1',
        title: 'Inception',
        type: 'movie',
        grandparent_title: null,
        parent_index: null,
        index: null,
        duration: 7200000,
        view_offset: 3600000,
        player: { title: 'Chrome', state: 'playing' },
        user: { title: 'john' },
      },
    ])
    render(<NowPlayingPanel />, { wrapper })
    expect(await screen.findByText('Inception')).toBeInTheDocument()
    expect(screen.getByText('john')).toBeInTheDocument()
  })

  it('renders episode with show context', async () => {
    vi.mocked(getPlexSessions).mockResolvedValue([
      {
        rating_key: '2',
        title: 'Pilot',
        type: 'episode',
        grandparent_title: 'Breaking Bad',
        parent_index: 1,
        index: 1,
        duration: 3000000,
        view_offset: 1000000,
        player: { title: 'Apple TV', state: 'paused' },
        user: { title: 'jane' },
      },
    ])
    render(<NowPlayingPanel />, { wrapper })
    expect(await screen.findByText(/Breaking Bad/)).toBeInTheDocument()
    expect(screen.getByText(/S1E1/)).toBeInTheDocument()
  })
})
```

**Step 2: Run test — expect FAIL**

```bash
cd frontend && npm run test -- --run NowPlayingPanel
```

Expected: module not found — component doesn't exist yet.

**Step 3: Create `frontend/src/components/features/plex/NowPlayingPanel.tsx`**

```tsx
import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { getPlexSessions, type PlexSession } from '@/services/plexService'

function SessionCard({ session }: { session: PlexSession }) {
  const pct =
    session.duration > 0
      ? Math.round((session.view_offset / session.duration) * 100)
      : 0

  const label =
    session.type === 'episode' && session.grandparent_title
      ? `${session.grandparent_title} · S${session.parent_index}E${session.index} · ${session.title}`
      : session.title

  const isPlaying = session.player.state === 'playing'

  return (
    <div className="flex flex-col gap-2 p-3 bg-slate-100 dark:bg-slate-800 rounded-lg">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-medium text-slate-900 dark:text-white truncate">
          {label}
        </span>
        <span className="text-xs text-slate-500 dark:text-slate-400 flex-shrink-0">
          {session.user.title}
        </span>
      </div>

      <div className="flex items-center gap-2">
        <div className="flex-1 h-1.5 bg-slate-300 dark:bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-amber-400 rounded-full transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="text-xs text-slate-500 dark:text-slate-400 flex-shrink-0 w-8 text-right">
          {pct}%
        </span>
      </div>

      <div className="flex items-center gap-1.5">
        <span
          className={`w-2 h-2 rounded-full flex-shrink-0 ${
            isPlaying ? 'bg-emerald-400' : 'bg-amber-400'
          }`}
        />
        <span className="text-xs text-slate-500 dark:text-slate-400 capitalize">
          {session.player.state} · {session.player.title}
        </span>
      </div>
    </div>
  )
}

export function NowPlayingPanel() {
  const { data: sessions = [], isLoading } = useQuery({
    queryKey: ['plex-sessions'],
    queryFn: getPlexSessions,
    refetchInterval: 15_000,
  })

  if (isLoading) {
    return (
      <div className="space-y-2">
        <div className="h-4 w-28 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
        <div className="h-20 bg-slate-200 dark:bg-slate-700 rounded-lg animate-pulse" />
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
        Now Playing
      </h3>
      {sessions.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400 italic">
          Nothing playing right now.
        </p>
      ) : (
        <div className="space-y-2">
          {sessions.map((s) => (
            <SessionCard key={s.rating_key} session={s} />
          ))}
        </div>
      )}
    </div>
  )
}
```

**Step 4: Run test — expect PASS**

```bash
cd frontend && npm run test -- --run NowPlayingPanel
```

Expected: 3 tests passing.

**Step 5: Wire into SystemHealthPage**

In `frontend/src/pages/SystemHealthPage.tsx`, add the import after the existing Plex import:

```tsx
import { NowPlayingPanel } from '@/components/features/plex/NowPlayingPanel'
```

Then, in the JSX, add a `NowPlayingPanel` card **above** the existing `PlexHealthPanel` card:

```tsx
      <Card variant="elevated">
        <NowPlayingPanel />
      </Card>

      <Card variant="elevated">
        <PlexHealthPanel />
      </Card>
```

(Replace the single existing `<Card variant="elevated"><PlexHealthPanel /></Card>` block.)

**Step 6: Run full frontend suite + type-check**

```bash
cd frontend && npm run test -- --run && npm run type-check
```

Expected: All tests pass, no type errors.

**Step 7: Lint**

```bash
cd frontend && npm run lint
```

Expected: No errors.

**Step 8: Commit**

```bash
git add frontend/src/components/features/plex/NowPlayingPanel.tsx \
        frontend/src/components/features/plex/__tests__/NowPlayingPanel.test.tsx \
        frontend/src/pages/SystemHealthPage.tsx
git commit -m "feat(plex): add NowPlayingPanel with live session polling"
```
