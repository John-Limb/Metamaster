# Collection Page Sync Improvements Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add "Push All to Plex", delete-with-Plex-removal, and Movies/TV page split to the Plex collections feature.

**Architecture:** Three independent features share the same backend router and frontend page. Backend changes are data-first (migration → ORM → service → router → schema); frontend changes build on the updated TypeScript types. The features can be implemented task-by-task in order — each task's changes are self-contained and testable.

**Tech Stack:** Python/FastAPI, SQLAlchemy, Alembic, Celery, React/TypeScript, Zustand, Vitest

---

## Chunk 1: Backend

### Task 1: DB migration + ORM for `content_type`

**Files:**
- Create: `alembic/versions/016_plex_collection_content_type.py`
- Modify: `app/domain/plex/collection_models.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_plex_collection_models.py`:

```python
@pytest.mark.unit
def test_plex_collection_has_content_type_column():
    """PlexCollection must have a nullable content_type column."""
    from app.domain.plex.collection_models import PlexCollection
    col = PlexCollection.__table__.c.get("content_type")
    assert col is not None, "content_type column missing from PlexCollection"
    assert col.nullable is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/john/Code/Metamaster/.worktrees/feat/collection-sync
pytest tests/test_plex_collection_models.py::test_plex_collection_has_content_type_column -v
```

Expected: FAIL — `AssertionError: content_type column missing from PlexCollection`

- [ ] **Step 3: Add the Alembic migration**

Create `alembic/versions/016_plex_collection_content_type.py`:

```python
"""Add content_type to plex_collections

Revision ID: 016
Revises: 015
Create Date: 2026-03-16
"""

import sqlalchemy as sa

from alembic import op

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "plex_collections",
        sa.Column("content_type", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("plex_collections", "content_type")
```

- [ ] **Step 4: Add the ORM column**

In `app/domain/plex/collection_models.py`, add after `is_default`:

```python
content_type = Column(String(20), nullable=True)  # "movie" | "tv_show" | None
```

The import for `String` is already present at line 8.

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_plex_collection_models.py::test_plex_collection_has_content_type_column -v
```

Expected: PASS

- [ ] **Step 6: Run full model tests**

```bash
pytest tests/test_plex_collection_models.py -v
```

Expected: all pass

- [ ] **Step 7: Stage**

```bash
git add alembic/versions/016_plex_collection_content_type.py app/domain/plex/collection_models.py tests/test_plex_collection_models.py
```

---

### Task 2: Tag `content_type` during pull and create

**Files:**
- Modify: `app/domain/plex/collection_service.py`
- Modify: `app/api/v1/plex/collection_router.py` (create endpoint only)
- Modify: `tests/test_plex_collection_service.py`

**Context:** `PlexCollectionService._upsert_pulled_collection(raw, connection_id, section_id)` already receives `section_id`. `self._movie_section` and `self._tv_section` are set in `__init__`. The collection create endpoint lives at `POST /plex/collections` (router line 169).

- [ ] **Step 1: Write failing tests**

Add to `tests/test_plex_collection_service.py`:

```python
@pytest.mark.unit
def test_upsert_pulled_collection_tags_movie(db_session, mock_collection_client):
    """_upsert_pulled_collection sets content_type='movie' for movie section."""
    from app.domain.plex.collection_service import PlexCollectionService
    from app.domain.plex.collection_models import PlexCollection
    from app.domain.plex.collection_builder import BuilderResolver

    resolver = MagicMock(spec=BuilderResolver)
    mock_collection_client.get_collection_item_keys.return_value = []
    svc = PlexCollectionService(
        db=db_session,
        collection_client=mock_collection_client,
        resolver=resolver,
        movie_section_id="1",
        tv_section_id="2",
    )
    raw = {"ratingKey": "key-movie", "title": "Action Hits", "summary": ""}
    svc._upsert_pulled_collection(raw, connection_id=1, section_id="1")
    db_session.flush()
    coll = db_session.query(PlexCollection).filter_by(plex_rating_key="key-movie").first()
    assert coll is not None
    assert coll.content_type == "movie"


@pytest.mark.unit
def test_upsert_pulled_collection_tags_tv(db_session, mock_collection_client):
    """_upsert_pulled_collection sets content_type='tv_show' for tv section."""
    from app.domain.plex.collection_service import PlexCollectionService
    from app.domain.plex.collection_models import PlexCollection
    from app.domain.plex.collection_builder import BuilderResolver

    resolver = MagicMock(spec=BuilderResolver)
    mock_collection_client.get_collection_item_keys.return_value = []
    svc = PlexCollectionService(
        db=db_session,
        collection_client=mock_collection_client,
        resolver=resolver,
        movie_section_id="1",
        tv_section_id="2",
    )
    raw = {"ratingKey": "key-tv", "title": "Crime Dramas", "summary": ""}
    svc._upsert_pulled_collection(raw, connection_id=1, section_id="2")
    db_session.flush()
    coll = db_session.query(PlexCollection).filter_by(plex_rating_key="key-tv").first()
    assert coll is not None
    assert coll.content_type == "tv_show"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_plex_collection_service.py::test_upsert_pulled_collection_tags_movie tests/test_plex_collection_service.py::test_upsert_pulled_collection_tags_tv -v
