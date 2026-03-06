# Plex Integration Design

**Date:** 2026-03-05
**Status:** Approved

## Overview

MetaMaster integrates with Plex Media Server as a two-way bridge:

- **MetaMaster → Plex:** Library refresh triggers after file operations, and match-locking items to the correct TMDB entry to prevent misidentification.
- **Plex → MetaMaster:** Watch status and play counts pulled periodically for analytics and enrichment queue prioritisation.

Plex manages its own metadata (titles, descriptions, posters, ratings) via its native agents — MetaMaster does not duplicate or overwrite this. The integration is additive, not competitive.

---

## Architecture

### New modules

```
app/
├── infrastructure/
│   └── external_apis/
│       └── plex/
│           ├── __init__.py
│           ├── client.py       # Raw Plex HTTP API calls
│           ├── auth.py         # OAuth flow + token management
│           └── schemas.py      # Pydantic models for Plex API responses
│
├── domain/
│   └── plex/
│       ├── models.py           # PlexConnection, PlexSyncRecord ORM models
│       ├── schemas.py          # Pydantic schemas for API layer
│       └── service.py          # PlexSyncService — orchestrates push/pull
│
├── tasks/
│   └── plex.py                 # Celery tasks: refresh_library, lock_match, poll_watched
│
└── api/v1/
    └── plex/
        ├── __init__.py
        ├── router.py           # Connection config, manual sync, OAuth callback
        └── schemas.py          # Request/response schemas
```

### Configuration (`.env`)

```
PLEX_SERVER_URL=http://192.168.1.x:32400
PLEX_TOKEN=                          # manual fallback; OAuth stores token in DB
PLEX_LIBRARY_MOVIES=Movies           # must match Plex library name exactly (case-sensitive)
PLEX_LIBRARY_TV=TV Shows             # must match Plex library name exactly (case-sensitive)
PLEX_SYNC_POLL_INTERVAL_SECONDS=300
```

Library section IDs are resolved dynamically at connection time by querying `/library/sections` and matching against the configured names. Resolved IDs are cached in the `PlexConnection` DB record — runtime calls do not re-query sections on every operation.

---

## Data Model

### `plex_connections`

One row per configured Plex server. Supports future multi-server scenarios.

| Column | Type | Notes |
|---|---|---|
| `id` | INT PK | |
| `server_url` | VARCHAR(500) | e.g. `http://192.168.1.x:32400` |
| `token` | VARCHAR(500) | Encrypted at rest |
| `movie_library_id` | INT | Resolved from `PLEX_LIBRARY_MOVIES` name |
| `tv_library_id` | INT | Resolved from `PLEX_LIBRARY_TV` name |
| `is_active` | BOOLEAN | False if connection fails or token expires |
| `created_at` | DATETIME | |
| `last_connected_at` | DATETIME | |

### `plex_sync_records`

One row per MetaMaster item. Tracks full sync history and is the analytics foundation for watch trends, sync coverage, and enrichment correlations.

| Column | Type | Notes |
|---|---|---|
| `id` | INT PK | |
| `connection_id` | INT FK | → `plex_connections` |
| `item_type` | ENUM | `movie`, `tv_show`, `episode` |
| `item_id` | INT | FK to `movies.id` / `tv_shows.id` / `episodes.id` |
| `plex_rating_key` | VARCHAR(50) | Cached Plex internal ID |
| `last_matched_at` | DATETIME | Last time match was confirmed/locked in Plex |
| `last_pulled_at` | DATETIME | Last watch status pull from Plex |
| `watch_count` | INT | |
| `last_watched_at` | DATETIME | |
| `is_watched` | BOOLEAN | |
| `sync_status` | ENUM | `pending`, `synced`, `failed`, `not_found` |
| `last_error` | TEXT | |

### Future: Collections (not in scope for this iteration)

Planned tables for a future collections feature:

```
plex_collections
  id, connection_id, name, plex_collection_key,
  source ENUM(tmdb_collection, manual),
  tmdb_collection_id, created_at

plex_collection_items
  id, collection_id, sync_record_id
```

Collections will be fully user-managed: create from scratch, auto-seed from TMDB `belongs_to_collection` data (captured during enrichment), and edit membership freely. A full CRUD UI and API will be required. Custom poster upload will use Plex's `POST /library/metadata/{key}/posters` endpoint.

MetaMaster will provide a UI-first collection and poster management experience, abstracting the YAML-based configuration (as used by tools like Kometa) away from standard users, while exposing raw config export/import for power users.

---

## Data Flow

### A) Library Refresh (MetaMaster → Plex)

Triggered automatically after any file operation (move, rename, delete) via a post-operation hook in the file organisation service:

```
File operation completes
        ↓
Celery task: refresh_plex_library_section
        ↓
GET /library/sections/{id}/refresh
        ↓
Plex rescans the section and matches files via naming convention
```

