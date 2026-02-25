# Organisation Page Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move file renaming from a modal into a dedicated `/organisation` page with a collapsible TV Show → Season → Episode accordion tree; keep only the Plex/Jellyfin preset selector in Settings.

**Architecture:** New `OrganisationPage` at `/organisation`. Backend `get_preview` gains `show_title` + `season_number` on episode entries so the frontend can group them without path-parsing. `App.tsx` and `Sidebar.tsx` get the new route/nav entry. `OrganisationModal` is deleted; `SettingsPage` retains only the preset selector.

**Tech Stack:** FastAPI/SQLAlchemy (Python 3.13), React 19/TypeScript/Tailwind, existing `organisationService.ts`.

---

### Task 1: Create feature branch

**Step 1: Create and switch to the new branch**

Run from the repo root (currently on `feat/file-organisation`):

```bash
git checkout -b feat/organisation-page
```

**Step 2: Verify you're on the right branch**

```bash
git branch --show-current
# Expected: feat/organisation-page
```

**Step 3: Commit (nothing to commit yet — just the branch)**

No commit needed; the branch is ready.

---

### Task 2: Backend — add show_title and season_number to preview

**Files:**
- Modify: `app/domain/organisation/service.py` (lines 180–200 — the episode `append` inside `get_preview`)
- Modify: `app/api/v1/organisation/endpoints.py` (lines 44–48 — `RenamePreviewItem`)
- Test: `tests/test_organisation_service.py`

**Step 1: Write the failing test**

Add to the bottom of `tests/test_organisation_service.py`:

```python
# ---------------------------------------------------------------------------
# get_preview — episode fields
# ---------------------------------------------------------------------------

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.domain.tv_shows.models import TVShow, Season, Episode, EpisodeFile
from app.domain.organisation.service import get_preview


@pytest.fixture
def preview_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_get_preview_episode_includes_show_and_season(preview_db):
    """Episode entries in get_preview include show_title and season_number."""
    show = TVShow(title="Breaking Bad")
    preview_db.add(show)
    preview_db.flush()

    season = Season(show_id=show.id, season_number=1)
    preview_db.add(season)
    preview_db.flush()

    episode = Episode(season_id=season.id, episode_number=1, title="Pilot")
    preview_db.add(episode)
    preview_db.flush()

    # Path that won't match the Plex target, so it appears in preview
    ef = EpisodeFile(episode_id=episode.id, file_path="/downloads/bb_s01e01.mkv")
    preview_db.add(ef)
    preview_db.commit()

    result = get_preview(preview_db, "plex")

    assert len(result["episodes"]) == 1
    ep = result["episodes"][0]
    assert ep["show_title"] == "Breaking Bad"
    assert ep["season_number"] == 1
```

**Step 2: Run it to verify it fails**

```bash
pytest tests/test_organisation_service.py::test_get_preview_episode_includes_show_and_season -v
```

Expected: `FAILED` — `KeyError: 'show_title'`

**Step 3: Add fields to `get_preview` in `app/domain/organisation/service.py`**

Find the `episodes.append({...})` block inside the `for ef in episode.files:` loop (around line 194) and add two fields:

```python
                    if Path(ef.file_path).resolve() != Path(target).resolve():
                        episodes.append({
                            "file_id": ef.id,
                            "file_type": "episode",
                            "current_path": ef.file_path,
                            "target_path": target,
                            "show_title": show.title,
                            "season_number": season.season_number,
                        })
```

**Step 4: Add optional fields to `RenamePreviewItem` in `app/api/v1/organisation/endpoints.py`**

Replace the existing `RenamePreviewItem` class (lines 44–48):

```python
class RenamePreviewItem(BaseModel):
    file_id: int
    file_type: str
    current_path: str
    target_path: str
    show_title: str | None = None
    season_number: int | None = None
```

**Step 5: Run the test to verify it passes**

```bash
pytest tests/test_organisation_service.py::test_get_preview_episode_includes_show_and_season -v
```

Expected: `PASSED`

**Step 6: Run the full backend test suite**

```bash
pytest
```

Expected: all tests pass.

**Step 7: Commit**

