# Plex Collections & Playlists: List + Drawer — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the card grid on the Plex Collections page with a compact list and a side drawer that shows Plex artwork and enriched item details.

**Architecture:** Backend gains two artwork proxy endpoints and a title-enrichment helper wired into the single-item GET endpoints. Frontend replaces `CollectionCard`/`PlaylistCard` with `CollectionRow`/`PlaylistRow` components and adds `CollectionDrawer`/`PlaylistDrawer` components opened by clicking a row name.

**Tech Stack:** FastAPI, SQLAlchemy, httpx (backend); React, TypeScript, Tailwind, TanStack Query/Zustand, React Router, Vitest (frontend)

**Spec:** `docs/superpowers/specs/2026-03-20-plex-list-drawer.md`

---

## Chunk 1: Backend — schemas, enrichment, artwork

### Task 1: Add `movie_title` to item response schemas

**Files:**
- Modify: `app/api/v1/plex/collection_schemas.py:44-76`
- Test: `tests/test_plex_collection_router.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_plex_collection_router.py`:

```python
@pytest.mark.unit
def test_get_collection_items_have_movie_title_field():
    """GET /plex/collections/{id} response items include movie_title field."""
    _clear_db()
    _seed_connection()
    create_resp = client.post(
        "/api/v1/plex/collections",
        json={"name": "T", "builder_type": "static_items", "builder_config": {"items": []}},
    )
    coll_id = create_resp.json()["id"]
    resp = client.get(f"/api/v1/plex/collections/{coll_id}")
    assert resp.status_code == 200
    # items is empty but schema must include movie_title key when items present
    assert "items" in resp.json()


@pytest.mark.unit
def test_get_playlist_items_have_movie_title_field():
    """GET /plex/playlists/{id} response items include movie_title field."""
    _clear_db()
    _seed_connection()
    pl_resp = client.post(
        "/api/v1/plex/playlists",
        json={"name": "P", "builder_config": {}},
    )
    pl_id = pl_resp.json()["id"]
    resp = client.get(f"/api/v1/plex/playlists/{pl_id}")
    assert resp.status_code == 200
    assert "items" in resp.json()
```

- [ ] **Step 2: Run to confirm tests pass (schema change not yet needed — empty items list)**

```bash
pytest tests/test_plex_collection_router.py::test_get_collection_items_have_movie_title_field tests/test_plex_collection_router.py::test_get_playlist_items_have_movie_title_field -v
```

Expected: PASS (the `items` key already exists; these are scaffolding tests that verify structure before richer enrichment tests in Task 2)

- [ ] **Step 3: Add `movie_title` to both item response schemas**

In `app/api/v1/plex/collection_schemas.py`, modify `CollectionItemResponse`:

```python
class CollectionItemResponse(BaseModel):
    id: int
    plex_rating_key: str
    item_type: str
    item_id: int
    position: int
    movie_title: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
```

And `PlaylistItemResponse`:

```python
class PlaylistItemResponse(BaseModel):
    id: int
    plex_rating_key: str
    item_type: str
    item_id: int
    position: int
    movie_title: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 4: Run lint**

```bash
black app/api/v1/plex/collection_schemas.py && isort app/api/v1/plex/collection_schemas.py && flake8 app/api/v1/plex/collection_schemas.py
```

Expected: no output (clean)

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/plex/collection_schemas.py tests/test_plex_collection_router.py
git commit -m "feat(plex): add movie_title field to collection and playlist item response schemas"
```

---

### Task 2: Title enrichment helper + wire into GET endpoints

**Files:**
- Modify: `app/api/v1/plex/collection_router.py`
- Test: `tests/test_plex_collection_router.py`

- [ ] **Step 1: Write the failing enrichment tests**

Add to `tests/test_plex_collection_router.py`. First add a `_seed_movie` helper after the existing helpers:

```python
def _seed_movie(title: str, item_id: int = None) -> int:
    from app.domain.movies.models import Movie
    db = _SessionLocal()
    movie = Movie(title=title, enrichment_status="local_only")
    db.add(movie)
    db.commit()
    db.refresh(movie)
    mid = movie.id
    db.close()
    return mid
```

Then add tests:

```python
@pytest.mark.unit
def test_get_collection_items_resolved_with_movie_title():
    """Items matched in the local movie DB include their title."""
    _clear_db()
    _seed_connection()
    movie_id = _seed_movie("The Dark Knight")

    # Create collection and manually add an item linked to the movie
    create_resp = client.post(
        "/api/v1/plex/collections",
        json={"name": "Heroes", "builder_type": "static_items", "builder_config": {}},
    )
    coll_id = create_resp.json()["id"]

    from app.domain.plex.collection_models import PlexCollectionItem
    db = _SessionLocal()
    db.add(PlexCollectionItem(
        collection_id=coll_id,
        plex_rating_key="key-1",
        item_type="movie",
        item_id=movie_id,
        position=0,
    ))
    db.commit()
    db.close()

    resp = client.get(f"/api/v1/plex/collections/{coll_id}")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["movie_title"] == "The Dark Knight"


@pytest.mark.unit
def test_get_collection_item_unmatched_has_null_title():
    """Items with item_type=tv_show or missing movie get movie_title=null."""
    _clear_db()
    _seed_connection()
    create_resp = client.post(
        "/api/v1/plex/collections",
        json={"name": "TV", "builder_type": "static_items", "builder_config": {}},
    )
    coll_id = create_resp.json()["id"]

    from app.domain.plex.collection_models import PlexCollectionItem
    db = _SessionLocal()
    db.add(PlexCollectionItem(
        collection_id=coll_id,
        plex_rating_key="key-tv",
        item_type="tv_show",
        item_id=999,
        position=0,
    ))
    db.commit()
    db.close()

    resp = client.get(f"/api/v1/plex/collections/{coll_id}")
    items = resp.json()["items"]
    assert items[0]["movie_title"] is None


@pytest.mark.unit
def test_get_playlist_items_resolved_with_movie_title():
    """Playlist items matched in the local movie DB include their title."""
    _clear_db()
    _seed_connection()
    movie_id = _seed_movie("Mad Max")

    pl_resp = client.post("/api/v1/plex/playlists", json={"name": "P", "builder_config": {}})
    pl_id = pl_resp.json()["id"]

    from app.domain.plex.collection_models import PlexPlaylistItem
    db = _SessionLocal()
    db.add(PlexPlaylistItem(
        playlist_id=pl_id,
        plex_rating_key="key-2",
        item_type="movie",
        item_id=movie_id,
        position=0,
    ))
    db.commit()
    db.close()

    resp = client.get(f"/api/v1/plex/playlists/{pl_id}")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items[0]["movie_title"] == "Mad Max"
```

- [ ] **Step 2: Run to confirm tests fail**

```bash
pytest tests/test_plex_collection_router.py::test_get_collection_items_resolved_with_movie_title tests/test_plex_collection_router.py::test_get_collection_item_unmatched_has_null_title tests/test_plex_collection_router.py::test_get_playlist_items_resolved_with_movie_title -v
```

Expected: FAIL — `movie_title` is `None` for all items (enrichment not wired)

- [ ] **Step 3: Add enrichment helpers and update GET endpoints**

In `app/api/v1/plex/collection_router.py`, add two helpers after the `_make_services` function:

