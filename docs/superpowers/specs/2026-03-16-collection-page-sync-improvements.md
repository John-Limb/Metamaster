# Collection Page Sync Improvements

**Date:** 2026-03-16
**Status:** Approved

## Problem

Three gaps in the collections page:

1. No way to push all enabled collections to Plex in bulk — users must push individually.
2. Deleting a collection from MetaMaster leaves it in Plex (orphaned).
3. The collections list mixes movie and TV show collections with no visual separation, making it confusing.

---

## Feature 1: Push All to Plex

### Backend

**New endpoint:** `POST /api/v1/plex/collections/push-all`

- Registered in `app/api/v1/plex/collection_router.py`.
- Requires `get_current_user` auth dependency (consistent with existing collection endpoints).
- Retrieves the active `PlexConnection` for the current user (same pattern as existing endpoints).
- Queues the existing Celery task `push_all_collections(connection_id)` from `app/tasks/plex_collections.py`.
- Returns `{"status": "queued"}` with HTTP 202.
- No new service logic required — the task already pushes all enabled collections.

### Frontend

- New **"Push All to Plex"** button added to `PlexCollectionsPage.tsx`, placed alongside the existing "Discover Collections" button in the page header.
- Button is disabled and shows a spinner while the request is in-flight.
- On 202 response: show a success toast ("Collections queued for push to Plex").
- On error: show an inline error message.
- Uses the existing `apiClient` pattern from `plexCollectionService.ts` — add a `pushAllCollections()` function that calls `POST /plex/collections/push-all`.

---

## Feature 2: Delete Also Removes from Plex

### Backend

**Modified endpoint:** `DELETE /api/v1/plex/collections/{collection_id}`

- Add query parameter `delete_from_plex: bool = Query(default=False)`.
- If `delete_from_plex=True` and `collection.plex_rating_key` is not null:
  - Build `PlexCollectionClient` using the active connection (`_get_active_connection`, the same helper used by other endpoints in the router).
  - Call `PlexCollectionClient.delete_collection(collection.plex_rating_key)`.
  - If the Plex API call fails (e.g. collection already gone), log the error and continue — still delete the DB row.
- Then delete the DB row and return 204 as before.

`PlexCollectionClient.delete_collection()` already exists at `app/infrastructure/external_apis/plex/collection_client.py` — no new client code needed.

### Frontend

**Confirmation modal** added to `CollectionCard.tsx` (currently deletes immediately on click):

- Clicking the delete button opens a small modal with:
  - Message: "Delete **{collection name}**?"
  - Checkbox: "Also delete from Plex" — shown only when `collection.plex_rating_key` is set; checked by default when shown.
  - "Cancel" and "Delete" buttons.
- On confirm: call `deleteCollection(id, deleteFromPlex)`, passing the checkbox state.
- `deleteCollection` in `plexCollectionStore.ts` updated to accept and forward the `deleteFromPlex` boolean. The store's TypeScript interface for `deleteCollection` must also be updated from `(id: number) => Promise<void>` to `(id: number, deleteFromPlex?: boolean) => Promise<void>`.
- `deleteCollection` in `plexCollectionService.ts` (line ~125) updated to accept a `deleteFromPlex: boolean` parameter and append `?delete_from_plex=true` to the DELETE request URL when the flag is set.

---

## Feature 3: Movies / TV Split

### Backend — DB Migration

Add nullable `content_type` column to `PlexCollection`:

```python
content_type = Column(String(20), nullable=True)  # "movie" | "tv_show" | None
```

Values: `"movie"`, `"tv_show"`, or `None` (unknown / legacy rows).

Alembic migration required. Existing rows left as `NULL`.

### Backend — Pull Collections

The pull logic lives in `app/domain/plex/collection_service.py`. The method `_upsert_pulled_collection` receives a `section_id` parameter. The service already holds `self._movie_section` and `self._tv_section` (populated from the Plex connection's library IDs). Set `content_type` inside `_upsert_pulled_collection`:

- If `section_id == self._movie_section` → `content_type = "movie"`.
- If `section_id == self._tv_section` → `content_type = "tv_show"`.
- Otherwise → leave `content_type` as `None`.

### Backend — Collection Create

In the collection builder flow (`POST /plex/collections`), set `content_type = "movie"` on creation — the builder is movies-only.

### Backend — API Response

Add `content_type: str | None` to `CollectionResponse` schema in `app/api/v1/plex/collection_schemas.py`.

### Frontend — TypeScript Type

Add `content_type: string | null` to the `PlexCollection` interface in `frontend/src/services/plexCollectionService.ts` (alongside the existing fields like `plex_rating_key`, `enabled`, etc.). Without this, TypeScript will error when accessing `collection.content_type` in the page split.

### Frontend — Page Split

`PlexCollectionsPage.tsx` splits the collection list into two labelled sections:

- **Movies** — collections where `content_type === "movie"` or `content_type === null`.
- **TV Shows** — collections where `content_type === "tv_show"`.

If the TV Shows section is empty, it is not rendered (no empty-state shown for it).

Each section has a bold heading (`<h2>` or equivalent) using the existing page heading style.

No other changes to `CollectionCard` or filtering logic.

---

## Out of Scope

- Per-set-type push buttons (push all genre collections, etc.) — superseded by global push all.
- Pagination or filtering within each section.
- TV show collection builder (existing builder remains movies-only).
- Handling the case where `movie_library_id` or `tv_library_id` is null on the connection (skip tagging for that section, leave `content_type` null).
