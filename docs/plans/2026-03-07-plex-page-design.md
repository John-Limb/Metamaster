# Plex Now Playing Page — Design

**Goal:** A dedicated `/plex` page showing live Plex playback sessions, reusing existing components with no duplication.

**Architecture:** Thin page component wrapping the `NowPlayingPanel` component (already planned in `2026-03-07-plex-now-playing.md`). The page adds a route, a sidebar nav item, and a "not connected" fallback. All data fetching, polling, and session rendering lives in `NowPlayingPanel` — the page owns none of it.

**No duplication:** `NowPlayingPanel`, `PlexSession` types, `getPlexSessions()`, `Card`, and `Button` are all used as-is. Nothing is copied or re-implemented.

---

## Route

`/plex` — lazy-loaded, protected, wrapped in `MainLayout` (same pattern as all other pages).

## Sidebar

Add a "Plex" nav item to `Sidebar.tsx` using `SiPlex` from `react-icons/si` (Plex brand icon). Placed between TV Shows and Organisation.

## Page layout

```
Plex                              Updated just now / X seconds ago
──────────────────────────────────────────────────────────────────
[NowPlayingPanel — full width cards, one per active session]

[Empty state if nothing playing: "Nothing playing right now."]

[Not connected state: "Plex is not connected — configure it in Settings" + link]
```

- "Last updated" timestamp uses TanStack Query's `dataUpdatedAt` from the `NowPlayingPanel` query — surfaced via a `onDataUpdated` callback prop or by lifting the query one level if needed. If the panel owns the query internally, the page shows a static "Updates every 15s" subtitle instead (simpler, no prop drilling).
- "Not connected" state: if `getPlexConnection()` returns 404, show the fallback. Reuses `usePlexStore` (already used in `PlexSettings`) to read connection status without an extra fetch.

## Files

| File | Change |
|---|---|
| `frontend/src/pages/PlexPage.tsx` | **Create** — page shell, not-connected fallback, wraps `NowPlayingPanel` |
| `frontend/src/App.tsx` | Add lazy import + `/plex` route |
| `frontend/src/components/layout/Sidebar/Sidebar.tsx` | Add `SiPlex` nav item between TV Shows and Organisation |

## Out of scope

- `NowPlayingPanel` component — implemented in the now-playing plan
- `PlexSession` types and `getPlexSessions()` — implemented in the now-playing plan
- `PlexHealthPanel` stays on SystemHealthPage unchanged
- No changes to backend
