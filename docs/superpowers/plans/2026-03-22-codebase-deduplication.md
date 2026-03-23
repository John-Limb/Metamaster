# Codebase Deduplication Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate ~1,700 lines of duplicated logic by extracting shared hooks/utils, merging the two near-identical media collection pages into a config-driven component, and replacing raw HTML with the existing common component library throughout the app.

**Architecture:** Five independent chunks — foundation utilities first, then consumers, then the flagship `MediaCollectionPage` merge, then common-UI enforcement. Each chunk compiles clean and passes tests before moving on.

**Tech Stack:** React 18, TypeScript, Vitest + @testing-library/react, Zustand, Vite

---

## Chunk 1: Foundation — shared hooks and utilities

**Files:**
- Create: `frontend/src/hooks/useEscapeKey.ts`
- Create: `frontend/src/hooks/useFocusTrap.ts`
- Create: `frontend/src/hooks/index.ts`
- Create: `frontend/src/utils/formatting.ts`
- Create: `frontend/src/services/queryUtils.ts`
- Create: `frontend/src/hooks/__tests__/useEscapeKey.test.ts`
- Create: `frontend/src/hooks/__tests__/useFocusTrap.test.ts`
- Create: `frontend/src/utils/__tests__/formatting.test.ts`
- Create: `frontend/src/services/__tests__/queryUtils.test.ts`

---

### Task 1: `useEscapeKey` hook

- [ ] **Step 1: Write the failing test**

```ts
// frontend/src/hooks/__tests__/useEscapeKey.test.ts
import { renderHook } from '@testing-library/react'
import { fireEvent } from '@testing-library/dom'
import { useEscapeKey } from '../useEscapeKey'

describe('useEscapeKey', () => {
  it('calls handler when Escape is pressed and enabled is true', () => {
    const handler = vi.fn()
    renderHook(() => useEscapeKey(handler, true))
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(handler).toHaveBeenCalledTimes(1)
  })

  it('does not call handler when disabled', () => {
    const handler = vi.fn()
    renderHook(() => useEscapeKey(handler, false))
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(handler).not.toHaveBeenCalled()
  })

  it('does not call handler for non-Escape keys', () => {
    const handler = vi.fn()
    renderHook(() => useEscapeKey(handler))
    fireEvent.keyDown(document, { key: 'Enter' })
    expect(handler).not.toHaveBeenCalled()
  })

  it('removes event listener on unmount', () => {
    const handler = vi.fn()
    const spy = vi.spyOn(document, 'removeEventListener')
    const { unmount } = renderHook(() => useEscapeKey(handler))
    unmount()
    expect(spy).toHaveBeenCalledWith('keydown', expect.any(Function))
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npm run test -- src/hooks/__tests__/useEscapeKey.test.ts
```

Expected: FAIL — `useEscapeKey` does not exist

- [ ] **Step 3: Implement `useEscapeKey`**

```ts
// frontend/src/hooks/useEscapeKey.ts
import { useEffect } from 'react'

export function useEscapeKey(handler: () => void, enabled = true): void {
  useEffect(() => {
    if (!enabled) return
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handler()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [enabled, handler])
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd frontend && npm run test -- src/hooks/__tests__/useEscapeKey.test.ts
```

Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/hooks/useEscapeKey.ts frontend/src/hooks/__tests__/useEscapeKey.test.ts
git commit -m "feat(hooks): add useEscapeKey shared hook"
```

---

### Task 2: `useFocusTrap` hook

- [ ] **Step 1: Write the failing test**

```ts
// frontend/src/hooks/__tests__/useFocusTrap.test.ts
import { renderHook } from '@testing-library/react'
import { render, screen, fireEvent } from '@testing-library/react'
import { useRef } from 'react'
import { useFocusTrap } from '../useFocusTrap'

function TrapFixture({ enabled }: { enabled: boolean }) {
  const ref = useRef<HTMLDivElement>(null)
  useFocusTrap(ref, enabled)
  return (
    <div ref={ref}>
      <button data-testid="btn1">First</button>
      <button data-testid="btn2">Second</button>
    </div>
  )
}

describe('useFocusTrap', () => {
  it('focuses the first focusable element when enabled', () => {
    render(<TrapFixture enabled={true} />)
    expect(document.activeElement).toBe(screen.getByTestId('btn1'))
  })

  it('does not move focus when disabled', () => {
    const before = document.activeElement
    render(<TrapFixture enabled={false} />)
    expect(document.activeElement).toBe(before)
  })

  it('wraps Tab from last to first element', () => {
    render(<TrapFixture enabled={true} />)
    const last = screen.getByTestId('btn2')
    last.focus()
    fireEvent.keyDown(document, { key: 'Tab' })
    expect(document.activeElement).toBe(screen.getByTestId('btn1'))
  })

  it('wraps Shift+Tab from first to last element', () => {
    render(<TrapFixture enabled={true} />)
    const first = screen.getByTestId('btn1')
    first.focus()
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true })
    expect(document.activeElement).toBe(screen.getByTestId('btn2'))
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npm run test -- src/hooks/__tests__/useFocusTrap.test.ts
```

Expected: FAIL — `useFocusTrap` does not exist

- [ ] **Step 3: Implement `useFocusTrap`**

```ts
// frontend/src/hooks/useFocusTrap.ts
import { useEffect, type RefObject } from 'react'

const FOCUSABLE =
  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'

export function useFocusTrap(ref: RefObject<HTMLElement | null>, enabled = true): void {
  useEffect(() => {
    if (!enabled || !ref.current) return
    const el = ref.current
    const focusable = el.querySelectorAll<HTMLElement>(FOCUSABLE)
    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    first?.focus()

    const trap = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last?.focus() }
      } else {
        if (document.activeElement === last) { e.preventDefault(); first?.focus() }
      }
    }
    document.addEventListener('keydown', trap)
    return () => document.removeEventListener('keydown', trap)
  }, [enabled, ref])
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd frontend && npm run test -- src/hooks/__tests__/useFocusTrap.test.ts
```

Expected: PASS (4 tests)

- [ ] **Step 5: Create barrel `src/hooks/index.ts`**

```ts
// frontend/src/hooks/index.ts
export { useEscapeKey } from './useEscapeKey'
export { useFocusTrap } from './useFocusTrap'
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/hooks/useFocusTrap.ts frontend/src/hooks/__tests__/useFocusTrap.test.ts frontend/src/hooks/index.ts
git commit -m "feat(hooks): add useFocusTrap shared hook and barrel export"
```

---

### Task 3: `formatting.ts` utilities

The canonical `formatBytes` uses decimal (1e9-based) matching the existing `StoragePage` implementation. Callers of `helpers.formatFileSize` (binary/1024-based) will be migrated to decimal — a minor display difference (~7%).

- [ ] **Step 1: Write the failing test**

```ts
// frontend/src/utils/__tests__/formatting.test.ts
import { formatBytes, formatDuration, formatCodec } from '../formatting'

describe('formatBytes', () => {
  it('formats terabytes', () => expect(formatBytes(1.5e12)).toBe('1.5 TB'))
  it('formats gigabytes', () => expect(formatBytes(4.2e9)).toBe('4.2 GB'))
  it('formats megabytes', () => expect(formatBytes(300e6)).toBe('300 MB'))
  it('formats raw bytes', () => expect(formatBytes(500)).toBe('500 B'))
  it('formats exactly 1 GB', () => expect(formatBytes(1e9)).toBe('1.0 GB'))
})

