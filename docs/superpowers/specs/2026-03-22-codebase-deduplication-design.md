# Codebase Deduplication & Common UI Enforcement

**Date:** 2026-03-22
**Branch:** ui-improvements
**Status:** Approved for implementation

---

## Overview

The frontend codebase contains ~1,700 lines of duplicated logic across pages, utilities, services, and components. This spec covers a full deduplication pass and enforcement of the existing common UI component library (`Button`, `AlertMessage`, `EmptyState`, `Pagination`, `SkeletonCard`) across all call sites.

**Guiding constraint:** No behaviour changes except one explicitly noted UX improvement (scan result → toast). All TypeScript must pass `tsc -b` clean. CC ≤ 8 and ≤ 80 lines/function maintained in all new and modified files.

---

## Section 1 — `MediaCollectionPage` (config-driven shared page)

### Problem

`components/features/movies/MoviesPage/MoviesPage.tsx` (~430 lines) and `components/features/tvshows/TVShowsPage/TVShowsPage.tsx` (~410 lines) are ~90% identical. The files in `pages/MoviesPage.tsx` and `pages/TVShowsPage.tsx` are unused legacy copies that should be deleted.

### Solution

A single config-driven `MediaCollectionPage` component. All shared behaviour lives inside it. Each media type provides a typed config object. The thin page files become ~50-line config assemblers.

**New file:** `src/components/features/media/MediaCollectionPage/MediaCollectionPage.tsx`

### Store interface

`MediaCollectionPage` accepts a `useStore` hook that returns `MediaCollectionStore<TItem>`. This is a named subset of the existing `MediaState<T>` from `createMediaStore.ts` — not the aliased wrappers from `useMovieStore` / `useTVShowStore`.

```ts
// src/components/features/media/MediaCollectionPage/MediaCollectionPage.tsx

export interface MediaCollectionStore<TItem> {
  items: TItem[]
  total: number
  currentPage: number
  isLoading: boolean
  error: string | null
  fetchItems: (page?: number, pageSize?: number) => Promise<void>
}
```

Each thin page wrapper provides a local adapter hook that maps the aliased store names to this interface:

```ts
// In MoviesPage.tsx (thin wrapper):
function useMoviesCollectionStore(): MediaCollectionStore<Movie> {
  const { movies, totalMovies, currentPage, isLoading, error, fetchMovies } = useMovieStore()
  return { items: movies, total: totalMovies, currentPage, isLoading, error, fetchItems: fetchMovies }
}
```

### Config interface

```ts
export interface MediaCollectionConfig<TItem extends { id: string }> {
  // Identity & styling
  title: string
  mediaType: 'movie' | 'tv_show'
  cssPrefix: string                    // e.g. 'movies-page' — used for BEM class names

  // Data
  useStore: () => MediaCollectionStore<TItem>
  onScanDirectory: () => Promise<{ files_synced: number; items_created: number }>
  formatScanResult: (result: { files_synced: number; items_created: number }) => string

  // Rendering
  renderCard: (item: TItem, mismatch: PlexMismatchItem | undefined) => React.ReactNode

  // Toolbar config
  filterSections: FilterSection[]
  sortOptions: SortOption[]
  defaultSort: string
}
```

**`onScanDirectory` normalisation:** `movieService.scanDirectory()` returns `{ files_synced, movies_created }` and `tvShowService.scanDirectory()` returns `{ files_synced, shows_created }`. Each thin page wrapper maps its service result to the common `{ files_synced, items_created }` shape before passing to the config.

### Scan result: intentional UX change

The current pages display the scan result via a local `scanResult` state variable rendered as an inline `<AlertMessage>` that auto-clears after 5 seconds via `setTimeout`. `MediaCollectionPage` replaces this with `addToast` from `useUIStore`. This is a deliberate UX improvement (toast is non-blocking and uses the same toast system as the rest of the app). The `scanResult` state variable and its `setTimeout` are removed.

### Shared behaviour inside `MediaCollectionPage`

- Scan directory (button, `isPushing` state, result via `addToast`, error via `addToast`)
- Error display via `<AlertMessage>`
- View mode toggle (grid / list) — uses `cssPrefix` for class names (e.g. `${cssPrefix}__grid--${viewMode}`)
- Filter panel (`FilterPanel`)
- Sort dropdown (`SortDropdown`)
- Pagination (`Pagination` component)
- Media detail modal (`MediaDetailModal`)
- Plex mismatch lookup from `usePlexStore`

### CSS class names

