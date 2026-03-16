# Collection Builder UX Redesign

**Date:** 2026-03-16
**Branch:** fix/plex-nav-items
**Status:** Approved

## Problem

The current collection builder presents a raw JSON textarea for all builder types. This is too technical for general users and provides no discoverability of what values are valid.

## Design Decisions

### Terminology

| Old | New |
|---|---|
| Builder Type | Category |
| static_items | Custom (UI label only; backend value `static_items` unchanged) |

### Category Behaviour Matrix

| Category | Name/Desc fields | UI control | Scope |
|---|---|---|---|
| Custom | Shown, user-editable | Search + tag picker | Movies only |
| TMDB Collection | Hidden, auto-filled from TMDB | Library matches + live TMDB search | Movies only |
| Genre | Hidden, auto-named from selection | Single-select pill buttons | Movies only |
| Decade | Hidden, auto-named from selection | Single-select grid buttons | Movies only |

All four categories are **movies only**. TV shows are excluded. This requires a backend fix to `BuilderResolver.resolve_genre()`, which currently queries both movies and TV shows — it must be scoped to movies only.

**Default category when the form opens:** Custom (`static_items`).

### Auto-naming Rules

Name/description fields are hidden for TMDB Collection, Genre, and Decade. The frontend constructs the name silently and includes it in the `CollectionCreate` payload:

- **TMDB Collection** — name and description are taken from the TMDB API response at the moment the user selects a collection result (e.g. "The Dark Knight Collection")
- **Genre** — name is the genre string exactly as returned from the library (e.g. `"Action"`)
- **Decade** — name is `"{decade}s Movies"` (e.g. `"2010s Movies"` for decade `2010`, i.e. the button labelled "2010s" maps to value `2010`)

`sort_title` is always sent as `undefined` on create. It is not exposed in the form.

Switching category resets all selection state for the previous category.

### Form Validation on Submit

The "Create Collection" button is **disabled** until all required fields for the active category are complete:

- **Custom** — Name is non-empty AND at least one movie is selected
- **TMDB Collection** — a collection has been selected
- **Genre** — a genre pill is selected
- **Decade** — a decade button is selected

No inline error on attempted submit — prevention via button disable is sufficient.

### Info Banner Copy

Shown whenever name/description fields are hidden:

- **TMDB Collection:** `"Name and description will be pulled automatically from the TMDB collection you select."`
- **Genre:** `"This collection will be named after the genre you pick, e.g. \"Action\". Movies only."`
- **Decade:** `"This collection will be named after the decade you pick, e.g. \"2010s Movies\". Movies only."`

### Loading and Error States

All three new API calls (`getMovieGenres`, `getLocalTmdbCollections`, `searchTmdbCollections`) use the app's existing pattern: show `LoadingSpinner` while loading, show an inline error message on failure within the relevant section of the form.

### Modal Sizing

The modal uses `max-w-xl` (wider than the current `max-w-lg`) to accommodate the richer content. The modal body (everything between the header and footer buttons) is `overflow-y-auto max-h-[70vh]` so it scrolls independently without the header/footer scrolling off screen.

---

## Category UI Details

### Custom

- `TextInput` for Name (required) and Description (optional)
- Search input (`TextInput` with left search icon) — debounced 300 ms — calls `GET /api/v1/movies/search?q=`
- Results list: movie title + year, Add button per row. Each result row carries `id`, `title`, `year`, and `tmdb_id` (string, may be null). Movies with `tmdb_id = null` are shown but their Add button is disabled with tooltip `"Not yet enriched — no TMDB ID"`.
- Selected items shown as removable indigo pill tags
- `builder_config` sent: `{"items": [{"tmdb_id": "573435", "item_type": "movie"}, ...]}` where `tmdb_id` is the string value from `Movie.tmdb_id`
- Empty search (< 2 chars) shows no results list

### TMDB Collection

- Name and Description fields replaced by an info banner
- **"Matched in your library"** section — calls `GET /api/v1/plex/tmdb-collections/local` on mount. Empty state: shows the text `"No TMDB collections matched in your library yet."` (section remains visible, not hidden).
- **"Search TMDB"** section — debounced 500 ms text input. Calls `GET /api/v1/plex/tmdb-collections/search?q=`. Shows collection name and ID only (no film count). Empty query shows no results.
- Selecting any result marks it with a green highlight and "Remove" button (replaces "Select"). Only one collection can be selected at a time; selecting a new one deselects the previous.
- The selected collection's `name` and `description` (from TMDB) are stored in local form state and submitted in the payload.
- `builder_config` sent: `{"tmdb_collection_id": 123}`

### Genre

- Name and Description fields replaced by an info banner
- Pill buttons populated from `GET /api/v1/movies/genres` on mount
- Single-select radio behaviour: clicking a pill deselects the previous
- `builder_config` sent: `{"genre": "Action"}`

### Decade