```

Expected: FAIL — `AssertionError: assert None == 'movie'`

- [ ] **Step 3: Update `_upsert_pulled_collection` in `collection_service.py`**

At the end of the existing code that sets `existing.name`, `existing.description`, `existing.last_synced_at` (lines 125–127), add content_type assignment:

```python
if section_id == self._movie_section:
    existing.content_type = "movie"
elif section_id == self._tv_section:
    existing.content_type = "tv_show"
```

- [ ] **Step 4: Update `create_collection` endpoint in `collection_router.py`**

In the `PlexCollection(...)` constructor call (lines 177–186), add `content_type="movie"` as a keyword argument:

```python
coll = PlexCollection(
    connection_id=conn.id,
    name=payload.name,
    description=payload.description,
    sort_title=payload.sort_title,
    builder_type=payload.builder_type,
    builder_config=payload.builder_config,
    enabled=False,
    is_default=False,
    content_type="movie",
)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_plex_collection_service.py::test_upsert_pulled_collection_tags_movie tests/test_plex_collection_service.py::test_upsert_pulled_collection_tags_tv -v
```

Expected: PASS

- [ ] **Step 6: Run full service tests**

```bash
pytest tests/test_plex_collection_service.py -v
```

Expected: all pass

- [ ] **Step 7: Stage**

```bash
git add app/domain/plex/collection_service.py app/api/v1/plex/collection_router.py tests/test_plex_collection_service.py
```

---

### Task 3: Add `content_type` to `CollectionResponse` schema

**Files:**
- Modify: `app/api/v1/plex/collection_schemas.py`
- Modify: `tests/test_plex_collection_schemas.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_plex_collection_schemas.py`:

```python
@pytest.mark.unit
def test_collection_response_includes_content_type():
    """CollectionResponse must expose content_type."""
    from app.api.v1.plex.collection_schemas import CollectionResponse
    fields = CollectionResponse.model_fields
    assert "content_type" in fields, "content_type missing from CollectionResponse"
    # field must be Optional[str]
    import typing
    annotation = fields["content_type"].annotation
    args = typing.get_args(annotation)
    assert type(None) in args, "content_type must be Optional (allow None)"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_plex_collection_schemas.py::test_collection_response_includes_content_type -v
```

Expected: FAIL — `AssertionError: content_type missing from CollectionResponse`

- [ ] **Step 3: Add the field to `CollectionResponse`**

In `app/api/v1/plex/collection_schemas.py`, add to `CollectionResponse` after `is_default`:

```python
content_type: Optional[str] = None
```

The `Optional` import is already present at line 4.

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_plex_collection_schemas.py -v
```

Expected: all pass

- [ ] **Step 5: Stage**

```bash
git add app/api/v1/plex/collection_schemas.py tests/test_plex_collection_schemas.py
```

---

### Task 4: `POST /plex/collections/push-all` endpoint (202)

**Files:**
- Modify: `app/api/v1/plex/collection_router.py`
- Modify: `tests/test_plex_collection_router.py`

**Context:** `push_all_collections` Celery task is in `app/tasks/plex_collections.py`. Import it at the top of the router module alongside the other task imports. The router has helpers `_get_active_connection(db)`. The endpoint must return 202 with `{"status": "queued"}`.

**Important:** In the router file, the static paths `/collections/pull` (line 193) and `/collections/export` (line 206) appear **before** the parameterised `GET /collections/{collection_id}` route (line 228). Insert `push-all` after `/collections/export` and before that parameterised route to avoid FastAPI routing the literal `push-all` into the `collection_id` path parameter.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_plex_collection_router.py`:

```python
@pytest.mark.unit
def test_push_all_collections_queues_task():
    """POST /plex/collections/push-all returns 202 and queues Celery task with connection id."""
    _clear_db()
    conn_id = _seed_connection()
    with patch(
        "app.api.v1.plex.collection_router.push_all_collections"
    ) as mock_task:
        resp = client.post("/api/v1/plex/collections/push-all")
    assert resp.status_code == 202
    assert resp.json() == {"status": "queued"}
    mock_task.delay.assert_called_once_with(conn_id)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_plex_collection_router.py::test_push_all_collections_queues_task -v