The existing `.movies-page__*` and `.tvshows-page__*` CSS class names are preserved by threading `cssPrefix` through the config. The grid container uses `${cssPrefix}__grid ${cssPrefix}__grid--${viewMode}`, the pagination container uses `${cssPrefix}__pagination`, etc. Each thin page file continues to import its own CSS file (`MoviesPage.css`, `TVShowsPage.css`).

### Refactored thin page files (~50 lines each)

```
components/features/movies/MoviesPage/MoviesPage.tsx  — adapter hook + config + <MediaCollectionPage>
components/features/tvshows/TVShowsPage/TVShowsPage.tsx — adapter hook + config + <MediaCollectionPage>
```

### Deleted files

```
src/pages/MoviesPage.tsx       — legacy unused page (see note)
src/pages/TVShowsPage.tsx      — legacy unused page
```

**Note:** `pages/MoviesPage.tsx` is a tracked, modified file in the current branch (`ui-improvements`). Before deleting it, verify via `App.tsx` and all route definitions that no active route points to it. If the file is confirmed unreachable, delete it. Both page files were modified in an earlier iteration of this branch and superseded by the `components/features/` versions.

Routes in `App.tsx` (or the router file) verified to already point at the `components/features/` versions; if not, updated.

---

## Section 2 — Utilities consolidation

### 2a. Formatting (`src/utils/formatting.ts` — new canonical file)

**Exports:**
- `formatBytes(bytes: number): string` — consolidates `helpers.formatFileSize`, `businessLogic.fileManagement.formatSize`, and the inline `formatBytes` in `StoragePage.tsx`
- `formatDuration(seconds: number | undefined): string` — `file_duration` is typed as `number | undefined` (`?: number`) in `@/types`. Consolidates the inline versions in `StoragePage.tsx` and `MediaDetailModal.tsx`. `StoragePage`'s existing signature `number | null` is widened to match.
- `formatCodec(codec: string | null | undefined): string` — consolidates the inline lookup table in `StoragePage.tsx`

**Migration steps:**
1. Before removing any export from `helpers.ts` or `businessLogic.ts`, run a codebase-wide search for all import sites of `formatFileSize`, `fileManagement.formatSize`, and the inline definitions.
2. Update all call sites to import from `@/utils/formatting`.
3. Remove the duplicated implementations from `helpers.ts` and `businessLogic.ts`.
4. Run `tsc -b` to confirm no missed callers.

### 2b. Pagination query helper (`src/services/queryUtils.ts` — new file)

**Exports:**
```ts
// Returns a query string (e.g. "page=2&pageSize=20"), empty string if no params
export function buildPaginationQuery(page?: number, pageSize?: number): string
```

**Scope:** Replaces `buildPaginationQuery` in `movieService.ts` and `tvShowService.ts` for the methods that use it: `searchMovies`, `getMoviesByGenre`, `getPopularMovies`, `getTopRatedMovies`, and their TV show equivalents. The `getMovies` and `getTVShows` methods build their own inline `URLSearchParams` to append an additional `status` parameter — these are **not** in scope and are left unchanged.

### 2c. File type utilities

`helpers.ts` already has the canonical `isVideoFile`, `isImageFile`, `isAudioFile`, `getFileExtension` functions. The overlapping implementations in `businessLogic.ts` are removed and their callers redirected to `helpers.ts`. Same search-before-delete discipline as 2a.

---

## Section 3 — Shared hooks (`src/hooks/`)

New directory with two hooks and a barrel export:

### `useEscapeKey(handler: () => void, enabled?: boolean): void`

Replaces the copy-pasted `useEffect` + `document.addEventListener('keydown', ...)` Escape key pattern in:
- `components/common/ConfirmDialog.tsx`
- `components/features/media/MediaDetailModal.tsx`
- `pages/PlexCollectionsPage.tsx`
- `pages/PlexPlaylistsPage.tsx`

### `useFocusTrap(ref: RefObject<HTMLElement | null>, enabled?: boolean): void`

Replaces the Tab-key focus cycling `useEffect` in:
- `components/common/ConfirmDialog.tsx`

`MediaDetailModal.tsx` has no focus trap implementation — it is **not** a consumer of this hook.

Both hooks default `enabled` to `true`. Implementation is ~12–15 lines each.

**New files:**
```
src/hooks/useEscapeKey.ts
src/hooks/useFocusTrap.ts
src/hooks/index.ts   ← re-exports both
```

---

## Section 4 — Plex row consolidation

