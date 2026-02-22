# Local Enrichment with Deferred External Metadata Design

**Date**: 2026-02-21
**Status**: Approved

## Problem

When external APIs (OMDB, TVDB) are unavailable, the entire enrichment pipeline fails — no local technical metadata is stored either. Users have no visibility into what is pending, failed, or needs manual attention.

## Goal

Decouple local ffprobe enrichment from external API enrichment so that:
1. Technical metadata (resolution, codecs, duration, audio channels) is always captured locally
2. External metadata (title details, ratings, poster) is retrieved when APIs are available
3. Items needing manual intervention are clearly surfaced to the user

---

## Data Model

### New columns on `Movie` and `TVShow`

| Column | Type | Purpose |
|---|---|---|
| `enrichment_status` | enum | Current state in enrichment pipeline |
| `detected_external_id` | string (nullable) | OMDB/IMDB/TVDB ID parsed from filename or folder name at scan time |
| `manual_external_id` | string (nullable) | OMDB/IMDB/TVDB ID entered manually by the user; always takes priority |
| `enrichment_error` | string (nullable) | Last error message, shown in the UI for context |

### `enrichment_status` enum values

| Value | Meaning |
|---|---|
| `pending_local` | File detected, ffprobe not yet run |
| `local_only` | ffprobe complete, external enrichment not yet attempted |
| `pending_external` | External enrichment task dispatched, in-flight |
| `fully_enriched` | OMDB/TVDB data successfully retrieved |
| `external_failed` | API call failed (unavailable/timeout); will auto-retry |
| `not_found` | API responded but no match found; awaiting manual input |

### Migration

Single Alembic migration:
- Add `enrichment_status_enum` PostgreSQL type
- Add `enrichment_status` (default `pending_local`), `detected_external_id`, `manual_external_id`, `enrichment_error` to `movies` and `tv_shows` tables

---

## Enrichment Flow

### Stage 1 — Local scan (always succeeds)

1. File detected by scanner
2. **Filename/folder parsing**: scan file path and parent folder for embedded IDs using patterns:
   - `{imdb-ttXXXXXXX}` / `{tvdb-XXXXX}` (Plex/Jellyfin convention)
   - `(ttXXXXXXX)` (parenthesis style)
   - Bare `ttXXXXXXX`
3. If ID found: store in `detected_external_id`
4. Run ffprobe → populate technical fields (resolution, codec, bitrate, duration, audio_channels)
5. Set `enrichment_status = local_only`
6. Dispatch Stage 2 Celery task asynchronously
7. ffprobe failure: set `enrichment_status = pending_local`, log error

### Stage 2 — External enrichment (`enrich_external_metadata` Celery task)

**ID resolution priority:**
1. `manual_external_id` (user-supplied, always wins)
2. `detected_external_id` (parsed from filename/folder)
3. Title + year fuzzy search via OMDB/TVDB

**Outcomes:**
- **API unavailable/timeout**: set `external_failed`, store error in `enrichment_error` — periodic retry will handle it
- **API returns no match**: set `not_found`, store message in `enrichment_error` — stops auto-retry, awaits manual ID input
- **Success**: populate `omdb_id`/`tvdb_id`, `plot`, `rating`, `genres`, `poster_url`, set `fully_enriched`

### Periodic retry (`retry_failed_enrichment` Celery Beat task)

- Runs every **2 hours** (configurable)
- Queries for `enrichment_status IN ('local_only', 'external_failed')`
- Dispatches `enrich_external_metadata` for each, batched with existing rate limiting
- Items with `not_found` are excluded (manual intervention required)

---

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `PATCH` | `/api/v1/movies/{id}/external-id` | Set `manual_external_id`, trigger enrichment immediately |
| `PATCH` | `/api/v1/tv-shows/{id}/external-id` | Same for TV shows |
| `POST` | `/api/v1/movies/{id}/enrich` | Manually trigger external enrichment for one movie |
| `POST` | `/api/v1/tv-shows/{id}/enrich` | Manually trigger external enrichment for one show |
| `GET` | `/api/v1/movies?enrichment_status=not_found` | Filter movies by enrichment status |
| `GET` | `/api/v1/tv-shows?enrichment_status=not_found` | Filter shows by enrichment status |
| `GET` | `/api/v1/enrichment/pending` | Dashboard — all items needing attention across both types |

---

## UI

### Card badges

Every movie/show card displays an enrichment status indicator:

| State | Badge |
|---|---|
| `fully_enriched` | ✓ green tick |
| `local_only` / `external_failed` | `Local only` amber pill |
| `not_found` | `Manual needed` red pill |
| `pending_local` / `pending_external` | Loading spinner |

### Dedicated "Needs Attention" view

A new page listing items requiring action, grouped by status:
- **Manual needed** (`not_found`): inline form to enter OMDB/IMDB/TVDB ID
- **Failed** (`external_failed`): "Retry now" button per item
- **Local only** (`local_only`): informational list (auto-retry will handle)
- Bulk action: "Retry all failed"

### Movie/Show detail page

Small enrichment status section showing:
- Current status
- Last error message (if any)
- Detected ID (if parsed from filename)
- Manual ID (if set by user)
- Trigger enrichment button

---

## Key Design Decisions

- **`detected_external_id` and `manual_external_id` are separate fields** so we can always audit where an ID came from. Manual always wins.
- **`not_found` stops auto-retry** to avoid hammering the API on genuinely unmatched content. Only manual ID input resets the state.
- **Stage 1 is always non-fatal** — ffprobe results are stored regardless of any API availability.
- **Existing Celery infrastructure is reused** — no new queue table; the existing task retry + beat scheduling handles periodic enrichment.
