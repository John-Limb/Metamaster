# Plex UI Deduplication Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate ~80% duplication across Plex Collection and Playlist components by extracting shared infrastructure (AlertMessage, useClickOutside) and shared view components (PlexItemRow, PlexItemDrawer), leaving thin wrappers as the public API.

**Architecture:** Phase 1 extracts horizontal concerns shared across the wider app (AlertMessage, useClickOutside). Phase 2 creates shared Plex-specific components (PlexItemRow, PlexItemDrawer) that implement full logic; original Collection/Playlist files become thin wrappers that assemble the correct props. Existing callers in CollectionsSection, PlaylistsSection, PlexCollectionsPage, PlexPlaylistsPage are unchanged.

**Tech Stack:** React 18, TypeScript, Tailwind CSS, React Router

**Spec:** `docs/superpowers/specs/2026-03-22-plex-ui-deduplication-design.md`

**Note on commits:** Per project policy (`CLAUDE.md`), always stage with `git add` but do NOT commit — the user commits manually.

**Note on Button adoption:** Phase 1 of the spec calls for replacing raw `<button>` with `<Button>` in the original drawer/row files. Since Phase 2 rewrites those files as thin wrappers, the Button adoption is implemented directly in the new PlexItemRow and PlexItemDrawer (Tasks 3 and 5), avoiding double work.

---

## Chunk 1: AlertMessage + useClickOutside

### Task 1: Extract `AlertMessage` component

**Files:**
- Create: `frontend/src/components/common/AlertMessage.tsx`
- Modify: `frontend/src/components/common/index.ts`
- Modify: `frontend/src/pages/PlexCollectionsPage.tsx`
- Modify: `frontend/src/pages/PlexPlaylistsPage.tsx`
- Modify: `frontend/src/components/features/plex/CollectionsSection.tsx`
- Modify: `frontend/src/components/features/plex/PlaylistsSection.tsx`
- Modify: `frontend/src/components/features/plex/YamlImportModal.tsx`

- [ ] **Step 1: Create `AlertMessage.tsx`**

```tsx
import React from 'react'

export interface AlertMessageProps {
  variant: 'error' | 'success'
  message: string
  className?: string
}

export function AlertMessage({ variant, message, className = '' }: AlertMessageProps) {
  const styles =
    variant === 'error'
      ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-700 dark:text-red-400'
      : 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-700 dark:text-green-400'
  return (
    <div className={`rounded-lg border px-4 py-3 text-sm ${styles} ${className}`}>
      {message}
    </div>
  )
}

export default AlertMessage
```

- [ ] **Step 2: Export from `index.ts`**

Add after the `ApiErrorBoundary` export at the end of `frontend/src/components/common/index.ts`:

```ts
export { AlertMessage } from './AlertMessage'
export type { AlertMessageProps } from './AlertMessage'
```

- [ ] **Step 3: Update `PlexCollectionsPage.tsx`**

Add to the import on line 10 (existing `Button` import):
```ts
import { Button, AlertMessage } from '@/components/common'
```
(Replace the existing `import { Button } from '@/components/common/Button'` line.)

Replace the success banner (around line 97):
```tsx
// Before:
{discoverMessage && (
  <div className="rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 px-4 py-3 text-sm text-green-700 dark:text-green-400">{discoverMessage}</div>
)}
// After:
{discoverMessage && <AlertMessage variant="success" message={discoverMessage} />}
```

Replace the error banner (around line 100):
```tsx
// Before:
{pushAllError && (
  <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-400">{pushAllError}</div>
)}
// After:
{pushAllError && <AlertMessage variant="error" message={pushAllError} />}
```

- [ ] **Step 4: Update `PlexPlaylistsPage.tsx`**

Add `AlertMessage` to the existing `Button` import:
```ts
import { Button, AlertMessage } from '@/components/common'
```
(Replace `import { Button } from '@/components/common/Button'`.)

Replace the error banner (around line 134):
```tsx
// Before:
{playlistsError && (
  <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-400">
    {playlistsError}
  </div>
)}
// After:
{playlistsError && <AlertMessage variant="error" message={playlistsError} />}
```

- [ ] **Step 5: Update `CollectionsSection.tsx`**

