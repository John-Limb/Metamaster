# Organisation Page Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:writing-plans to create the implementation plan.

**Goal:** Move file renaming out of the Settings modal into a dedicated `/organisation` page with a collapsible TV Show → Season → Episode tree.

**Architecture:** New `OrganisationPage` at `/organisation` with a sidebar entry. The backend `/preview` endpoint gains `show_title` and `season_number` on episode entries. Settings page retains only the Plex/Jellyfin preset selector.

**Tech Stack:** React/TypeScript, Tailwind, existing `organisationService`, FastAPI/SQLAlchemy backend.

---

## Routing & Navigation

- New route `/organisation` in `frontend/src/config/routes.tsx` (lazy-loaded `OrganisationPage`)
- New sidebar entry `{ label: 'Organisation', path: '/organisation', icon: <FaFolderOpen> }` — placed between Enrichment and Settings in `Sidebar.tsx`

## Settings Page Changes

Remove from `SettingsPage.tsx`:
- `orgStats`, `orgStatsLoading`, `orgModalOpen` state
- Stats grid (movies/episodes match/need-rename/unenriched)
- "Preview & Apply" button
- `OrganisationModal` import and usage
- `useEffect` that fetches stats

Keep in `SettingsPage.tsx`:
- `orgPreset` state
- `useEffect` that fetches saved preset
- Plex/Jellyfin radio/toggle selector + `handleOrgPresetChange` that saves via `organisationService.saveSettings`

## Backend Changes

**`app/domain/organisation/service.py` — `get_preview`:**
Add `show_title` and `season_number` fields to episode entries:
```python
episodes.append({
    "file_id": ef.id,
    "file_type": "episode",
    "current_path": ef.file_path,
    "target_path": target,
    "show_title": show.title,
    "season_number": season.season_number,
})
```

**`app/api/v1/organisation/endpoints.py` — `RenameProposal` Pydantic model:**
Add optional fields:
```python
class RenameProposal(BaseModel):
    file_id: int
    file_type: Literal["movie", "episode"]
    current_path: str
    target_path: str
    show_title: str | None = None
    season_number: int | None = None
```

**`frontend/src/services/organisationService.ts` — `RenameProposal` type:**
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

## OrganisationPage Layout

```
┌─────────────────────────────────────────────────────────────┐
│ File Organisation                    [Refresh]              │
│ Format: Plex  (change in Settings)                          │
├─────────────────────────────────────────────────────────────┤
│ Stats bar: 12 movies · 47 episodes need renaming            │
├─────────────────────────────────────────────────────────────┤
│ ▼ Movies (12)                              [select all]     │
│   ☑ /old/path/movie.mkv  →  /new/path/movie.mkv            │
├─────────────────────────────────────────────────────────────┤
│ ▼ TV Shows (47 episodes, 3 shows)    [expand/collapse all]  │
│                                                             │
│   ▼ Breaking Bad (12)                      [select all]     │
│     ▼ Season 01 (6)                        [select all]     │
│       ☑ /old/...  →  /new/...                               │
│     ▶ Season 02 (6)                        [select all]     │
│   ▶ The Wire (35)                          [select all]     │
├─────────────────────────────────────────────────────────────┤
│ [sticky footer]  42 selected    [Apply 42 changes]          │
└─────────────────────────────────────────────────────────────┘
```

## State

```typescript
// Collapse state — empty set = all expanded
const [collapsedSections, setCollapsedSections] = useState<Set<'movies' | 'tv'>>(new Set())
const [collapsedShows, setCollapsedShows] = useState<Set<string>>(new Set())
const [collapsedSeasons, setCollapsedSeasons] = useState<Set<string>>(new Set())
// key format: `${showTitle}::S${seasonNumber}`

// Selection — initialised with all file keys on load
const [selected, setSelected] = useState<Set<string>>(new Set())
// key format: `movie-${id}` or `episode-${id}`

// Data
const [preview, setPreview] = useState<OrganisationPreview | null>(null)
const [preset, setPreset] = useState<OrganisationPreset>('plex')
const [loading, setLoading] = useState(false)
const [applying, setApplying] = useState(false)
const [result, setResult] = useState<ApplyResult | null>(null)

// Derived: group episodes into Map<showTitle, Map<seasonNumber, EpisodeProposal[]>>
```

## Checkbox Cascade

- **Season checkbox**: checked = all its episodes selected; indeterminate = some; unchecked = none
- **Show checkbox**: checked = all seasons fully selected; indeterminate = mixed; unchecked = none
- Clicking show checkbox → select/deselect all its episodes in one `setSelected` updater
- Clicking season checkbox → select/deselect that season's episodes only

## After Apply

- On success: remove renamed items from preview state (filter by snapshot of selected)
- Result shown in sticky footer: `✓ N renamed  ✗ N failed`
- No full re-fetch needed

## Files to Create / Modify

| Action | File |
|--------|------|
| Create | `frontend/src/pages/OrganisationPage.tsx` |
| Modify | `frontend/src/config/routes.tsx` |
| Modify | `frontend/src/components/layout/Sidebar/Sidebar.tsx` |
| Modify | `frontend/src/pages/SettingsPage.tsx` (strip org section) |
| Modify | `frontend/src/services/organisationService.ts` (add fields to type) |
| Modify | `app/domain/organisation/service.py` (add show_title, season_number to preview) |
| Modify | `app/api/v1/organisation/endpoints.py` (add fields to RenameProposal) |
| Modify | `tests/test_organisation_service.py` (update preview tests) |
| Delete | `frontend/src/components/features/organisation/OrganisationModal.tsx` |