describe('formatDuration', () => {
  it('formats hours and minutes', () => expect(formatDuration(7384)).toBe('2h 3m'))
  it('formats minutes only when under an hour', () => expect(formatDuration(195)).toBe('3m'))
  it('returns dash for undefined', () => expect(formatDuration(undefined)).toBe('—'))
  it('returns dash for zero', () => expect(formatDuration(0)).toBe('—'))
})

describe('formatCodec', () => {
  it('maps h264 to H.264', () => expect(formatCodec('h264')).toBe('H.264'))
  it('maps hevc to H.265', () => expect(formatCodec('hevc')).toBe('H.265'))
  it('uppercases unknown codecs', () => expect(formatCodec('xyz')).toBe('XYZ'))
  it('returns dash for null', () => expect(formatCodec(null)).toBe('—'))
  it('returns dash for undefined', () => expect(formatCodec(undefined)).toBe('—'))
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npm run test -- src/utils/__tests__/formatting.test.ts
```

Expected: FAIL — `../formatting` does not exist

- [ ] **Step 3: Implement `formatting.ts`**

```ts
// frontend/src/utils/formatting.ts

export function formatBytes(bytes: number): string {
  if (bytes >= 1e12) return `${(bytes / 1e12).toFixed(1)} TB`
  if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(1)} GB`
  if (bytes >= 1e6) return `${(bytes / 1e6).toFixed(0)} MB`
  return `${bytes} B`
}

export function formatDuration(seconds: number | undefined): string {
  if (!seconds) return '—'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

const CODEC_LABEL: Record<string, string> = {
  h264: 'H.264',
  hevc: 'H.265',
  av1: 'AV1',
  vp9: 'VP9',
  mpeg2video: 'MPEG-2',
  vc1: 'VC-1',
  wmv3: 'WMV',
}

export function formatCodec(codec: string | null | undefined): string {
  if (!codec) return '—'
  return CODEC_LABEL[codec.toLowerCase()] ?? codec.toUpperCase()
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd frontend && npm run test -- src/utils/__tests__/formatting.test.ts
```

Expected: PASS (14 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/formatting.ts frontend/src/utils/__tests__/formatting.test.ts
git commit -m "feat(utils): add canonical formatting utilities (formatBytes, formatDuration, formatCodec)"
```

---

### Task 4: `queryUtils.ts`

- [ ] **Step 1: Write the failing test**

```ts
// frontend/src/services/__tests__/queryUtils.test.ts
import { buildPaginationQuery } from '../queryUtils'

describe('buildPaginationQuery', () => {
  it('returns empty string when no args', () => expect(buildPaginationQuery()).toBe(''))
  it('returns page param only', () => expect(buildPaginationQuery(2)).toBe('page=2'))
  it('returns pageSize param only', () => expect(buildPaginationQuery(undefined, 20)).toBe('pageSize=20'))
  it('returns both params', () => expect(buildPaginationQuery(3, 10)).toBe('page=3&pageSize=10'))
  it('ignores page < 1', () => expect(buildPaginationQuery(0, 10)).toBe('pageSize=10'))
  it('ignores pageSize <= 0', () => expect(buildPaginationQuery(1, 0)).toBe('page=1'))
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npm run test -- src/services/__tests__/queryUtils.test.ts
```

Expected: FAIL — `../queryUtils` does not exist

- [ ] **Step 3: Implement `queryUtils.ts`**

```ts
// frontend/src/services/queryUtils.ts

export function buildPaginationQuery(page?: number, pageSize?: number): string {
  const params = new URLSearchParams()
  if (page && page >= 1) params.append('page', String(page))
  if (pageSize && pageSize > 0) params.append('pageSize', String(pageSize))
  return params.toString()
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd frontend && npm run test -- src/services/__tests__/queryUtils.test.ts
```

Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/queryUtils.ts frontend/src/services/__tests__/queryUtils.test.ts
git commit -m "feat(services): add buildPaginationQuery shared utility"
```

---

## Chunk 2: Adopt shared hooks in consumers

**Files:**
- Modify: `frontend/src/components/common/ConfirmDialog.tsx`
- Modify: `frontend/src/components/features/media/MediaDetailModal.tsx`
- Modify: `frontend/src/pages/PlexCollectionsPage.tsx`
- Modify: `frontend/src/pages/PlexPlaylistsPage.tsx`

---

### Task 5: `ConfirmDialog` — use `useEscapeKey` and `useFocusTrap`

The existing `ConfirmDialog.tsx` has three `useEffect` blocks:
1. Lines 33-42: Focus-return on close (keep as-is — not covered by a shared hook)
2. Lines 44-51: Escape key → replace with `useEscapeKey`
3. Lines 53-72: Focus trap + initial focus → replace with `useFocusTrap`

- [ ] **Step 1: Verify existing ConfirmDialog tests pass**

```bash
cd frontend && npm run test -- src/components/common/__tests__/ConfirmDialog
```

Expected: all pass (baseline)

- [ ] **Step 2: Update `ConfirmDialog.tsx`**

Replace the import line and the two useEffects:

```tsx
// frontend/src/components/common/ConfirmDialog.tsx
import React, { useEffect, useRef } from 'react'
import { FaExclamationTriangle, FaTimes } from 'react-icons/fa'
import { useEscapeKey, useFocusTrap } from '@/hooks'
```

Remove the `useEffect` at lines 44-51 (escape key) and replace with:
```tsx
useEscapeKey(onCancel, isOpen)
```

Remove the `useEffect` at lines 53-72 (focus trap) and replace with:
```tsx
useFocusTrap(dialogRef, isOpen)
```

The result after the three hooks (focus-return `useEffect`, `useEscapeKey`, `useFocusTrap`):
```tsx
const titleId = React.useId()
const dialogRef = useRef<HTMLDivElement>(null)
const triggerRef = useRef<Element | null>(null)

useEffect(() => {
  if (isOpen) {
    triggerRef.current = document.activeElement
  } else {
    if (triggerRef.current instanceof HTMLElement) {
      triggerRef.current.focus()
    }
  }
}, [isOpen])

useEscapeKey(onCancel, isOpen)
useFocusTrap(dialogRef, isOpen)
```

- [ ] **Step 3: Run tests**

```bash
cd frontend && npm run test -- src/components/common/__tests__/ConfirmDialog
```

Expected: all pass

- [ ] **Step 4: Type-check**

```bash
cd frontend && npm run type-check
```

Expected: 0 errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/common/ConfirmDialog.tsx
git commit -m "refactor(common): replace useEffect escape/trap in ConfirmDialog with shared hooks"
```

---

### Task 6: `MediaDetailModal` — use `useEscapeKey`

`MediaDetailModal.tsx` has a `useEffect` at lines 87-94 that listens for Escape. Replace it with `useEscapeKey`.

- [ ] **Step 1: Update `MediaDetailModal.tsx`**

Add import:
```tsx
import { useEscapeKey } from '@/hooks'
```

Remove the `useEffect` at lines 87-94 and replace with:
```tsx
useEscapeKey(onClose, isOpen)
```

Remove `useEffect` from the React import if it's no longer used (check for other useEffects first — there's still the data-fetch useEffect at lines 63-85, so keep `useEffect` in the import).

- [ ] **Step 2: Run type-check**

```bash
cd frontend && npm run type-check
```

Expected: 0 errors

- [ ] **Step 3: Run tests**

```bash
cd frontend && npm run test -- src/components/features/media
```

Expected: pass

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/features/media/MediaDetailModal.tsx
git commit -m "refactor(media): replace escape useEffect in MediaDetailModal with useEscapeKey"
```

---

### Task 7: `PlexCollectionsPage` and `PlexPlaylistsPage` — use `useEscapeKey`

Both pages have a `useEffect` that listens for Escape to close a drawer.

- [ ] **Step 1: Update `PlexCollectionsPage.tsx`**

Add import:
```tsx
import { useEscapeKey } from '@/hooks'
```

Find the `useEffect` that calls `handleCloseDrawer` on Escape (around line 41-46). Remove it and replace with:
```tsx
useEscapeKey(handleCloseDrawer, isDrawerOpen)
```

Where `isDrawerOpen` is the state variable controlling drawer visibility (check the actual variable name in the file — likely `selectedCollection !== null` or a dedicated boolean).

- [ ] **Step 2: Update `PlexPlaylistsPage.tsx`**

Same pattern: remove the Escape `useEffect` and replace with:
```tsx
useEscapeKey(handleCloseDrawer, isDrawerOpen)
```

- [ ] **Step 3: Run tests**

```bash
cd frontend && npm run test -- src/pages/__tests__/PlexCollectionsPage
```

Expected: pass (the existing "closes drawer on Escape key" test must still pass)

- [ ] **Step 4: Type-check**

```bash
cd frontend && npm run type-check
```

Expected: 0 errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/PlexCollectionsPage.tsx frontend/src/pages/PlexPlaylistsPage.tsx
git commit -m "refactor(plex): replace escape useEffects with useEscapeKey in Plex pages"
```

---

## Chunk 3: Adopt utilities — formatting and queryUtils

**Files:**
- Modify: `frontend/src/pages/StoragePage.tsx`
- Modify: `frontend/src/components/features/media/MediaDetailModal.tsx`
- Modify: `frontend/src/components/features/movies/MovieDetailPage/MovieDetailPage.tsx`
- Modify: `frontend/src/components/features/movies/MovieCard/MovieCard.tsx`
- Modify: `frontend/src/components/dashboard/StorageChart/StorageChart.tsx`
- Modify: `frontend/src/components/dashboard/LibraryStats/LibraryStats.tsx`
- Modify: `frontend/src/services/movieService.ts`
- Modify: `frontend/src/services/tvShowService.ts`
- Modify: `frontend/src/utils/helpers.ts` (remove `formatFileSize`)
- Modify: `frontend/src/utils/businessLogic.ts` (remove `fileManagement.formatSize`)

---

### Task 8: Migrate `formatFileSize` callers to `formatting.formatBytes`

`helpers.formatFileSize` uses binary (1024), while the new `formatBytes` uses decimal (1e9). Migration replaces both implementations with one canonical function. These 5 files currently import `formatFileSize` from `@/utils/helpers`.

- [ ] **Step 1: Update `MediaDetailModal.tsx`**

Change:
```tsx
import { formatFileSize } from '@/utils/helpers'
```
To:
```tsx
import { formatBytes, formatDuration } from '@/utils/formatting'
```

Replace:
- `formatFileSize(movie.file_size)` → `formatBytes(movie.file_size)`
- The local `formatDuration` function (lines 20-24 in the original) — delete it and use the imported `formatDuration` instead. The local function takes `number`, but `file_duration` in types is `number | undefined`, so the imported `formatDuration(seconds: number | undefined)` signature is correct.

Check usage: anywhere `formatDuration(movie.file_duration)` is called — the imported version handles `undefined`, so no change needed at call sites.

- [ ] **Step 2: Update `MovieDetailPage.tsx`, `MovieCard.tsx`, `StorageChart.tsx`, `LibraryStats.tsx`**

In each file, change:
```tsx
import { formatFileSize } from '@/utils/helpers'
```
To:
```tsx
import { formatBytes } from '@/utils/formatting'
```

And rename all `formatFileSize(...)` calls to `formatBytes(...)`.

- [ ] **Step 3: Remove `formatFileSize` from `helpers.ts`**

Delete lines 2-10 (the `formatFileSize` export) from `src/utils/helpers.ts`.

- [ ] **Step 4: Type-check to confirm no missed callers**

```bash
cd frontend && npm run type-check
```

Expected: 0 errors. If any error mentions `formatFileSize`, update that caller too.

- [ ] **Step 5: Run tests**

```bash
cd frontend && npm run test
```

Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add \
  frontend/src/components/features/media/MediaDetailModal.tsx \
  frontend/src/components/features/movies/MovieDetailPage/MovieDetailPage.tsx \
  frontend/src/components/features/movies/MovieCard/MovieCard.tsx \
  frontend/src/components/dashboard/StorageChart/StorageChart.tsx \
  frontend/src/components/dashboard/LibraryStats/LibraryStats.tsx \
  frontend/src/utils/helpers.ts
git commit -m "refactor(utils): migrate formatFileSize callers to formatting.formatBytes"
```

---

### Task 9: Clean up `StoragePage.tsx` inline functions

`StoragePage.tsx` currently defines `formatBytes`, `formatDuration`, and `formatCodec` inline (lines 5-33, including the `CODEC_LABEL` lookup table). This task migrates all three to `@/utils/formatting` (created in Task 3, which already exports all three).

- [ ] **Step 1: Update `StoragePage.tsx`**

Add at the top of imports:
```tsx
import { formatBytes, formatDuration, formatCodec } from '@/utils/formatting'
```

Delete lines 5-33 (the `CODEC_LABEL` record and the three inline functions).

All existing call sites (`formatBytes(...)`, `formatDuration(...)`, `formatCodec(...)`) remain unchanged since the function names are identical.

Note: `StoragePage` currently has `formatDuration(seconds: number | null)` — the new canonical version accepts `number | undefined`. Since `null` is falsy like `undefined`, the `if (!seconds) return '—'` guard handles both. No call-site changes needed, but update the `StorageSummary`/`StorageFileItem` type annotation if it says `null` (the function will accept `null` due to falsy check, TypeScript will allow `number | undefined` where `number | null` was before — actually no, TypeScript will complain if you pass `null` to `(number | undefined)`. Check the actual type of `item.file_duration` in storageService types.

If `file_duration` is typed as `number | null` in `StorageFileItem`, add `| null` to `formatDuration`'s signature in `formatting.ts`:
```ts
export function formatDuration(seconds: number | null | undefined): string {
```

Run type-check to determine which signature is needed.

- [ ] **Step 2: Type-check**

```bash
cd frontend && npm run type-check
```

Fix any type errors (null vs undefined for `formatDuration`).

- [ ] **Step 3: Run tests**

```bash
cd frontend && npm run test -- src/pages/__tests__/StoragePage
```

Expected: pass

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/StoragePage.tsx frontend/src/utils/formatting.ts
git commit -m "refactor(storage): replace inline format functions with formatting utils"
```

---

### Task 10: Remove dead code from `businessLogic.ts` (Sections 2a and 2c)

`businessLogic.ts` contains `fileManagement.formatSize` (Section 2a duplicate) and `fileManagement.isVideoFile`, `isImageFile`, `isAudioFile` (Section 2c overlaps with `helpers.ts`). A codebase search confirms none of these have callers outside `businessLogic.ts` itself — they are dead code. Delete them.

- [ ] **Step 1: Confirm no callers**

```bash
cd frontend && grep -r "fileManagement\.\(formatSize\|isVideoFile\|isImageFile\|isAudioFile\)" src/ --include="*.ts" --include="*.tsx"
```

Expected: no output (no callers).

- [ ] **Step 2: Remove dead functions from `businessLogic.ts`**

Open `src/utils/businessLogic.ts` and delete:
- `formatSize` method (lines 32-41)
- `isVideoFile` method (lines 43-46)
- `isImageFile` method (lines 48-51)
- `isAudioFile` method (lines 53-56)

Keep: `getExtension`, `getFileType`, `filterByType`, `filterFiles` and all search/filter logic.

- [ ] **Step 3: Type-check**

```bash
cd frontend && npm run type-check
```

Expected: 0 errors

- [ ] **Step 4: Run tests**

```bash
cd frontend && npm run test
```

Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/businessLogic.ts
git commit -m "refactor(utils): remove dead duplicate functions from businessLogic (formatSize, isVideoFile, isImageFile, isAudioFile)"
```

---

### Task 11: Migrate `movieService.ts` and `tvShowService.ts` to `queryUtils`

Both services define an identical private `buildPaginationQuery` function (lines 5-14 in each file). Replace with the shared export.

- [ ] **Step 1: Update `movieService.ts`**

Add import:
```ts
import { buildPaginationQuery } from './queryUtils'
```

Delete the private `buildPaginationQuery` function definition (lines 5-14).

The existing call sites (`buildPaginationQuery(page, pageSize)`) remain unchanged.

- [ ] **Step 2: Update `tvShowService.ts`**

Same change — add import, delete local definition.

- [ ] **Step 3: Type-check**

```bash
cd frontend && npm run type-check
```

Expected: 0 errors

- [ ] **Step 4: Run tests**

```bash
cd frontend && npm run test -- src/services
```

Expected: pass

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/movieService.ts frontend/src/services/tvShowService.ts
git commit -m "refactor(services): replace duplicate buildPaginationQuery with shared queryUtils"
```

---

## Chunk 4: `MediaCollectionPage` + thin wrappers + PlaylistRow deletion

**Files:**
- Create: `frontend/src/components/features/media/MediaCollectionPage/MediaCollectionPage.tsx`
- Create: `frontend/src/components/features/media/MediaCollectionPage/__tests__/MediaCollectionPage.test.tsx`
- Modify: `frontend/src/components/features/movies/MoviesPage/MoviesPage.tsx` (thin wrapper, ~50 lines)
- Modify: `frontend/src/components/features/tvshows/TVShowsPage/TVShowsPage.tsx` (thin wrapper, ~50 lines)
- Delete: `frontend/src/pages/MoviesPage.tsx`
- Delete: `frontend/src/pages/TVShowsPage.tsx`
- Delete: `frontend/src/components/features/plex/PlaylistRow.tsx`
- Modify: `frontend/src/components/features/plex/PlaylistsSection.tsx` (use `PlexItemRow` directly)
- Modify: `frontend/src/pages/PlexPlaylistsPage.tsx` (use `PlexItemRow` directly)
- Modify: `frontend/src/components/features/media/index.ts` (add `MediaCollectionPage` export if barrel exists)

---

### Task 12: Verify legacy page files are unreachable

Before deleting `pages/MoviesPage.tsx` and `pages/TVShowsPage.tsx`, confirm `App.tsx` routes to the `components/features/` versions.

- [ ] **Step 1: Check routes**

```bash
grep -n "MoviesPage\|TVShowsPage\|movies\|tvshows\|tv-shows" frontend/src/App.tsx
```

Confirm the active routes import from `components/features/` (or use lazy imports pointing there), not from `pages/`. If any route still points to `pages/MoviesPage` or `pages/TVShowsPage`, update it to the `components/features/` version before proceeding.

---

### Task 13: Build `MediaCollectionPage`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/components/features/media/MediaCollectionPage/__tests__/MediaCollectionPage.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { MediaCollectionPage, type MediaCollectionConfig, type MediaCollectionStore } from '../MediaCollectionPage'

function makeStore<T>(overrides: Partial<MediaCollectionStore<T>> = {}): MediaCollectionStore<T> {
  return {
    items: [],
    total: 0,
    currentPage: 1,
    isLoading: false,
    error: null,
    fetchItems: vi.fn(),
    ...overrides,
  }
}

const baseConfig: MediaCollectionConfig<{ id: string; title: string }> = {
  title: 'Test Library',
  mediaType: 'movie',
  cssPrefix: 'test-page',
  useStore: () => makeStore(),
  onScanDirectory: vi.fn().mockResolvedValue({ files_synced: 2, items_created: 1 }),
  formatScanResult: (r) => `${r.files_synced} synced, ${r.items_created} created`,
  renderCard: (item) => <div key={item.id}>{item.title}</div>,
  filterSections: [],
  sortOptions: [],
  defaultSort: 'name-asc',
}

function renderPage(configOverrides = {}) {
  const config = { ...baseConfig, ...configOverrides }
  return render(
    <MemoryRouter>
      <MediaCollectionPage config={config} />
    </MemoryRouter>
  )
}

describe('MediaCollectionPage', () => {
  it('renders the page title', () => {
    renderPage()
    expect(screen.getByRole('heading', { name: 'Test Library' })).toBeInTheDocument()
  })

  it('calls fetchItems on mount', () => {
    const fetchItems = vi.fn()
    renderPage({ useStore: () => makeStore({ fetchItems }) })
    expect(fetchItems).toHaveBeenCalledWith(1, 12)
  })

  it('shows loading skeletons when isLoading=true', () => {
    renderPage({ useStore: () => makeStore({ isLoading: true }) })
    // SkeletonCard renders with data-testid or specific class — check actual SkeletonCard output
    expect(document.querySelectorAll('.skeleton-card').length).toBeGreaterThan(0)
  })

  it('shows error AlertMessage when error is set', () => {
    renderPage({ useStore: () => makeStore({ error: 'Network error' }) })
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText('Network error')).toBeInTheDocument()
  })

  it('shows scan button and triggers scan', async () => {
    const onScanDirectory = vi.fn().mockResolvedValue({ files_synced: 3, items_created: 2 })
    renderPage({ onScanDirectory })
    fireEvent.click(screen.getByRole('button', { name: /scan now/i }))
    await waitFor(() => expect(onScanDirectory).toHaveBeenCalled())
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npm run test -- src/components/features/media/MediaCollectionPage/__tests__/MediaCollectionPage.test.tsx
```

Expected: FAIL — `MediaCollectionPage` does not exist

- [ ] **Step 3: Implement `MediaCollectionPage`**

```tsx
// frontend/src/components/features/media/MediaCollectionPage/MediaCollectionPage.tsx
import React, { useState, useCallback, useEffect } from 'react'
import { Button, Pagination, EmptyState, SkeletonCard, AlertMessage } from '@/components/common'
import { FilterPanel, type FilterSection } from '@/components/features/filter'
import { SortDropdown, type SortOption } from '@/components/features/sort'
import { MediaDetailModal } from '@/components/features/media/MediaDetailModal'
import { useUIStore } from '@/stores/uiStore'
import type { PlexMismatchItem } from '@/services/plexService'
import { usePlexStore } from '@/stores/plexStore'

export interface MediaCollectionStore<TItem> {
  items: TItem[]
  total: number
  currentPage: number
  isLoading: boolean
  error: string | null
  fetchItems: (page?: number, pageSize?: number) => Promise<void>
}

export interface MediaCollectionConfig<TItem extends { id: string }> {
  title: string
  mediaType: 'movie' | 'tv_show'
  cssPrefix: string
  useStore: () => MediaCollectionStore<TItem>
  onScanDirectory: () => Promise<{ files_synced: number; items_created: number }>
  formatScanResult: (result: { files_synced: number; items_created: number }) => string
  renderCard: (item: TItem, mismatch: PlexMismatchItem | undefined) => React.ReactNode
  filterSections: FilterSection[]
  sortOptions: SortOption[]
  defaultSort: string
}

const ITEMS_PER_PAGE = 12

const GRID_ICON = (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
    <rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" />
  </svg>
)

const LIST_ICON = (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="8" y1="6" x2="21" y2="6" /><line x1="8" y1="12" x2="21" y2="12" />
    <line x1="8" y1="18" x2="21" y2="18" /><line x1="3" y1="6" x2="3.01" y2="6" />
    <line x1="3" y1="12" x2="3.01" y2="12" /><line x1="3" y1="18" x2="3.01" y2="18" />
  </svg>
)

const SEARCH_ICON = (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
  </svg>
)

function pageSubtitle(isLoading: boolean, total: number, noun: string): string {
  if (isLoading) return 'Loading...'
  if (total > 0) return `${total} ${noun}${total !== 1 ? 's' : ''} in your library`
  return `No ${noun}s found`
}

interface GridBodyProps<TItem extends { id: string }> {
  isLoading: boolean
  items: TItem[]
  viewMode: 'grid' | 'list'
  cssPrefix: string
  currentPage: number
  totalPages: number
  mismatches: PlexMismatchItem[]
  onClearFilters: () => void
  onItemClick: (id: string) => void
  onPageChange: (page: number) => void
  renderCard: (item: TItem, mismatch: PlexMismatchItem | undefined) => React.ReactNode
  emptyTitle: string
  emptyDescription: string
}

function GridBody<TItem extends { id: string }>({
  isLoading, items, viewMode, cssPrefix, currentPage, totalPages,
  mismatches, onClearFilters, onItemClick, onPageChange, renderCard,
  emptyTitle, emptyDescription,
}: GridBodyProps<TItem>) {
  if (isLoading) {
    return (
      <div className={`${cssPrefix}__grid ${cssPrefix}__grid--${viewMode}`}>
        {Array.from({ length: ITEMS_PER_PAGE }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }
  if (items.length === 0) {
    return (
      <EmptyState
        variant="empty"
        title={emptyTitle}
        description={emptyDescription}
        action={{ label: 'Clear filters', onClick: onClearFilters }}
      />
    )
  }
  return (
    <>
      <div className={`${cssPrefix}__grid ${cssPrefix}__grid--${viewMode}`}>
        {items.map((item) => {
          const mismatch = mismatches.find((m) => m.item_id === Number(item.id))
          return (
            <div key={item.id} onClick={() => onItemClick(item.id)}>
              {renderCard(item, mismatch)}
            </div>
          )
        })}
      </div>
      {totalPages > 1 && (
        <div className={`${cssPrefix}__pagination`}>
          <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={onPageChange} />
        </div>
      )}
    </>
  )
}

export function MediaCollectionPage<TItem extends { id: string }>({
  config,
}: {
  config: MediaCollectionConfig<TItem>
}) {
  const {
    title, cssPrefix, mediaType, useStore,
    onScanDirectory, formatScanResult,
    renderCard, filterSections, sortOptions, defaultSort,
  } = config

  const store = useStore()
  const { items, total, currentPage, isLoading, error, fetchItems } = store
  const { mismatches } = usePlexStore()
  const { addToast } = useUIStore()

  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({})
  const [sortValue, setSortValue] = useState(defaultSort)
  const [isScanning, setIsScanning] = useState(false)
  const [modalItemId, setModalItemId] = useState<string | null>(null)

  useEffect(() => {
    fetchItems(1, ITEMS_PER_PAGE)
  }, [fetchItems])

  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)
  const noun = mediaType === 'movie' ? 'movie' : 'show'

  const handleFilterChange = useCallback((sectionId: string, values: string[]) => {
    setSelectedFilters((prev) => ({ ...prev, [sectionId]: values }))
  }, [])

  const handleClearFilters = useCallback(() => setSelectedFilters({}), [])

  const handlePageChange = useCallback((page: number) => {
    fetchItems(page, ITEMS_PER_PAGE)
  }, [fetchItems])

  const handleScanDirectory = useCallback(async () => {
    setIsScanning(true)
    try {
      const result = await onScanDirectory()
      addToast({ type: 'success', message: formatScanResult(result), duration: 5000 })
      fetchItems(1, ITEMS_PER_PAGE)
    } catch {
      addToast({ type: 'error', message: 'Scan failed. Check the server logs for details.', duration: 5000 })
    } finally {
      setIsScanning(false)
    }
  }, [onScanDirectory, formatScanResult, fetchItems, addToast])

  return (
    <div className={cssPrefix}>
      <header className={`${cssPrefix}__header`}>
        <div className={`${cssPrefix}__title-section`}>
          <h1 className={`${cssPrefix}__title`}>{title}</h1>
          <p className={`${cssPrefix}__subtitle`}>{pageSubtitle(isLoading, total, noun)}</p>
        </div>
        <div className={`${cssPrefix}__search`}>
          <input
            type="text"
            placeholder={`Search ${title.toLowerCase()}...`}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={`${cssPrefix}__search-input`}
            aria-label={`Search ${title.toLowerCase()}`}
          />
        </div>
      </header>

      <div className={`${cssPrefix}__toolbar`}>
        <div className={`${cssPrefix}__toolbar-left`}>
          <FilterPanel
            sections={filterSections}
            selectedFilters={selectedFilters}
            onFilterChange={handleFilterChange}
            onClearAll={handleClearFilters}
            isOpen={isFilterOpen}
            onToggle={() => setIsFilterOpen(!isFilterOpen)}
          />
          <SortDropdown options={sortOptions} value={sortValue} onChange={setSortValue} />
        </div>
        <div className={`${cssPrefix}__toolbar-right`}>
          <Button variant="secondary" size="sm" onClick={handleScanDirectory} disabled={isScanning}>
            {isScanning ? 'Scanning...' : 'Scan Now'}
          </Button>
          <div className={`${cssPrefix}__view-toggle`} role="group" aria-label="View mode">
            <Button variant={viewMode === 'grid' ? 'primary' : 'secondary'} size="sm" onClick={() => setViewMode('grid')} aria-pressed={viewMode === 'grid'}>{GRID_ICON}</Button>
            <Button variant={viewMode === 'list' ? 'primary' : 'secondary'} size="sm" onClick={() => setViewMode('list')} aria-pressed={viewMode === 'list'}>{LIST_ICON}</Button>
          </div>
        </div>
      </div>

      <main className={`${cssPrefix}__content`}>
        {error && (
          <AlertMessage
            variant="error"
            message={<><p>{error}</p><button onClick={() => fetchItems(currentPage, ITEMS_PER_PAGE)} className="mt-2 text-sm underline hover:no-underline">Try again</button></>}
            className="mb-4"
          />
        )}
        <GridBody
          isLoading={isLoading}
          items={items}
          viewMode={viewMode}
          cssPrefix={cssPrefix}
          currentPage={currentPage}
          totalPages={totalPages}
          mismatches={mismatches}
          onClearFilters={handleClearFilters}
          onItemClick={setModalItemId}
          onPageChange={handlePageChange}
          renderCard={renderCard}
          emptyTitle={`No ${title.toLowerCase()} found`}
          emptyDescription={`Your ${title.toLowerCase()} library will appear here once media files are synced.`}
        />
      </main>

      <MediaDetailModal
        isOpen={modalItemId !== null}
        mediaType={mediaType}
        mediaId={modalItemId || ''}
        onClose={() => setModalItemId(null)}
        onMetadataSynced={() => fetchItems(currentPage, ITEMS_PER_PAGE)}
      />
    </div>
  )
}
```

**`renderCard` signature matches the spec (two args):**
```tsx
renderCard: (item: TItem, mismatch: PlexMismatchItem | undefined) => React.ReactNode
```

The `GridBody` keeps the outer `div onClick={() => setModalItemId(item.id)}` wrapper as shown above. Card-level action buttons (edit, delete, add to queue) must call `e.stopPropagation()` to prevent bubble-up — the existing card components already do this. Each thin page's `renderCard` passes `onClick={() => setModalItemId(item.id)}` directly to the card as well if the card component requires it, but the outer wrapper is the primary mechanism.

- [ ] **Step 4: Run tests**

```bash
cd frontend && npm run test -- src/components/features/media/MediaCollectionPage
```

Expected: pass

- [ ] **Step 5: Type-check**

```bash
cd frontend && npm run type-check
```

Expected: 0 errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/features/media/MediaCollectionPage/
git commit -m "feat(media): add config-driven MediaCollectionPage shared component"
```

---

### Task 14: Refactor `MoviesPage.tsx` and `TVShowsPage.tsx` to thin wrappers

Replace the existing large components with thin adapter-hook + config assemblers (~50 lines each).

- [ ] **Step 1: Rewrite `MoviesPage.tsx`**

```tsx
// frontend/src/components/features/movies/MoviesPage/MoviesPage.tsx
import React from 'react'
import { MovieCard } from '../MovieCard'
import { MediaCollectionPage, type MediaCollectionConfig, type MediaCollectionStore } from '@/components/features/media/MediaCollectionPage/MediaCollectionPage'
import { useMovieStore } from '@/stores/movieStore'
import { movieService } from '@/services/movieService'
import type { Movie } from '@/types'
import type { PlexMismatchItem } from '@/services/plexService'
import './MoviesPage.css'

function useMoviesCollectionStore(): MediaCollectionStore<Movie> {
  const { movies, totalMovies, currentPage, isLoading, error, fetchMovies } = useMovieStore()
  return { items: movies, total: totalMovies, currentPage, isLoading, error, fetchItems: fetchMovies }
}

const filterSections = [
  {
    id: 'genre', label: 'Genre', multiSelect: true,
    options: [
      { value: 'action', label: 'Action', count: 0 },
      { value: 'comedy', label: 'Comedy', count: 0 },
      { value: 'drama', label: 'Drama', count: 0 },
      { value: 'horror', label: 'Horror', count: 0 },
      { value: 'sci-fi', label: 'Sci-Fi', count: 0 },
      { value: 'thriller', label: 'Thriller', count: 0 },
    ],
  },
  {
    id: 'year', label: 'Year', multiSelect: true,
    options: [
      { value: '2024', label: '2024', count: 0 }, { value: '2023', label: '2023', count: 0 },
      { value: '2022', label: '2022', count: 0 }, { value: '2021', label: '2021', count: 0 },
      { value: '2020', label: '2020', count: 0 },
    ],
  },
  {
    id: 'rating', label: 'Rating', multiSelect: false,
    options: [
      { value: '5', label: '5 Stars', count: 0 }, { value: '4', label: '4+ Stars', count: 0 },
      { value: '3', label: '3+ Stars', count: 0 },
    ],
  },
]

const sortOptions = [
  { value: 'title-asc', label: 'Title', direction: 'asc' as const },
  { value: 'title-desc', label: 'Title', direction: 'desc' as const },
  { value: 'year-asc', label: 'Year', direction: 'asc' as const },
  { value: 'year-desc', label: 'Year', direction: 'desc' as const },
  { value: 'rating-asc', label: 'Rating', direction: 'asc' as const },
  { value: 'rating-desc', label: 'Rating', direction: 'desc' as const },
  { value: 'date-added', label: 'Date Added' },
]

// renderCard matches the spec 2-arg signature. The outer click-to-open-modal wrapper
// is handled by GridBody inside MediaCollectionPage.
function renderMovieCard(movie: Movie, mismatch: PlexMismatchItem | undefined) {
  return (
    <MovieCard
      key={movie.id}
      id={String(movie.id)}
      title={movie.title}
      year={movie.year ?? 0}
      rating={movie.rating}
      poster_url={movie.poster_url}
      genres={movie.genre}
      quality={movie.quality}
      resolution={movie.resolution}
      codec_video={movie.codec_video}
      codec_audio={movie.codec_audio}
      audio_channels={movie.audio_channels}
      file_size={movie.file_size}
      file_duration={movie.file_duration}
      mismatch={mismatch}
      ourTmdbId={movie.tmdb_id ?? ''}
      onResolve={async () => {}}
      onClick={() => {}}
      onAddToQueue={() => console.log('Add to queue:', movie.id)}
      onScan={() => movieService.scanMovie(String(movie.id))}
      onEdit={() => console.log('Edit:', movie.id)}
      onDelete={() => console.log('Delete:', movie.id)}
      isWatched={movie.is_watched}
    />
  )
}

const moviesConfig: MediaCollectionConfig<Movie> = {
  title: 'Movies',
  mediaType: 'movie',
  cssPrefix: 'movies-page',
  useStore: useMoviesCollectionStore,
  onScanDirectory: async () => {
    const result = await movieService.scanDirectory()
    return { files_synced: result.files_synced, items_created: result.movies_created }
  },
  formatScanResult: (r) => `Scan complete: ${r.files_synced} file(s) synced, ${r.items_created} movie(s) created`,
  renderCard: renderMovieCard,
  filterSections,
  sortOptions,
  defaultSort: 'title-asc',
}

const MoviesPage: React.FC = () => <MediaCollectionPage config={moviesConfig} />

export default MoviesPage
```

- [ ] **Step 2: Rewrite `TVShowsPage.tsx`**

```tsx
// frontend/src/components/features/tvshows/TVShowsPage/TVShowsPage.tsx
import React from 'react'
import { TVShowCard } from '../TVShowCard'
import { MediaCollectionPage, type MediaCollectionConfig, type MediaCollectionStore } from '@/components/features/media/MediaCollectionPage/MediaCollectionPage'
import { useTVShowStore } from '@/stores/tvShowStore'
import { tvShowService } from '@/services/tvShowService'
import { usePlexStore } from '@/stores/plexStore'
import type { TVShow } from '@/types'
import type { PlexMismatchItem } from '@/services/plexService'
import './TVShowsPage.css'

function useTVShowsCollectionStore(): MediaCollectionStore<TVShow> {
  const { tvShows, totalTVShows, currentPage, isLoading, error, fetchTVShows } = useTVShowStore()
  return { items: tvShows, total: totalTVShows, currentPage, isLoading, error, fetchItems: fetchTVShows }
}

const filterSections = [
  {
    id: 'genre', label: 'Genre', multiSelect: true,
    options: [
      { value: 'action', label: 'Action', count: 0 },
      { value: 'comedy', label: 'Comedy', count: 0 },
      { value: 'drama', label: 'Drama', count: 0 },
      { value: 'horror', label: 'Horror', count: 0 },
      { value: 'sci-fi', label: 'Sci-Fi', count: 0 },
      { value: 'thriller', label: 'Thriller', count: 0 },
    ],
  },
  {
    id: 'status', label: 'Status', multiSelect: true,
    options: [
      { value: 'continuing', label: 'Continuing', count: 0 },
      { value: 'ended', label: 'Ended', count: 0 },
    ],
  },
  {
    id: 'rating', label: 'Rating', multiSelect: false,
    options: [
      { value: '5', label: '5 Stars', count: 0 }, { value: '4', label: '4+ Stars', count: 0 },
      { value: '3', label: '3+ Stars', count: 0 },
    ],
  },
]

const sortOptions = [
  { value: 'name-asc', label: 'Name', direction: 'asc' as const },
  { value: 'name-desc', label: 'Name', direction: 'desc' as const },
  { value: 'rating-asc', label: 'Rating', direction: 'asc' as const },
  { value: 'rating-desc', label: 'Rating', direction: 'desc' as const },
]

// renderCard uses the 2-arg spec signature. resolveMismatch is accessed via hook
// inside the component, so TVShowsPage defines config inside the component body.
// (The static config object above holds everything except renderCard.)

const tvShowsStaticConfig = {
  title: 'TV Shows',
  mediaType: 'tv_show' as const,
  cssPrefix: 'tvshows-page',
  useStore: useTVShowsCollectionStore,
  onScanDirectory: async () => {
    const result = await tvShowService.scanDirectory()
    return { files_synced: result.files_synced, items_created: result.shows_created }
  },
  formatScanResult: (r: { files_synced: number; items_created: number }) =>
    `Scan complete: ${r.files_synced} file(s) synced, ${r.items_created} episode(s) created`,
  filterSections,
  sortOptions,
  defaultSort: 'name-asc',
}

const TVShowsPage: React.FC = () => {
  const { resolveMismatch } = usePlexStore()
  const config: MediaCollectionConfig<TVShow> = {
    ...tvShowsStaticConfig,
    renderCard: (show, mismatch) => (
      <TVShowCard
        key={show.id}
        id={String(show.id)}
        title={show.title}
        rating={show.rating}
        poster_url={show.poster_url}
        genres={show.genre}
        seasons={show.seasons}
        episodes={show.episodes}
        mismatch={mismatch}
        ourTmdbId={show.tmdb_id ?? ''}
        onResolve={resolveMismatch}
        onClick={() => {}}
        onAddToQueue={() => console.log('Add to queue:', show.id)}
        onEdit={() => console.log('Edit:', show.id)}
        onDelete={() => console.log('Delete:', show.id)}
        watchedEpisodeCount={show.watched_episode_count}
        totalEpisodeCount={show.total_episode_count}
      />
    ),
  }
  return <MediaCollectionPage config={config} />
}

export default TVShowsPage
```

The same inside-component pattern works for `MoviesPage` if it needs store hooks. Since `MoviesPage` uses `movieService.scanMovie` (no hook needed), its module-level `renderMovieCard` and `moviesConfig` are fine as-is.

- [ ] **Step 3: Type-check**

```bash
cd frontend && npm run type-check
```

Expected: 0 errors. If type errors on `useTVShowStore` returning `fetchTVShows` — check the store exports and adjust the adapter hook accordingly.

- [ ] **Step 4: Run tests**

```bash
cd frontend && npm run test
```

Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add \
  frontend/src/components/features/movies/MoviesPage/MoviesPage.tsx \
  frontend/src/components/features/tvshows/TVShowsPage/TVShowsPage.tsx
git commit -m "refactor(media): replace MoviesPage and TVShowsPage with thin MediaCollectionPage wrappers"
```

---

### Task 15: Delete legacy page files

- [ ] **Step 1: Confirm routes are clear (from Task 12)**

If not already done, confirm `App.tsx` has no routes pointing to `pages/MoviesPage` or `pages/TVShowsPage`.

- [ ] **Step 2: Delete the files**

```bash
rm frontend/src/pages/MoviesPage.tsx frontend/src/pages/TVShowsPage.tsx
```

- [ ] **Step 3: Type-check**

```bash
cd frontend && npm run type-check
```

Expected: 0 errors. If any import errors appear, update the importer.

- [ ] **Step 4: Run all tests**

```bash
cd frontend && npm run test
```

Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add -A frontend/src/pages/MoviesPage.tsx frontend/src/pages/TVShowsPage.tsx
git commit -m "chore: delete legacy pages/MoviesPage.tsx and pages/TVShowsPage.tsx"
```

---

### Task 16: Delete `PlaylistRow.tsx` and update call sites

`PlaylistRow` is a zero-logic passthrough to `PlexItemRow`. Two consumers: `PlaylistsSection.tsx` and `PlexPlaylistsPage.tsx`.

- [ ] **Step 1: Update `PlaylistsSection.tsx`**

Change:
```tsx
import { PlaylistRow } from './PlaylistRow'
```
To:
```tsx
import { PlexItemRow } from './PlexItemRow'
```

Replace every `<PlaylistRow` with `<PlexItemRow` (same props — `PlaylistRow` passes all its props through).

- [ ] **Step 2: Update `PlexPlaylistsPage.tsx`**

Same: replace `PlaylistRow` import with `PlexItemRow` and rename all usage.

- [ ] **Step 3: Delete `PlaylistRow.tsx`**

```bash
rm frontend/src/components/features/plex/PlaylistRow.tsx
```

Also delete the test file if it only tests the passthrough behaviour (it will fail after deletion):
```bash
rm frontend/src/components/features/plex/__tests__/PlaylistRow.test.tsx
```

- [ ] **Step 4: Update `PlexCollectionsPage.test.tsx`**

The test file at `src/pages/__tests__/PlexCollectionsPage.test.tsx` has a `vi.mock` for `PlaylistRow` (line 56). Remove or update that mock since `PlaylistRow` no longer exists.

- [ ] **Step 5: Type-check and test**

```bash
cd frontend && npm run type-check && npm run test
```

Expected: 0 errors, all tests pass

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor(plex): delete PlaylistRow passthrough — use PlexItemRow directly"
```

---

## Chunk 5: Common UI enforcement

**Files:**
- Modify: `frontend/src/pages/EnrichmentPage.tsx`
- Modify: `frontend/src/pages/OrganisationPage.tsx`

---

### Task 17: `EnrichmentPage` — replace raw `<button>` pagination with `<Pagination>` and `usePagination`

`EnrichmentPage.tsx` manages page state with `const [page, setPage] = useState(1)` and renders raw `<button>` Previous/Next elements (lines 220-242).

- [ ] **Step 1: Read the full pagination state in `EnrichmentPage.tsx`**

Identify: the `page` state variable, `totalPages` computation, and the `<button>` pagination block.

- [ ] **Step 2: Update `EnrichmentPage.tsx`**

Add imports:
```tsx
import { Pagination } from '@/components/common'
import { usePagination } from '@/hooks/usePagination'
```

Replace `const [page, setPage] = useState(1)` with:
```tsx
const { currentPage: page, goToPage, nextPage, prevPage, canGoNext, canGoPrev } = usePagination({
  totalPages,
  initialPage: 1,
})
```

Anywhere `setPage(...)` is called, replace with `goToPage(...)`.

Replace the pagination `<div>` block (lines 220-242) with:
```tsx
{totalPages > 1 && (
  <div className="flex items-center justify-between text-sm text-hint">
    <span>{total} total</span>
    <Pagination currentPage={page} totalPages={totalPages} onPageChange={goToPage} />
  </div>
)}
```

**Note:** Check `usePagination`'s actual API at `src/hooks/usePagination.ts`. The hook may accept `{ totalPages, initialPage }` or `{ total, pageSize }` — read the file first and match the call signature.

- [ ] **Step 3: Type-check**

```bash
cd frontend && npm run type-check
```

Expected: 0 errors

- [ ] **Step 4: Run tests**

```bash
cd frontend && npm run test -- src/pages/__tests__/EnrichmentPage
```

Expected: pass

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/EnrichmentPage.tsx
git commit -m "refactor(enrichment): replace raw pagination buttons with Pagination component"
```

---

### Task 18: `StoragePage` — replace `<Button>` Previous/Next pagination with `<Pagination>`

`StoragePage.tsx` already uses `<Button>` (not raw `<button>`) for Previous/Next pagination inside `StorageFileTable` (lines ~297-318). Replace with the `<Pagination>` component and `usePagination` hook for consistency with the spec.

- [ ] **Step 1: Read the pagination section of `StoragePage.tsx`**

Identify the state variable for `page`, `totalPages` computation, `onPageChange` prop or local state setter, and the `<Button>` Previous/Next block.

- [ ] **Step 2: Update `StoragePage.tsx`**

Add imports:
```tsx
import { Pagination } from '@/components/common'
import { usePagination } from '@/hooks/usePagination'
```

Replace the `page` state and setter in the component that manages pagination (likely `StorageFileTable` or the parent) with `usePagination`. Check `src/hooks/usePagination.ts` for the exact API first.

Replace the `<Button>` Previous/Next block with:
```tsx
{totalPages > 1 && (
  <div className="flex items-center justify-between px-4 py-3 border-t border-edge">
    <Pagination currentPage={page} totalPages={totalPages} onPageChange={goToPage} />
  </div>
)}
```

- [ ] **Step 3: Type-check**

```bash
cd frontend && npm run type-check
```

Expected: 0 errors

- [ ] **Step 4: Run tests**

```bash
cd frontend && npm run test -- src/pages/__tests__/StoragePage
```

Expected: pass (or no test file — check)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/StoragePage.tsx
git commit -m "refactor(storage): replace Previous/Next buttons with Pagination component"
```

---

### Task 19: `SettingsPage` — verify and enforce common UI

`SettingsPage.tsx` is listed in the spec for a common UI enforcement pass. The current version already imports `Button`, `CheckboxInput`, `RadioInput` from `@/components/common`. This task confirms no raw `<button>` or inline alert `<div>` patterns remain.

- [ ] **Step 1: Check for raw `<button>` elements**

```bash
grep -n '<button' frontend/src/pages/SettingsPage.tsx
```

If any raw `<button>` appear (outside component library internals), replace with `<Button>`.

- [ ] **Step 2: Check for inline alert divs**

```bash
grep -n 'text-red\|text-green\|alert\|bg-red\|bg-green' frontend/src/pages/SettingsPage.tsx
```

If any inline status/alert divs appear (not using `<AlertMessage>`), replace with `<AlertMessage variant="error|success">`.

- [ ] **Step 3: Type-check and lint**

```bash
cd frontend && npm run type-check && npm run lint
```

Expected: 0 errors

- [ ] **Step 4: Commit if changes were made**

```bash
git add frontend/src/pages/SettingsPage.tsx
git commit -m "refactor(settings): enforce common UI components"
```

If no changes were needed, skip the commit.

---

### Task 20: `OrganisationPage` — replace raw `<button>` elements with `<Button>`

`OrganisationPage.tsx` has approximately 8 raw `<button>` elements (confirmed from codebase grep). Replace each with the `<Button>` component.

- [ ] **Step 1: Read `OrganisationPage.tsx` fully**

Identify all raw `<button>` elements, their `onClick` handlers, `disabled` states, and CSS classes.

- [ ] **Step 2: Replace each `<button>` with `<Button>`**

Pattern: `<button type="button" onClick={fn} className="...hover:underline...">text</button>` becomes `<Button variant="ghost" size="sm" onClick={fn}>text</Button>` (or `variant="secondary"` for more prominent buttons).

Preserve `disabled` props directly — `<Button disabled={...}>` is supported.

For the expand/collapse text buttons (`onExpandAll`, `onCollapseAll`) that use `hover:underline` style — use `variant="ghost"`.

For the primary action buttons (Apply, Preview etc.) — use existing `variant="primary"` or `variant="secondary"` as appropriate.

- [ ] **Step 3: Type-check and lint**

```bash
cd frontend && npm run type-check && npm run lint
```

Expected: 0 errors

- [ ] **Step 4: Run tests**

```bash
cd frontend && npm run test -- src/pages/__tests__/OrganisationPage
```

Expected: pass (or no test file exists — check)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/OrganisationPage.tsx
git commit -m "refactor(organisation): replace raw button elements with Button component"
```

---

## Final validation

- [ ] **Run full test suite**

```bash
cd frontend && npm run test
```

Expected: all pass

- [ ] **Run type-check**

```bash
cd frontend && npm run type-check
```

Expected: 0 errors

- [ ] **Run lint**

```bash
cd frontend && npm run lint
```

Expected: 0 errors/warnings introduced by this work

- [ ] **Stage all changes**

```bash
git status
```

Review staged files. Per project CLAUDE.md: stage only, do not commit — let the user commit.