MetaMaster follows Plex naming conventions during file organisation, so Plex will match items correctly after a rescan without any metadata push.

### B) Match Locking (MetaMaster → Plex)

For items where MetaMaster has a confirmed TMDB ID, it can lock the Plex match to prevent misidentification:

```
Item reaches fully_enriched with confirmed tmdb_id
        ↓
Celery task: lock_plex_match
        ↓
PlexSyncService.resolve_plex_key()
    → GET /library/all?guid=tmdb://{tmdb_id}  (against configured section)
        ↓
Cache plex_rating_key in plex_sync_records
        ↓
PUT /library/metadata/{ratingKey}/match  (lock to correct TMDB entry)
        ↓
Update plex_sync_records (last_matched_at, sync_status=synced)
```

### C) Watch Status Pull (Plex → MetaMaster)

```
Celery Beat: every PLEX_SYNC_POLL_INTERVAL_SECONDS
        ↓
Celery task: poll_plex_watched_status
        ↓
GET /library/sections/{id}/all?type=1   # movies (type=4 for episodes)
        ↓
For each item: diff viewCount/lastViewedAt against plex_sync_records
        ↓
Update watch_count, last_watched_at, is_watched
        ↓
Re-score enrichment queue priority for recently watched unmatched items
```

### D) Manual Full Sync

`POST /api/v1/plex/sync` dispatches a Celery task that runs B then C for all items. Progress is surfaced via the existing queue/health endpoint.

---

## Error Handling

### Connection failure
Plex is non-critical. If unreachable at startup, MetaMaster logs a warning and starts normally. Celery tasks retry with exponential backoff (3 attempts, max 5 min delay). After all retries are exhausted, `sync_status` is set to `failed` and surfaced in the admin UI.

### Library name mismatch
If `PLEX_LIBRARY_MOVIES` or `PLEX_LIBRARY_TV` don't resolve to a Plex section, MetaMaster:
- Logs a clear error listing available section names
- Disables Plex sync until resolved
- Surfaces a connection health alert in the UI — same treatment as TMDB/API credential failures

### Match not found
If a TMDB ID lookup returns no Plex item (media not yet scanned, or naming mismatch):
- Item is marked `not_found` in `plex_sync_records`
- Item is **skipped** — processing continues for all remaining items without interruption
- Health status page aggregates all `not_found` items after the sync pass completes
- User can trigger a re-sync per item from the health page once Plex has scanned the file

### Token expiry
OAuth tokens are refreshed automatically. If refresh fails, the connection is marked `is_active=false` and the admin is notified via the existing notification system.

### Logging
All Plex client calls (request URL, response status, retry attempts) are logged at `INFO` level to the Celery worker console via `logging_config.py`. Failures and retries log at `WARNING`/`ERROR`. This keeps Plex diagnostics alongside all other Celery task output.

---

## Authentication

Two modes, both supported:

**OAuth (primary):** MetaMaster redirects through plex.tv OAuth to obtain a token. Token is stored encrypted in `plex_connections`. Refresh is handled automatically.

**Manual token (fallback):** User pastes their `X-Plex-Token` directly into settings via `PLEX_TOKEN` in `.env`. Intended for headless or power-user setups.

---

## Testing

### Backend unit tests
- `plex/client.py` — mock HTTP responses for all Plex API calls (sections, match, refresh, poll)
- `plex/service.py` — push/pull logic, match resolution, sync record updates, skip-on-not-found behaviour
- `plex/auth.py` — OAuth flow, token refresh, fallback token handling

### Backend integration tests
- Full sync cycle against a mocked Plex server (`respx`)
- Library name resolution (match, mismatch, empty section list)
- Celery task retry behaviour on connection failure
- `not_found` items do not block remaining items in a sync pass

### Frontend tests
- Plex connection settings form (OAuth flow, manual token entry)
- Health status page — `not_found` items display and per-item re-sync trigger
- Connection alert banner for library name mismatch

---

## Out of Scope (this iteration)

- Collections management (create, edit, poster upload)
- Kometa-style YAML config generation
- Multi-server support (data model supports it, UI does not)
- Plex webhook support (requires Plex Pass; polling covers the use case)
- Pushing metadata fields (titles, descriptions, ratings, posters for individual items) — Plex manages these natively

---

## Documentation Required

A `docs/plex-setup.md` user guide must be produced alongside implementation, covering:

1. How to find or generate a Plex token (manual fallback method)
2. The OAuth connection flow walkthrough
3. How to set `PLEX_LIBRARY_MOVIES` and `PLEX_LIBRARY_TV` — where to find library names in Plex, case-sensitivity note
4. What MetaMaster reads vs writes to Plex
5. How to use the health page to identify and resolve unmatched items
6. Troubleshooting: library name mismatch alert, token expiry, Celery worker logs
