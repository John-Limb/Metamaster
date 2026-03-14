# Unwatched Space Optimisation Design

**Goal:** Surface library files that have never been watched via Plex so the user can identify space-optimisation candidates.

**Architecture:** Extend `StorageService.get_files()` with a `watched_status` filter backed by a path-keyed JOIN across `MovieFile`/`EpisodeFile` and `PlexSyncRecord`. The Storage page gains a Watched Status filter, a recoverable-space banner, and TV episode grouping by show.

**Tech Stack:** SQLAlchemy (queries), FastAPI (endpoint param), React + TypeScript (filter + grouping)

---

## Data & API

No schema changes. `PlexSyncRecord.is_watched` already captures watch state at movie and episode level.

### `StorageService` changes

New private `_get_path_watch_info(self) -> Dict[str, dict]`:
- Query 1: `MovieFile → Movie ⟵ PlexSyncRecord(item_type='movie')` — yields `{file_path: {is_watched, title}}`
- Query 2: `EpisodeFile → Episode → Season → TVShow ⟵ PlexSyncRecord(item_type='episode')` — yields `{file_path: {is_watched, show_title, show_fully_unwatched}}` where `show_fully_unwatched=True` when no episode in that show has `is_watched=True`
- Called once per `get_files()` invocation; result used for per-row enrichment and filtering

`get_files()` gains `watched_status: Optional[str]` param:
- `'unwatched'` → filter to rows where `is_watched is False`
- `'watched'` → filter to rows where `is_watched is True`
- absent/other → no change (existing behaviour)

Each file row gains three new fields:
- `is_watched: Optional[bool]` — `None` for files not in `MovieFile`/`EpisodeFile`
- `show_title: Optional[str]` — populated for TV episode files only
- `show_fully_unwatched: Optional[bool]` — `True` if no episode in that show is watched

`get_summary()` gains two new aggregate fields computed via DB queries:
- `unwatched_movie_size_bytes: int`
- `unwatched_tv_size_bytes: int`

### Endpoint change

`GET /api/v1/storage/files` gains `watchedStatus` query param (passed through to `StorageService.get_files()`).

---

## Frontend

### `storageService.ts`
- Add `watchedStatus?: 'watched' | 'unwatched'` to `StorageFilesParams`
- Add `is_watched: boolean | null`, `show_title: string | null`, `show_fully_unwatched: boolean | null` to `StorageFileItem`
- Add `unwatched_movie_size_bytes: number` and `unwatched_tv_size_bytes: number` to summary type

### `StoragePage.tsx`
- Add "Watched Status" filter dropdown (All / Unwatched / Watched) alongside existing Media Type and Efficiency filters
- When `watchedStatus='unwatched'` is active, show a banner above the table: **"X.X GB potentially recoverable"** (sum of `unwatched_movie_size_bytes + unwatched_tv_size_bytes` from the summary endpoint)
- When `watchedStatus='unwatched'`, group TV episode rows by `show_title`: sort by show title first, then render a group-header row on show change. Fully-unwatched shows labelled "Never watched"; partially-watched shows labelled "Partially watched". Movie rows remain flat.
- Grouping is purely a frontend concern — no new endpoint or route needed.