Add `AlertMessage` to the existing `Button` import:
```ts
import { Button, AlertMessage } from '@/components/common'
```
(Replace `import { Button } from '@/components/common/Button'`.)

Replace the error banner (around line 98):
```tsx
// Before:
{collectionsError && (
  <div className="mb-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-400">
    {collectionsError}
  </div>
)}
// After:
{collectionsError && (
  <AlertMessage variant="error" message={collectionsError} className="mb-4" />
)}
```

- [ ] **Step 6: Update `PlaylistsSection.tsx`**

Add `AlertMessage` to the existing `Button` import:
```ts
import { Button, AlertMessage } from '@/components/common'
```
(Replace `import { Button } from '@/components/common/Button'`.)

Replace the error banner (around line 80):
```tsx
// Before:
{playlistsError && (
  <div className="mb-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-400">
    {playlistsError}
  </div>
)}
// After:
{playlistsError && (
  <AlertMessage variant="error" message={playlistsError} className="mb-4" />
)}
```

- [ ] **Step 7: Update `YamlImportModal.tsx`**

Add import:
```ts
import { AlertMessage } from '@/components/common'
```

Replace the error div (around line 73):
```tsx
// Before:
{error && (
  <div
    role="alert"
    className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-400"
  >
    {error}
  </div>
)}
// After:
{error && <AlertMessage variant="error" message={error} />}
```

- [ ] **Step 8: TypeScript check and lint**

```bash
cd frontend && npm run type-check 2>&1 | head -20 && npm run lint 2>&1 | head -20
```

Expected: 0 errors, 0 new warnings.

- [ ] **Step 9: Stage**

```bash
git add frontend/src/components/common/AlertMessage.tsx \
        frontend/src/components/common/index.ts \
        frontend/src/pages/PlexCollectionsPage.tsx \
        frontend/src/pages/PlexPlaylistsPage.tsx \
        frontend/src/components/features/plex/CollectionsSection.tsx \
        frontend/src/components/features/plex/PlaylistsSection.tsx \
        frontend/src/components/features/plex/YamlImportModal.tsx
```

---

### Task 2: Extract `useClickOutside` hook

**Files:**
- Create: `frontend/src/hooks/useClickOutside.ts`

- [ ] **Step 1: Create `useClickOutside.ts`**

```ts
import { useEffect, type RefObject } from 'react'

export function useClickOutside<T extends HTMLElement>(
  ref: RefObject<T | null>,
  onClose: () => void
): void {
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [ref, onClose])
}
```

- [ ] **Step 2: TypeScript check**

```bash
cd frontend && npm run type-check 2>&1 | head -10
```

Expected: 0 errors.

- [ ] **Step 3: Stage**

```bash
git add frontend/src/hooks/useClickOutside.ts
```

Note on `PlexPlaylistsPage`: The spec mentions using `useClickOutside` "in both drawers (and `PlexPlaylistsPage`)". `PlexPlaylistsPage` does **not** have any click-outside handler today — it only has an Escape listener. Since `PlexItemDrawer` (used by `PlaylistDrawer`) already handles click-outside internally via `useClickOutside`, adding it again to the page level would be redundant. No changes are made to `PlexPlaylistsPage` for click-outside.

---

## Chunk 2: Shared Row Component

### Task 3: Create `PlexItemRow`

**Files:**
- Create: `frontend/src/components/features/plex/PlexItemRow.tsx`

- [ ] **Step 1: Create `PlexItemRow.tsx`**

