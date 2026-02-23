# Episode Detail Display — Design Doc

**Date:** 2026-02-23
**Status:** Approved

## Problem

The episode list in `TVShowDetailPage` only shows the episode number. Users need to see episode name, runtime, quality, and a brief synopsis at a glance when browsing seasons.

## Design

### Episode row layout

```
[E01]  Pilot                                 [1080p]  45m
       Walter White, a struggling chemistry…  ★ 9.0
```

Fields shown per episode row:
- **Episode number** — zero-padded monospace label (`E01`)
- **Title** — episode name, falls back to `Episode N` if missing
- **Quality badge** — small badge derived from `EpisodeFile.resolution` (e.g. "1080p", "4K", "720p"); hidden if no file is associated
- **Runtime** — derived from `EpisodeFile.duration` (seconds → `Xh Ym` or `Ym`); hidden if unavailable
- **Synopsis** — `ep.plot`, truncated to 2 lines (`line-clamp-2`), muted colour

Air date and rating remain in the right-hand meta column as they are today.

### Data flow

`EpisodeFile` already stores `resolution` (e.g. `"1920x1080"`) and `duration` (seconds). The API response does not yet expose these.

**Backend:**
- Add `quality: Optional[str]` and `runtime: Optional[int]` to `EpisodeResponse` in `app/schemas.py`
- Populate them in the episode endpoint by eagerly loading the first `EpisodeFile` for each episode
- `quality` is derived from `resolution` (e.g. `"1920x1080"` → `"1080p"`)
- No DB migration required — existing tables are used as-is

**Frontend:**
- Add `quality` and `runtime` to the `Episode` interface in `frontend/src/types/index.ts`
- Update the episode row in `TVShowDetailPage.tsx` to render all five fields
- Runtime formatted as `Xh Ym` / `Ym` using existing `formatRuntime` helper pattern

## Out of scope

- Showing quality/runtime in the `MediaDetailModal` (quick-view card from the grid page)
- Episode thumbnails
- Sorting/filtering by quality or runtime