`PlaylistRow.tsx` (41 lines) is a zero-logic passthrough wrapper — it has no own state and passes all props directly to `PlexItemRow`. It is deleted and its call sites in `PlexPlaylistsPage` (or `PlaylistsSection`) updated to use `PlexItemRow` directly.

`CollectionRow.tsx` (57 lines) is **not** deleted. It has real behaviour: a `deleteFromPlex` local state, a builder-type badge rendered as a `<td>`, and a `deleteConfirmExtra` checkbox. It already delegates to `PlexItemRow` so the consolidation is already done there. No changes to `CollectionRow`.

---

## Section 5 — Common UI enforcement

A systematic pass replacing raw HTML with the existing common component library. All files in `pages/`, `components/features/`, `components/layout/`, and `components/settings/` are in scope.

| Raw pattern | Replace with |
|-------------|-------------|
| `<button>` outside `AlertMessage` message prop | `<Button>` |
| Inline alert/status `<div>` with colour utility classes | `<AlertMessage variant="error\|success\|warning">` |
| Hand-rolled Previous/Next + page counter | `<Pagination>` (already exists in common) |
| Inline "No results" / empty-state text block | `<EmptyState>` |
| Inline loading skeleton grids outside feature pages | `<SkeletonCard>` / `<LoadingState>` |

`StoragePage.tsx` and `EnrichmentPage.tsx` both have hand-rolled Previous/Next pagination — both are migrated to `<Pagination>` for the UI. An existing `usePagination` hook lives at `src/hooks/usePagination.ts` providing `goToPage`, `nextPage`, `prevPage`, `canGoNext`, `canGoPrev`. Where `StoragePage` and `EnrichmentPage` manage page state with a plain `useState`, they should adopt `usePagination` to eliminate the manual page arithmetic alongside the `<Pagination>` component switch.

---

## File change summary

### New files
| Path | Purpose |
|------|---------|
| `src/components/features/media/MediaCollectionPage/MediaCollectionPage.tsx` | Shared config-driven page |
| `src/utils/formatting.ts` | Canonical formatting utilities |
| `src/services/queryUtils.ts` | Shared pagination query builder |
| `src/hooks/useEscapeKey.ts` | Shared escape key hook |
| `src/hooks/useFocusTrap.ts` | Shared focus trap hook |
| `src/hooks/index.ts` | Barrel export |

### Deleted files
| Path | Reason |
|------|--------|
| `src/pages/MoviesPage.tsx` | Legacy unused page |
| `src/pages/TVShowsPage.tsx` | Legacy unused page |
| `src/components/features/plex/PlaylistRow.tsx` | Zero-logic passthrough — replaced by `PlexItemRow` directly |

### Key modified files
| Path | Change |
|------|--------|
| `src/components/features/movies/MoviesPage/MoviesPage.tsx` | Thin config wrapper (~50 lines) |
| `src/components/features/tvshows/TVShowsPage/TVShowsPage.tsx` | Thin config wrapper (~50 lines) |
| `src/services/movieService.ts` | Use `buildPaginationQuery` from `queryUtils` |
| `src/services/tvShowService.ts` | Use `buildPaginationQuery` from `queryUtils` |
| `src/utils/helpers.ts` | Remove formatting duplicates (after caller audit) |
| `src/utils/businessLogic.ts` | Remove file/formatting duplicates (after caller audit) |
| `src/pages/StoragePage.tsx` | Use `formatting` utils; use `<Pagination>` |
| `src/pages/EnrichmentPage.tsx` | Use `<Pagination>` |
| `src/components/common/ConfirmDialog.tsx` | Use `useEscapeKey`, `useFocusTrap` |
| `src/components/features/media/MediaDetailModal.tsx` | Use `useEscapeKey` |
| `src/pages/PlexCollectionsPage.tsx` | Use `useEscapeKey` |
| `src/pages/PlexPlaylistsPage.tsx` | Use `useEscapeKey`; use `PlexItemRow` in place of `PlaylistRow` |
| `src/pages/OrganisationPage.tsx` | Common UI enforcement pass (any remaining raw `<button>` / inline alerts) |
| `src/pages/SettingsPage.tsx` | Common UI enforcement pass (any remaining raw `<button>` / inline alerts) |
| `src/App.tsx` | Verify/update routes for deleted page files |

---

## Out of scope

- Merging `movieStore` and `tvShowStore` (already share `createMediaStore`; further merging adds risk)
- Form styling constants (`INPUT_CLASS` etc.) in `PlexSettings` — isolated and trivial
- `CollectionRow.tsx` — already delegates to `PlexItemRow`; has real logic; keep as-is
- Backend changes