```bash
git add app/domain/organisation/service.py \
        app/api/v1/organisation/endpoints.py \
        tests/test_organisation_service.py
git commit -m "feat: add show_title and season_number to preview episode entries"
```

---

### Task 3: Frontend — update RenameProposal type

**Files:**
- Modify: `frontend/src/services/organisationService.ts` (lines 15–20 — `RenameProposal` interface)

**Step 1: Update the interface**

In `frontend/src/services/organisationService.ts`, replace the `RenameProposal` interface:

```typescript
export interface RenameProposal {
  file_id: number
  file_type: 'movie' | 'episode'
  current_path: string
  target_path: string
  show_title?: string
  season_number?: number
}
```

**Step 2: Type-check**

```bash
cd frontend && npm run type-check
```

Expected: no errors.

**Step 3: Commit**

```bash
git add frontend/src/services/organisationService.ts
git commit -m "feat: add show_title and season_number to RenameProposal type"
```

---

### Task 4: Strip the org section from SettingsPage

**Files:**
- Modify: `frontend/src/pages/SettingsPage.tsx`

What to remove:
- `OrganisationModal` import (line 4)
- `OrganisationStats` from the organisationService import (line 3)
- `orgStats`, `orgStatsLoading`, `orgModalOpen` state (lines 56–58)
- The `useEffect` that fetches stats (lines 64–72) — replace with a simpler one that only fetches the preset
- Stats fetch in `handleOrgPresetChange` — simplify to just save
- The stats grid JSX, the "Preview & Apply" button JSX, and the `<OrganisationModal ... />` usage
- `FaFolder` icon is still needed for the section; keep it

What to keep / add:
- `orgPreset` state and the preset `<select>`
- A link to `/organisation` (add `Link` import from `react-router-dom`)

**Step 1: Update imports**

Change line 1–7 of `SettingsPage.tsx` to:

```typescript
import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { FaCog, FaPalette, FaBell, FaSync, FaFolder } from 'react-icons/fa'
import { organisationService, type OrganisationPreset } from '@/services/organisationService'
import { scanScheduleService } from '@/services/configurationService'
import { useSettingsStore } from '@/stores/settingsStore'
import { useTheme } from '@/context/ThemeContext'
```

**Step 2: Replace the three org state lines (56–58)**

Remove:
```typescript
  const [orgStats, setOrgStats] = useState<OrganisationStats | null>(null)
  const [orgStatsLoading, setOrgStatsLoading] = useState(false)
  const [orgModalOpen, setOrgModalOpen] = useState(false)
```

Keep only:
```typescript
  const [orgPreset, setOrgPreset] = useState<OrganisationPreset>('plex')
```

**Step 3: Replace the org useEffect (lines 64–72)**

Remove the effect that chained `getSettings` → `getStats`. Replace with:

```typescript
  useEffect(() => {
    organisationService.getSettings()
      .then(({ preset }) => setOrgPreset(preset))
      .catch(() => {})
  }, [])
```

**Step 4: Simplify handleOrgPresetChange (lines 110–122)**

Replace with:

```typescript
  const handleOrgPresetChange = async (preset: OrganisationPreset) => {
    setOrgPreset(preset)
    try {
      await organisationService.saveSettings(preset)
    } catch {
      // non-fatal
    }
  }
```

**Step 5: Replace the File Organisation SettingsSection JSX (lines 253–310)**

Remove the entire `{/* File Organisation */}` section and replace with:

```tsx
      {/* File Organisation */}
      <SettingsSection
        icon={<FaFolder />}
        title="File Organisation"
        description="Choose the naming convention for your media server"
      >
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Naming Preset
            </label>
            <select
              value={orgPreset}
              onChange={(e) => handleOrgPresetChange(e.target.value as OrganisationPreset)}
              className="w-full sm:w-48 px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="plex">Plex</option>
              <option value="jellyfin">Jellyfin</option>
            </select>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            To rename and organise files, visit the{' '}
            <Link to="/organisation" className="text-indigo-600 dark:text-indigo-400 hover:underline">
              Organisation page
            </Link>
            .
          </p>
        </div>
      </SettingsSection>
```

**Step 6: Remove the OrganisationModal usage (lines 312–319)**