```tsx
import React, { useState } from 'react'
import { Checkbox, CheckboxInput, Button } from '@/components/common'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { formatSyncDate } from './plexUtils'

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
  badge?: React.ReactNode
  deleteConfirmExtra?: React.ReactNode
  onDeleteConfirm?: () => void
  selectable?: boolean
  bulkSelected?: boolean
  onBulkSelect?: (id: number, checked: boolean) => void
}

export function PlexItemRow({
  item,
  isSelected,
  onToggleEnabled,
  onPush,
  onDelete,
  onSelect,
  badge,
  deleteConfirmExtra,
  onDeleteConfirm,
  selectable,
  bulkSelected,
  onBulkSelect,
}: PlexItemRowProps) {
  const [showConfirm, setShowConfirm] = useState(false)

  const handleDeleteConfirm = () => {
    setShowConfirm(false)
    if (onDeleteConfirm) {
      onDeleteConfirm()
    } else {
      onDelete(item.id)
    }
  }

  return (
    <>
      <tr
        className={`border-l-4 transition-colors ${
          isSelected
            ? 'border-primary-500 bg-primary-500/10 dark:bg-primary-500/15'
            : 'border-transparent hover:bg-slate-800/30'
        }`}
      >
        <td className="py-2 pl-3 pr-2">
          <div className="flex items-center gap-2">
            {selectable && (
              <CheckboxInput
                checked={!!bulkSelected}
                onChange={checked => onBulkSelect?.(item.id, checked)}
                aria-label={`Select ${item.name}`}
              />
            )}
            <button
              onClick={() => onSelect(item.id)}
              className="text-left font-medium text-slate-900 dark:text-white hover:text-primary-600 dark:hover:text-primary-400 hover:underline transition-colors truncate max-w-xs"
            >
              {item.name}
            </button>
          </div>
        </td>
        {badge}
        <td className="py-2 px-2 text-sm text-slate-500 dark:text-slate-400">
          {item.items.length}
        </td>
        <td className="py-2 px-2 text-sm text-slate-500 dark:text-slate-400 whitespace-nowrap">
          {formatSyncDate(item.last_synced_at)}
        </td>
        <td className="py-2 pl-2 pr-3">
          <div className="flex items-center justify-end gap-2">
            <Checkbox
              label="Enabled"
              checked={item.enabled}
              onChange={checked => onToggleEnabled(item.id, checked)}
            />
            <Button
              variant="primary"
              size="sm"
              onClick={() => onPush(item.id)}
              disabled={!item.enabled}
            >
              Push
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => setShowConfirm(true)}
            >
              Delete
            </Button>
          </div>
        </td>
      </tr>

      <ConfirmDialog
        isOpen={showConfirm}
        title={`Delete ${item.name}?`}
        confirmText="Delete"
        isDangerous
        onConfirm={handleDeleteConfirm}
        onCancel={() => setShowConfirm(false)}
      >
        {deleteConfirmExtra}
      </ConfirmDialog>
    </>
  )
}

export default PlexItemRow
```

Note on the `badge` prop: it is a full `<td>` element supplied by the wrapper. `CollectionRow` passes it; `PlaylistRow` does not. The table in `CollectionsSection` has a "Type" column header for this cell; the table in `PlaylistsSection` (and `PlexPlaylistsPage`) does not. This asymmetry is intentional — the column count differs between the two tables.

- [ ] **Step 2: TypeScript check**

```bash
cd frontend && npm run type-check 2>&1 | head -20
```

Expected: 0 errors.

- [ ] **Step 3: Stage**

```bash
git add frontend/src/components/features/plex/PlexItemRow.tsx
```

---

### Task 4: Make `CollectionRow` and `PlaylistRow` thin wrappers

**Files:**
- Modify: `frontend/src/components/features/plex/CollectionRow.tsx`
- Modify: `frontend/src/components/features/plex/PlaylistRow.tsx`

- [ ] **Step 1: Rewrite `CollectionRow.tsx`**

Replace the entire file content:

```tsx
import React, { useState } from 'react'
import type { PlexCollection } from '../../../services/plexCollectionService'
import { Checkbox } from '@/components/common/Checkbox'
import { BUILDER_LABELS } from './plexUtils'
import { PlexItemRow } from './PlexItemRow'

interface CollectionRowProps {
  collection: PlexCollection
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number, deleteFromPlex: boolean) => void
  onSelect: (id: number) => void
  isSelected: boolean
}

export function CollectionRow({
  collection,
  onToggleEnabled,
  onPush,
  onDelete,
  onSelect,
  isSelected,
}: CollectionRowProps) {
  const [deleteFromPlex, setDeleteFromPlex] = useState(!!collection.plex_rating_key)

  const badge = (
    <td className="py-2 px-2">
      <span className="inline-flex px-2 py-0.5 rounded text-xs font-medium bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400">
        {BUILDER_LABELS[collection.builder_type] ?? collection.builder_type}
      </span>
    </td>
  )

  const deleteConfirmExtra = collection.plex_rating_key ? (
    <Checkbox
      label="Also delete from Plex"
      checked={deleteFromPlex}
      onChange={setDeleteFromPlex}
    />
  ) : undefined

  return (
    <PlexItemRow
      item={collection}
      isSelected={isSelected}
      onToggleEnabled={onToggleEnabled}
      onPush={onPush}
      onDelete={() => onDelete(collection.id, deleteFromPlex)}
      onSelect={onSelect}
      badge={badge}
      deleteConfirmExtra={deleteConfirmExtra}
    />
  )
}

export default CollectionRow
```