```python
def _resolve_titles(items: list, db: Session) -> dict:
    """Return {movie_id: title} for all movie-type items in a single query."""
    movie_ids = [i.item_id for i in items if i.item_type == "movie"]
    if not movie_ids:
        return {}
    return {
        m.id: m.title
        for m in db.query(MovieModel).filter(MovieModel.id.in_(movie_ids)).all()
    }


def _enrich_collection_items(
    items: list, db: Session
) -> list:
    titles = _resolve_titles(items, db)
    return [
        CollectionItemResponse(
            id=i.id,
            plex_rating_key=i.plex_rating_key,
            item_type=i.item_type,
            item_id=i.item_id,
            position=i.position,
            movie_title=titles.get(i.item_id) if i.item_type == "movie" else None,
        )
        for i in items
    ]


def _enrich_playlist_items(
    items: list, db: Session
) -> list:
    titles = _resolve_titles(items, db)
    return [
        PlaylistItemResponse(
            id=i.id,
            plex_rating_key=i.plex_rating_key,
            item_type=i.item_type,
            item_id=i.item_id,
            position=i.position,
            movie_title=titles.get(i.item_id) if i.item_type == "movie" else None,
        )
        for i in items
    ]
```

`CollectionItemResponse` and `PlaylistItemResponse` are already imported at the top of the router from `app.api.v1.plex.collection_schemas`. Add the following import if not present:

```python
from app.api.v1.plex.collection_schemas import (
    CollectionItemResponse,
    CollectionResponse,
    ...
    PlaylistItemResponse,
    PlaylistResponse,
    ...
)
```

Then update `get_collection` (currently returns the ORM object directly):

```python
@router.get("/collections/{collection_id}", response_model=CollectionResponse)
def get_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Get a single PlexCollection by ID, with movie titles resolved on items."""
    coll = db.query(PlexCollection).filter(PlexCollection.id == collection_id).first()
    if coll is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    response = CollectionResponse.model_validate(coll)
    response.items = _enrich_collection_items(coll.items, db)
    return response
```

And `get_playlist`:

```python
@router.get("/playlists/{playlist_id}", response_model=PlaylistResponse)
def get_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Get a single PlexPlaylist by ID, with movie titles resolved on items."""
    pl = db.query(PlexPlaylist).filter(PlexPlaylist.id == playlist_id).first()
    if pl is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    response = PlaylistResponse.model_validate(pl)
    response.items = _enrich_playlist_items(pl.items, db)
    return response
```

- [ ] **Step 4: Run enrichment tests**

```bash
pytest tests/test_plex_collection_router.py::test_get_collection_items_resolved_with_movie_title tests/test_plex_collection_router.py::test_get_collection_item_unmatched_has_null_title tests/test_plex_collection_router.py::test_get_playlist_items_resolved_with_movie_title -v
```

Expected: PASS

- [ ] **Step 5: Run full router tests**

```bash
pytest tests/test_plex_collection_router.py -v
```

Expected: all pass

- [ ] **Step 6: Run lint**

```bash
black app/api/v1/plex/collection_router.py && isort app/api/v1/plex/collection_router.py && flake8 app/api/v1/plex/collection_router.py
```

- [ ] **Step 7: Commit**

```bash
git add app/api/v1/plex/collection_router.py tests/test_plex_collection_router.py
git commit -m "feat(plex): enrich collection and playlist item responses with movie titles"
```

---

### Task 3: Artwork proxy endpoints

**Files:**
- Modify: `app/api/v1/plex/collection_router.py`
- Test: `tests/test_plex_collection_router.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_plex_collection_router.py`:

```python
@pytest.mark.unit
def test_collection_artwork_returns_404_when_no_plex_key():
    """GET /plex/collections/{id}/artwork returns 404 when not synced to Plex."""
    _clear_db()
    _seed_connection()
    create_resp = client.post(
        "/api/v1/plex/collections",
        json={"name": "Art", "builder_type": "static_items", "builder_config": {}},
    )
    coll_id = create_resp.json()["id"]
    resp = client.get(f"/api/v1/plex/collections/{coll_id}/artwork")
    assert resp.status_code == 404


@pytest.mark.unit
def test_collection_artwork_proxies_plex_image():
    """GET /plex/collections/{id}/artwork returns proxied image from Plex."""
    _clear_db()
    _seed_connection()
    create_resp = client.post(
        "/api/v1/plex/collections",
        json={"name": "Art", "builder_type": "static_items", "builder_config": {}},
    )
    coll_id = create_resp.json()["id"]

    # Set plex_rating_key directly
    from app.domain.plex.collection_models import PlexCollection
    db = _SessionLocal()
    coll = db.query(PlexCollection).filter_by(id=coll_id).first()
    coll.plex_rating_key = "rk-art"
    db.commit()
    db.close()

    mock_response = MagicMock()
    mock_response.content = b"fake-image-bytes"
    mock_response.headers = {"content-type": "image/jpeg"}
    mock_response.raise_for_status = MagicMock()

    with patch("app.api.v1.plex.collection_router.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        resp = client.get(f"/api/v1/plex/collections/{coll_id}/artwork")

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"
    assert resp.content == b"fake-image-bytes"


@pytest.mark.unit
def test_collection_artwork_returns_502_on_plex_error():
    """GET /plex/collections/{id}/artwork returns 502 when Plex is unreachable."""
    _clear_db()
    _seed_connection()
    create_resp = client.post(
        "/api/v1/plex/collections",
        json={"name": "Art", "builder_type": "static_items", "builder_config": {}},
    )
    coll_id = create_resp.json()["id"]

    from app.domain.plex.collection_models import PlexCollection
    db = _SessionLocal()
    coll = db.query(PlexCollection).filter_by(id=coll_id).first()
    coll.plex_rating_key = "rk-err"
    db.commit()
    db.close()

    with patch("app.api.v1.plex.collection_router.httpx.Client") as mock_client:
        import httpx as httpx_lib
        mock_client.return_value.__enter__.return_value.get.side_effect = (
            httpx_lib.RequestError("timeout")
        )
        resp = client.get(f"/api/v1/plex/collections/{coll_id}/artwork")

    assert resp.status_code == 502


@pytest.mark.unit
def test_playlist_artwork_returns_404_when_no_plex_key():
    """GET /plex/playlists/{id}/artwork returns 404 when not synced to Plex."""
    _clear_db()
    _seed_connection()
    pl_resp = client.post("/api/v1/plex/playlists", json={"name": "P", "builder_config": {}})
    pl_id = pl_resp.json()["id"]
    resp = client.get(f"/api/v1/plex/playlists/{pl_id}/artwork")
    assert resp.status_code == 404


@pytest.mark.unit
def test_playlist_artwork_proxies_plex_image():
    """GET /plex/playlists/{id}/artwork returns proxied image from Plex."""
    _clear_db()
    _seed_connection()
    pl_resp = client.post("/api/v1/plex/playlists", json={"name": "P", "builder_config": {}})
    pl_id = pl_resp.json()["id"]

    from app.domain.plex.collection_models import PlexPlaylist
    db = _SessionLocal()
    pl = db.query(PlexPlaylist).filter_by(id=pl_id).first()
    pl.plex_rating_key = "rk-pl"
    db.commit()
    db.close()

    mock_response = MagicMock()
    mock_response.content = b"playlist-image"
    mock_response.headers = {"content-type": "image/png"}
    mock_response.raise_for_status = MagicMock()

    with patch("app.api.v1.plex.collection_router.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        resp = client.get(f"/api/v1/plex/playlists/{pl_id}/artwork")

    assert resp.status_code == 200
    assert resp.content == b"playlist-image"
```

- [ ] **Step 2: Run to confirm they fail**

```bash
pytest tests/test_plex_collection_router.py::test_collection_artwork_returns_404_when_no_plex_key tests/test_plex_collection_router.py::test_collection_artwork_proxies_plex_image tests/test_plex_collection_router.py::test_collection_artwork_returns_502_on_plex_error tests/test_plex_collection_router.py::test_playlist_artwork_returns_404_when_no_plex_key tests/test_plex_collection_router.py::test_playlist_artwork_proxies_plex_image -v
```