- Name and Description fields replaced by an info banner
- Static grid of decade buttons: 1960s, 1970s, 1980s, 1990s, 2000s, 2010s, 2020s. 2030s shown disabled as a placeholder. Range is UI-enforced only; the backend does not validate the decade value.
- Button label "2010s" maps to integer value `2010` in the config (the decade start year).
- Single-select radio behaviour, same as Genre
- `builder_config` sent: `{"decade": 2010}`

### Common UI Components Used

- `TextInput` — Name, Description, search inputs
- `Select` — Category dropdown (value cast to `BuilderType` on change, default `"static_items"`)
- `Button` (primary) — "Create Collection" (disabled until valid); (secondary/outline) — "Cancel", "Add", "Select", "Remove"
- Info banner — inline `div` with blue border/background and info SVG icon (no new component)
- Pill tags — inline styled spans with `✕` button

---

## Backend Changes Required

### New API Endpoints (all require `get_current_user` auth dependency)

#### `GET /api/v1/movies/genres`

Added to the movies router (`app/api/v1/movies/`). **Must be registered before `GET /{movie_id}`** in the router file to avoid FastAPI's catch-all path parameter shadowing the `/genres` literal segment. Returns distinct non-null genres from the movie library.

The `Movie.genres` column is stored as `Text` (JSON-encoded string), not a PostgreSQL array. The endpoint must fetch all rows where `genres IS NOT NULL`, parse each with `json.loads`, flatten, deduplicate, and sort alphabetically in application code (a SQL DISTINCT/unnest is not possible on this column type).

**Response:**
```json
{ "genres": ["Action", "Comedy", "Drama", "Horror"] }
```

#### `GET /api/v1/plex/tmdb-collections/local`

Added to `app/api/v1/plex/collection_router.py` (not `router.py`). Queries the global movie library (no Plex connection scoping required — this endpoint does not interact with Plex). Returns movies where `tmdb_collection_id IS NOT NULL`, grouped by collection.

`name` is taken from the first matched movie's `tmdb_collection_name` field, falling back to `"Collection {tmdb_collection_id}"`. Sorted by `movie_count DESC, tmdb_collection_id ASC` for stable ordering.

**Response:**
```json
[
  { "tmdb_collection_id": 263, "name": "The Dark Knight Collection", "movie_count": 3 }
]
```

#### `GET /api/v1/plex/tmdb-collections/search?q=`

Added to `app/api/v1/plex/collection_router.py` as an **`async def`** route. This is intentionally the only async handler in that file — required by `httpx.AsyncClient`. All other handlers in that file are synchronous `def`. Proxies to `GET https://api.themoviedb.org/3/search/collection?query={q}` using `httpx.AsyncClient` with `await`.

Auth: `TMDB_READ_ACCESS_TOKEN` → Bearer header. Fallback: `TMDB_API_KEY` → `?api_key=` param. If neither configured → HTTP 503 `{"detail": "TMDB API key not configured"}`.

Returns up to 20 results (TMDB default page size). No pagination in this implementation.

**Response:**
```json
[
  { "id": 9485, "name": "Christopher Nolan Collection" },
  { "id": 948,  "name": "Batman Collection" }
]
```

### Backend Fix Required

`app/domain/plex/collection_builder.py` → `resolve_genre()` must query `Movie` only, removing the `TVShow` query. **Breaking change:** existing genre collections will no longer include TV shows on next push.

### Existing Endpoints Used

- `GET /api/v1/movies/search?q=` — Custom category movie search
- `POST /api/v1/plex/collections` — unchanged

### No `CollectionCreate` Schema Changes

`CollectionCreate` fields (`name`, `description`, `builder_type`, `builder_config`) are unchanged. `sort_title` is always omitted.

---

## Frontend Changes Required

### Modified Files

- `frontend/src/components/features/plex/CollectionForm.tsx` — replaces JSON textarea with category-aware form, delegates to sub-components
- `frontend/src/services/plexCollectionService.ts` — add `getLocalTmdbCollections()`, `searchTmdbCollections(q)`
- `frontend/src/services/movieService.ts` (or equivalent movies service file) — add `getMovieGenres()` (belongs in the movies domain, not plex)

### New Sub-components (co-located alongside `CollectionForm.tsx`)

- `CustomBuilder.tsx` — movie search + selected items tag picker
- `TmdbCollectionBuilder.tsx` — local matches section + live TMDB search section
- `GenreBuilder.tsx` — single-select pill grid
- `DecadeBuilder.tsx` — single-select decade grid

Each sub-component receives an `onSelect` / `onAdd` / `onRemove` callback to lift selection state up to `CollectionForm`, which owns all form state and calls `createCollection` (in `frontend/src/stores/plexCollectionStore.ts`) on submit.

### No Store Changes

`createCollection` in `plexCollectionStore.ts` is called on submit without modification.

---

## Out of Scope

- TV show collections (future work)
- Editing existing collections via this form (create-only)
- Playlist builder (separate feature)
- Pagination of TMDB search results