Note on `onDelete` closure: `() => onDelete(collection.id, deleteFromPlex)` is a zero-parameter closure passed as `(id: number) => void`. In TypeScript callback position, a function with fewer parameters is assignable to a function with more parameters — this is standard TS structural typing. When `PlexItemRow` calls `onDelete(item.id)`, the `id` argument is passed but ignored; the closure reads `deleteFromPlex` from its enclosing scope at call time (i.e., after the user has potentially checked/unchecked the "Also delete from Plex" checkbox). This is correct — `onDeleteConfirm` is not needed here.

- [ ] **Step 2: Rewrite `PlaylistRow.tsx`**

Replace the entire file content:

```tsx
import React from 'react'
import type { PlexPlaylist } from '../../../services/plexCollectionService'
import { PlexItemRow } from './PlexItemRow'

interface PlaylistRowProps {
  playlist: PlexPlaylist
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number) => void
  onSelect: (id: number) => void
  isSelected: boolean
  selectable?: boolean
  bulkSelected?: boolean
  onBulkSelect?: (id: number, selected: boolean) => void
}

export function PlaylistRow({
  playlist,
  onToggleEnabled,
  onPush,
  onDelete,
  onSelect,
  isSelected,
  selectable,
  bulkSelected,
  onBulkSelect,
}: PlaylistRowProps) {
  return (
    <PlexItemRow
      item={playlist}
      isSelected={isSelected}
      onToggleEnabled={onToggleEnabled}
      onPush={onPush}
      onDelete={onDelete}
      onSelect={onSelect}
      selectable={selectable}
      bulkSelected={bulkSelected}
      onBulkSelect={onBulkSelect}
    />
  )
}

export default PlaylistRow
```

- [ ] **Step 3: TypeScript check and lint**

```bash
cd frontend && npm run type-check 2>&1 | head -20 && npm run lint 2>&1 | head -20
```

Expected: 0 errors, 0 new warnings. The callers (`CollectionsSection`, `PlaylistsSection`, `PlexPlaylistsPage`) are unchanged; their prop interfaces match the new wrappers exactly.

- [ ] **Step 4: Stage**

```bash
git add frontend/src/components/features/plex/CollectionRow.tsx \
        frontend/src/components/features/plex/PlaylistRow.tsx
```

---

## Chunk 3: Shared Drawer Component

### Task 5: Create `PlexItemDrawer`

**Files:**
- Create: `frontend/src/components/features/plex/PlexItemDrawer.tsx`

- [ ] **Step 1: Create `PlexItemDrawer.tsx`**

