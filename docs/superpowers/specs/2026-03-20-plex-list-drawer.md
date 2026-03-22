# Plex Collections & Playlists: List + Drawer

**Date:** 2026-03-20
**Branch:** feature/plex-list-drawer
**Status:** Approved

## Overview

Replace the 3-column card grid on the Plex Collections page with a compact table-style list for both collections and playlists. Clicking a collection or playlist name opens a right-side drawer showing Plex artwork, metadata, and a resolved items list with links to movie pages.

## Layout Change

The card grid (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`) is replaced with a full-width list. Column definitions differ between collections and playlists.

### Collections list columns

| Column | Content |
|--------|---------|
| Name | Clickable — opens drawer. Underlined on hover. |
| Type | Builder type badge using existing `BUILDER_LABELS` map: `tmdb_collection → TMDB`, `genre → Genre`, `decade → Decade`, `static_items → Static` |
| Items | Item count |
| Last Synced | Relative or formatted timestamp; `—` if never |
| Actions | Enabled checkbox, Push to Plex button, Delete button |

### Playlists list columns

Playlists have no `builder_type`. The Type column is **omitted** for the playlist list:

| Column | Content |
|--------|---------|
| Name | Clickable — opens drawer |
| Items | Item count |
| Last Synced | Relative or formatted timestamp; `—` if never |
| Actions | Select checkbox (in select mode), Enabled checkbox, Push to Plex button, Delete button |

Movie and TV sub-section headers are preserved above their respective collection lists. The existing bulk-select mode for playlists is retained, with row-level checkboxes appearing when `selectMode` is true.

### Delete confirmation

The existing two-step delete confirmation from `CollectionCard` (confirm dialog + "Also delete from Plex" checkbox) is **preserved in `CollectionRow`**.

For `PlaylistRow`, the confirm dialog is a **simple "Are you sure?" prompt with no "Also delete from Plex" checkbox** — the existing `delete_playlist` endpoint unconditionally deletes from Plex when `plex_rating_key` is set, so the checkbox would have no effect.

### Loading skeleton

During initial load, render 5 skeleton rows (full-width, `h-10`, `animate-pulse`) in place of the list, matching the existing page's pulse pattern.

### Old components

`CollectionCard` and `PlaylistCard` are **deleted** as part of this change — they are only used in `PlexCollectionsPage`.

## Drawer

### Opening and closing

Clicking a collection name sets `selectedCollectionId`. Clicking a playlist name sets `selectedPlaylistId`. **Opening one clears the other** — these two state values are mutually exclusive. Only one drawer is visible at a time.

Closing: clicking ✕, pressing Escape, or clicking outside the drawer.

### Layout

When a drawer is open the page uses a flex row: the list takes `flex-1 min-w-0`, the drawer takes `w-80` fixed width with a left border. On screens narrower than `lg`, the drawer overlays the list (fixed right panel) rather than pushing it.

### Drawer content (top to bottom)

1. **Header** — name + ✕ close button
2. **Artwork** — `<img>` rendered via `useEffect` + `URL.createObjectURL` pattern: fetch `GET /plex/collections/{id}/artwork` with `responseType: 'blob'`, create an object URL, set as `src`. Revoke on unmount. Falls back to a grey placeholder if `plex_rating_key` is null or the request fails.
3. **Metadata row** — type badge (collections only), item count, last synced
4. **Description** — shown if present
5. **Controls row** — enabled checkbox, Push to Plex button, Delete button (with same confirm dialog as the row)
6. **Items list** — see below

### Items list

Each row: `title | plex_rating_key | →`

- **Title** is resolved via the enriched item response (see Backend §2). Falls back to italic `—` if `movie_title` is null (unmatched or TV show type — see note below).
- **Plex rating key** shown in monospace.
- **`→`** is a `<Link>` to `/movies/{item_id}`. Hidden when `movie_title` is null.

**TV show items:** `item_type == "tv_show"` items are **not resolved** against the TV show DB in this iteration. They render as unmatched (italic, no link). This is by design and can be addressed in a future update.

## Backend Changes

### 1. Artwork proxy endpoints

```
GET /plex/collections/{id}/artwork
GET /plex/playlists/{id}/artwork
```

Both endpoints follow the same pattern:

- Require `get_current_user`
- Look up the collection/playlist by ID
- Verify `connection_id` matches the active connection (same `_get_active_connection` check)
- If `plex_rating_key` is null → return 404
- Fetch `{server_url}/library/metadata/{plex_rating_key}/thumb?X-Plex-Token={token}` from Plex using `httpx`
- Stream the response back, preserving the `Content-Type` header
- On Plex error → return 502

Tests must verify:
- `plex_rating_key=None` → 404
- Successful proxy forwards `Content-Type`
- Plex HTTP error → 502

### 2. Enrich items with movie titles

Modify `CollectionItemResponse` and `PlaylistItemResponse` in `app/api/v1/plex/collection_schemas.py` to add:

```python
movie_title: Optional[str] = None
```

Add a router-level helper `_enrich_items_with_titles(items, db)` in `collection_router.py`. The helper returns a list of `CollectionItemResponse` Pydantic objects directly — it does **not** mutate ORM instances:

```python
def _enrich_items_with_titles(
    items: list[PlexCollectionItem], db: Session
) -> list[CollectionItemResponse]:
    movie_ids = [i.item_id for i in items if i.item_type == "movie"]
    titles = {
        m.id: m.title
        for m in db.query(MovieModel).filter(MovieModel.id.in_(movie_ids)).all()
    }
    return [
        CollectionItemResponse(
            id=i.id,
            plex_rating_key=i.plex_rating_key,
            item_type=i.item_type,
            item_id=i.item_id,
            position=i.position,
            movie_title=titles.get(i.item_id) if i.item_type == "movie" else None,
        )
        for i in items
    ]
```

TV show items get `movie_title = None`. The same helper is reused for playlist items, returning `PlaylistItemResponse` objects (same field set).

Apply this helper in:
- `get_collection` (`GET /plex/collections/{id}`)
- `get_playlist` (`GET /plex/playlists/{id}`)

The `list_collections` and `list_playlists` endpoints do **not** enrich items (items aren't needed for the list rows).

## Frontend Changes

### Service layer

Extend `CollectionItem` and `PlaylistItem` interfaces in `frontend/src/services/plexCollectionService.ts`:

```ts
export interface CollectionItem {
  // existing fields...
  movie_title: string | null
}

export interface PlaylistItem {
  // existing fields...
  movie_title: string | null
}
```

### New components

| Component | Replaces | Purpose |
|-----------|---------|---------|
| `CollectionRow` | `CollectionCard` | Single table row for a collection |
| `PlaylistRow` | `PlaylistCard` | Single table row for a playlist |
| `CollectionDrawer` | — | Right-side drawer for a collection |
| `PlaylistDrawer` | — | Right-side drawer for a playlist |

### `PlexCollectionsPage` state additions

```ts
const [selectedCollectionId, setSelectedCollectionId] = useState<number | null>(null)
const [selectedPlaylistId, setSelectedPlaylistId] = useState<number | null>(null)
```

Opening a collection clears `selectedPlaylistId`; opening a playlist clears `selectedCollectionId`. The page renders a flex-row container when either is non-null.

### Service layer artwork functions

Add to `plexCollectionService.ts` (consistent with the established pattern of all API calls going through the service layer):

```ts
export async function getCollectionArtwork(id: number): Promise<Blob> {
  const { data } = await apiClient.get(`/plex/collections/${id}/artwork`, { responseType: 'blob' })
  return data
}

export async function getPlaylistArtwork(id: number): Promise<Blob> {
  const { data } = await apiClient.get(`/plex/playlists/${id}/artwork`, { responseType: 'blob' })
  return data
}
```

### Artwork in drawer

The cleanup function must be returned directly from the `useEffect` callback, not from the Promise, to ensure blob URLs are revoked on unmount:

```ts
useEffect(() => {
  if (!collection.plex_rating_key) return
  let objectUrl: string | null = null
  let cancelled = false
  getCollectionArtwork(collection.id)
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
}, [collection.id, collection.plex_rating_key])
```

The `cancelled` flag prevents `setArtworkUrl` being called on an unmounted component and ensures the blob URL is not leaked if the drawer is closed while the fetch is still in flight.

### Routing

The `→` link uses React Router `<Link to={`/movies/${item.item_id}`}>`. Omitted when `item.movie_title === null`.

## What Is Not Changing

- All existing store actions (`pushCollection`, `deleteCollection`, `updateCollection`, etc.) remain unchanged
- `CollectionForm`, `YamlImportModal`, `CollectionSetToggles` are untouched
- No database migrations required
- The `fix/plex-delete-slow` branch changes are independent and not affected

## Testing

### Backend

- Artwork proxy: 404 on null key, 200 with correct `Content-Type` forwarded, 502 on Plex error
- Title enrichment: items with matched movies get `movie_title`; unmatched and TV show items get `null`

### Frontend

- `CollectionRow`: renders name, type badge, item count, enabled toggle, push/delete; delete opens confirm dialog
- `PlaylistRow`: renders name, item count, enabled toggle, push/delete; select checkbox in select mode
- `PlexCollectionsPage`: opening a collection drawer clears selected playlist and vice versa; ESC closes drawer