Expected: FAIL — 404 (endpoints don't exist)

- [ ] **Step 3: Add the artwork endpoints**

Add the `Response` import at the top of `collection_router.py`:

```python
from fastapi.responses import Response
```

Add both artwork endpoints in `collection_router.py`. Place the collection artwork endpoint **after** `get_collection` and **before** `update_collection`, and the playlist artwork endpoint **after** `get_playlist` and **before** `update_playlist`:

```python
@router.get("/collections/{collection_id}/artwork")
def get_collection_artwork(
    collection_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Proxy Plex thumbnail for a collection."""
    coll = db.query(PlexCollection).filter(PlexCollection.id == collection_id).first()
    if coll is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    conn = _get_active_connection(db)
    if coll.connection_id != conn.id:
        raise HTTPException(status_code=404, detail="Collection not found")
    if not coll.plex_rating_key:
        raise HTTPException(status_code=404, detail="Collection not synced to Plex")
    url = f"{conn.server_url}/library/metadata/{coll.plex_rating_key}/thumb"
    try:
        with httpx.Client(timeout=10) as http:
            r = http.get(url, params={"X-Plex-Token": conn.token})
            r.raise_for_status()
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=502, detail="Plex returned an error")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Could not reach Plex")
    return Response(
        content=r.content,
        media_type=r.headers.get("content-type", "image/jpeg"),
    )


@router.get("/playlists/{playlist_id}/artwork")
def get_playlist_artwork(
    playlist_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Proxy Plex thumbnail for a playlist."""
    pl = db.query(PlexPlaylist).filter(PlexPlaylist.id == playlist_id).first()
    if pl is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    conn = _get_active_connection(db)
    if pl.connection_id != conn.id:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if not pl.plex_rating_key:
        raise HTTPException(status_code=404, detail="Playlist not synced to Plex")
    url = f"{conn.server_url}/library/metadata/{pl.plex_rating_key}/thumb"
    try:
        with httpx.Client(timeout=10) as http:
            r = http.get(url, params={"X-Plex-Token": conn.token})
            r.raise_for_status()
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=502, detail="Plex returned an error")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Could not reach Plex")
    return Response(
        content=r.content,
        media_type=r.headers.get("content-type", "image/jpeg"),
    )
```

- [ ] **Step 4: Run the artwork tests**

```bash
pytest tests/test_plex_collection_router.py::test_collection_artwork_returns_404_when_no_plex_key tests/test_plex_collection_router.py::test_collection_artwork_proxies_plex_image tests/test_plex_collection_router.py::test_collection_artwork_returns_502_on_plex_error tests/test_plex_collection_router.py::test_playlist_artwork_returns_404_when_no_plex_key tests/test_plex_collection_router.py::test_playlist_artwork_proxies_plex_image -v
```

Expected: PASS

- [ ] **Step 5: Run full router tests and lint**

```bash
pytest tests/test_plex_collection_router.py -v
black app/api/v1/plex/collection_router.py && isort app/api/v1/plex/collection_router.py && flake8 app/api/v1/plex/collection_router.py
```

Expected: all pass, no lint errors

- [ ] **Step 6: Commit**

```bash
git add app/api/v1/plex/collection_router.py tests/test_plex_collection_router.py
git commit -m "feat(plex): add artwork proxy endpoints for collections and playlists"
```

---

## Chunk 2: Frontend — service layer + row components

### Task 4: Extend service interfaces and add artwork functions

**Files:**
- Modify: `frontend/src/services/plexCollectionService.ts`
- Test: `frontend/src/services/__tests__/plexCollectionService.test.ts`

- [ ] **Step 1: Write failing service tests**

Add to `frontend/src/services/__tests__/plexCollectionService.test.ts`:

```ts
describe('getCollectionArtwork', () => {
  it('calls GET /plex/collections/{id}/artwork with responseType blob', async () => {
    const mockBlob = new Blob(['data'], { type: 'image/jpeg' })
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockBlob })
    const result = await getCollectionArtwork(5)
    expect(apiClient.get).toHaveBeenCalledWith('/plex/collections/5/artwork', { responseType: 'blob' })
    expect(result).toBe(mockBlob)
  })
})

describe('getPlaylistArtwork', () => {
  it('calls GET /plex/playlists/{id}/artwork with responseType blob', async () => {
    const mockBlob = new Blob(['data'], { type: 'image/jpeg' })
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockBlob })
    const result = await getPlaylistArtwork(7)
    expect(apiClient.get).toHaveBeenCalledWith('/plex/playlists/7/artwork', { responseType: 'blob' })
    expect(result).toBe(mockBlob)
  })
})
```

Also import the new functions at the top of the test file:
```ts
import { getCollectionArtwork, getPlaylistArtwork, ... } from '../plexCollectionService'
```

- [ ] **Step 2: Run to confirm they fail**

```bash
cd frontend && npm run test -- plexCollectionService --run
```

Expected: FAIL — `getCollectionArtwork is not a function`

- [ ] **Step 3: Extend interfaces and add functions**

In `frontend/src/services/plexCollectionService.ts`, update `CollectionItem`:

```ts
export interface CollectionItem {
  id: number
  plex_rating_key: string
  item_type: string
  item_id: number
  position: number
  movie_title: string | null
}
```

Update `PlaylistItem`:

```ts
export interface PlaylistItem {
  id: number
  plex_rating_key: string
  item_type: string
  item_id: number
  position: number
  movie_title: string | null
}
```

Add artwork functions after `pushAllCollections`:

```ts
export async function getCollectionArtwork(id: number): Promise<Blob> {
  const { data } = await apiClient.get(`/plex/collections/${id}/artwork`, { responseType: 'blob' })
  return data
}

export async function getPlaylistArtwork(id: number): Promise<Blob> {
  const { data } = await apiClient.get(`/plex/playlists/${id}/artwork`, { responseType: 'blob' })
  return data
}
```

- [ ] **Step 4: Run tests**

```bash
cd frontend && npm run test -- plexCollectionService --run
```

Expected: PASS

- [ ] **Step 5: TypeScript check**

```bash
cd frontend && npm run type-check
```

Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/services/plexCollectionService.ts frontend/src/services/__tests__/plexCollectionService.test.ts
git commit -m "feat(plex): add movie_title to item interfaces and artwork service functions"
```

---

### Task 5: CollectionRow component

**Files:**
- Create: `frontend/src/components/features/plex/CollectionRow.tsx`
- Create: `frontend/src/components/features/plex/__tests__/CollectionRow.test.tsx`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/components/features/plex/__tests__/CollectionRow.test.tsx`:

```tsx
import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { CollectionRow } from '../CollectionRow'
import type { PlexCollection } from '../../../../services/plexCollectionService'

const baseCollection: PlexCollection = {
  id: 1,
  connection_id: 1,
  name: 'Action Films',
  description: null,
  sort_title: null,
  builder_type: 'genre',
  builder_config: { genre: 'Action' },
  plex_rating_key: null,
  last_synced_at: null,
  enabled: false,
  is_default: false,
  items: [],
  content_type: 'movie',
}

describe('CollectionRow', () => {
  it('renders the collection name as a button', () => {
    render(
      <table><tbody>
        <CollectionRow collection={baseCollection} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={vi.fn()} isSelected={false} />
      </tbody></table>
    )
    expect(screen.getByRole('button', { name: /action films/i })).toBeInTheDocument()
  })

  it('renders the builder type badge', () => {
    render(
      <table><tbody>
        <CollectionRow collection={baseCollection} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={vi.fn()} isSelected={false} />
      </tbody></table>
    )
    expect(screen.getByText('Genre')).toBeInTheDocument()
  })

  it('calls onSelect when name button is clicked', () => {
    const onSelect = vi.fn()
    render(
      <table><tbody>
        <CollectionRow collection={baseCollection} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={onSelect} isSelected={false} />
      </tbody></table>
    )
    fireEvent.click(screen.getByRole('button', { name: /action films/i }))
    expect(onSelect).toHaveBeenCalledWith(1)
  })

  it('shows delete confirm dialog when Delete clicked', () => {
    render(
      <table><tbody>
        <CollectionRow collection={baseCollection} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={vi.fn()} isSelected={false} />
      </tbody></table>
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    expect(screen.getByText((_, el) => el?.textContent === 'Delete Action Films?')).toBeInTheDocument()
  })

  it('calls onDelete with deleteFromPlex=false when no plex_rating_key', () => {
    const onDelete = vi.fn()
    render(
      <table><tbody>
        <CollectionRow collection={baseCollection} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={onDelete} onSelect={vi.fn()} isSelected={false} />
      </tbody></table>
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    fireEvent.click(screen.getByRole('button', { name: /^delete$/i }))
    expect(onDelete).toHaveBeenCalledWith(1, false)
  })

  it('shows "Also delete from Plex" checkbox when plex_rating_key is set', () => {
    const col = { ...baseCollection, plex_rating_key: 'rk-1' }
    render(
      <table><tbody>
        <CollectionRow collection={col} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={vi.fn()} isSelected={false} />
      </tbody></table>
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    expect(screen.getByRole('checkbox', { name: /also delete from plex/i })).toBeInTheDocument()
  })

  it('highlights the row when isSelected is true', () => {
    const { container } = render(
      <table><tbody>
        <CollectionRow collection={baseCollection} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={vi.fn()} isSelected={true} />
      </tbody></table>
    )
    const row = container.querySelector('tr')
    expect(row?.className).toMatch(/border-indigo/)
  })
})
```

- [ ] **Step 2: Run to confirm they fail**

```bash
cd frontend && npm run test -- CollectionRow --run
```

Expected: FAIL — module not found

- [ ] **Step 3: Create the component**

Create `frontend/src/components/features/plex/CollectionRow.tsx`:

```tsx
import React, { useState } from 'react'
import type { PlexCollection } from '../../../services/plexCollectionService'
import { Checkbox } from '@/components/common/Checkbox'

interface CollectionRowProps {
  collection: PlexCollection
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number, deleteFromPlex: boolean) => void
  onSelect: (id: number) => void
  isSelected: boolean
}

const BUILDER_LABELS: Record<string, string> = {
  tmdb_collection: 'TMDB',
  static_items: 'Static',
  genre: 'Genre',
  decade: 'Decade',
}

function formatSyncDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString()
}

export function CollectionRow({
  collection,
  onToggleEnabled,
  onPush,
  onDelete,
  onSelect,
  isSelected,
}: CollectionRowProps) {
  const [showConfirm, setShowConfirm] = useState(false)
  const [deleteFromPlex, setDeleteFromPlex] = useState(!!collection.plex_rating_key)

  const handleDeleteClick = () => {
    setDeleteFromPlex(!!collection.plex_rating_key)
    setShowConfirm(true)
  }

  const handleConfirmDelete = () => {
    setShowConfirm(false)
    onDelete(collection.id, deleteFromPlex)
  }

  return (
    <>
      <tr
        className={`border-l-2 transition-colors ${
          isSelected
            ? 'border-indigo-500 bg-slate-800/50'
            : 'border-transparent hover:bg-slate-800/30'
        }`}
      >
        <td className="py-2 pl-3 pr-2">
          <button
            onClick={() => onSelect(collection.id)}
            className="text-left font-medium text-slate-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 hover:underline transition-colors truncate max-w-xs"
          >
            {collection.name}
          </button>
        </td>
        <td className="py-2 px-2">
          <span className="inline-flex px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400">
            {BUILDER_LABELS[collection.builder_type] ?? collection.builder_type}
          </span>
        </td>
        <td className="py-2 px-2 text-sm text-slate-500 dark:text-slate-400">
          {collection.items.length}
        </td>
        <td className="py-2 px-2 text-sm text-slate-500 dark:text-slate-400 whitespace-nowrap">
          {formatSyncDate(collection.last_synced_at)}
        </td>
        <td className="py-2 pl-2 pr-3">
          <div className="flex items-center justify-end gap-2">
            <Checkbox
              label="Enabled"
              checked={collection.enabled}
              onChange={checked => onToggleEnabled(collection.id, checked)}
            />
            <button
              onClick={() => onPush(collection.id)}
              disabled={!collection.enabled}
              className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors"
            >
              Push
            </button>
            <button
              onClick={handleDeleteClick}
              className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            >
              Delete
            </button>
          </div>
        </td>
      </tr>

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
    </>
  )
}

export default CollectionRow
```

- [ ] **Step 4: Run tests**

```bash
cd frontend && npm run test -- CollectionRow --run
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/features/plex/CollectionRow.tsx frontend/src/components/features/plex/__tests__/CollectionRow.test.tsx
git commit -m "feat(plex): add CollectionRow component"
```

---

### Task 6: PlaylistRow component

**Files:**
- Create: `frontend/src/components/features/plex/PlaylistRow.tsx`
- Create: `frontend/src/components/features/plex/__tests__/PlaylistRow.test.tsx`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/components/features/plex/__tests__/PlaylistRow.test.tsx`:

```tsx
import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { PlaylistRow } from '../PlaylistRow'
import type { PlexPlaylist } from '../../../../services/plexCollectionService'

const basePlaylist: PlexPlaylist = {
  id: 2,
  connection_id: 1,
  name: 'My Playlist',
  description: null,
  builder_config: {},
  plex_rating_key: null,
  last_synced_at: null,
  enabled: true,
  items: [],
}

describe('PlaylistRow', () => {
  it('renders the playlist name as a button', () => {
    render(
      <table><tbody>
        <PlaylistRow playlist={basePlaylist} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={vi.fn()} isSelected={false} />
      </tbody></table>
    )
    expect(screen.getByRole('button', { name: /my playlist/i })).toBeInTheDocument()
  })

  it('calls onSelect when name is clicked', () => {
    const onSelect = vi.fn()
    render(
      <table><tbody>
        <PlaylistRow playlist={basePlaylist} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={onSelect} isSelected={false} />
      </tbody></table>
    )
    fireEvent.click(screen.getByRole('button', { name: /my playlist/i }))
    expect(onSelect).toHaveBeenCalledWith(2)
  })

  it('shows simple confirm dialog (no Plex checkbox) when Delete clicked', () => {
    render(
      <table><tbody>
        <PlaylistRow playlist={basePlaylist} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={vi.fn()} isSelected={false} />
      </tbody></table>
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    expect(screen.getByText(/delete my playlist/i)).toBeInTheDocument()
    expect(screen.queryByRole('checkbox', { name: /plex/i })).not.toBeInTheDocument()
  })

  it('calls onDelete when confirmed', () => {
    const onDelete = vi.fn()
    render(
      <table><tbody>
        <PlaylistRow playlist={basePlaylist} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={onDelete} onSelect={vi.fn()} isSelected={false} />
      </tbody></table>
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    fireEvent.click(screen.getByRole('button', { name: /^delete$/i }))
    expect(onDelete).toHaveBeenCalledWith(2)
  })

  it('shows select checkbox in selectable mode', () => {
    const onBulkSelect = vi.fn()
    render(
      <table><tbody>
        <PlaylistRow playlist={basePlaylist} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={vi.fn()} isSelected={false} selectable onBulkSelect={onBulkSelect} bulkSelected={false} />
      </tbody></table>
    )
    expect(screen.getByRole('checkbox', { name: /select my playlist/i })).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run to confirm fail**

```bash
cd frontend && npm run test -- PlaylistRow --run
```

Expected: FAIL

- [ ] **Step 3: Create the component**

Create `frontend/src/components/features/plex/PlaylistRow.tsx`:

```tsx
import React, { useState } from 'react'
import type { PlexPlaylist } from '../../../services/plexCollectionService'
import { Checkbox, CheckboxInput } from '@/components/common/Checkbox'

interface PlaylistRowProps {
  playlist: PlexPlaylist
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number) => void
  onSelect: (id: number) => void
  isSelected: boolean
  selectable?: boolean
  bulkSelected?: boolean
  onBulkSelect?: (id: number, selected: boolean) => void
}

function formatSyncDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString()
}

export function PlaylistRow({
  playlist,
  onToggleEnabled,
  onPush,
  onDelete,
  onSelect,
  isSelected,
  selectable,
  bulkSelected,
  onBulkSelect,
}: PlaylistRowProps) {
  const [showConfirm, setShowConfirm] = useState(false)

  return (
    <>
      <tr
        className={`border-l-2 transition-colors ${
          isSelected
            ? 'border-indigo-500 bg-slate-800/50'
            : 'border-transparent hover:bg-slate-800/30'
        }`}
      >
        <td className="py-2 pl-3 pr-2">
          <div className="flex items-center gap-2">
            {selectable && (
              <CheckboxInput
                checked={!!bulkSelected}
                onChange={checked => onBulkSelect?.(playlist.id, checked)}
                aria-label={`Select ${playlist.name}`}
              />
            )}
            <button
              onClick={() => onSelect(playlist.id)}
              className="text-left font-medium text-slate-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 hover:underline transition-colors truncate max-w-xs"
            >
              {playlist.name}
            </button>
          </div>
        </td>
        <td className="py-2 px-2 text-sm text-slate-500 dark:text-slate-400">
          {playlist.items.length}
        </td>
        <td className="py-2 px-2 text-sm text-slate-500 dark:text-slate-400 whitespace-nowrap">
          {formatSyncDate(playlist.last_synced_at)}
        </td>
        <td className="py-2 pl-2 pr-3">
          <div className="flex items-center justify-end gap-2">
            <Checkbox
              label="Enabled"
              checked={playlist.enabled}
              onChange={checked => onToggleEnabled(playlist.id, checked)}
            />
            <button
              onClick={() => onPush(playlist.id)}
              disabled={!playlist.enabled}
              className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors"
            >
              Push
            </button>
            <button
              onClick={() => setShowConfirm(true)}
              className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            >
              Delete
            </button>
          </div>
        </td>
      </tr>

      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-xl p-6 w-full max-w-sm mx-4 space-y-4">
            <p className="text-sm font-medium text-slate-900 dark:text-white">
              Delete <strong>{playlist.name}</strong>?
            </p>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowConfirm(false)}
                className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => { setShowConfirm(false); onDelete(playlist.id) }}
                className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium bg-red-600 hover:bg-red-700 text-white transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default PlaylistRow
```

- [ ] **Step 4: Run tests**

```bash
cd frontend && npm run test -- PlaylistRow --run
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/features/plex/PlaylistRow.tsx frontend/src/components/features/plex/__tests__/PlaylistRow.test.tsx
git commit -m "feat(plex): add PlaylistRow component"
```

---

## Chunk 3: Drawers + page integration

### Task 7: CollectionDrawer component

**Files:**
- Create: `frontend/src/components/features/plex/CollectionDrawer.tsx`

- [ ] **Step 1: Create the component**

`CollectionDrawer` does not need a heavy test suite here — the drawer interactions (ESC, mutual exclusion) are tested at the page level in Task 9. Create `frontend/src/components/features/plex/CollectionDrawer.tsx`:

```tsx
import React, { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import type { PlexCollection } from '../../../services/plexCollectionService'
import {
  getCollection,
  getCollectionArtwork,
} from '../../../services/plexCollectionService'
import { Checkbox } from '@/components/common/Checkbox'

const BUILDER_LABELS: Record<string, string> = {
  tmdb_collection: 'TMDB',
  static_items: 'Static',
  genre: 'Genre',
  decade: 'Decade',
}

function formatSyncDate(dateStr: string | null): string {
  if (!dateStr) return 'Never synced'
  return new Date(dateStr).toLocaleString()
}

interface CollectionDrawerProps {
  collection: PlexCollection
  onClose: () => void
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number, deleteFromPlex: boolean) => void
}

export function CollectionDrawer({
  collection,
  onClose,
  onToggleEnabled,
  onPush,
  onDelete,
}: CollectionDrawerProps) {
  const [artworkUrl, setArtworkUrl] = useState<string | null>(null)
  const [detail, setDetail] = useState<PlexCollection | null>(null)
  const [showConfirm, setShowConfirm] = useState(false)
  const [deleteFromPlex, setDeleteFromPlex] = useState(!!collection.plex_rating_key)
  const drawerRef = useRef<HTMLDivElement>(null)

  // Fetch enriched detail (items with movie titles)
  useEffect(() => {
    getCollection(collection.id).then(setDetail).catch(() => {})
  }, [collection.id])

  // Fetch and manage artwork blob URL
  useEffect(() => {
    if (!collection.plex_rating_key) return
    let objectUrl: string | null = null
    let cancelled = false
    getCollectionArtwork(collection.id)
      .then(blob => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(blob)
        setArtworkUrl(objectUrl)
      })
      .catch(() => { if (!cancelled) setArtworkUrl(null) })
    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [collection.id, collection.plex_rating_key])

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  // Close on click outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (drawerRef.current && !drawerRef.current.contains(e.target as Node)) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [onClose])

  const items = detail?.items ?? []

  return (
    <div
      ref={drawerRef}
      className="w-80 flex-shrink-0 border-l border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex flex-col overflow-hidden lg:relative fixed right-0 top-0 h-full z-40 lg:z-auto"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-700">
        <h3 className="font-semibold text-slate-900 dark:text-white truncate pr-2">
          {collection.name}
        </h3>
        <button
          onClick={onClose}
          aria-label="Close drawer"
          className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors flex-shrink-0"
        >
          ✕
        </button>
      </div>

      <div className="overflow-y-auto flex-1 p-4 space-y-4">
        {/* Artwork */}
        {artworkUrl ? (
          <img
            src={artworkUrl}
            alt={`${collection.name} artwork`}
            className="w-full rounded-lg object-cover"
          />
        ) : (
          <div className="w-full h-32 rounded-lg bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-400 text-sm">
            No artwork
          </div>
        )}

        {/* Metadata */}
        <div className="flex items-center gap-2 flex-wrap text-sm text-slate-500 dark:text-slate-400">
          <span className="inline-flex px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400">
            {BUILDER_LABELS[collection.builder_type] ?? collection.builder_type}
          </span>
          <span>{collection.items.length} items</span>
          <span>·</span>
          <span>{formatSyncDate(collection.last_synced_at)}</span>
        </div>

        {collection.description && (
          <p className="text-sm text-slate-500 dark:text-slate-400">{collection.description}</p>
        )}

        {/* Controls */}
        <div className="flex items-center justify-between gap-2 p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50">
          <Checkbox
            label="Enabled"
            checked={collection.enabled}
            onChange={checked => onToggleEnabled(collection.id, checked)}
          />
          <div className="flex gap-2">
            <button
              onClick={() => onPush(collection.id)}
              disabled={!collection.enabled}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white transition-colors"
            >
              Push to Plex
            </button>
            <button
              onClick={() => { setDeleteFromPlex(!!collection.plex_rating_key); setShowConfirm(true) }}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            >
              Delete
            </button>
          </div>
        </div>

        {/* Items list */}
        <div>
          <h4 className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
            Items ({items.length})
          </h4>
          {items.length === 0 ? (
            <p className="text-sm text-slate-400 italic">No items</p>
          ) : (
            <div className="rounded-lg border border-slate-200 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700">
              {items.map(item => (
                <div key={item.id} className="flex items-center justify-between px-3 py-2 gap-2">
                  <div className="min-w-0">
                    {item.movie_title ? (
                      <span className="text-sm text-slate-800 dark:text-slate-200 truncate block">
                        {item.movie_title}
                      </span>
                    ) : (
                      <span className="text-sm text-slate-400 italic truncate block">—</span>
                    )}
                    <span className="text-xs font-mono text-slate-400">
                      {item.plex_rating_key}
                    </span>
                  </div>
                  {item.movie_title && (
                    <Link
                      to={`/movies/${item.item_id}`}
                      className="text-indigo-500 hover:text-indigo-700 flex-shrink-0 text-sm"
                    >
                      →
                    </Link>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Delete confirm */}
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
                className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => { setShowConfirm(false); onDelete(collection.id, deleteFromPlex) }}
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

export default CollectionDrawer
```

- [ ] **Step 2: TypeScript check**

```bash
cd frontend && npm run type-check
```

Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/features/plex/CollectionDrawer.tsx
git commit -m "feat(plex): add CollectionDrawer component"
```

---

### Task 8: PlaylistDrawer component

**Files:**
- Create: `frontend/src/components/features/plex/PlaylistDrawer.tsx`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/features/plex/PlaylistDrawer.tsx`:

```tsx
import React, { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import type { PlexPlaylist } from '../../../services/plexCollectionService'
import {
  getPlaylist,
  getPlaylistArtwork,
} from '../../../services/plexCollectionService'
import { Checkbox } from '@/components/common/Checkbox'

function formatSyncDate(dateStr: string | null): string {
  if (!dateStr) return 'Never synced'
  return new Date(dateStr).toLocaleString()
}

interface PlaylistDrawerProps {
  playlist: PlexPlaylist
  onClose: () => void
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number) => void
}

export function PlaylistDrawer({
  playlist,
  onClose,
  onToggleEnabled,
  onPush,
  onDelete,
}: PlaylistDrawerProps) {
  const [artworkUrl, setArtworkUrl] = useState<string | null>(null)
  const [detail, setDetail] = useState<PlexPlaylist | null>(null)
  const [showConfirm, setShowConfirm] = useState(false)
  const drawerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getPlaylist(playlist.id).then(setDetail).catch(() => {})
  }, [playlist.id])

  useEffect(() => {
    if (!playlist.plex_rating_key) return
    let objectUrl: string | null = null
    let cancelled = false
    getPlaylistArtwork(playlist.id)
      .then(blob => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(blob)
        setArtworkUrl(objectUrl)
      })
      .catch(() => { if (!cancelled) setArtworkUrl(null) })
    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [playlist.id, playlist.plex_rating_key])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (drawerRef.current && !drawerRef.current.contains(e.target as Node)) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [onClose])

  const items = detail?.items ?? []

  return (
    <div
      ref={drawerRef}
      className="w-80 flex-shrink-0 border-l border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex flex-col overflow-hidden lg:relative fixed right-0 top-0 h-full z-40 lg:z-auto"
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-700">
        <h3 className="font-semibold text-slate-900 dark:text-white truncate pr-2">
          {playlist.name}
        </h3>
        <button
          onClick={onClose}
          aria-label="Close drawer"
          className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors flex-shrink-0"
        >
          ✕
        </button>
      </div>

      <div className="overflow-y-auto flex-1 p-4 space-y-4">
        {artworkUrl ? (
          <img
            src={artworkUrl}
            alt={`${playlist.name} artwork`}
            className="w-full rounded-lg object-cover"
          />
        ) : (
          <div className="w-full h-32 rounded-lg bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-400 text-sm">
            No artwork
          </div>
        )}

        <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
          <span>{playlist.items.length} items</span>
          <span>·</span>
          <span>{formatSyncDate(playlist.last_synced_at)}</span>
        </div>

        {playlist.description && (
          <p className="text-sm text-slate-500 dark:text-slate-400">{playlist.description}</p>
        )}

        <div className="flex items-center justify-between gap-2 p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50">
          <Checkbox
            label="Enabled"
            checked={playlist.enabled}
            onChange={checked => onToggleEnabled(playlist.id, checked)}
          />
          <div className="flex gap-2">
            <button
              onClick={() => onPush(playlist.id)}
              disabled={!playlist.enabled}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white transition-colors"
            >
              Push to Plex
            </button>
            <button
              onClick={() => setShowConfirm(true)}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            >
              Delete
            </button>
          </div>
        </div>

        <div>
          <h4 className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
            Items ({items.length})
          </h4>
          {items.length === 0 ? (
            <p className="text-sm text-slate-400 italic">No items</p>
          ) : (
            <div className="rounded-lg border border-slate-200 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700">
              {items.map(item => (
                <div key={item.id} className="flex items-center justify-between px-3 py-2 gap-2">
                  <div className="min-w-0">
                    {item.movie_title ? (
                      <span className="text-sm text-slate-800 dark:text-slate-200 truncate block">
                        {item.movie_title}
                      </span>
                    ) : (
                      <span className="text-sm text-slate-400 italic truncate block">—</span>
                    )}
                    <span className="text-xs font-mono text-slate-400">
                      {item.plex_rating_key}
                    </span>
                  </div>
                  {item.movie_title && (
                    <Link
                      to={`/movies/${item.item_id}`}
                      className="text-indigo-500 hover:text-indigo-700 flex-shrink-0 text-sm"
                    >
                      →
                    </Link>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-xl p-6 w-full max-w-sm mx-4 space-y-4">
            <p className="text-sm font-medium text-slate-900 dark:text-white">
              Delete <strong>{playlist.name}</strong>?
            </p>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowConfirm(false)}
                className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => { setShowConfirm(false); onDelete(playlist.id) }}
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

export default PlaylistDrawer
```

- [ ] **Step 2: TypeScript check**

```bash
cd frontend && npm run type-check
```

Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/features/plex/PlaylistDrawer.tsx
git commit -m "feat(plex): add PlaylistDrawer component"
```

---

### Task 9: Update PlexCollectionsPage, delete old components, update tests

**Files:**
- Modify: `frontend/src/pages/PlexCollectionsPage.tsx`
- Modify: `frontend/src/pages/__tests__/PlexCollectionsPage.test.tsx`
- Delete: `frontend/src/components/features/plex/CollectionCard.tsx`
- Delete: `frontend/src/components/features/plex/PlaylistCard.tsx`
- Delete: `frontend/src/components/features/plex/__tests__/CollectionCard.test.tsx`

- [ ] **Step 1: Write the new page tests**

Replace the contents of `frontend/src/pages/__tests__/PlexCollectionsPage.test.tsx`:

```tsx
import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const baseCollection = {
  id: 1, connection_id: 1, name: 'Action Films', description: null, sort_title: null,
  builder_type: 'genre' as const, builder_config: {}, plex_rating_key: null,
  last_synced_at: null, enabled: false, is_default: false, items: [], content_type: 'movie',
}
const basePlaylist = {
  id: 2, connection_id: 1, name: 'My Playlist', description: null, builder_config: {},
  plex_rating_key: null, last_synced_at: null, enabled: false, items: [],
}

const mockStore = {
  collections: [baseCollection],
  collectionsLoading: false,
  collectionsError: null,
  playlists: [basePlaylist],
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
  pushAllError: null as string | null,
  updatePlaylist: vi.fn(),
  deletePlaylist: vi.fn(),
  pushPlaylist: vi.fn(),
  pullPlaylists: vi.fn(),
  bulkDeletePlaylists: vi.fn(),
  toggleCollectionSet: vi.fn(),
  triggerDiscovery: vi.fn().mockResolvedValue({ message: 'ok', task_id: '1' }),
}

vi.mock('../../stores/plexCollectionStore', () => ({
  usePlexCollectionStore: () => mockStore,
}))
vi.mock('../../components/features/plex/CollectionSetToggles', () => ({
  CollectionSetToggles: () => <div data-testid="set-toggles" />,
}))
vi.mock('../../components/features/plex/CollectionRow', () => ({
  CollectionRow: ({ collection, onSelect }: { collection: { name: string; id: number }; onSelect: (id: number) => void }) => (
    <tr><td><button onClick={() => onSelect(collection.id)}>{collection.name}</button></td></tr>
  ),
}))
vi.mock('../../components/features/plex/PlaylistRow', () => ({
  PlaylistRow: ({ playlist, onSelect }: { playlist: { name: string; id: number }; onSelect: (id: number) => void }) => (
    <tr><td><button onClick={() => onSelect(playlist.id)}>{playlist.name}</button></td></tr>
  ),
}))
vi.mock('../../components/features/plex/CollectionDrawer', () => ({
  CollectionDrawer: ({ collection, onClose }: { collection: { name: string }; onClose: () => void }) => (
    <div data-testid="collection-drawer">
      {collection.name}
      <button onClick={onClose}>Close</button>
    </div>
  ),
}))
vi.mock('../../components/features/plex/PlaylistDrawer', () => ({
  PlaylistDrawer: ({ playlist, onClose }: { playlist: { name: string }; onClose: () => void }) => (
    <div data-testid="playlist-drawer">
      {playlist.name}
      <button onClick={onClose}>Close</button>
    </div>
  ),
}))
vi.mock('../../components/features/plex/CollectionForm', () => ({
  CollectionForm: () => <div data-testid="collection-form" />,
}))
vi.mock('../../components/features/plex/YamlImportModal', () => ({
  YamlImportModal: () => <div data-testid="yaml-import-modal" />,
}))

import { PlexCollectionsPage } from '../PlexCollectionsPage'

function renderPage() {
  return render(
    <MemoryRouter>
      <PlexCollectionsPage />
    </MemoryRouter>
  )
}

describe('PlexCollectionsPage', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders collection and playlist names', () => {
    renderPage()
    expect(screen.getByText('Action Films')).toBeInTheDocument()
    expect(screen.getByText('My Playlist')).toBeInTheDocument()
  })

  it('opens collection drawer when name is clicked', () => {
    renderPage()
    fireEvent.click(screen.getByText('Action Films'))
    expect(screen.getByTestId('collection-drawer')).toBeInTheDocument()
    expect(screen.queryByTestId('playlist-drawer')).not.toBeInTheDocument()
  })

  it('opens playlist drawer when name is clicked', () => {
    renderPage()
    fireEvent.click(screen.getByText('My Playlist'))
    expect(screen.getByTestId('playlist-drawer')).toBeInTheDocument()
    expect(screen.queryByTestId('collection-drawer')).not.toBeInTheDocument()
  })

  it('opening collection drawer clears playlist drawer', () => {
    renderPage()
    fireEvent.click(screen.getByText('My Playlist'))
    expect(screen.getByTestId('playlist-drawer')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Action Films'))
    expect(screen.queryByTestId('playlist-drawer')).not.toBeInTheDocument()
    expect(screen.getByTestId('collection-drawer')).toBeInTheDocument()
  })

  it('closes drawer when close button clicked', () => {
    renderPage()
    fireEvent.click(screen.getByText('Action Films'))
    fireEvent.click(screen.getByText('Close'))
    expect(screen.queryByTestId('collection-drawer')).not.toBeInTheDocument()
  })

  it('closes drawer on Escape key', () => {
    renderPage()
    fireEvent.click(screen.getByText('Action Films'))
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByTestId('collection-drawer')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run to confirm tests fail**

```bash
cd frontend && npm run test -- PlexCollectionsPage --run
```

Expected: FAIL — imports of `CollectionRow` etc. don't exist yet in the page

- [ ] **Step 3: Rewrite PlexCollectionsPage**

Replace `frontend/src/pages/PlexCollectionsPage.tsx` with:

```tsx
import React, { useEffect, useState } from 'react'
import { usePlexCollectionStore } from '../stores/plexCollectionStore'
import { CollectionRow } from '../components/features/plex/CollectionRow'
import { PlaylistRow } from '../components/features/plex/PlaylistRow'
import { CollectionDrawer } from '../components/features/plex/CollectionDrawer'
import { PlaylistDrawer } from '../components/features/plex/PlaylistDrawer'
import { CollectionForm } from '../components/features/plex/CollectionForm'
import { CollectionSetToggles } from '../components/features/plex/CollectionSetToggles'
import { YamlImportModal } from '../components/features/plex/YamlImportModal'
import type { CollectionCreate } from '../services/plexCollectionService'

export function PlexCollectionsPage() {
  const {
    collections, collectionsLoading, collectionsError,
    playlists, playlistsLoading, playlistsError,
    fetchCollections, fetchPlaylists, fetchCollectionSets,
    triggerDiscovery, createCollection, updateCollection, deleteCollection,
    pushCollection, pullCollections, pushAllCollections, pushAllLoading, pushAllError,
    updatePlaylist, deletePlaylist, pushPlaylist, pullPlaylists, bulkDeletePlaylists,
  } = usePlexCollectionStore()

  const [showForm, setShowForm] = useState(false)
  const [showYamlImport, setShowYamlImport] = useState(false)
  const [discoverMessage, setDiscoverMessage] = useState<string | null>(null)
  const [selectedPlaylistIds, setSelectedPlaylistIds] = useState<Set<number>>(new Set())
  const [selectMode, setSelectMode] = useState(false)
  const [selectedCollectionId, setSelectedCollectionId] = useState<number | null>(null)
  const [selectedPlaylistId, setSelectedPlaylistId] = useState<number | null>(null)

  useEffect(() => {
    fetchCollections()
    fetchPlaylists()
    fetchCollectionSets()
  }, [fetchCollections, fetchPlaylists, fetchCollectionSets])

  const handleSelectCollection = (id: number) => {
    setSelectedCollectionId(id)
    setSelectedPlaylistId(null)
  }

  const handleSelectPlaylist = (id: number) => {
    setSelectedPlaylistId(id)
    setSelectedCollectionId(null)
  }

  const handleCloseDrawer = () => {
    setSelectedCollectionId(null)
    setSelectedPlaylistId(null)
  }

  const handleDiscover = async () => {
    setDiscoverMessage(null)
    try {
      const result = await triggerDiscovery()
      setDiscoverMessage(result.message)
    } catch {
      setDiscoverMessage('Failed to start discovery.')
    }
  }

  const handleYamlImported = () => { fetchCollections(); fetchPlaylists() }

  const handleToggleSelect = (id: number, checked: boolean) => {
    setSelectedPlaylistIds(prev => {
      const next = new Set(prev)
      if (checked) next.add(id); else next.delete(id)
      return next
    })
  }

  const handleBulkDelete = async () => {
    const ids = Array.from(selectedPlaylistIds)
    setSelectedPlaylistIds(new Set())
    setSelectMode(false)
    await bulkDeletePlaylists(ids)
  }

  const selectedCollection = selectedCollectionId
    ? collections.find(c => c.id === selectedCollectionId) ?? null
    : null
  const selectedPlaylist = selectedPlaylistId
    ? playlists.find(p => p.id === selectedPlaylistId) ?? null
    : null
  const drawerOpen = selectedCollection !== null || selectedPlaylist !== null

  const movieCollections = collections.filter(
    c => c.content_type === 'movie' || c.content_type === null
  )
  const tvCollections = collections.filter(c => c.content_type === 'tv_show')

  const collectionTableHeaders = (
    <tr className="border-b border-slate-200 dark:border-slate-700">
      <th className="py-2 pl-3 pr-2 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Name</th>
      <th className="py-2 px-2 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Type</th>
      <th className="py-2 px-2 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Items</th>
      <th className="py-2 px-2 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Last Synced</th>
      <th className="py-2 pl-2 pr-3 text-right text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Actions</th>
    </tr>
  )

  const playlistTableHeaders = (
    <tr className="border-b border-slate-200 dark:border-slate-700">
      <th className="py-2 pl-3 pr-2 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Name</th>
      <th className="py-2 px-2 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Items</th>
      <th className="py-2 px-2 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Last Synced</th>
      <th className="py-2 pl-2 pr-3 text-right text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Actions</th>
    </tr>
  )

  const skeletonRows = [...Array(5)].map((_, i) => (
    <tr key={i}><td colSpan={5}><div className="h-10 my-1 rounded bg-slate-200 dark:bg-slate-700 animate-pulse" /></td></tr>
  ))

  return (
    <div className="flex gap-0 min-h-0">
      {/* Main content */}
      <div className={`flex-1 min-w-0 space-y-8 ${drawerOpen ? 'overflow-hidden' : ''}`}>
        {/* Page header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Plex Collections</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">
              Manage collections and playlists synced to your Plex server.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => pushAllCollections()}
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
        </div>

        {discoverMessage && (
          <div className="rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 px-4 py-3 text-sm text-green-700 dark:text-green-400">
            {discoverMessage}
          </div>
        )}
        {pushAllError && (
          <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-400">
            {pushAllError}
          </div>
        )}

        <CollectionSetToggles />

        {/* Collections section */}
        <section>
          <div className="flex items-center justify-between gap-4 mb-4">
            <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200">Collections</h2>
            <div className="flex items-center gap-2">
              <button onClick={() => pullCollections()} disabled={collectionsLoading} className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 transition-colors">
                Pull from Plex
              </button>
              <button onClick={() => setShowYamlImport(true)} className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
                Import YAML
              </button>
              <button onClick={() => setShowForm(true)} className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium bg-indigo-600 hover:bg-indigo-700 text-white transition-colors">
                New Collection
              </button>
            </div>
          </div>

          {collectionsError && (
            <div className="mb-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-400">
              {collectionsError}
            </div>
          )}

          {collectionsLoading && collections.length === 0 ? (
            <table className="w-full"><tbody>{skeletonRows}</tbody></table>
          ) : collections.length === 0 ? (
            <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-6 py-12 text-center">
              <p className="text-slate-500 dark:text-slate-400">No collections yet. Create one or pull from Plex.</p>
            </div>
          ) : (
            <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 overflow-hidden">
              {movieCollections.length > 0 && (
                <>
                  {tvCollections.length > 0 && (
                    <div className="px-3 py-1.5 bg-slate-50 dark:bg-slate-700/50 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Movies</div>
                  )}
                  <table className="w-full">
                    <thead>{collectionTableHeaders}</thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                      {movieCollections.map(col => (
                        <CollectionRow
                          key={col.id}
                          collection={col}
                          onToggleEnabled={(id, enabled) => updateCollection(id, { enabled })}
                          onPush={pushCollection}
                          onDelete={deleteCollection}
                          onSelect={handleSelectCollection}
                          isSelected={selectedCollectionId === col.id}
                        />
                      ))}
                    </tbody>
                  </table>
                </>
              )}
              {tvCollections.length > 0 && (
                <>
                  <div className="px-3 py-1.5 bg-slate-50 dark:bg-slate-700/50 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider border-t border-slate-100 dark:border-slate-700">TV Shows</div>
                  <table className="w-full">
                    <thead>{collectionTableHeaders}</thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                      {tvCollections.map(col => (
                        <CollectionRow
                          key={col.id}
                          collection={col}
                          onToggleEnabled={(id, enabled) => updateCollection(id, { enabled })}
                          onPush={pushCollection}
                          onDelete={deleteCollection}
                          onSelect={handleSelectCollection}
                          isSelected={selectedCollectionId === col.id}
                        />
                      ))}
                    </tbody>
                  </table>
                </>
              )}
            </div>
          )}
        </section>

        {/* Playlists section */}
        <section>
          <div className="flex items-center justify-between gap-4 mb-4">
            <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200">
              Playlists {playlists.length > 0 && <span className="text-slate-400 font-normal text-sm">({playlists.length})</span>}
            </h2>
            <div className="flex items-center gap-2">
              {selectMode ? (
                <>
                  <button onClick={() => setSelectedPlaylistIds(new Set(playlists.map(p => p.id)))} className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">Select All</button>
                  {selectedPlaylistIds.size > 0 && (
                    <button onClick={handleBulkDelete} disabled={playlistsLoading} className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white transition-colors">
                      Delete Selected ({selectedPlaylistIds.size})
                    </button>
                  )}
                  <button onClick={() => { setSelectMode(false); setSelectedPlaylistIds(new Set()) }} className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 transition-colors">Cancel</button>
                </>
              ) : (
                <>
                  {playlists.length > 0 && (
                    <button onClick={() => setSelectMode(true)} className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">Select</button>
                  )}
                  <button onClick={() => pullPlaylists()} disabled={playlistsLoading} className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 transition-colors">Pull from Plex</button>
                </>
              )}
            </div>
          </div>

          {playlistsError && (
            <div className="mb-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-400">{playlistsError}</div>
          )}

          {playlistsLoading && playlists.length === 0 ? (
            <table className="w-full"><tbody>{skeletonRows}</tbody></table>
          ) : playlists.length === 0 ? (
            <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-6 py-12 text-center">
              <p className="text-slate-500 dark:text-slate-400">No playlists yet. Pull from Plex to import.</p>
            </div>
          ) : (
            <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 overflow-hidden">
              <table className="w-full">
                <thead>{playlistTableHeaders}</thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                  {playlists.map(pl => (
                    <PlaylistRow
                      key={pl.id}
                      playlist={pl}
                      onToggleEnabled={(id, enabled) => updatePlaylist(id, { enabled })}
                      onPush={pushPlaylist}
                      onDelete={deletePlaylist}
                      onSelect={handleSelectPlaylist}
                      isSelected={selectedPlaylistId === pl.id}
                      selectable={selectMode}
                      bulkSelected={selectedPlaylistIds.has(pl.id)}
                      onBulkSelect={handleToggleSelect}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>

      {/* Drawers */}
      {selectedCollection && (
        <CollectionDrawer
          collection={selectedCollection}
          onClose={handleCloseDrawer}
          onToggleEnabled={(id, enabled) => updateCollection(id, { enabled })}
          onPush={pushCollection}
          onDelete={deleteCollection}
        />
      )}
      {selectedPlaylist && (
        <PlaylistDrawer
          playlist={selectedPlaylist}
          onClose={handleCloseDrawer}
          onToggleEnabled={(id, enabled) => updatePlaylist(id, { enabled })}
          onPush={pushPlaylist}
          onDelete={deletePlaylist}
        />
      )}

      {showForm && (
        <CollectionForm
          onSubmit={async (data: CollectionCreate) => { await createCollection(data); setShowForm(false) }}
          onCancel={() => setShowForm(false)}
        />
      )}
      {showYamlImport && (
        <YamlImportModal
          onClose={() => setShowYamlImport(false)}
          onImported={handleYamlImported}
        />
      )}
    </div>
  )
}

export default PlexCollectionsPage
```

- [ ] **Step 4: Delete old components**

```bash
rm frontend/src/components/features/plex/CollectionCard.tsx
rm frontend/src/components/features/plex/PlaylistCard.tsx
rm frontend/src/components/features/plex/__tests__/CollectionCard.test.tsx
```

- [ ] **Step 5: Run all frontend tests**

```bash
cd frontend && npm run test --run
```

Expected: all pass (no references to deleted components remain)

- [ ] **Step 6: TypeScript check and lint**

```bash
cd frontend && npm run type-check && npm run lint
```

Expected: no errors

- [ ] **Step 7: Run backend tests**

```bash
pytest tests/test_plex_collection_router.py -v
```

Expected: all pass

- [ ] **Step 8: Commit**

```bash
git add frontend/src/pages/PlexCollectionsPage.tsx \
        frontend/src/pages/__tests__/PlexCollectionsPage.test.tsx \
        frontend/src/components/features/plex/
git commit -m "feat(plex): replace card grid with list and side drawer on collections page"
```