```tsx
import React, { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Checkbox, Button } from '@/components/common'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { useClickOutside } from '@/hooks/useClickOutside'
import { formatSyncDate } from './plexUtils'

export type PlexItemDrawerItem = {
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
  badge?: React.ReactNode
  deleteConfirmExtra?: React.ReactNode
}

export function PlexItemDrawer({
  item,
  fetchDetail,
  fetchArtwork,
  onClose,
  onToggleEnabled,
  onPush,
  onDelete,
  badge,
  deleteConfirmExtra,
}: PlexItemDrawerProps) {
  const [artworkUrl, setArtworkUrl] = useState<string | null>(null)
  const [detail, setDetail] = useState<PlexItemDrawerItem | null>(null)
  const [showConfirm, setShowConfirm] = useState(false)
  const drawerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchDetail(item.id).then(setDetail).catch(() => {})
  }, [item.id, fetchDetail])

  useEffect(() => {
    if (!item.plex_rating_key) return
    let objectUrl: string | null = null
    let cancelled = false
    fetchArtwork(item.id)
      .then(blob => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(blob)
        setArtworkUrl(objectUrl)
      })
      .catch(() => { if (!cancelled) setArtworkUrl(null) })
    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [item.id, item.plex_rating_key, fetchArtwork])

  useClickOutside(drawerRef, onClose)

  const items = detail?.items ?? []

  return (
    <div
      ref={drawerRef}
      className="w-80 flex-shrink-0 border-l border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex flex-col overflow-hidden fixed right-0 top-16 h-[calc(100vh-4rem)] z-40"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-700">
        <h3 className="font-semibold text-slate-900 dark:text-white truncate pr-2">
          {item.name}
        </h3>
        <button
          onClick={onClose}
          aria-label="Close drawer"
          className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors flex-shrink-0"
        >
          ✕
        </button>
      </div>

      <div className="overflow-y-auto flex-1 p-4 space-y-4">
        {/* Artwork */}
        {artworkUrl ? (
          <img
            src={artworkUrl}
            alt={`${item.name} artwork`}
            className="w-full rounded-lg object-cover"
          />
        ) : (
          <div className="w-full h-32 rounded-lg bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-400 text-sm">
            No artwork
          </div>
        )}

        {/* Metadata */}
        <div className="flex items-center gap-2 flex-wrap text-sm text-slate-500 dark:text-slate-400">
          {badge}
          <span>{items.length} items</span>
          <span>·</span>
          <span>{formatSyncDate(item.last_synced_at)}</span>
        </div>

        {item.description && (
          <p className="text-sm text-slate-500 dark:text-slate-400">{item.description}</p>
        )}

        {/* Controls */}
        <div className="flex items-center justify-between gap-2 p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50">
          <Checkbox
            label="Enabled"
            checked={item.enabled}
            onChange={checked => onToggleEnabled(item.id, checked)}
          />
          <div className="flex gap-2">
            <Button
              variant="primary"
              size="sm"
              onClick={() => onPush(item.id)}
              disabled={!item.enabled}
            >
              Push to Plex
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => setShowConfirm(true)}
            >
              Delete
            </Button>
          </div>
        </div>

        {/* Items list */}
        <div>
          <h4 className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
            Items ({items.length})
          </h4>
          {items.length === 0 ? (
            <p className="text-sm text-slate-400 italic">No items</p>
          ) : (
            <div className="rounded-lg border border-slate-200 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700">
              {items.map(i => (
                <div key={i.id} className="flex items-center justify-between px-3 py-2 gap-2">
                  <div className="min-w-0">
                    {i.movie_title ? (
                      <span className="text-sm font-semibold text-slate-800 dark:text-slate-200 truncate block">
                        {i.movie_title}
                      </span>
                    ) : (
                      <span className="text-sm text-slate-400 italic truncate block">—</span>
                    )}
                    <span className="text-xs font-mono text-slate-400">
                      {i.plex_rating_key}
                    </span>
                  </div>
                  {i.movie_title && (
                    <Link
                      to={`/movies/${i.item_id}`}
                      className="text-primary-500 hover:text-primary-700 flex-shrink-0 text-sm"
                    >
                      →
                    </Link>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <ConfirmDialog
        isOpen={showConfirm}
        title={`Delete ${item.name}?`}
        confirmText="Delete"
        isDangerous
        onConfirm={() => { setShowConfirm(false); onDelete(item.id) }}
        onCancel={() => setShowConfirm(false)}
      >
        {deleteConfirmExtra}
      </ConfirmDialog>
    </div>
  )
}

export default PlexItemDrawer
```

Note: The Escape-key listener present in the original drawers is **intentionally omitted**. The parent page (`PlexCollectionsPage`, `PlexPlaylistsPage`) already registers an Escape listener that calls `handleCloseDrawer`. The drawer's own Escape listener was redundant.

- [ ] **Step 2: TypeScript check**

```bash
cd frontend && npm run type-check 2>&1 | head -20
```

Expected: 0 errors. If TypeScript reports incompatibility between `PlexCollection` / `PlexPlaylist` and `PlexItemDrawerItem`, both types are structurally compatible (both `CollectionItem` and `PlaylistItem` have a superset of the fields required by `PlexItemDrawerItem.items`).

- [ ] **Step 3: Stage**

```bash
git add frontend/src/components/features/plex/PlexItemDrawer.tsx
```

---

### Task 6: Make `CollectionDrawer` and `PlaylistDrawer` thin wrappers

