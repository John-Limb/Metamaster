# Plex Integration — Phase 7: Frontend — Health Page Integration

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Surface Plex sync issues on the existing health status page: `not_found` items as a drilldown list with per-item re-sync trigger, and a library name mismatch alert banner.

**Architecture:** Adds a new `PlexHealthPanel` component. New API endpoint `GET /api/v1/plex/health` returns `not_found` counts and mismatch status. Wired into the existing health page alongside current health panels.

**Tech Stack:** React, TypeScript, TanStack Query, Vitest, FastAPI

**Prerequisite:** Phases 1–6 complete.

---

### Task 1: Backend health endpoint

**Files:**
- Modify: `app/api/v1/plex/router.py`
- Modify: `tests/test_plex_api.py`

**Step 1: Write failing test**

```python
# append to tests/test_plex_api.py

@patch("app.api.v1.plex.router.get_db")
@patch("app.api.v1.plex.router.get_current_user")
def test_plex_health_returns_not_found_count(mock_user, mock_db):
    mock_user.return_value = MagicMock(id=1)
    mock_session = MagicMock()

    not_found_records = [
        MagicMock(id=1, item_type="movie", item_id=10, last_error=None),
        MagicMock(id=2, item_type="movie", item_id=11, last_error=None),
    ]
    mock_session.query.return_value.filter.return_value.all.return_value = not_found_records
    mock_db.return_value = iter([mock_session])

    response = client.get("/api/v1/plex/health", headers=auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["not_found_count"] == 2
    assert len(data["not_found_items"]) == 2
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_plex_api.py -v -k "health"
```
Expected: 404

**Step 3: Add health endpoint**

```python
# append to app/api/v1/plex/router.py
from app.domain.plex.models import PlexSyncStatus


@router.get("/health")
def get_plex_health(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Return Plex sync health: not_found items and connection status."""
    not_found = (
        db.query(PlexSyncRecord)
        .filter(PlexSyncRecord.sync_status == PlexSyncStatus.NOT_FOUND)
        .all()
    )
    conn = db.query(PlexConnection).filter(PlexConnection.is_active.is_(True)).first()

    return {
        "connected": conn is not None,
        "not_found_count": len(not_found),
        "not_found_items": [
            {
                "id": r.id,
                "item_type": r.item_type,
                "item_id": r.item_id,
                "last_error": r.last_error,
            }
            for r in not_found
        ],
    }
```

**Step 4: Run test**

```bash
pytest tests/test_plex_api.py -v -k "health"
```
Expected: PASSED.

**Step 5: Add per-item re-sync endpoint**

```python
# append to app/api/v1/plex/router.py

@router.post("/sync/{sync_record_id}", status_code=202)
def resync_item(
    sync_record_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Re-queue a single not_found item for Plex match resolution."""
    record = db.query(PlexSyncRecord).filter(PlexSyncRecord.id == sync_record_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Sync record not found")

    record.sync_status = PlexSyncStatus.PENDING
    db.commit()
    task = lock_plex_match.delay(
        record.item_type, record.item_id, None, record.connection_id
    )
    return {"task_id": task.id, "message": "Re-sync queued"}
```

**Step 6: Commit**

```bash
git add app/api/v1/plex/router.py tests/test_plex_api.py
git commit -m "feat(plex): add Plex health and per-item resync endpoints"
```

---

### Task 2: Library mismatch alert

**Files:**
- Modify: `app/api/v1/plex/router.py`

Add mismatch detection to the health endpoint. When `PlexConnection` exists but library resolution fails, include `library_mismatch: true` and the available library names.

**Step 1: Update health endpoint**

Replace the `get_plex_health` function body with:

```python
    not_found = (
        db.query(PlexSyncRecord)
        .filter(PlexSyncRecord.sync_status == PlexSyncStatus.NOT_FOUND)
        .all()
    )
    conn = db.query(PlexConnection).filter(PlexConnection.is_active.is_(True)).first()

    library_mismatch = False
    available_libraries: list = []

    if conn:
        try:
            from app.infrastructure.external_apis.plex.client import PlexClient
            from app.domain.plex.service import PlexSyncService
            client = PlexClient(server_url=conn.server_url, token=conn.token)
            svc = PlexSyncService(
                db=db, client=client,
                movie_library_name=settings.plex_library_movies,
                tv_library_name=settings.plex_library_tv,
            )
            svc.resolve_library_ids()
        except ValueError as e:
            library_mismatch = True
            sections = client.get_library_sections()
            available_libraries = [s.title for s in sections]
            logger.warning("Plex health: library mismatch — %s", e)

    return {
        "connected": conn is not None,
        "library_mismatch": library_mismatch,
        "available_libraries": available_libraries,
        "not_found_count": len(not_found),
        "not_found_items": [
            {
                "id": r.id,
                "item_type": r.item_type,
                "item_id": r.item_id,
                "last_error": r.last_error,
            }
            for r in not_found
        ],
    }
```

**Step 2: Run full API tests**

```bash
pytest tests/test_plex_api.py -v
```
Expected: All PASSED.

**Step 3: Commit**