Delete:
```tsx
      <OrganisationModal
        isOpen={orgModalOpen}
        preset={orgPreset}
        onClose={() => {
          setOrgModalOpen(false)
          organisationService.getStats(orgPreset).then(setOrgStats).catch(() => {})
        }}
      />
```

**Step 7: Type-check and build**

```bash
cd frontend && npm run type-check
```

Expected: no errors.

**Step 8: Commit**

```bash
git add frontend/src/pages/SettingsPage.tsx
git commit -m "refactor: move org rename UI to dedicated page, keep preset in settings"
```

---

### Task 5: Create OrganisationPage

**Files:**
- Create: `frontend/src/pages/OrganisationPage.tsx`

**Step 1: Create the file with this complete content**

```tsx
import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { FaChevronDown, FaChevronRight, FaSync } from 'react-icons/fa'
import {
  organisationService,
  type ApplyResult,
  type OrganisationPreset,
  type OrganisationPreview,
  type RenameProposal,
} from '@/services/organisationService'

// ---------------------------------------------------------------------------
// Grouping helpers
// ---------------------------------------------------------------------------

interface SeasonGroup {
  season_number: number
  episodes: RenameProposal[]
}

interface ShowGroup {
  show_title: string
  seasons: SeasonGroup[]
}

function groupEpisodes(episodes: RenameProposal[]): ShowGroup[] {
  const showMap = new Map<string, Map<number, RenameProposal[]>>()
  for (const ep of episodes) {
    const show = ep.show_title ?? 'Unknown Show'
    const season = ep.season_number ?? 0
    if (!showMap.has(show)) showMap.set(show, new Map())
    const seasonMap = showMap.get(show)!
    if (!seasonMap.has(season)) seasonMap.set(season, [])
    seasonMap.get(season)!.push(ep)
  }
  return Array.from(showMap.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([show_title, seasonMap]) => ({
      show_title,
      seasons: Array.from(seasonMap.entries())
        .sort(([a], [b]) => a - b)
        .map(([season_number, eps]) => ({ season_number, episodes: eps })),
    }))
}

// ---------------------------------------------------------------------------
// Indeterminate checkbox
// ---------------------------------------------------------------------------

interface IndeterminateCheckboxProps {
  keys: string[]
  selected: Set<string>
  onChange: () => void
  className?: string
}

function IndeterminateCheckbox({ keys, selected, onChange, className }: IndeterminateCheckboxProps) {
  const count = keys.filter((k) => selected.has(k)).length
  const checked = keys.length > 0 && count === keys.length
  const indeterminate = count > 0 && count < keys.length
  const ref = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (ref.current) ref.current.indeterminate = indeterminate
  }, [indeterminate])

  return (
    <input
      ref={ref}
      type="checkbox"
      checked={checked}
      onChange={onChange}
      className={className ?? 'w-3.5 h-3.5 text-indigo-600 rounded'}
    />
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

function maybeShorten(path: string): string {
  const parts = path.split('/')
  return parts.length <= 3 ? path : `…/${parts.slice(-3).join('/')}`
}

export function OrganisationPage() {
  const [preset, setPreset] = useState<OrganisationPreset>('plex')
  const [preview, setPreview] = useState<OrganisationPreview | null>(null)
  const [loading, setLoading] = useState(false)
  const [applying, setApplying] = useState(false)
  const [result, setResult] = useState<ApplyResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())

  // Collapse state — item in set = collapsed
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(new Set())
  const [collapsedShows, setCollapsedShows] = useState<Set<string>>(new Set())
  const [collapsedSeasons, setCollapsedSeasons] = useState<Set<string>>(new Set())

  const showGroups = useMemo(
    () => groupEpisodes(preview?.episodes ?? []),
    [preview?.episodes],
  )

  const loadPreview = (p: OrganisationPreset) => {
    setLoading(true)
    setError(null)
    setResult(null)
    organisationService
      .getPreview(p)
      .then((data) => {
        setPreview(data)
        setSelected(
          new Set([
            ...data.movies.map((m) => `movie-${m.file_id}`),
            ...data.episodes.map((e) => `episode-${e.file_id}`),
          ]),
        )
      })
      .catch(() => setError('Failed to load preview. Please try again.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    organisationService
      .getSettings()
      .then(({ preset: p }) => {
        setPreset(p)
        loadPreview(p)
      })
      .catch(() => loadPreview('plex'))
  }, [])

  // ---- Collapse helpers ----

  const toggleSection = (key: string) =>
    setCollapsedSections((prev) => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })

  const toggleShow = (key: string) =>
    setCollapsedShows((prev) => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })

  const toggleSeason = (key: string) =>
    setCollapsedSeasons((prev) => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })

  const collapseAllShows = () =>
    setCollapsedShows(new Set(showGroups.map((g) => g.show_title)))

  const expandAllShows = () => {
    setCollapsedShows(new Set())
    setCollapsedSeasons(new Set())
  }

  // ---- Selection helpers ----

  const toggleItem = (key: string) =>
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })

  const toggleKeys = (keys: string[]) =>
    setSelected((prev) => {
      const allSelected = keys.every((k) => prev.has(k))
      const next = new Set(prev)
      if (allSelected) keys.forEach((k) => next.delete(k))
      else keys.forEach((k) => next.add(k))
      return next
    })

  const movieKeys = (preview?.movies ?? []).map((m) => `movie-${m.file_id}`)
  const allEpisodeKeys = (preview?.episodes ?? []).map((e) => `episode-${e.file_id}`)

  const showKeys = (group: ShowGroup) =>
    group.seasons.flatMap((s) => s.episodes.map((e) => `episode-${e.file_id}`))

  const seasonKeys = (season: SeasonGroup) =>
    season.episodes.map((e) => `episode-${e.file_id}`)

  // ---- Apply ----

  const handleApply = async () => {
    if (!preview) return
    const snapshot = new Set(selected)
    setApplying(true)
    setResult(null)

    const items: RenameProposal[] = [
      ...preview.movies
        .filter((m) => snapshot.has(`movie-${m.file_id}`))
        .map((m) => ({ ...m, file_type: 'movie' as const })),
      ...preview.episodes
        .filter((e) => snapshot.has(`episode-${e.file_id}`))
        .map((e) => ({ ...e, file_type: 'episode' as const })),
    ]

    try {
      const res = await organisationService.applyRenames(items)
      setResult(res)
      setPreview((prev) =>
        prev
          ? {
              movies: prev.movies.filter((m) => !snapshot.has(`movie-${m.file_id}`)),
              episodes: prev.episodes.filter((e) => !snapshot.has(`episode-${e.file_id}`)),
            }
          : null,
      )
      setSelected(new Set())
    } catch {
      setResult({ success: 0, failed: items.length, errors: ['Request failed'] })
    } finally {
      setApplying(false)
    }
  }

  const selectedCount = selected.size
  const movies = preview?.movies ?? []
  const episodes = preview?.episodes ?? []

  return (
    <div className="space-y-6 pb-20">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">File Organisation</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Format:{' '}
            <span className="font-medium capitalize text-gray-700 dark:text-gray-200">{preset}</span>
            {' · '}
            <Link
              to="/settings"
              className="text-indigo-600 dark:text-indigo-400 hover:underline text-xs"
            >
              change in Settings
            </Link>
          </p>
        </div>
        <button
          onClick={() => loadPreview(preset)}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition disabled:opacity-50"
        >
          <FaSync className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stats bar */}
      {preview && (
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/50 rounded-lg px-4 py-2.5">
          <span>
            {movies.length} movie{movies.length !== 1 ? 's' : ''} need renaming
          </span>
          <span className="text-gray-300 dark:text-gray-600">·</span>
          <span>
            {episodes.length} episode{episodes.length !== 1 ? 's' : ''} need renaming
          </span>
          {showGroups.length > 0 && (
            <>
              <span className="text-gray-300 dark:text-gray-600">·</span>
              <span>
                across {showGroups.length} show{showGroups.length !== 1 ? 's' : ''}
              </span>
            </>
          )}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-16">
          <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <p className="text-center py-8 text-red-500 dark:text-red-400 text-sm">{error}</p>
      )}

      {/* Content */}
      {!loading && preview && (
        <>
          {/* ---- Movies section ---- */}
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
            {/* Section header */}
            <div className="flex items-center justify-between">
              <button
                className="flex items-center gap-3 flex-1 px-5 py-3.5 text-left hover:bg-slate-50 dark:hover:bg-slate-700/30 transition"
                onClick={() => toggleSection('movies')}
              >
                {collapsedSections.has('movies') ? (
                  <FaChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                ) : (
                  <FaChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                )}
                <span className="font-semibold text-slate-800 dark:text-slate-100">
                  Movies
                  <span className="ml-2 text-sm font-normal text-slate-400">({movies.length})</span>
                </span>
              </button>
              {movies.length > 0 && !collapsedSections.has('movies') && (
                <button
                  className="px-5 text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
                  onClick={() => toggleKeys(movieKeys)}
                >
                  select all
                </button>
              )}
            </div>

            {/* Movies body */}
            {!collapsedSections.has('movies') && (
              movies.length === 0 ? (
                <p className="px-5 py-6 text-sm text-slate-400 dark:text-slate-500 border-t border-slate-100 dark:border-slate-700">
                  All movies already match the {preset} format.
                </p>
              ) : (
                <table className="w-full text-xs border-t border-slate-200 dark:border-slate-700">
                  <thead>
                    <tr className="bg-slate-50 dark:bg-slate-700/30 text-slate-400 dark:text-slate-500 text-left">
                      <th className="px-5 py-2 w-10">
                        <IndeterminateCheckbox
                          keys={movieKeys}
                          selected={selected}
                          onChange={() => toggleKeys(movieKeys)}
                        />
                      </th>
                      <th className="py-2 pr-4">Current path</th>
                      <th className="py-2 pr-5">Proposed path</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
                    {movies.map((m) => {
                      const key = `movie-${m.file_id}`
                      return (
                        <tr key={key} className="hover:bg-slate-50 dark:hover:bg-slate-700/20">
                          <td className="px-5 py-2">
                            <input
                              type="checkbox"
                              checked={selected.has(key)}
                              onChange={() => toggleItem(key)}
                              className="w-3.5 h-3.5 text-indigo-600 rounded"
                            />
                          </td>
                          <td className="py-2 pr-4 font-mono text-slate-500 dark:text-slate-400">
                            {maybeShorten(m.current_path)}
                          </td>
                          <td className="py-2 pr-5 font-mono text-slate-800 dark:text-slate-200">
                            {maybeShorten(m.target_path)}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )
            )}
          </div>

          {/* ---- TV Shows section ---- */}
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
            {/* Section header */}
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-200 dark:border-slate-700">
              <button
                className="flex items-center gap-3 flex-1 text-left hover:text-slate-600 dark:hover:text-slate-300 transition"
                onClick={() => toggleSection('tv')}
              >
                {collapsedSections.has('tv') ? (
                  <FaChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                ) : (
                  <FaChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                )}
                <span className="font-semibold text-slate-800 dark:text-slate-100">
                  TV Shows
                  <span className="ml-2 text-sm font-normal text-slate-400">
                    ({episodes.length} episode{episodes.length !== 1 ? 's' : ''},{' '}
                    {showGroups.length} show{showGroups.length !== 1 ? 's' : ''})
                  </span>
                </span>
              </button>
              {showGroups.length > 0 && !collapsedSections.has('tv') && (
                <div className="flex gap-3 text-xs text-indigo-600 dark:text-indigo-400 shrink-0">
                  <button onClick={expandAllShows} className="hover:underline">
                    expand all
                  </button>
                  <button onClick={collapseAllShows} className="hover:underline">
                    collapse all
                  </button>
                </div>
              )}
            </div>

            {!collapsedSections.has('tv') && (
              showGroups.length === 0 ? (
                <p className="px-5 py-6 text-sm text-slate-400 dark:text-slate-500">
                  All episodes already match the {preset} format.
                </p>
              ) : (
                showGroups.map((group) => {
                  const isShowCollapsed = collapsedShows.has(group.show_title)
                  const allShowKeys = showKeys(group)

                  return (
                    <div
                      key={group.show_title}
                      className="border-b border-slate-100 dark:border-slate-700/50 last:border-b-0"
                    >
                      {/* Show header */}
                      <div className="flex items-center justify-between px-5 py-2.5 bg-slate-50/50 dark:bg-slate-700/20">
                        <button
                          className="flex items-center gap-2 flex-1 text-left min-w-0"
                          onClick={() => toggleShow(group.show_title)}
                        >
                          {isShowCollapsed ? (
                            <FaChevronRight className="w-3 h-3 text-slate-400 shrink-0" />
                          ) : (
                            <FaChevronDown className="w-3 h-3 text-slate-400 shrink-0" />
                          )}
                          <IndeterminateCheckbox
                            keys={allShowKeys}
                            selected={selected}
                            onChange={() => toggleKeys(allShowKeys)}
                          />
                          <span className="text-sm font-medium text-slate-700 dark:text-slate-200 ml-1 truncate">
                            {group.show_title}
                            <span className="ml-2 text-xs font-normal text-slate-400">
                              ({allShowKeys.length})
                            </span>
                          </span>
                        </button>
                        <button
                          className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline shrink-0 ml-3"
                          onClick={() => toggleKeys(allShowKeys)}
                        >
                          select all
                        </button>
                      </div>

                      {/* Seasons */}
                      {!isShowCollapsed &&
                        group.seasons.map((season) => {
                          const seasonKey = `${group.show_title}::S${season.season_number}`
                          const isSeasonCollapsed = collapsedSeasons.has(seasonKey)
                          const sKeys = seasonKeys(season)

                          return (
                            <div key={seasonKey}>
                              {/* Season header */}
                              <div className="flex items-center justify-between pl-10 pr-5 py-2 border-t border-slate-100 dark:border-slate-700/30">
                                <button
                                  className="flex items-center gap-2 flex-1 text-left min-w-0"
                                  onClick={() => toggleSeason(seasonKey)}
                                >
                                  {isSeasonCollapsed ? (
                                    <FaChevronRight className="w-3 h-3 text-slate-400 shrink-0" />
                                  ) : (
                                    <FaChevronDown className="w-3 h-3 text-slate-400 shrink-0" />
                                  )}
                                  <IndeterminateCheckbox
                                    keys={sKeys}
                                    selected={selected}
                                    onChange={() => toggleKeys(sKeys)}
                                  />
                                  <span className="text-xs font-medium text-slate-600 dark:text-slate-300 ml-1">
                                    Season {String(season.season_number).padStart(2, '0')}
                                    <span className="ml-2 font-normal text-slate-400">
                                      ({season.episodes.length})
                                    </span>
                                  </span>
                                </button>
                                <button
                                  className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline shrink-0 ml-3"
                                  onClick={() => toggleKeys(sKeys)}
                                >
                                  select all
                                </button>
                              </div>

                              {/* Episode rows */}
                              {!isSeasonCollapsed && (
                                <table className="w-full text-xs">
                                  <tbody className="divide-y divide-slate-100 dark:divide-slate-700/30">
                                    {season.episodes.map((ep) => {
                                      const key = `episode-${ep.file_id}`
                                      return (
                                        <tr
                                          key={key}
                                          className="hover:bg-slate-50 dark:hover:bg-slate-700/20"
                                        >
                                          <td className="pl-16 pr-3 py-1.5 w-16">
                                            <input
                                              type="checkbox"
                                              checked={selected.has(key)}
                                              onChange={() => toggleItem(key)}
                                              className="w-3.5 h-3.5 text-indigo-600 rounded"
                                            />
                                          </td>
                                          <td className="py-1.5 pr-4 font-mono text-slate-500 dark:text-slate-400">
                                            {maybeShorten(ep.current_path)}
                                          </td>
                                          <td className="py-1.5 pr-5 font-mono text-slate-700 dark:text-slate-300">
                                            {maybeShorten(ep.target_path)}
                                          </td>
                                        </tr>
                                      )
                                    })}
                                  </tbody>
                                </table>
                              )}
                            </div>
                          )
                        })}
                    </div>
                  )
                })
              )
            )}
          </div>
        </>
      )}

      {/* Sticky footer */}
      <div className="sticky bottom-0 z-10 -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8 py-3 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between gap-4">
        <div className="text-sm text-slate-500 dark:text-slate-400">
          {selectedCount > 0
            ? `${selectedCount} file${selectedCount !== 1 ? 's' : ''} selected`
            : 'No files selected'}
          {result && (
            <span className="ml-4">
              {result.success > 0 && (
                <span className="text-green-600 dark:text-green-400">✓ {result.success} renamed</span>
              )}
              {result.failed > 0 && (
                <span className="ml-2 text-red-500 dark:text-red-400">✗ {result.failed} failed</span>
              )}
            </span>
          )}
        </div>
        <button
          onClick={handleApply}
          disabled={applying || selectedCount === 0}
          className="px-5 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium"
        >
          {applying
            ? 'Applying…'
            : `Apply ${selectedCount > 0 ? selectedCount : ''} change${selectedCount !== 1 ? 's' : ''}`}
        </button>
      </div>
    </div>
  )
}
```

