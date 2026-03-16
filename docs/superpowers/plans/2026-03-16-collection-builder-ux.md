# Collection Builder UX Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the raw JSON textarea in the collection builder form with friendly per-category UI controls — a movie picker for Custom, TMDB collection search for TMDB, pill buttons for Genre, and a decade grid for Decade.

**Architecture:** Three new backend endpoints serve the data each category needs. The frontend `CollectionForm.tsx` is replaced with a thin orchestrator that renders one of four sub-components based on the selected category. Each sub-component manages its own display state and calls a parent callback to update the shared form state. The `CollectionCreate` payload shape is unchanged.

**Tech Stack:** FastAPI, SQLAlchemy, httpx (backend); React, TypeScript, Zustand, Tailwind CSS (frontend); Vitest + React Testing Library (frontend tests); pytest (backend tests).

**Spec:** `docs/superpowers/specs/2026-03-16-collection-builder-ux-design.md`

---

## File Map

**Backend — new/modified:**
- `app/domain/plex/collection_builder.py` — fix `resolve_genre()` to movies only
- `app/api/v1/movies/endpoints.py` — add `GET /genres` (before `/{movie_id}`)
- `app/api/v1/plex/collection_router.py` — add `/tmdb-collections/local` and `/tmdb-collections/search`
- `tests/test_plex_collection_builder.py` — add genre-movies-only test
- `tests/test_plex_collection_router.py` — add tests for two new plex endpoints
- `tests/test_movies_endpoints.py` (or nearest movies test file) — add genres endpoint test

**Frontend — new:**
- `frontend/src/components/features/plex/DecadeBuilder.tsx`
- `frontend/src/components/features/plex/GenreBuilder.tsx`
- `frontend/src/components/features/plex/CustomBuilder.tsx`
- `frontend/src/components/features/plex/TmdbCollectionBuilder.tsx`

**Frontend — modified:**
- `frontend/src/components/features/plex/CollectionForm.tsx` — full rewrite
- `frontend/src/services/movieService.ts` — add `getMovieGenres()`
- `frontend/src/services/plexCollectionService.ts` — add `getLocalTmdbCollections()`, `searchTmdbCollections()`

---

## Chunk 1: Backend

### Task 1: Fix resolve_genre() to movies only

**Files:**
- Modify: `app/domain/plex/collection_builder.py`
- Test: `tests/test_plex_collection_builder.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_plex_collection_builder.py`:

```python
@pytest.mark.unit
def test_resolve_genre_excludes_tv_shows(db_session):
    """resolve_genre must return only movies, not TV shows."""
    import json
    from app.domain.movies.models import Movie
    from app.domain.tv_shows.models import TVShow
    from app.domain.plex.models import PlexConnection, PlexSyncRecord, PlexSyncStatus

    conn = PlexConnection(
        name="test", url="http://x", token="t", machine_identifier="m"
    )
    db_session.add(conn)
    db_session.flush()

    movie = Movie(
        title="Action Movie",
        file_path="/m/action.mkv",
        genres=json.dumps(["Action"]),
    )
    show = TVShow(
        title="Action Show",
        directory_path="/tv/action",
        genres=json.dumps(["Action"]),
    )
    db_session.add_all([movie, show])
    db_session.flush()

    movie_record = PlexSyncRecord(
        connection_id=conn.id,
        item_type="movie",
        item_id=movie.id,
        plex_rating_key="111",
        status=PlexSyncStatus.SYNCED,
    )
    show_record = PlexSyncRecord(
        connection_id=conn.id,
        item_type="tv_show",
        item_id=show.id,
        plex_rating_key="222",
        status=PlexSyncStatus.SYNCED,
    )
    db_session.add_all([movie_record, show_record])
    db_session.flush()

    resolver = BuilderResolver(db=db_session, connection_id=conn.id)
    results = resolver.resolve_genre({"genre": "Action"})

    assert len(results) == 1
    assert results[0].plex_rating_key == "111"
    assert results[0].item_type == "movie"
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
cd /Users/john/Code/Metamaster/.worktrees/fix-plex-nav
pytest tests/test_plex_collection_builder.py::test_resolve_genre_excludes_tv_shows -v
```

Expected: FAIL — the test will find 2 results instead of 1.

- [ ] **Step 3: Fix resolve_genre() to movies only**

In `app/domain/plex/collection_builder.py`, replace the `resolve_genre` method:

```python
def resolve_genre(self, config: Dict[str, Any]) -> List[ResolvedItem]:
    """Return synced movies matching the given genre (movies only)."""
    genre = config["genre"]
    return self._resolve_genre_for_model(genre, Movie, "movie")
```

Also remove the unused `TVShow` import if it is no longer referenced elsewhere in the file. Check first:

```bash
grep -n "TVShow" app/domain/plex/collection_builder.py
```