```bash
git add app/api/v1/plex/router.py
git commit -m "feat(plex): add library mismatch detection to health endpoint"
```

---

### Task 3: PlexHealthPanel frontend component

**Files:**
- Create: `frontend/src/components/features/plex/PlexHealthPanel.tsx`
- Create: `frontend/src/components/features/plex/__tests__/PlexHealthPanel.test.tsx`

**Step 1: Add health query to plexService**

```typescript
// append to frontend/src/services/plexService.ts
export interface PlexHealthResponse {
  connected: boolean
  library_mismatch: boolean
  available_libraries: string[]
  not_found_count: number
  not_found_items: Array<{
    id: number
    item_type: string
    item_id: number
    last_error: string | null
  }>
}

export async function getPlexHealth(): Promise<PlexHealthResponse> {
  const { data } = await axios.get<PlexHealthResponse>('/api/v1/plex/health')
  return data
}

export async function resyncPlexItem(syncRecordId: number): Promise<void> {
  await axios.post(`/api/v1/plex/sync/${syncRecordId}`)
}
```

**Step 2: Write failing tests**

```typescript
// frontend/src/components/features/plex/__tests__/PlexHealthPanel.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PlexHealthPanel } from '../PlexHealthPanel'
import * as plexService from '../../../../services/plexService'

vi.mock('../../../../services/plexService')

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
)

describe('PlexHealthPanel', () => {
  it('shows library mismatch alert when mismatch detected', async () => {
    vi.mocked(plexService.getPlexHealth).mockResolvedValue({
      connected: true,
      library_mismatch: true,
      available_libraries: ['Films', 'Series'],
      not_found_count: 0,
      not_found_items: [],
    })
    render(<PlexHealthPanel />, { wrapper })
    expect(await screen.findByRole('alert')).toHaveTextContent(/library.*mismatch/i)
    expect(screen.getByText('Films')).toBeInTheDocument()
  })

  it('shows not_found items with resync button', async () => {
    vi.mocked(plexService.getPlexHealth).mockResolvedValue({
      connected: true,
      library_mismatch: false,
      available_libraries: [],
      not_found_count: 1,
      not_found_items: [{ id: 5, item_type: 'movie', item_id: 42, last_error: null }],
    })
    vi.mocked(plexService.resyncPlexItem).mockResolvedValue(undefined)
    render(<PlexHealthPanel />, { wrapper })
    expect(await screen.findByText(/movie #42/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /re-sync/i })).toBeInTheDocument()
  })

  it('shows healthy state when no issues', async () => {
    vi.mocked(plexService.getPlexHealth).mockResolvedValue({
      connected: true,
      library_mismatch: false,
      available_libraries: [],
      not_found_count: 0,
      not_found_items: [],
    })
    render(<PlexHealthPanel />, { wrapper })
    expect(await screen.findByText(/all items matched/i)).toBeInTheDocument()
  })
})
```

**Step 3: Run to verify failure**

```bash
cd frontend && npm run test -- PlexHealthPanel --run
```
Expected: Cannot find module `../PlexHealthPanel`

**Step 4: Implement component**

```tsx
// frontend/src/components/features/plex/PlexHealthPanel.tsx
import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getPlexHealth, resyncPlexItem } from '../../../services/plexService'

export function PlexHealthPanel() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['plex-health'],
    queryFn: getPlexHealth,
  })

  const resync = useMutation({
    mutationFn: resyncPlexItem,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['plex-health'] }),
  })

  if (isLoading || !data) return <div>Loading Plex health...</div>

  return (
    <div>
      <h4>Plex Sync Status</h4>

      {data.library_mismatch && (
        <div role="alert">
          Library mismatch: configured library names not found in Plex.
          Available libraries: {data.available_libraries.join(', ')}
        </div>
      )}

      {data.not_found_count === 0 && !data.library_mismatch ? (
        <p>All items matched in Plex.</p>
      ) : (
        <div>
          <p>{data.not_found_count} item(s) not found in Plex</p>
          <ul>
            {data.not_found_items.map(item => (
              <li key={item.id}>
                {item.item_type} #{item.item_id}
                {item.last_error && <span> — {item.last_error}</span>}
                <button
                  onClick={() => resync.mutate(item.id)}
                  disabled={resync.isPending}
                >
                  Re-sync
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
```

**Step 5: Run tests**

```bash
cd frontend && npm run test -- PlexHealthPanel --run
```
Expected: All PASSED.

**Step 6: Wire into health page**

Find the health page:
```bash
grep -rl "health\|Health" frontend/src/pages/ | head -5
```

Import and add `<PlexHealthPanel />` alongside existing health panels.

**Step 7: Run full frontend test suite**

```bash
cd frontend && npm run test --run
```
Expected: No regressions.

**Step 8: Type check and lint**

```bash
cd frontend && npm run type-check && npm run lint
```

**Step 9: Commit**

```bash
git add frontend/src/components/features/plex/PlexHealthPanel.tsx \
        frontend/src/components/features/plex/__tests__/PlexHealthPanel.test.tsx \
        frontend/src/services/plexService.ts
git commit -m "feat(plex): add Plex health panel with mismatch alert and not_found list"
```