**Step 2: Type-check**

```bash
cd frontend && npm run type-check
```

Expected: no errors.

**Step 3: Commit**

```bash
git add frontend/src/pages/OrganisationPage.tsx
git commit -m "feat: add OrganisationPage with collapsible TV show/season accordion"
```

---

### Task 6: Wire up route, sidebar entry, delete OrganisationModal

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/layout/Sidebar/Sidebar.tsx`
- Delete: `frontend/src/components/features/organisation/OrganisationModal.tsx`

**Step 1: Add route to App.tsx**

In `App.tsx`, add a lazy import after the `StoragePage` import (line 23):

```typescript
const OrganisationPage = lazy(() =>
  import('./pages/OrganisationPage').then(m => ({ default: m.OrganisationPage }))
)
```

Then add the route before the `{/* Redirects */}` comment (after the `/storage` route):

```tsx
        <Route
          path="/organisation"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<LoadingFallback />}>
                  <OrganisationPage />
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        />
```

**Step 2: Add sidebar entry**

In `frontend/src/components/layout/Sidebar/Sidebar.tsx`:

Add `FaFolderOpen` to the react-icons import at the top (line 3):

```typescript
import {
  FaHome,
  FaFolder,
  FaFolderOpen,
  FaSearch,
  FaFilm,
  FaTv,
  FaCog,
  FaChevronLeft,
  FaChevronRight,
  FaInfoCircle,
  FaDatabase,
} from 'react-icons/fa'
```

Add the Organisation entry to `navItems` between TV Shows and Storage:

```typescript
const navItems: NavItem[] = [
  { label: 'Home', path: '/', icon: <FaHome className="w-5 h-5" /> },
  { label: 'Files', path: '/files', icon: <FaFolder className="w-5 h-5" /> },
  { label: 'Search', path: '/search', icon: <FaSearch className="w-5 h-5" /> },
  { label: 'Movies', path: '/movies', icon: <FaFilm className="w-5 h-5" />, badge: 'New' },
  { label: 'TV Shows', path: '/tv-shows', icon: <FaTv className="w-5 h-5" /> },
  { label: 'Organisation', path: '/organisation', icon: <FaFolderOpen className="w-5 h-5" /> },
  { label: 'Storage', path: '/storage', icon: <FaDatabase className="w-5 h-5" /> },
  { label: 'Settings', path: '/settings', icon: <FaCog className="w-5 h-5" /> },
]
```

**Step 3: Delete OrganisationModal**

```bash
rm frontend/src/components/features/organisation/OrganisationModal.tsx
```

**Step 4: Type-check and build**

```bash
cd frontend && npm run type-check && npm run build
```

Expected: clean build, no errors.

**Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/components/layout/Sidebar/Sidebar.tsx
git rm frontend/src/components/features/organisation/OrganisationModal.tsx
git commit -m "feat: wire /organisation route, sidebar entry; remove OrganisationModal"
```

---

## Done

Backend tests: `pytest` — all pass.
Frontend: `npm run type-check && npm run build` — clean.

The Organisation page is at `/organisation` with:
- Plex/Jellyfin format displayed (read from saved settings)
- Collapsible Movies section (flat table)
- Collapsible TV Shows section → shows → seasons → episode rows
- Indeterminate checkboxes at show and season level
- Sticky Apply footer with rename count
- Settings page retains only the preset selector with a link to the Organisation page