**Files:**
- Modify: `frontend/src/components/features/plex/CollectionDrawer.tsx`
- Modify: `frontend/src/components/features/plex/PlaylistDrawer.tsx`

- [ ] **Step 1: Rewrite `CollectionDrawer.tsx`**

Replace the entire file content:

```tsx
import React, { useState } from 'react'
import type { PlexCollection } from '../../../services/plexCollectionService'
import {
  getCollection,
  getCollectionArtwork,
} from '../../../services/plexCollectionService'
import { Checkbox } from '@/components/common/Checkbox'
import { BUILDER_LABELS } from './plexUtils'
import { PlexItemDrawer } from './PlexItemDrawer'
import type { PlexItemDrawerItem } from './PlexItemDrawer'

interface CollectionDrawerProps {
  collection: PlexCollection
  onClose: () => void
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number, deleteFromPlex: boolean) => void
}

export function CollectionDrawer({
  collection,
  onClose,
  onToggleEnabled,
  onPush,
  onDelete,
}: CollectionDrawerProps) {
  const [deleteFromPlex, setDeleteFromPlex] = useState(!!collection.plex_rating_key)

  const badge = (
    <span className="inline-flex px-2 py-0.5 rounded text-xs font-medium bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400">
      {BUILDER_LABELS[collection.builder_type] ?? collection.builder_type}
    </span>
  )

  const deleteConfirmExtra = collection.plex_rating_key ? (
    <Checkbox
      label="Also delete from Plex"
      checked={deleteFromPlex}
      onChange={setDeleteFromPlex}
    />
  ) : undefined

  return (
    <PlexItemDrawer
      item={collection as PlexItemDrawerItem}
      fetchDetail={id => getCollection(id) as Promise<PlexItemDrawerItem>}
      fetchArtwork={getCollectionArtwork}
      onClose={onClose}
      onToggleEnabled={onToggleEnabled}
      onPush={onPush}
      onDelete={() => onDelete(collection.id, deleteFromPlex)}
      badge={badge}
      deleteConfirmExtra={deleteConfirmExtra}
    />
  )
}

export default CollectionDrawer
```

Note: The `as PlexItemDrawerItem` cast is needed because `PlexCollection` carries extra fields (`builder_type`, `builder_config`, etc.) and TypeScript's strict checking doesn't automatically allow passing a wider type for a generic `item` prop. Both `CollectionItem` and `PlaylistItem` have a superset of `PlexItemDrawerItem.items[*]`, so structurally this is sound.

- [ ] **Step 2: Rewrite `PlaylistDrawer.tsx`**

Replace the entire file content:

```tsx
import React from 'react'
import type { PlexPlaylist } from '../../../services/plexCollectionService'
import {
  getPlaylist,
  getPlaylistArtwork,
} from '../../../services/plexCollectionService'
import { PlexItemDrawer } from './PlexItemDrawer'
import type { PlexItemDrawerItem } from './PlexItemDrawer'

interface PlaylistDrawerProps {
  playlist: PlexPlaylist
  onClose: () => void
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number) => void
}

export function PlaylistDrawer({
  playlist,
  onClose,
  onToggleEnabled,
  onPush,
  onDelete,
}: PlaylistDrawerProps) {
  return (
    <PlexItemDrawer
      item={playlist as PlexItemDrawerItem}
      fetchDetail={id => getPlaylist(id) as Promise<PlexItemDrawerItem>}
      fetchArtwork={getPlaylistArtwork}
      onClose={onClose}
      onToggleEnabled={onToggleEnabled}
      onPush={onPush}
      onDelete={onDelete}
    />
  )
}

export default PlaylistDrawer
```

- [ ] **Step 3: TypeScript check and lint**

```bash
cd frontend && npm run type-check 2>&1 | head -20 && npm run lint 2>&1 | head -20
```

Expected: 0 errors, 0 new warnings. Callers in `PlexCollectionsPage` and `PlexPlaylistsPage` pass the same props as before — the wrapper interfaces are unchanged.

- [ ] **Step 4: Final test run**

```bash
cd frontend && npm run test 2>&1 | tail -20
```

Expected: all tests pass (test files are out of scope but should not be broken).

- [ ] **Step 5: Stage**

```bash
git add frontend/src/components/features/plex/CollectionDrawer.tsx \
        frontend/src/components/features/plex/PlaylistDrawer.tsx
```