If `TVShow` only appears in the `resolve_genre` method and the import, remove the import line:
```python
from app.domain.tv_shows.models import TVShow  # DELETE this line
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
pytest tests/test_plex_collection_builder.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add app/domain/plex/collection_builder.py tests/test_plex_collection_builder.py
git commit -m "fix(plex): scope genre collections to movies only"
```

---

### Task 2: Add GET /api/v1/movies/genres endpoint

**Files:**
- Modify: `app/api/v1/movies/endpoints.py`
- Test: nearest movies test file (search for `test_movies` or `test_movie_endpoints`)

- [ ] **Step 1: Find the existing movies endpoint test file**

```bash
find tests/ -name "*movie*" | grep -v __pycache__
```

- [ ] **Step 2: Write the failing test**

Add to the movies endpoint test file:

```python
def test_get_genres_returns_sorted_deduplicated_list(client, db_session):
    """GET /movies/genres returns sorted, deduplicated genres from movie library."""
    import json
    from app.domain.movies.models import Movie

    db_session.add(Movie(
        title="Film A", file_path="/m/a.mkv",
        genres=json.dumps(["Action", "Thriller"]),
    ))
    db_session.add(Movie(
        title="Film B", file_path="/m/b.mkv",
        genres=json.dumps(["Action", "Comedy"]),
    ))
    db_session.add(Movie(
        title="Film C", file_path="/m/c.mkv",
        genres=None,  # no genres — must be excluded
    ))
    db_session.commit()

    response = client.get("/api/v1/movies/genres")
    assert response.status_code == 200
    data = response.json()
    assert data["genres"] == ["Action", "Comedy", "Thriller"]  # sorted, deduped
```

- [ ] **Step 3: Run test to confirm it fails**

```bash
pytest tests/<movies-test-file>.py::test_get_genres_returns_sorted_deduplicated_list -v
```

Expected: FAIL — endpoint does not exist yet (404).

- [ ] **Step 4: Add the endpoint**

In `app/api/v1/movies/endpoints.py`, add the following **immediately after the `router = APIRouter(...)` line and before `@router.get("/enrichment-stats")`** (i.e. as the very first route registered, to avoid being shadowed by `/{movie_id}`):

```python
@router.get("/genres")
def get_movie_genres(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Return a sorted, deduplicated list of genres from the movie library."""
    import json as _json

    rows = db.query(MovieModel.genres).filter(MovieModel.genres.isnot(None)).all()
    genre_set: set = set()
    for (raw,) in rows:
        try:
            genres = _json.loads(raw or "[]")
            genre_set.update(genres)
        except (ValueError, TypeError):
            continue
    return {"genres": sorted(genre_set)}
```

Also add the `get_current_user` import at the top of the file if not already present:
```python
from app.api.v1.auth.endpoints import get_current_user
```

Check first: `grep "get_current_user" app/api/v1/movies/endpoints.py`

- [ ] **Step 5: Run tests**

```bash
pytest tests/<movies-test-file>.py -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add app/api/v1/movies/endpoints.py tests/<movies-test-file>.py
git commit -m "feat(movies): add GET /movies/genres endpoint"
```

---

### Task 3: Add GET /plex/tmdb-collections/local endpoint

**Files:**
- Modify: `app/api/v1/plex/collection_router.py`
- Test: `tests/test_plex_collection_router.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_plex_collection_router.py`:

```python
def test_get_local_tmdb_collections_groups_by_collection(db):
    """Returns movies grouped by tmdb_collection_id, sorted by count desc."""
    from app.domain.movies.models import Movie

    db.add(Movie(
        title="Batman Begins", file_path="/m/bb.mkv",
        tmdb_collection_id=263, tmdb_collection_name="The Dark Knight Collection",
    ))
    db.add(Movie(
        title="The Dark Knight", file_path="/m/tdk.mkv",
        tmdb_collection_id=263, tmdb_collection_name="The Dark Knight Collection",
    ))
    db.add(Movie(
        title="Inception", file_path="/m/inc.mkv",
        tmdb_collection_id=536, tmdb_collection_name="Inception Collection",
    ))
    db.add(Movie(title="No Collection", file_path="/m/nc.mkv"))
    db.commit()

    response = client.get("/api/v1/plex/tmdb-collections/local")
    assert response.status_code == 200
    data = response.json()
    # sorted by movie_count desc: 263 (2) before 536 (1)
    assert len(data) == 2
    assert data[0]["tmdb_collection_id"] == 263
    assert data[0]["movie_count"] == 2
    assert data[0]["name"] == "The Dark Knight Collection"
    assert data[1]["tmdb_collection_id"] == 536
    assert data[1]["movie_count"] == 1


def test_get_local_tmdb_collections_fallback_name(db):
    """Falls back to 'Collection {id}' when tmdb_collection_name is None."""
    from app.domain.movies.models import Movie

    db.add(Movie(
        title="Mystery Film", file_path="/m/myst.mkv",
        tmdb_collection_id=999, tmdb_collection_name=None,
    ))
    db.commit()

    response = client.get("/api/v1/plex/tmdb-collections/local")
    assert response.status_code == 200
    names = [item["name"] for item in response.json()]
    assert "Collection 999" in names
```

