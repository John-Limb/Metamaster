# Storage Analytics Design

**Date:** 2026-02-23
**Status:** Approved

## Goal

Add proper storage analytics to MetaMaster: a dashboard widget showing library and disk-level storage breakdown, and a dedicated `/storage` page with per-file efficiency analysis using GB/min calculations, codec detection, and estimated savings.

## User Problem

Large media collections accumulate inefficient files — particularly Blu-ray REMUXes that can reach 25–40 GB for a 2-hour film (~250 MB/min). Without visibility into which files are bloated and why, users cannot make informed decisions about re-encoding. The dashboard currently shows a "coming soon" placeholder for storage.

---

## Data Model

Three new nullable columns added to `FileItem` via Alembic migration:

| Column | Type | Description |
|---|---|---|
| `duration_seconds` | `Integer, nullable` | Media runtime in seconds |
| `video_codec` | `String(20), nullable` | FFprobe codec name: `h264`, `hevc`, `av1`, `mpeg2video`, etc. |
| `video_width` | `Integer, nullable` | Horizontal resolution (e.g. `3840`) |
| `video_height` | `Integer, nullable` | Vertical resolution (e.g. `2160`) |

Width and height are required for resolution tier classification (SD / 720p / 1080p / 4K), which determines the target bitrate used in savings estimates.

---

## Backend

### New router: `/api/v1/storage`

#### `GET /storage/summary`

Feeds the dashboard widget and the storage page header cards.

```json
{
  "disk": {
    "total_bytes": 4000000000000,
    "used_bytes": 2100000000000,
    "available_bytes": 1900000000000
  },
  "library": {
    "movies_bytes": 1400000000000,
    "tv_bytes": 700000000000,
    "other_bytes": 0
  },
  "potential_savings_bytes": 850000000000,
  "files_analyzed": 342,
  "files_pending_analysis": 15
}
```

- Disk stats via `os.statvfs()` on the media mount paths (works inside Docker with bind mounts)
- Library breakdown via DB-level `SUM(size)` grouped by path prefix (`MOVIE_DIR` vs `TV_DIR`)
- `potential_savings_bytes` is the sum of `estimated_savings_bytes` across all files where savings > 0

#### `GET /storage/files`

Paginated, sortable file list for the sub-page. Supports query params: `page`, `page_size`, `sort_by`, `sort_dir`, `media_type`, `codec`, `resolution_tier`, `efficiency_tier`.

```json
{
  "total": 342,
  "items": [
    {
      "id": 1,
      "name": "The Dark Knight (2008).mkv",
      "media_type": "movie",
      "size_bytes": 31000000000,
      "duration_seconds": 9240,
      "video_codec": "h264",
      "video_width": 1920,
      "video_height": 1080,
      "mb_per_min": 254.0,
      "resolution_tier": "1080p",
      "efficiency_tier": "large",
      "estimated_savings_bytes": 26200000000
    }
  ]
}
```

#### `POST /storage/scan-technical`

Triggers the `enrich_file_technical_metadata` Celery task for all files missing technical metadata. Returns `202 Accepted` immediately.

---

### Efficiency tiers

Computed server-side per file:

| Tier | Criteria |
|---|---|
| `efficient` | AV1 (any bitrate); H.265 < 50 MB/min; H.264 < 30 MB/min |
| `moderate` | H.264 30–100 MB/min; H.265 50–150 MB/min |
| `large` | Any codec > 100 MB/min; MPEG-2 or VC-1 regardless of bitrate |
| `unknown` | Technical metadata not yet gathered |

### Savings estimate

Files already in AV1 or H.265 return `estimated_savings_bytes = 0`.

For all others, the estimate assumes re-encoding to H.265 at a resolution-appropriate target:

| Resolution tier | Target bitrate | Target MB/min |
|---|---|---|
| 4K (≥ 3840×2160) | 12 Mbps | ~90 MB/min |
| 1080p (≥ 1920×1080) | 4 Mbps | ~30 MB/min |
| 720p (≥ 1280×720) | 2 Mbps | ~15 MB/min |
| SD | 1 Mbps | ~7.5 MB/min |

```
estimated_target_bytes = (duration_seconds / 60) * target_mb_per_min * 1_048_576
estimated_savings_bytes = max(0, size_bytes - estimated_target_bytes)
```

---

### FFprobe pipeline

FFprobe already runs during file scanning. Extend it to extract and persist the four new fields.

**New files:** populated automatically during the existing scan pipeline.

**Existing files:** a new Celery task `enrich_file_technical_metadata` processes files with null technical data in batches of 50. Triggered via `POST /storage/scan-technical`.

Files with null technical data are included in `/storage/files` responses with `mb_per_min: null` and `efficiency_tier: "unknown"`. They are excluded from savings estimates and `potential_savings_bytes`.

---

## Frontend

### Dashboard widget

The existing `StorageChart` donut chart is wired to real data from `GET /storage/summary`:

- **Donut** — Movies vs TV Shows slices (library breakdown); total library size displayed in the centre
- **Disk bar** — a thin progress bar below the donut showing "X TB used of Y TB total", colour-coded: green < 70%, amber 70–90%, red > 90%
- Clicking anywhere on the widget navigates to `/storage`

### Storage page (`/storage`)

**Header cards (4):**

| Card | Source |
|---|---|
| Total Library | `library.movies_bytes + library.tv_bytes` |
| Disk Available | `disk.available_bytes` of `disk.total_bytes` |
| Potential Savings | `potential_savings_bytes` |
| Files Analyzed | `files_analyzed` / `files_analyzed + files_pending_analysis` |

**Pending analysis banner** (shown when `files_pending_analysis > 0`):
> "Technical metadata is being gathered for X files — refresh to update."

**File table:**

| Column | Notes |
|---|---|
| File | File name |
| Type | Movie / TV |
| Size | Formatted bytes |
| Duration | Formatted as Xh Ym |
| MB/min | Calculated; `—` if pending |
| Codec | Display name (H.264, H.265, AV1, etc.) |
| Resolution | SD / 720p / 1080p / 4K |
| Est. Savings | Formatted bytes; `—` if already efficient or pending |
| Tier | Colour-coded badge: 🟢 Efficient / 🟡 Moderate / 🔴 Large / ⬜ Unknown |

Sortable by any column. Filterable by type, codec, resolution tier, efficiency tier. Paginated at 50 rows per page.

### Sidebar navigation

A new "Storage" item added to the sidebar with a storage/database icon, linking to `/storage`.

---

## Out of Scope (for now)

- Actions (flagging files, triggering re-encodes)
- Historical storage growth tracking
- Orphaned file detection
- Per-show or per-season breakdowns
- Storage quota management
