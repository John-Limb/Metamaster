# Plex UI Deduplication Design

**Date:** 2026-03-22
**Scope:** Frontend — `frontend/src/components/features/plex/` and related common components

---

## Problem

The Plex Collections UI has accumulated significant duplication across its Collection and Playlist components:

- `CollectionDrawer` and `PlaylistDrawer` share ~85% of their code
- `CollectionRow` and `PlaylistRow` share ~70% of their code
- Five files repeat the same error banner `<div>` verbatim
- Both drawers register their own Escape-key listener despite the parent page already handling it
- "Push" and "Delete" action buttons use hand-rolled Tailwind classes instead of the existing `Button` component

---

## Phase 1 — Mechanical Wins

### 1. Replace raw `<button>` with `<Button>`

**Files:** `CollectionRow`, `PlaylistRow`, `CollectionDrawer`, `PlaylistDrawer`

The action buttons use hand-rolled Tailwind instead of the existing `Button` component. Swap:

- Push button → `<Button variant="primary" size="sm">`
- Delete button → `<Button variant="danger" size="sm">`

Note: Do **not** use `variant="outline"` with a red className override — the `outline` variant hardcodes `border-primary-600` and `text-primary-600` which will conflict. Use `variant="danger"` directly.

The `Button` component already handles `disabled` opacity, dark mode, focus rings, and sizing.

### 2. Extract `AlertMessage` component

**New file:** `frontend/src/components/common/AlertMessage.tsx`

The following pattern appears verbatim in 5 files:
```tsx
<div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-400">
  {message}
</div>
```

Extract to:
```ts
interface AlertMessageProps {
  variant: 'error' | 'success'
  message: string
  className?: string
}
```

The `success` variant covers the green discovery-result banner in `PlexCollectionsPage`:
```tsx
<div className="rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 px-4 py-3 text-sm text-green-700 dark:text-green-400">
```

**Files to update after extraction:**
- `PlexCollectionsPage` (error + success banners)
- `PlexPlaylistsPage` (error banner)
- `CollectionsSection` (error banner)
- `PlaylistsSection` (error banner)
- `YamlImportModal` (error banner)

Note: `QueueStats` uses a different two-line title+body layout with `role="alert"` — it is **not** updated in this task.

### 3. Deduplicate Escape-key listener

**Files:** `CollectionDrawer`, `PlaylistDrawer`

Both drawers register `document.addEventListener('keydown', ...)` for Escape. The parent `PlexCollectionsPage` also registers this listener and calls `handleCloseDrawer`. The drawer's own Escape listener is redundant.

- Remove the Escape listener from both drawers.
- Extract the click-outside logic to a `useClickOutside(ref, onClose)` hook in `frontend/src/hooks/useClickOutside.ts` and use it in both drawers (and `PlexPlaylistsPage`).

---

## Phase 2 — Structural Merges

### 4. `PlexItemDrawer` — shared drawer component

**New file:** `frontend/src/components/features/plex/PlexItemDrawer.tsx`
**Replaces:** `CollectionDrawer.tsx` and `PlaylistDrawer.tsx`

#### Shared structure (both drawers)
- Outer container div (fixed sidebar, z-40)
- Header: title + close button
- Artwork: blob URL fetch with cancel-on-unmount, fallback placeholder
- Metadata row: item count + last-synced date
- Optional description paragraph
- Controls bar: Checkbox "Enabled" + Push button + Delete button
- Items list: bordered table of `{ movie_title, plex_rating_key, item_id }` rows with Link

#### Props

```ts
type PlexItemDrawerItem = {
  id: number
  name: string
  description: string | null
  plex_rating_key: string | null
  last_synced_at: string | null
  enabled: boolean
  items: Array<{
    id: number
    plex_rating_key: string
    item_id: number
    movie_title: string | null
  }>
}

interface PlexItemDrawerProps {
  item: PlexItemDrawerItem
  fetchDetail: (id: number) => Promise<PlexItemDrawerItem>
  fetchArtwork: (id: number) => Promise<Blob>
  onClose: () => void
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number) => void
  badge?: React.ReactNode           // collection type badge (omitted for playlists)
  deleteConfirmExtra?: React.ReactNode  // "Also delete from Plex" checkbox (omitted for playlists)
}
```

`CollectionDrawer` and `PlaylistDrawer` become thin wrappers that assemble the correct props and pass them to `PlexItemDrawer`.

### 5. `PlexItemRow` — shared row component

**New file:** `frontend/src/components/features/plex/PlexItemRow.tsx`
**Replaces:** `CollectionRow.tsx` and `PlaylistRow.tsx`

#### Shared structure (both rows)
- `<tr>` with `isSelected` left-border highlight
- Name column: clickable button → `onSelect`
- Item count cell
- Last-synced cell
- Actions cell: Checkbox "Enabled" + Push button + Delete button + `ConfirmDialog`

#### Props

Keep bulk-select as three flat props (matching the existing callers in `PlaylistsSection` and `PlexPlaylistsPage`) to avoid cascading changes to those files:

```ts
interface PlexItemRowProps {
  item: {
    id: number
    name: string
    plex_rating_key: string | null
    last_synced_at: string | null
    enabled: boolean
    items: unknown[]
  }
  isSelected: boolean
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number) => void
  onSelect: (id: number) => void
  badge?: React.ReactNode                  // type badge cell (collection only)
  deleteConfirmExtra?: React.ReactNode     // extra ConfirmDialog content (collection only)
  onDeleteConfirm?: () => void             // called on confirm; default calls onDelete(item.id)
  // Bulk-select (playlist only) — kept flat to match existing callers
  selectable?: boolean
  bulkSelected?: boolean
  onBulkSelect?: (id: number, checked: boolean) => void
}
```

`CollectionRow` and `PlaylistRow` become thin wrappers.

---

## What Is Not Changed

- `CollectionsSection` and `PlaylistsSection` — different enough (movie/TV split, different toolbar) to keep separate
- `PlexCollectionsPage` and `PlexPlaylistsPage` — different page-level concerns; no merge
- `QueueStats` — uses a different two-line alert layout; out of scope
- `ConfirmDialog` buttons — internal implementation, not part of this task
- Test files — not in scope

---

## File Inventory

### New files
| File | Purpose |
|------|---------|
| `components/common/AlertMessage.tsx` | Error/success banner component |
| `hooks/useClickOutside.ts` | Reusable click-outside detection hook |
| `components/features/plex/PlexItemDrawer.tsx` | Shared drawer for collections and playlists |
| `components/features/plex/PlexItemRow.tsx` | Shared table row for collections and playlists |

### Modified files
| File | Change |
|------|--------|
| `CollectionDrawer.tsx` | Thin wrapper around `PlexItemDrawer` |
| `PlaylistDrawer.tsx` | Thin wrapper around `PlexItemDrawer` |
| `CollectionRow.tsx` | Thin wrapper around `PlexItemRow` |
| `PlaylistRow.tsx` | Thin wrapper around `PlexItemRow` |
| `PlexCollectionsPage.tsx` | Use `AlertMessage`; remove redundant Escape listener |
| `PlexPlaylistsPage.tsx` | Use `AlertMessage`; use `useClickOutside` |
| `CollectionsSection.tsx` | Use `AlertMessage` |
| `PlaylistsSection.tsx` | Use `AlertMessage` |
| `YamlImportModal.tsx` | Use `AlertMessage` |