Note: if the test file uses a `db` fixture that auto-rollbacks, use it. Check the existing fixture names at the top of `test_plex_collection_router.py`.

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_plex_collection_router.py::test_get_local_tmdb_collections_groups_by_collection -v
pytest tests/test_plex_collection_router.py::test_get_local_tmdb_collections_fallback_name -v
```

Expected: FAIL — 404.

- [ ] **Step 3: Add the endpoint**

In `app/api/v1/plex/collection_router.py`, add this after the imports and before the first route. Also add `MovieModel` import:

```python
from app.domain.movies.models import Movie as MovieModel
```

Then add the endpoint (place it near other GET collection endpoints):

```python
@router.get("/tmdb-collections/local")
def get_local_tmdb_collections(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Return TMDB collections that are already matched in the local movie library."""
    from sqlalchemy import func

    rows = (
        db.query(
            MovieModel.tmdb_collection_id,
            MovieModel.tmdb_collection_name,
            func.count(MovieModel.id).label("movie_count"),
        )
        .filter(MovieModel.tmdb_collection_id.isnot(None))
        .group_by(MovieModel.tmdb_collection_id, MovieModel.tmdb_collection_name)
        .order_by(func.count(MovieModel.id).desc(), MovieModel.tmdb_collection_id.asc())
        .all()
    )

    seen: dict = {}
    results = []
    for tmdb_id, name, count in rows:
        if tmdb_id not in seen:
            seen[tmdb_id] = True
            results.append({
                "tmdb_collection_id": tmdb_id,
                "name": name or f"Collection {tmdb_id}",
                "movie_count": count,
            })
    return results
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_plex_collection_router.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/plex/collection_router.py tests/test_plex_collection_router.py
git commit -m "feat(plex): add GET /plex/tmdb-collections/local endpoint"
```

---

### Task 4: Add GET /plex/tmdb-collections/search endpoint

**Files:**
- Modify: `app/api/v1/plex/collection_router.py`
- Test: `tests/test_plex_collection_router.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_plex_collection_router.py`:

```python
def test_search_tmdb_collections_returns_results(monkeypatch):
    """Proxies to TMDB and returns id + name list."""
    import httpx

    fake_response_data = {
        "results": [
            {"id": 9485, "name": "Christopher Nolan Collection"},
            {"id": 948, "name": "Batman Collection"},
        ]
    }

    async def mock_get(self, url, **kwargs):
        mock = MagicMock()
        mock.raise_for_status = MagicMock()
        mock.json.return_value = fake_response_data
        return mock

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    # Patch settings so TMDB token is set
    with patch("app.api.v1.plex.collection_router.settings") as mock_settings:
        mock_settings.tmdb_read_access_token = "fake-token"
        mock_settings.tmdb_api_key = None
        response = client.get("/api/v1/plex/tmdb-collections/search?q=nolan")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0] == {"id": 9485, "name": "Christopher Nolan Collection"}


def test_search_tmdb_collections_returns_503_when_no_credentials(monkeypatch):
    """Returns 503 when no TMDB credentials are configured."""
    with patch("app.api.v1.plex.collection_router.settings") as mock_settings:
        mock_settings.tmdb_read_access_token = None
        mock_settings.tmdb_api_key = None
        response = client.get("/api/v1/plex/tmdb-collections/search?q=batman")

    assert response.status_code == 503
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_plex_collection_router.py::test_search_tmdb_collections_returns_results -v
pytest tests/test_plex_collection_router.py::test_search_tmdb_collections_returns_503_when_no_credentials -v
```

Expected: FAIL — 404.

- [ ] **Step 3: Add the async endpoint**

First add the required imports to `app/api/v1/plex/collection_router.py`:

```python
import httpx
from app.core.config import settings
```

Then add the endpoint (note: this is the only `async def` in the file — that is intentional):

```python
@router.get("/tmdb-collections/search")
async def search_tmdb_collections(
    q: str = Query(..., min_length=1),
    _: object = Depends(get_current_user),
):
    """Proxy to TMDB collection search API."""
    if settings.tmdb_read_access_token:
        headers = {"Authorization": f"Bearer {settings.tmdb_read_access_token}"}
        params = {"query": q}
    elif settings.tmdb_api_key:
        headers = {}
        params = {"query": q, "api_key": settings.tmdb_api_key}
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TMDB API key not configured",
        )

    async with httpx.AsyncClient() as client_http:
        resp = await client_http.get(
            "https://api.themoviedb.org/3/search/collection",
            headers=headers,
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()

    return [
        {"id": item["id"], "name": item["name"]}
        for item in data.get("results", [])
    ]
```

Also add `Query` to the fastapi imports at the top:
```python
from fastapi import APIRouter, Depends, HTTPException, Query, status
```

- [ ] **Step 4: Run all backend tests**

```bash
pytest tests/test_plex_collection_router.py tests/test_plex_collection_builder.py -v
```

Expected: all pass.

- [ ] **Step 5: Run full backend lint**

```bash
cd /Users/john/Code/Metamaster/.worktrees/fix-plex-nav
black app/ tests/ && isort app/ tests/ && flake8 app/ tests/ && mypy app/
```

Fix any issues before committing.

- [ ] **Step 6: Commit**

```bash
git add app/api/v1/plex/collection_router.py tests/test_plex_collection_router.py
git commit -m "feat(plex): add TMDB collection search and local-match endpoints"
```

---

## Chunk 2: Frontend Services

### Task 5: Add getMovieGenres() to movieService.ts

**Files:**
- Modify: `frontend/src/services/movieService.ts`

- [ ] **Step 1: Add the function**

In `frontend/src/services/movieService.ts`, add inside the `movieService` object (after the last existing method):

```typescript
getMovieGenres: async (): Promise<string[]> => {
  try {
    const response = await apiClient.get<{ genres: string[] }>('/movies/genres')
    return response.data.genres
  } catch (error) {
    errorHandler.handleError(error, 'getMovieGenres')
    throw error
  }
},
```

- [ ] **Step 2: Run lint + type-check**

```bash
cd /Users/john/Code/Metamaster/.worktrees/fix-plex-nav/frontend
npm run lint && npm run type-check
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/movieService.ts
git commit -m "feat(frontend): add getMovieGenres service function"
```

---

### Task 6: Add TMDB collection service functions to plexCollectionService.ts

**Files:**
- Modify: `frontend/src/services/plexCollectionService.ts`

- [ ] **Step 1: Add the types and functions**

First add the new types near the top of `frontend/src/services/plexCollectionService.ts` (after existing type definitions):

```typescript
export interface LocalTmdbCollection {
  tmdb_collection_id: number
  name: string
  movie_count: number
}

export interface TmdbCollectionSearchResult {
  id: number
  name: string
}
```

Then add the functions at the bottom of the file (before `export default` if one exists, otherwise just append):

```typescript
export async function getLocalTmdbCollections(): Promise<LocalTmdbCollection[]> {
  const response = await apiClient.get<LocalTmdbCollection[]>('/plex/tmdb-collections/local')
  return response.data
}

export async function searchTmdbCollections(q: string): Promise<TmdbCollectionSearchResult[]> {
  const response = await apiClient.get<TmdbCollectionSearchResult[]>(
    `/plex/tmdb-collections/search?q=${encodeURIComponent(q)}`
  )
  return response.data
}
```

- [ ] **Step 2: Run lint + type-check**

```bash
cd /Users/john/Code/Metamaster/.worktrees/fix-plex-nav/frontend
npm run lint && npm run type-check
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/plexCollectionService.ts
git commit -m "feat(frontend): add TMDB collection service functions"
```

---

## Chunk 3: Frontend Sub-components

### Task 7: DecadeBuilder component

**Files:**
- Create: `frontend/src/components/features/plex/DecadeBuilder.tsx`

- [ ] **Step 1: Create the component**

```tsx
import React from 'react'

const DECADES = [1960, 1970, 1980, 1990, 2000, 2010, 2020]

interface DecadeBuilderProps {
  selected: number | null
  onSelect: (decade: number) => void
}

export function DecadeBuilder({ selected, onSelect }: DecadeBuilderProps) {
  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-4">
      <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3">
        Choose one decade
      </p>
      <div className="grid grid-cols-4 gap-2">
        {DECADES.map((decade) => (
          <button
            key={decade}
            type="button"
            onClick={() => onSelect(decade)}
            className={`rounded-lg py-2.5 text-sm font-medium text-center transition-colors ${
              selected === decade
                ? 'bg-indigo-600 text-white border-2 border-indigo-600'
                : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-indigo-400 dark:hover:border-indigo-500'
            }`}
          >
            {decade}s
          </button>
        ))}
        <button
          type="button"
          disabled
          className="rounded-lg py-2.5 text-sm text-center text-slate-300 dark:text-slate-600 border border-dashed border-slate-200 dark:border-slate-700 cursor-not-allowed"
        >
          2030s
        </button>
      </div>
      <p className="text-xs text-slate-400 dark:text-slate-500 mt-3">
        One decade per collection · Movies only
      </p>
    </div>
  )
}

export default DecadeBuilder
```

- [ ] **Step 2: Lint + type-check**

```bash
cd /Users/john/Code/Metamaster/.worktrees/fix-plex-nav/frontend
npm run lint && npm run type-check
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/features/plex/DecadeBuilder.tsx
git commit -m "feat(plex): add DecadeBuilder component"
```

---

### Task 8: GenreBuilder component

**Files:**
- Create: `frontend/src/components/features/plex/GenreBuilder.tsx`

- [ ] **Step 1: Create the component**

```tsx
import React, { useEffect, useState } from 'react'
import { movieService } from '../../../services/movieService'
import LoadingSpinner from '@/components/common/LoadingSpinner'

interface GenreBuilderProps {
  selected: string | null
  onSelect: (genre: string) => void
}

export function GenreBuilder({ selected, onSelect }: GenreBuilderProps) {
  const [genres, setGenres] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    movieService.getMovieGenres()
      .then(setGenres)
      .catch(() => setError('Failed to load genres'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-4">
      <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3">
        Choose one genre
      </p>
      {loading && <LoadingSpinner />}
      {error && <p className="text-sm text-red-500">{error}</p>}
      {!loading && !error && (
        <div className="flex flex-wrap gap-2">
          {genres.map((genre) => (
            <button
              key={genre}
              type="button"
              onClick={() => onSelect(genre)}
              className={`rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors ${
                selected === genre
                  ? 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 border-2 border-indigo-500'
                  : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-indigo-400 dark:hover:border-indigo-500'
              }`}
            >
              {genre}
            </button>
          ))}
        </div>
      )}
      <p className="text-xs text-slate-400 dark:text-slate-500 mt-3">
        One genre per collection · Movies only · From your library
      </p>
    </div>
  )
}

export default GenreBuilder
```

- [ ] **Step 2: Lint + type-check**

```bash
cd /Users/john/Code/Metamaster/.worktrees/fix-plex-nav/frontend
npm run lint && npm run type-check
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/features/plex/GenreBuilder.tsx
git commit -m "feat(plex): add GenreBuilder component"
```

---

### Task 9: CustomBuilder component

**Files:**
- Create: `frontend/src/components/features/plex/CustomBuilder.tsx`

- [ ] **Step 1: Create the component**

```tsx
import React, { useState, useRef } from 'react'
import { FaSearch, FaTimes } from 'react-icons/fa'
import { movieService } from '../../../services/movieService'
import { TextInput } from '@/components/common/TextInput'
import { Button } from '@/components/common/Button'
import type { Movie } from '@/types'

export interface SelectedMovie {
  tmdb_id: string
  title: string
}

interface CustomBuilderProps {
  selected: SelectedMovie[]
  onAdd: (movie: SelectedMovie) => void
  onRemove: (tmdbId: string) => void
}

function useDebounce(value: string, delay: number) {
  const [debounced, setDebounced] = useState(value)
  const timer = useRef<ReturnType<typeof setTimeout>>()
  const update = (v: string) => {
    clearTimeout(timer.current)
    timer.current = setTimeout(() => setDebounced(v), delay)
  }
  return [debounced, update] as const
}

export function CustomBuilder({ selected, onAdd, onRemove }: CustomBuilderProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Movie[]>([])
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [, triggerSearch] = useDebounce('', 300)

  const selectedIds = new Set(selected.map((s) => s.tmdb_id))

  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setQuery(val)
    if (val.length < 2) {
      setResults([])
      return
    }
    triggerSearch(val)
    setSearching(true)
    setSearchError(null)
    movieService.searchMovies(val, 1, 8)
      .then((data) => setResults(data.results ?? []))
      .catch(() => setSearchError('Search failed'))
      .finally(() => setSearching(false))
  }

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-4 space-y-3">
      <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
        Search your library
      </p>

      <TextInput
        placeholder="Search movies..."
        value={query}
        onChange={handleQueryChange}
        leftIcon={<FaSearch className="w-3.5 h-3.5" />}
        type="search"
      />

      {searchError && <p className="text-sm text-red-500">{searchError}</p>}

      {results.length > 0 && (
        <div className="rounded-lg border border-slate-200 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700 overflow-hidden">
          {results.map((movie) => {
            const alreadyAdded = movie.tmdb_id ? selectedIds.has(movie.tmdb_id) : false
            const noId = !movie.tmdb_id
            return (
              <div
                key={movie.id}
                className="flex items-center justify-between px-3 py-2 bg-white dark:bg-slate-800"
              >
                <span className="text-sm text-slate-700 dark:text-slate-200">
                  🎬 {movie.title}
                  {movie.year && (
                    <span className="text-slate-400 dark:text-slate-500 ml-1">({movie.year})</span>
                  )}
                </span>
                <Button
                  size="sm"
                  variant={alreadyAdded ? 'secondary' : 'primary'}
                  disabled={alreadyAdded || noId}
                  title={noId ? 'Not yet enriched — no TMDB ID' : undefined}
                  onClick={() => {
                    if (movie.tmdb_id) {
                      onAdd({ tmdb_id: movie.tmdb_id, title: movie.title })
                    }
                  }}
                >
                  {alreadyAdded ? 'Added' : 'Add'}
                </Button>
              </div>
            )
          })}
        </div>
      )}

      {selected.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 mb-1.5">
            Selected ({selected.length})
          </p>
          <div className="flex flex-wrap gap-1.5">
            {selected.map((m) => (
              <span
                key={m.tmdb_id}
                className="inline-flex items-center gap-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 px-2.5 py-1 rounded-full text-xs font-medium"
              >
                {m.title}
                <button
                  type="button"
                  onClick={() => onRemove(m.tmdb_id)}
                  className="text-indigo-400 hover:text-indigo-600 dark:hover:text-indigo-200 ml-0.5"
                  aria-label={`Remove ${m.title}`}
                >
                  <FaTimes className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default CustomBuilder
```

- [ ] **Step 2: Lint + type-check**

```bash
cd /Users/john/Code/Metamaster/.worktrees/fix-plex-nav/frontend
npm run lint && npm run type-check
```

Fix any lint errors before proceeding.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/features/plex/CustomBuilder.tsx
git commit -m "feat(plex): add CustomBuilder movie picker component"
```

---

### Task 10: TmdbCollectionBuilder component

**Files:**
- Create: `frontend/src/components/features/plex/TmdbCollectionBuilder.tsx`

- [ ] **Step 1: Create the component**

```tsx
import React, { useEffect, useState, useRef } from 'react'
import { FaSearch } from 'react-icons/fa'
import {
  getLocalTmdbCollections,
  searchTmdbCollections,
  type LocalTmdbCollection,
  type TmdbCollectionSearchResult,
} from '../../../services/plexCollectionService'
import { TextInput } from '@/components/common/TextInput'
import { Button } from '@/components/common/Button'
import LoadingSpinner from '@/components/common/LoadingSpinner'

export interface SelectedTmdbCollection {
  id: number
  name: string
  description: string
}

interface TmdbCollectionBuilderProps {
  selected: SelectedTmdbCollection | null
  onSelect: (collection: SelectedTmdbCollection) => void
  onRemove: () => void
}

export function TmdbCollectionBuilder({ selected, onSelect, onRemove }: TmdbCollectionBuilderProps) {
  const [local, setLocal] = useState<LocalTmdbCollection[]>([])
  const [localLoading, setLocalLoading] = useState(true)
  const [localError, setLocalError] = useState<string | null>(null)

  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<TmdbCollectionSearchResult[]>([])
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const searchTimer = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    getLocalTmdbCollections()
      .then(setLocal)
      .catch(() => setLocalError('Failed to load library matches'))
      .finally(() => setLocalLoading(false))
  }, [])

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setSearchQuery(val)
    clearTimeout(searchTimer.current)
    if (!val) { setSearchResults([]); return }
    searchTimer.current = setTimeout(() => {
      setSearching(true)
      setSearchError(null)
      searchTmdbCollections(val)
        .then(setSearchResults)
        .catch(() => setSearchError('TMDB search failed'))
        .finally(() => setSearching(false))
    }, 500)
  }

  const isSelected = (id: number) => selected?.id === id

  const handleSelectLocal = (col: LocalTmdbCollection) => {
    onSelect({ id: col.tmdb_collection_id, name: col.name, description: '' })
  }

  const handleSelectSearch = (col: TmdbCollectionSearchResult) => {
    onSelect({ id: col.id, name: col.name, description: '' })
  }

  return (
    <div className="space-y-3">
      {/* Local matches */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-4">
        <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3">
          Matched in your library
        </p>
        {localLoading && <LoadingSpinner />}
        {localError && <p className="text-sm text-red-500">{localError}</p>}
        {!localLoading && !localError && local.length === 0 && (
          <p className="text-sm text-slate-400 dark:text-slate-500">
            No TMDB collections matched in your library yet.
          </p>
        )}
        {!localLoading && local.length > 0 && (
          <div className="rounded-lg border border-slate-200 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700 overflow-hidden">
            {local.map((col) => (
              <div
                key={col.tmdb_collection_id}
                className={`flex items-center justify-between px-3 py-2.5 ${
                  isSelected(col.tmdb_collection_id)
                    ? 'bg-green-50 dark:bg-green-900/20'
                    : 'bg-white dark:bg-slate-800'
                }`}
              >
                <div>
                  <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{col.name}</p>
                  <p className="text-xs text-slate-400">ID {col.tmdb_collection_id} · {col.movie_count} film{col.movie_count !== 1 ? 's' : ''} in library</p>
                </div>
                {isSelected(col.tmdb_collection_id) ? (
                  <Button size="sm" variant="outline" onClick={onRemove}>Remove</Button>
                ) : (
                  <Button size="sm" onClick={() => handleSelectLocal(col)}>Select</Button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* TMDB search */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-4">
        <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3">
          Search TMDB
        </p>
        <TextInput
          placeholder="e.g. Batman, James Bond..."
          value={searchQuery}
          onChange={handleSearchChange}
          leftIcon={<FaSearch className="w-3.5 h-3.5" />}
          type="search"
        />
        {searching && <div className="mt-2"><LoadingSpinner /></div>}
        {searchError && <p className="text-sm text-red-500 mt-2">{searchError}</p>}
        {!searching && searchResults.length > 0 && (
          <div className="mt-2 rounded-lg border border-slate-200 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700 overflow-hidden">
            {searchResults.map((col) => (
              <div
                key={col.id}
                className={`flex items-center justify-between px-3 py-2.5 ${
                  isSelected(col.id) ? 'bg-green-50 dark:bg-green-900/20' : 'bg-white dark:bg-slate-800'
                }`}
              >
                <div>
                  <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{col.name}</p>
                  <p className="text-xs text-slate-400">ID {col.id}</p>
                </div>
                {isSelected(col.id) ? (
                  <Button size="sm" variant="outline" onClick={onRemove}>Remove</Button>
                ) : (
                  <Button size="sm" onClick={() => handleSelectSearch(col)}>Select</Button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default TmdbCollectionBuilder
```

- [ ] **Step 2: Lint + type-check**

```bash
cd /Users/john/Code/Metamaster/.worktrees/fix-plex-nav/frontend
npm run lint && npm run type-check
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/features/plex/TmdbCollectionBuilder.tsx
git commit -m "feat(plex): add TmdbCollectionBuilder component"
```

---

## Chunk 4: CollectionForm Rewrite

### Task 11: Rewrite CollectionForm.tsx

**Files:**
- Modify: `frontend/src/components/features/plex/CollectionForm.tsx`

- [ ] **Step 1: Replace CollectionForm.tsx**

```tsx
import React, { useState } from 'react'
import { FaTimes } from 'react-icons/fa'
import type { CollectionCreate, BuilderType } from '../../../services/plexCollectionService'
import { TextInput } from '@/components/common/TextInput'
import { Select } from '@/components/common/Select'
import { Button } from '@/components/common/Button'
import { DecadeBuilder } from './DecadeBuilder'
import { GenreBuilder } from './GenreBuilder'
import { CustomBuilder, type SelectedMovie } from './CustomBuilder'
import { TmdbCollectionBuilder, type SelectedTmdbCollection } from './TmdbCollectionBuilder'

interface CollectionFormProps {
  onSubmit: (data: CollectionCreate) => void
  onCancel: () => void
}

const CATEGORY_OPTIONS = [
  { value: 'static_items', label: 'Custom' },
  { value: 'tmdb_collection', label: 'TMDB Collection' },
  { value: 'genre', label: 'Genre' },
  { value: 'decade', label: 'Decade' },
]

const AUTO_NAME_BANNERS: Partial<Record<BuilderType, string>> = {
  tmdb_collection: 'Name and description will be pulled automatically from the TMDB collection you select.',
  genre: 'This collection will be named after the genre you pick, e.g. "Action". Movies only.',
  decade: 'This collection will be named after the decade you pick, e.g. "2010s Movies". Movies only.',
}

function InfoBanner({ text }: { text: string }) {
  return (
    <div className="flex gap-2 items-start bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg px-3 py-2.5">
      <svg className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p className="text-xs text-blue-700 dark:text-blue-300 leading-relaxed">{text}</p>
    </div>
  )
}

function isValid(
  category: BuilderType,
  name: string,
  selectedMovies: SelectedMovie[],
  selectedGenre: string | null,
  selectedDecade: number | null,
  selectedTmdb: SelectedTmdbCollection | null,
): boolean {
  if (category === 'static_items') return name.trim().length > 0 && selectedMovies.length > 0
  if (category === 'genre') return selectedGenre !== null
  if (category === 'decade') return selectedDecade !== null
  if (category === 'tmdb_collection') return selectedTmdb !== null
  return false
}

function buildPayload(
  category: BuilderType,
  name: string,
  description: string,
  selectedMovies: SelectedMovie[],
  selectedGenre: string | null,
  selectedDecade: number | null,
  selectedTmdb: SelectedTmdbCollection | null,
): CollectionCreate {
  if (category === 'static_items') {
    return {
      name: name.trim(),
      description: description.trim() || undefined,
      builder_type: 'static_items',
      builder_config: {
        items: selectedMovies.map((m) => ({ tmdb_id: m.tmdb_id, item_type: 'movie' })),
      },
    }
  }
  if (category === 'genre' && selectedGenre) {
    return {
      name: selectedGenre,
      builder_type: 'genre',
      builder_config: { genre: selectedGenre },
    }
  }
  if (category === 'decade' && selectedDecade !== null) {
    return {
      name: `${selectedDecade}s Movies`,
      builder_type: 'decade',
      builder_config: { decade: selectedDecade },
    }
  }
  // tmdb_collection
  return {
    name: selectedTmdb?.name ?? '',
    description: selectedTmdb?.description || undefined,
    builder_type: 'tmdb_collection',
    builder_config: { tmdb_collection_id: selectedTmdb?.id },
  }
}

export function CollectionForm({ onSubmit, onCancel }: CollectionFormProps) {
  const [category, setCategory] = useState<BuilderType>('static_items')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [selectedMovies, setSelectedMovies] = useState<SelectedMovie[]>([])
  const [selectedGenre, setSelectedGenre] = useState<string | null>(null)
  const [selectedDecade, setSelectedDecade] = useState<number | null>(null)
  const [selectedTmdb, setSelectedTmdb] = useState<SelectedTmdbCollection | null>(null)

  const handleCategoryChange = (val: string) => {
    setCategory(val as BuilderType)
    setSelectedMovies([])
    setSelectedGenre(null)
    setSelectedDecade(null)
    setSelectedTmdb(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(buildPayload(category, name, description, selectedMovies, selectedGenre, selectedDecade, selectedTmdb))
  }

  const valid = isValid(category, name, selectedMovies, selectedGenre, selectedDecade, selectedTmdb)
  const bannerText = AUTO_NAME_BANNERS[category]
  const isCustom = category === 'static_items'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-xl rounded-xl bg-white dark:bg-slate-800 shadow-xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex-shrink-0">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">New Collection</h2>
          <button
            type="button"
            onClick={onCancel}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
            aria-label="Close"
          >
            <FaTimes className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable body */}
        <form onSubmit={handleSubmit} className="flex flex-col flex-1 min-h-0">
          <div className="px-6 py-4 space-y-4 overflow-y-auto max-h-[70vh]">
            {/* Name + Description — only for Custom */}
            {isCustom && (
              <>
                <TextInput
                  label="Name"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="My Collection"
                />
                <TextInput
                  label="Description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Optional description"
                />
              </>
            )}

            {/* Auto-name info banner */}
            {bannerText && <InfoBanner text={bannerText} />}

            {/* Category dropdown */}
            <Select
              label="Category"
              required
              options={CATEGORY_OPTIONS}
              value={category}
              onChange={handleCategoryChange}
            />

            {/* Per-category builder */}
            {category === 'static_items' && (
              <CustomBuilder
                selected={selectedMovies}
                onAdd={(m) => setSelectedMovies((prev) => [...prev, m])}
                onRemove={(id) => setSelectedMovies((prev) => prev.filter((m) => m.tmdb_id !== id))}
              />
            )}
            {category === 'tmdb_collection' && (
              <TmdbCollectionBuilder
                selected={selectedTmdb}
                onSelect={setSelectedTmdb}
                onRemove={() => setSelectedTmdb(null)}
              />
            )}
            {category === 'genre' && (
              <GenreBuilder
                selected={selectedGenre}
                onSelect={setSelectedGenre}
              />
            )}
            {category === 'decade' && (
              <DecadeBuilder
                selected={selectedDecade}
                onSelect={setSelectedDecade}
              />
            )}
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 dark:border-slate-700 flex-shrink-0">
            <Button type="button" variant="secondary" onClick={onCancel}>
              Cancel
            </Button>
            <Button type="submit" disabled={!valid}>
              Create Collection
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CollectionForm
```

- [ ] **Step 2: Run lint + type-check**

```bash
cd /Users/john/Code/Metamaster/.worktrees/fix-plex-nav/frontend
npm run lint && npm run type-check
```

Fix any errors. Common ones to watch for:
- Unused imports
- `description` field missing from `CollectionCreate` type — check the type definition in `plexCollectionService.ts`

- [ ] **Step 3: Run frontend tests**

```bash
npm run test
```

Expected: all pass (CollectionForm has no existing unit tests, so no regressions expected).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/features/plex/CollectionForm.tsx
git commit -m "feat(plex): rewrite CollectionForm with per-category UI builder"
```

---

### Task 12: Final verification

- [ ] **Step 1: Run full backend test suite**

```bash
cd /Users/john/Code/Metamaster/.worktrees/fix-plex-nav
pytest -v
```

Expected: all pass.

- [ ] **Step 2: Run full backend lint**

```bash
black app/ tests/ && isort app/ tests/ && flake8 app/ tests/ && mypy app/
```

- [ ] **Step 3: Run full frontend checks**

```bash
cd frontend
npm run lint && npm run type-check && npm run test
```

- [ ] **Step 4: Stage all remaining unstaged changes**

```bash
cd /Users/john/Code/Metamaster/.worktrees/fix-plex-nav
git status
```

Stage any files not yet committed.
