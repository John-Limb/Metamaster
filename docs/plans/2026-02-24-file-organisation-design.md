# File Organisation — Design Doc

**Date:** 2026-02-24
**Status:** Approved

## Problem

Media files often arrive with inconsistent naming (`breaking.bad.s01e06.mkv`, `the.matrix.1999.mkv`). Plex and Jellyfin expect specific folder/filename conventions to correctly identify and display media. Users need a way to see which files don't conform and rename/move them in bulk.

## Design

### Preset formats

Two selectable presets. The only meaningful difference is whether `(Year)` is included in TV show folder and filenames.

| | Plex | Jellyfin |
|---|---|---|
| Movie folder | `Movie Name (Year)/` | `Movie Name (Year)/` |
| Movie file | `Movie Name (Year).ext` | `Movie Name (Year).ext` |
| TV folder | `Show Name (Year)/Season 01/` | `Show Name/Season 01/` |
| TV file | `Show Name (Year) - S01E06 - Title.ext` | `Show Name - S01E06 - Title.ext` |

Files missing enriched metadata (no title, no year for movies, no episode title for TV) are excluded from preview with a count shown separately.

### Settings page — new "File Organisation" section

Added to the existing `SettingsPage` (`frontend/src/pages/SettingsPage.tsx`):

- Preset dropdown (Plex / Jellyfin), saved to backend via `PUT /api/v1/organisation/settings`
- Conformance stats card (fetched from `GET /api/v1/organisation/stats?preset=...`):
  - Movies: N match / N need renaming / N unenriched
  - TV episodes: N match / N need renaming / N unenriched
  - Stats refresh automatically when preset changes
- "Preview & Apply" button — opens the preview modal

### Preview modal

Tabs: Movies | TV Shows.

Each tab renders a table with columns: checkbox | current path | arrow | proposed path.

- All rows pre-selected; user can deselect individual files
- "Apply X changes" button executes only selected rows via `POST /api/v1/organisation/apply`
- After apply: inline success/failure count; modal stays open so user can see results

### Backend

**New router:** `app/api/v1/organisation/endpoints.py`

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/organisation/settings` | Return saved preset |
| PUT | `/api/v1/organisation/settings` | Save preset |
| GET | `/api/v1/organisation/stats` | Conformance counts (no file I/O) |
| POST | `/api/v1/organisation/preview` | Dry-run: return full list of proposed renames |
| POST | `/api/v1/organisation/apply` | Execute selected renames, update DB file paths |

**Rename logic** (`app/domain/organisation/service.py`):
- Pulls enriched metadata from existing Movie/EpisodeFile/Episode/Season/TVShow DB records
- Builds target path string per preset rules
- Compares normalised target to current `file_path` to determine conformance
- On apply: uses `os.rename` (or `shutil.move` for cross-device), creates intermediate directories with `Path.mkdir(parents=True)`, updates `file_path` in DB

**Persistence** (`app_settings` table):
- Simple key/value table (`key: str`, `value: str`, `updated_at: datetime`)
- Reusable for any future server-side settings
- Organisation preset stored as key `organisation_preset`, value `"plex"` or `"jellyfin"`

## Out of scope

- Auto-rename on scan (manual-only for now)
- Undo / rename history
- Custom format templates
- Subtitle or NFO file handling
