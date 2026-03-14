# Plex TMDB Mismatch Detection Design

**Goal:** Detect when Plex and MetaMaster have matched the same file to different TMDB IDs, surface the conflict in the UI, and let the user resolve it per-item.

**Architecture:** Two-step lookup during `lock_match` (tmdb_id first, title+year fallback). Mismatches stored on `PlexSyncRecord`. Resolution API pushes the winning ID to whichever side lost. Frontend shows a badge on library cards and a consolidated panel on the Plex page.

**Tech Stack:** SQLAlchemy / Alembic (schema), FastAPI (endpoints), Plex HTTP API (fix-match), React + Zustand (frontend)

---

## Data Model

### `PlexSyncStatus` enum
Add `MISMATCH = "mismatch"` to both the Python enum and the Postgres `SAEnum` string list.

### `PlexSyncRecord` new columns
- `plex_tmdb_id VARCHAR(50) NULLABLE` — what Plex resolved the item to when it differs from ours

When `sync_status = MISMATCH`:
- `plex_rating_key` is populated (we found the item, just under a different ID)
- `plex_tmdb_id` holds Plex's TMDB ID
- Our item's `tmdb_id` is unchanged

One Alembic migration covers both the column addition and the enum value.

---

## Detection

`lock_match` uses a two-step lookup:

1. **Search by our `tmdb_id`** (existing behaviour)
   - Found → `sync_status = SYNCED`, done
2. **Fallback: title + year search** via `PlexClient.find_by_title_year(section_id, title, year)`
   - Uses `/library/sections/{id}/all?title=...` and filters by year client-side
   - Found with a different `tmdb_id` → `sync_status = MISMATCH`, store `plex_tmdb_id` and `plex_rating_key`
   - Not found → `sync_status = NOT_FOUND` (unchanged from today)

### Interface changes
- `PlexClient.find_by_title_year(section_id, title, year)` → `Optional[PlexMediaItem]`
- `PlexSyncService.lock_match(...)` gains `title: str, year: Optional[int]`
- `lock_plex_match` Celery task loads `Movie`/`TVShow` to pass title and year

---

## Resolution API

### `GET /api/v1/plex/mismatches`
Returns all `MISMATCH` records with: `record_id`, `item_type`, `item_id`, `item_title`, `item_year`, `our_tmdb_id`, `plex_tmdb_id`.

### `POST /api/v1/plex/mismatches/{record_id}/resolve`
Body: `{"trust": "metamaster" | "plex"}`

**Trust MetaMaster:**
- Call Plex fix-match API: `PUT /library/metadata/{ratingKey}/match?guid=tmdb://{our_tmdb_id}&name=...`
- Clear `plex_tmdb_id`, set `sync_status = SYNCED`

**Trust Plex:**
- Update `Movie.tmdb_id` (or `TVShow.tmdb_id`) to `plex_tmdb_id`
- Dispatch enrichment task to re-fetch metadata with the new ID
- Clear `plex_tmdb_id`, set `sync_status = SYNCED`

**Note on Plex fix-match:** Plex's API is normally a two-step process (search candidates, then confirm). We skip the search step and `PUT` directly with the known TMDB guid (`tmdb://{id}`). Plex may take a few seconds to reprocess after the call.

---

## Frontend

### Library cards
- Fetch `GET /api/v1/plex/mismatches` once on load; build a lookup set of mismatched `item_id` values
- Render a warning badge on any card whose `id` is in the set
- Clicking the badge opens a resolve modal:
  - Shows item title
  - "MetaMaster: TMDB #603" vs "Plex: TMDB #9999"
  - **Trust MetaMaster** / **Trust Plex** buttons
  - On resolution, remove from mismatch set and hide badge

### Plex page
- "Mismatches" panel below Now Playing; hidden when there are no mismatches
- Lists mismatched items as rows: title, our TMDB ID, Plex's TMDB ID, inline resolve buttons
- Shares the same `GET /api/v1/plex/mismatches` data source as the library badge logic