```

Expected: FAIL — 404 or 422

- [ ] **Step 3: Add the import and endpoint to the router**

At the top of `collection_router.py`, add the import after existing task imports (search for the existing `from app.tasks` lines):

```python
from app.tasks.plex_collections import push_all_collections
```

Then add the endpoint after the `/collections/export` endpoint (around line 225, before the `@router.get("/collections/{collection_id}")` route):

```python
@router.post("/collections/push-all", status_code=202)
def push_all_collections_endpoint(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Queue a Celery task to push all enabled collections to Plex."""
    conn = _get_active_connection(db)
    push_all_collections.delay(conn.id)
    return {"status": "queued"}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_plex_collection_router.py::test_push_all_collections_queues_task -v
```

Expected: PASS

- [ ] **Step 5: Run full router tests**

```bash
pytest tests/test_plex_collection_router.py -v
```

Expected: all pass

- [ ] **Step 6: Stage**

```bash
git add app/api/v1/plex/collection_router.py tests/test_plex_collection_router.py
```

---

### Task 5: `DELETE /plex/collections/{id}?delete_from_plex=true`

**Files:**
- Modify: `app/api/v1/plex/collection_router.py`
- Modify: `tests/test_plex_collection_router.py`

**Context:** `PlexCollectionClient.delete_collection(collection_key)` already exists at `app/infrastructure/external_apis/plex/collection_client.py`. The existing DELETE handler is at lines 259–270. Build a `PlexCollectionClient` using `_make_clients(conn)` — same as other endpoints. If the Plex call fails, log and continue (still delete from DB).

- [ ] **Step 1: Write failing tests**

Add to `tests/test_plex_collection_router.py`:

```python
@pytest.mark.unit
def test_delete_collection_without_plex_flag():
    """DELETE /plex/collections/{id} without flag just deletes from DB (no Plex call)."""
    _clear_db()
    conn_id = _seed_connection()
    # Create a collection
    payload = {
        "name": "To Delete",
        "builder_type": "static_items",
        "builder_config": {"items": []},
    }
    create_resp = client.post("/api/v1/plex/collections", json=payload)
    coll_id = create_resp.json()["id"]

    with patch("app.api.v1.plex.collection_router._make_clients") as mock_clients:
        resp = client.delete(f"/api/v1/plex/collections/{coll_id}")

    assert resp.status_code == 204
    mock_clients.assert_not_called()


@pytest.mark.unit
def test_delete_collection_with_plex_flag_calls_client():
    """DELETE with ?delete_from_plex=true calls PlexCollectionClient.delete_collection."""
    _clear_db()
    _seed_connection()
    payload = {
        "name": "Plex Delete Test",
        "builder_type": "static_items",
        "builder_config": {"items": []},
    }
    create_resp = client.post("/api/v1/plex/collections", json=payload)
    coll_id = create_resp.json()["id"]

    # Manually set plex_rating_key so the branch is exercised
    db = _SessionLocal()
    from app.domain.plex.collection_models import PlexCollection
    coll = db.query(PlexCollection).filter_by(id=coll_id).first()
    coll.plex_rating_key = "plex-key-999"
    db.commit()
    db.close()

    mock_cc = MagicMock()
    with patch(
        "app.api.v1.plex.collection_router._make_clients",
        return_value=(MagicMock(), mock_cc, MagicMock()),
    ):
        resp = client.delete(f"/api/v1/plex/collections/{coll_id}?delete_from_plex=true")

    assert resp.status_code == 204
    mock_cc.delete_collection.assert_called_once_with("plex-key-999")
```

Add a third test covering the Plex-API-failure-and-continue path:

```python
@pytest.mark.unit
def test_delete_collection_plex_failure_still_deletes_db_row():
    """If Plex delete_collection raises, endpoint still returns 204 and removes DB row."""
    _clear_db()
    _seed_connection()
    payload = {
        "name": "Plex Fail Test",
        "builder_type": "static_items",
        "builder_config": {"items": []},
    }
    create_resp = client.post("/api/v1/plex/collections", json=payload)
    coll_id = create_resp.json()["id"]

    db = _SessionLocal()
    from app.domain.plex.collection_models import PlexCollection
    coll = db.query(PlexCollection).filter_by(id=coll_id).first()
    coll.plex_rating_key = "plex-key-fail"
    db.commit()
    db.close()

    mock_cc = MagicMock()
    mock_cc.delete_collection.side_effect = Exception("Plex unavailable")
    with patch(
        "app.api.v1.plex.collection_router._make_clients",
        return_value=(MagicMock(), mock_cc, MagicMock()),
    ):
        resp = client.delete(f"/api/v1/plex/collections/{coll_id}?delete_from_plex=true")

    assert resp.status_code == 204
    # Row must be gone from the DB
    db = _SessionLocal()
    assert db.query(PlexCollection).filter_by(id=coll_id).first() is None
    db.close()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_plex_collection_router.py::test_delete_collection_without_plex_flag tests/test_plex_collection_router.py::test_delete_collection_with_plex_flag_calls_client tests/test_plex_collection_router.py::test_delete_collection_plex_failure_still_deletes_db_row -v
```

Expected: FAIL

- [ ] **Step 3: Update the DELETE endpoint**

Replace the existing `delete_collection` function (lines 259–270) with:

```python
@router.delete("/collections/{collection_id}", status_code=204)
def delete_collection(
    collection_id: int,
    delete_from_plex: bool = Query(default=False),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Delete a PlexCollection from the DB, optionally also removing it from Plex."""
    coll = db.query(PlexCollection).filter(PlexCollection.id == collection_id).first()
    if coll is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    if delete_from_plex and coll.plex_rating_key:
        conn = _get_active_connection(db)
        _, cc, _ = _make_clients(conn)
        try:
            cc.delete_collection(coll.plex_rating_key)
        except Exception:
            logger.warning(
                "Failed to delete collection %s from Plex; continuing with DB delete",
                coll.plex_rating_key,
            )
    db.delete(coll)
    db.commit()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_plex_collection_router.py::test_delete_collection_without_plex_flag tests/test_plex_collection_router.py::test_delete_collection_with_plex_flag_calls_client tests/test_plex_collection_router.py::test_delete_collection_plex_failure_still_deletes_db_row -v
```

Expected: PASS

- [ ] **Step 5: Run full router tests**

```bash
pytest tests/test_plex_collection_router.py -v
```

Expected: all pass

- [ ] **Step 6: Run backend lint**

```bash
cd /Users/john/Code/Metamaster/.worktrees/feat/collection-sync
black app/ tests/ && isort app/ tests/ && flake8 app/ tests/ && mypy app/
```

Expected: no errors

- [ ] **Step 7: Run all backend tests**

```bash
pytest
```

Expected: all pass

- [ ] **Step 8: Stage**

```bash
git add app/api/v1/plex/collection_router.py tests/test_plex_collection_router.py
```

---

## Chunk 2: Frontend

### Task 6: TypeScript type update — `content_type` on `PlexCollection`

**Files:**
- Modify: `frontend/src/services/plexCollectionService.ts`

- [ ] **Step 1: Write the failing test**

Add to `frontend/src/services/__tests__/plexCollectionService.test.ts` (create file if it does not exist):

```typescript
import { describe, it, expect } from 'vitest'

describe('PlexCollection interface', () => {
  it('includes content_type field', () => {
    // Compile-time check — if TypeScript is happy, runtime is fine too
    const col: import('../plexCollectionService').PlexCollection = {
      id: 1,
      connection_id: 1,
      name: 'Test',
      description: null,
      sort_title: null,
      builder_type: 'static_items',
      builder_config: {},
      plex_rating_key: null,
      last_synced_at: null,
      enabled: false,
      is_default: false,
      items: [],
      content_type: null,
    }
    expect(col.content_type).toBeNull()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/john/Code/Metamaster/.worktrees/feat/collection-sync/frontend
npm run type-check 2>&1 | grep content_type
```

Expected: TypeScript error — `Object literal may only specify known properties`

- [ ] **Step 3: Add `content_type` to `PlexCollection` interface**

In `frontend/src/services/plexCollectionService.ts`, inside the `PlexCollection` interface (after `is_default`), add:

```typescript
content_type: string | null
```

- [ ] **Step 4: Run type-check and tests**

```bash
npm run type-check
npm run test -- --run
```

Expected: no type errors, all tests pass

- [ ] **Step 5: Stage**

```bash
git add frontend/src/services/plexCollectionService.ts frontend/src/services/__tests__/plexCollectionService.test.ts
```

---

### Task 7: Service functions — `pushAllCollections` + `deleteCollection` with flag

**Files:**
- Modify: `frontend/src/services/plexCollectionService.ts`

- [ ] **Step 1: Write the failing tests**

Add to `frontend/src/services/__tests__/plexCollectionService.test.ts`:

```typescript
import { vi } from 'vitest'
import * as api from '@/utils/api'

describe('pushAllCollections', () => {
  it('POSTs to /plex/collections/push-all', async () => {
    const spy = vi.spyOn(api.apiClient, 'post').mockResolvedValue({ data: { status: 'queued' } })
    const { pushAllCollections } = await import('../plexCollectionService')
    await pushAllCollections()
    expect(spy).toHaveBeenCalledWith('/plex/collections/push-all')
    spy.mockRestore()
  })
})

describe('deleteCollection', () => {
  it('DELETEs without query param by default', async () => {
    const spy = vi.spyOn(api.apiClient, 'delete').mockResolvedValue({ data: undefined })
    const { deleteCollection } = await import('../plexCollectionService')
    await deleteCollection(42)
    expect(spy).toHaveBeenCalledWith('/plex/collections/42')
    spy.mockRestore()
  })

  it('appends ?delete_from_plex=true when flag is set', async () => {
    const spy = vi.spyOn(api.apiClient, 'delete').mockResolvedValue({ data: undefined })
    const { deleteCollection } = await import('../plexCollectionService')
    await deleteCollection(42, true)
    expect(spy).toHaveBeenCalledWith('/plex/collections/42?delete_from_plex=true')
    spy.mockRestore()
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
npm run test -- --run frontend/src/services/__tests__/plexCollectionService.test.ts
```

Expected: FAIL — `pushAllCollections is not a function`

- [ ] **Step 3: Add `pushAllCollections` and update `deleteCollection`**

In `plexCollectionService.ts`, replace the existing `deleteCollection` function:

```typescript
export async function deleteCollection(id: number, deleteFromPlex = false): Promise<void> {
  const url = deleteFromPlex
    ? `/plex/collections/${id}?delete_from_plex=true`
    : `/plex/collections/${id}`
  await apiClient.delete(url)
}
```

Add `pushAllCollections` after `pullCollections`:

```typescript
export async function pushAllCollections(): Promise<void> {
  await apiClient.post('/plex/collections/push-all')
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
npm run test -- --run frontend/src/services/__tests__/plexCollectionService.test.ts
```

Expected: PASS

- [ ] **Step 5: Stage**

```bash
git add frontend/src/services/plexCollectionService.ts frontend/src/services/__tests__/plexCollectionService.test.ts
```

---

### Task 8: Store — `pushAllCollections` action + `deleteCollection` signature

**Files:**
- Modify: `frontend/src/stores/plexCollectionStore.ts`

**Context:** The current `deleteCollection: (id: number) => Promise<void>` interface (line 46) and implementation must accept an optional `deleteFromPlex?: boolean`. A new `pushAllCollections` action and `pushAllLoading: boolean` + `pushAllError: string | null` state fields need to be added.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/stores/__tests__/plexCollectionStore.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../services/plexCollectionService', () => ({
  getCollections: vi.fn().mockResolvedValue([]),
  getPlaylists: vi.fn().mockResolvedValue([]),
  getCollectionSets: vi.fn().mockResolvedValue([]),
  pushAllCollections: vi.fn().mockResolvedValue(undefined),
  deleteCollection: vi.fn().mockResolvedValue(undefined),
  createCollection: vi.fn(),
  updateCollection: vi.fn(),
  pushCollection: vi.fn(),
  pullCollections: vi.fn(),
  createPlaylist: vi.fn(),
  updatePlaylist: vi.fn(),
  deletePlaylist: vi.fn(),
  pushPlaylist: vi.fn(),
  pullPlaylists: vi.fn(),
  bulkDeletePlaylists: vi.fn(),
  updateCollectionSet: vi.fn(),
  triggerDiscovery: vi.fn(),
}))

describe('plexCollectionStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('has pushAllCollections action', () => {
    const { usePlexCollectionStore } = require('../../stores/plexCollectionStore')
    const state = usePlexCollectionStore.getState()
    expect(typeof state.pushAllCollections).toBe('function')
  })

  it('deleteCollection accepts deleteFromPlex flag', async () => {
    const svc = await import('../../services/plexCollectionService')
    const { usePlexCollectionStore } = require('../../stores/plexCollectionStore')
    const { deleteCollection } = usePlexCollectionStore.getState()
    await deleteCollection(99, true)
    expect(svc.deleteCollection).toHaveBeenCalledWith(99, true)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npm run test -- --run frontend/src/stores/__tests__/plexCollectionStore.test.ts
```

Expected: FAIL — `state.pushAllCollections is not a function`

- [ ] **Step 3: Update the store**

In `frontend/src/stores/plexCollectionStore.ts`:

1. Add import at the top:
```typescript
import {
  // ... existing imports ...
  pushAllCollections as svcPushAllCollections,
} from '../services/plexCollectionService'
```

2. In the `PlexCollectionState` interface, change `deleteCollection` signature and add new fields:
```typescript
deleteCollection: (id: number, deleteFromPlex?: boolean) => Promise<void>
pushAllCollections: () => Promise<void>
pushAllLoading: boolean
pushAllError: string | null
```

3. Add initial state values in the `create(...)` call:
```typescript
pushAllLoading: false,
pushAllError: null,
```

4. Update `deleteCollection` implementation:
```typescript
deleteCollection: async (id, deleteFromPlex = false) => {
  await svcDeleteCollection(id, deleteFromPlex)
  set(state => ({
    collections: state.collections.filter(c => c.id !== id),
  }))
},
```

5. Add `pushAllCollections` implementation after `pullCollections`:
```typescript
pushAllCollections: async () => {
  set({ pushAllLoading: true, pushAllError: null })
  try {
    await svcPushAllCollections()
  } catch {
    set({ pushAllError: 'Failed to queue push. Please try again.' })
  } finally {
    set({ pushAllLoading: false })
  }
},
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npm run test -- --run frontend/src/stores/__tests__/plexCollectionStore.test.ts
```

Expected: PASS

- [ ] **Step 5: Run all frontend tests**

```bash
npm run test -- --run
```

Expected: all pass

- [ ] **Step 6: Stage**

```bash
git add frontend/src/stores/plexCollectionStore.ts frontend/src/stores/__tests__/plexCollectionStore.test.ts
```

---

### Task 9: `CollectionCard` — delete confirmation modal

**Files:**
- Modify: `frontend/src/components/features/plex/CollectionCard.tsx`
- Create: `frontend/src/components/features/plex/__tests__/CollectionCard.test.tsx`

**Context:** `CollectionCard` currently calls `onDelete(collection.id)` directly on click (line 83). The `onDelete` prop must change signature from `(id: number) => void` to `(id: number, deleteFromPlex: boolean) => void`. The modal needs: message "Delete **{name}**?", optional "Also delete from Plex" checkbox (only shown when `plex_rating_key` is set, checked by default when shown), "Cancel" and "Delete" buttons.

- [ ] **Step 1: Write failing tests**

Create `frontend/src/components/features/plex/__tests__/CollectionCard.test.tsx`:

```typescript
import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { CollectionCard } from '../CollectionCard'
import type { PlexCollection } from '../../../../services/plexCollectionService'

const baseCollection: PlexCollection = {
  id: 1,
  connection_id: 1,
  name: 'My Collection',
  description: null,
  sort_title: null,
  builder_type: 'static_items',
  builder_config: {},
  plex_rating_key: null,
  last_synced_at: null,
  enabled: true,
  is_default: false,
  items: [],
  content_type: 'movie',
}

describe('CollectionCard delete modal', () => {
  it('shows confirmation modal when Delete clicked', () => {
    const onDelete = vi.fn()
    render(
      <CollectionCard
        collection={baseCollection}
        onToggleEnabled={vi.fn()}
        onPush={vi.fn()}
        onDelete={onDelete}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    expect(screen.getByText(/delete my collection/i)).toBeInTheDocument()
    expect(onDelete).not.toHaveBeenCalled()
  })

  it('does not show Plex checkbox when plex_rating_key is null', () => {
    render(
      <CollectionCard
        collection={baseCollection}
        onToggleEnabled={vi.fn()}
        onPush={vi.fn()}
        onDelete={vi.fn()}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    expect(screen.queryByRole('checkbox', { name: /delete from plex/i })).not.toBeInTheDocument()
  })

  it('shows checked Plex checkbox when plex_rating_key is set', () => {
    const col = { ...baseCollection, plex_rating_key: 'plex-123' }
    render(
      <CollectionCard
        collection={col}
        onToggleEnabled={vi.fn()}
        onPush={vi.fn()}
        onDelete={vi.fn()}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    const checkbox = screen.getByRole('checkbox', { name: /delete from plex/i }) as HTMLInputElement
    expect(checkbox.checked).toBe(true)
  })

  it('calls onDelete with deleteFromPlex=false when no Plex key', () => {
    const onDelete = vi.fn()
    render(
      <CollectionCard
        collection={baseCollection}
        onToggleEnabled={vi.fn()}
        onPush={vi.fn()}
        onDelete={onDelete}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    fireEvent.click(screen.getByRole('button', { name: /^delete$/i }))
    expect(onDelete).toHaveBeenCalledWith(1, false)
  })

  it('calls onDelete with deleteFromPlex=true when Plex key set and checkbox checked', () => {
    const col = { ...baseCollection, plex_rating_key: 'plex-123' }
    const onDelete = vi.fn()
    render(
      <CollectionCard
        collection={col}
        onToggleEnabled={vi.fn()}
        onPush={vi.fn()}
        onDelete={onDelete}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    fireEvent.click(screen.getByRole('button', { name: /^delete$/i }))
    expect(onDelete).toHaveBeenCalledWith(1, true)
  })

  it('Cancel closes the modal without calling onDelete', () => {
    const onDelete = vi.fn()
    render(
      <CollectionCard
        collection={baseCollection}
        onToggleEnabled={vi.fn()}
        onPush={vi.fn()}
        onDelete={onDelete}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
    expect(onDelete).not.toHaveBeenCalled()
    expect(screen.queryByText(/delete my collection/i)).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
npm run test -- --run frontend/src/components/features/plex/__tests__/CollectionCard.test.tsx
```

Expected: FAIL — modal does not exist yet

- [ ] **Step 3: Rewrite `CollectionCard.tsx`**

Replace the contents of `frontend/src/components/features/plex/CollectionCard.tsx`:

```typescript
import React, { useState } from 'react'
import { FaChevronDown, FaChevronUp } from 'react-icons/fa'
import type { PlexCollection } from '../../../services/plexCollectionService'
import { Checkbox } from '@/components/common/Checkbox'

interface CollectionCardProps {
  collection: PlexCollection
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number, deleteFromPlex: boolean) => void
}

const BUILDER_LABELS: Record<string, string> = {
  tmdb_collection: 'TMDB Collection',
  static_items: 'Static',
  genre: 'Genre',
  decade: 'Decade',
}

function formatSyncDate(dateStr: string | null): string {
  if (!dateStr) return 'Never synced'
  return new Date(dateStr).toLocaleString()
}

export function CollectionCard({ collection, onToggleEnabled, onPush, onDelete }: CollectionCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [deleteFromPlex, setDeleteFromPlex] = useState(!!collection.plex_rating_key)
  const builderLabel = BUILDER_LABELS[collection.builder_type] ?? collection.builder_type
  const hasItems = collection.items.length > 0

  const handleDeleteClick = () => {
    setDeleteFromPlex(!!collection.plex_rating_key)
    setShowConfirm(true)
  }

  const handleConfirmDelete = () => {
    setShowConfirm(false)
    onDelete(collection.id, deleteFromPlex)
  }

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="font-semibold text-slate-900 dark:text-white truncate">{collection.name}</h3>
          {collection.description && (
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5 truncate">{collection.description}</p>
          )}
        </div>
        <span className="shrink-0 inline-flex px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400">
          {builderLabel}
        </span>
      </div>

      <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
        <button
          onClick={() => hasItems && setExpanded(v => !v)}
          disabled={!hasItems}
          className="flex items-center gap-1 hover:text-slate-700 dark:hover:text-slate-200 disabled:cursor-default transition-colors"
        >
          <span>{collection.items.length} item{collection.items.length !== 1 ? 's' : ''}</span>
          {hasItems && (expanded ? <FaChevronUp className="w-3 h-3" /> : <FaChevronDown className="w-3 h-3" />)}
        </button>
        <span>{formatSyncDate(collection.last_synced_at)}</span>
      </div>

      {expanded && (
        <ul className="max-h-48 overflow-y-auto rounded-lg border border-slate-100 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700 text-xs">
          {collection.items.map(item => (
            <li key={item.id} className="flex items-center justify-between px-3 py-1.5 gap-2">
              <span className="font-mono text-slate-600 dark:text-slate-400 truncate">{item.plex_rating_key}</span>
              <span className="shrink-0 text-slate-400 dark:text-slate-500 capitalize">{item.item_type}</span>
            </li>
          ))}
        </ul>
      )}

      <div className="flex items-center justify-between gap-2 pt-1">
        <Checkbox
          label="Enabled"
          checked={collection.enabled}
          onChange={checked => onToggleEnabled(collection.id, checked)}
        />

        <div className="flex items-center gap-2">
          <button
            onClick={() => onPush(collection.id)}
            disabled={!collection.enabled}
            className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors"
          >
            Push to Plex
          </button>
          <button
            onClick={handleDeleteClick}
            className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
          >
            Delete
          </button>
        </div>
      </div>

      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-xl p-6 w-full max-w-sm mx-4 space-y-4">
            <p className="text-sm font-medium text-slate-900 dark:text-white">
              Delete <strong>{collection.name}</strong>?
            </p>
            {collection.plex_rating_key && (
              <Checkbox
                label="Also delete from Plex"
                checked={deleteFromPlex}
                onChange={setDeleteFromPlex}
              />
            )}
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowConfirm(false)}
                className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium bg-red-600 hover:bg-red-700 text-white transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CollectionCard
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
npm run test -- --run frontend/src/components/features/plex/__tests__/CollectionCard.test.tsx
```

Expected: PASS

- [ ] **Step 5: Stage**

```bash
git add frontend/src/components/features/plex/CollectionCard.tsx frontend/src/components/features/plex/__tests__/CollectionCard.test.tsx
```

---

### Task 10: `PlexCollectionsPage` — Push All button + Movies/TV split

**Files:**
- Modify: `frontend/src/pages/PlexCollectionsPage.tsx`
- Create: `frontend/src/pages/__tests__/PlexCollectionsPage.test.tsx`

**Context:** The page already uses `usePlexCollectionStore`. `deleteCollection` from the store now has signature `(id: number, deleteFromPlex?: boolean) => Promise<void>`. `CollectionCard.onDelete` now has `(id: number, deleteFromPlex: boolean) => void`. The page's `deleteCollection` handler must forward both args. The collections grid becomes two sections: Movies (`content_type === 'movie' || content_type === null`) and TV Shows (`content_type === 'tv_show'`). TV section only renders when non-empty.

- [ ] **Step 1: Write failing tests**

Create `frontend/src/pages/__tests__/PlexCollectionsPage.test.tsx`:

```typescript
import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockStore = {
  collections: [],
  collectionsLoading: false,
  collectionsError: null,
  playlists: [],
  playlistsLoading: false,
  playlistsError: null,
  collectionSets: [],
  setsLoading: false,
  fetchCollections: vi.fn(),
  fetchPlaylists: vi.fn(),
  fetchCollectionSets: vi.fn(),
  createCollection: vi.fn(),
  updateCollection: vi.fn(),
  deleteCollection: vi.fn(),
  pushCollection: vi.fn(),
  pullCollections: vi.fn(),
  pushAllCollections: vi.fn(),
  pushAllLoading: false,
  pushAllError: null,
  updatePlaylist: vi.fn(),
  deletePlaylist: vi.fn(),
  pushPlaylist: vi.fn(),
  pullPlaylists: vi.fn(),
  bulkDeletePlaylists: vi.fn(),
  toggleCollectionSet: vi.fn(),
  triggerDiscovery: vi.fn().mockResolvedValue({ message: 'ok' }),
}

vi.mock('../../stores/plexCollectionStore', () => ({
  usePlexCollectionStore: () => mockStore,
}))

vi.mock('../../components/features/plex/CollectionSetToggles', () => ({
  CollectionSetToggles: () => <div data-testid="set-toggles" />,
}))

import { PlexCollectionsPage } from '../PlexCollectionsPage'

const movieCol = {
  id: 1, connection_id: 1, name: 'Action Pack', description: null, sort_title: null,
  builder_type: 'static_items' as const, builder_config: {}, plex_rating_key: null,
  last_synced_at: null, enabled: true, is_default: false, items: [], content_type: 'movie',
}
const tvCol = {
  id: 2, connection_id: 1, name: 'Crime Dramas', description: null, sort_title: null,
  builder_type: 'static_items' as const, builder_config: {}, plex_rating_key: null,
  last_synced_at: null, enabled: true, is_default: false, items: [], content_type: 'tv_show',
}
const nullTypeCol = {
  ...movieCol, id: 3, name: 'Legacy Collection', content_type: null,
}

describe('PlexCollectionsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockStore.collections = []
    mockStore.pushAllLoading = false
    mockStore.pushAllError = null
  })

  it('renders Push All to Plex button', () => {
    render(<PlexCollectionsPage />)
    expect(screen.getByRole('button', { name: /push all to plex/i })).toBeInTheDocument()
  })

  it('Push All button calls pushAllCollections', () => {
    render(<PlexCollectionsPage />)
    fireEvent.click(screen.getByRole('button', { name: /push all to plex/i }))
    expect(mockStore.pushAllCollections).toHaveBeenCalled()
  })

  it('shows Movies section heading when movie or null collections exist', () => {
    mockStore.collections = [movieCol, nullTypeCol]
    render(<PlexCollectionsPage />)
    expect(screen.getByRole('heading', { name: /movies/i })).toBeInTheDocument()
    expect(screen.getByText('Action Pack')).toBeInTheDocument()
    expect(screen.getByText('Legacy Collection')).toBeInTheDocument()
  })

  it('shows TV Shows section only when tv collections exist', () => {
    mockStore.collections = [tvCol]
    render(<PlexCollectionsPage />)
    expect(screen.getByRole('heading', { name: /tv shows/i })).toBeInTheDocument()
    expect(screen.getByText('Crime Dramas')).toBeInTheDocument()
  })

  it('does not render TV Shows section when empty', () => {
    mockStore.collections = [movieCol]
    render(<PlexCollectionsPage />)
    expect(screen.queryByRole('heading', { name: /tv shows/i })).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
npm run test -- --run frontend/src/pages/__tests__/PlexCollectionsPage.test.tsx
```

Expected: FAIL — Push All button not found, sections not split

- [ ] **Step 3: Update `PlexCollectionsPage.tsx`**

Key changes to make (do not rewrite unrelated parts):

**a)** Add `pushAllCollections`, `pushAllLoading`, `pushAllError` to the destructured store values.

**b)** Add `handlePushAll`:
```typescript
const handlePushAll = () => {
  pushAllCollections()
}
```

**c)** Update `handleDiscover` (existing) to stay unchanged.

**d)** Update the delete handler signature:
```typescript
const handleDeleteCollection = (id: number, deleteFromPlex: boolean) => {
  deleteCollection(id, deleteFromPlex)
}
```

**e)** Replace the header button area to add "Push All to Plex" alongside "Discover Collections":
```typescript
<div className="flex items-center gap-2">
  <button
    onClick={handlePushAll}
    disabled={pushAllLoading}
    className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium border border-indigo-300 dark:border-indigo-600 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 disabled:opacity-40 transition-colors shrink-0"
  >
    {pushAllLoading ? 'Queuing…' : 'Push All to Plex'}
  </button>
  <button
    onClick={handleDiscover}
    className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium bg-indigo-600 hover:bg-indigo-700 text-white transition-colors shrink-0"
  >
    Discover Collections
  </button>
</div>
```

**f)** Add pushAllError display below the discoverMessage block:
```typescript
{pushAllError && (
  <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-400">
    {pushAllError}
  </div>
)}
```

**g)** Replace the collections grid with split sections. Derive:
```typescript
const movieCollections = collections.filter(
  c => c.content_type === 'movie' || c.content_type === null
)
const tvCollections = collections.filter(c => c.content_type === 'tv_show')
```

Replace the single `{collections.map(...)}` grid with:
```typescript
{collectionsLoading && collections.length === 0 ? (
  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
    {[...Array(3)].map((_, i) => (
      <div key={i} className="h-40 rounded-xl bg-slate-200 dark:bg-slate-700 animate-pulse" />
    ))}
  </div>
) : collections.length === 0 ? (
  <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-6 py-12 text-center">
    <p className="text-slate-500 dark:text-slate-400">No collections yet. Create one or pull from Plex.</p>
  </div>
) : (
  <>
    {movieCollections.length > 0 && (
      <div className="space-y-3">
        <h2 className="text-base font-semibold text-slate-800 dark:text-slate-200">Movies</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {movieCollections.map(col => (
            <CollectionCard
              key={col.id}
              collection={col}
              onToggleEnabled={handleToggleCollection}
              onPush={pushCollection}
              onDelete={handleDeleteCollection}
            />
          ))}
        </div>
      </div>
    )}
    {tvCollections.length > 0 && (
      <div className="space-y-3">
        <h2 className="text-base font-semibold text-slate-800 dark:text-slate-200">TV Shows</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {tvCollections.map(col => (
            <CollectionCard
              key={col.id}
              collection={col}
              onToggleEnabled={handleToggleCollection}
              onPush={pushCollection}
              onDelete={handleDeleteCollection}
            />
          ))}
        </div>
      </div>
    )}
  </>
)}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
npm run test -- --run frontend/src/pages/__tests__/PlexCollectionsPage.test.tsx
```

Expected: PASS

- [ ] **Step 5: Run all frontend tests**

```bash
npm run test -- --run
```

Expected: all pass

- [ ] **Step 6: Run frontend lint and type-check**

```bash
npm run lint
npm run type-check
```

Expected: no errors

- [ ] **Step 7: Run backend tests one final time**

```bash
cd /Users/john/Code/Metamaster/.worktrees/feat/collection-sync
pytest
```

Expected: all pass

- [ ] **Step 8: Stage**

```bash
git add frontend/src/pages/PlexCollectionsPage.tsx frontend/src/pages/__tests__/PlexCollectionsPage.test.tsx
```
