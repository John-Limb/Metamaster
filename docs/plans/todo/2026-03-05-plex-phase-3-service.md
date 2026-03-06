# Plex Integration — Phase 3: Config & PlexSyncService

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Plex settings to `config.py`, implement `PlexSyncService` with library name resolution and item match logic.

**Architecture:** `PlexSyncService` is the orchestration layer. It wraps `PlexClient`, resolves library section names to IDs, resolves TMDB IDs to Plex `ratingKey`s, and manages `PlexSyncRecord` rows. Keeps the Celery tasks in Phase 4 thin.

**Tech Stack:** Python, SQLAlchemy, httpx, respx, pytest

**Prerequisite:** Phases 1 and 2 complete.

---

### Task 1: Add Plex settings to config

**Files:**
- Modify: `app/core/config.py`

**Step 1: Add settings fields**

In `app/core/config.py`, inside the `Settings` class, add after the TMDB settings block:

```python
# Plex Media Server
plex_server_url: Optional[str] = None
plex_token: Optional[str] = None          # manual fallback; OAuth stores token in DB
plex_library_movies: str = "Movies"       # must match Plex library name exactly
plex_library_tv: str = "TV Shows"         # must match Plex library name exactly
plex_sync_poll_interval_seconds: int = 300
```

**Step 2: Verify settings load without error**

```bash
python -c "from app.core.config import settings; print(settings.plex_server_url)"
```
Expected: `None`

**Step 3: Commit**

```bash
git add app/core/config.py
git commit -m "feat(plex): add Plex config settings"
```

---

### Task 2: PlexSyncService — library resolution

**Files:**
- Create: `app/domain/plex/service.py`
- Create: `tests/test_plex_service.py`

**Step 1: Write failing tests for library resolution**

```python
# tests/test_plex_service.py
import pytest
from unittest.mock import MagicMock, patch
from app.domain.plex.service import PlexSyncService
from app.infrastructure.external_apis.plex.schemas import PlexLibrarySection


def make_service(movie_lib="Movies", tv_lib="TV Shows"):
    mock_db = MagicMock()
    mock_client = MagicMock()
    mock_client.get_library_sections.return_value = [
        PlexLibrarySection(key="1", title="Movies", type="movie"),
        PlexLibrarySection(key="2", title="TV Shows", type="show"),
    ]
    return PlexSyncService(db=mock_db, client=mock_client,
                           movie_library_name=movie_lib, tv_library_name=tv_lib)


def test_resolve_library_ids_success():
    svc = make_service()
    movie_id, tv_id = svc.resolve_library_ids()
    assert movie_id == "1"
    assert tv_id == "2"


def test_resolve_library_ids_movie_name_mismatch_raises():
    svc = make_service(movie_lib="Films")
    with pytest.raises(ValueError, match="Library 'Films' not found"):
        svc.resolve_library_ids()


def test_resolve_library_ids_tv_name_mismatch_raises():
    svc = make_service(tv_lib="Series")
    with pytest.raises(ValueError, match="Library 'Series' not found"):
        svc.resolve_library_ids()


def test_resolve_library_ids_error_includes_available_names():
    svc = make_service(movie_lib="Films")
    with pytest.raises(ValueError) as exc_info:
        svc.resolve_library_ids()
    assert "Movies" in str(exc_info.value)
    assert "TV Shows" in str(exc_info.value)
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_plex_service.py -v -k "resolve_library"
```
Expected: `ImportError`

**Step 3: Implement service skeleton with library resolution**

```python
# app/domain/plex/service.py
"""PlexSyncService — orchestrates metadata push and watch status pull"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.domain.plex.models import PlexSyncRecord, PlexSyncStatus, PlexItemType
from app.infrastructure.external_apis.plex.client import PlexClient

logger = logging.getLogger(__name__)


class PlexSyncService:
    def __init__(
        self,
        db: Session,
        client: PlexClient,
        movie_library_name: str,
        tv_library_name: str,
    ):
        self._db = db
        self._client = client
        self._movie_lib_name = movie_library_name
        self._tv_lib_name = tv_library_name

    def resolve_library_ids(self) -> Tuple[str, str]:
        """Resolve library names to Plex section IDs.

        Returns (movie_section_id, tv_section_id).
        Raises ValueError with available names if either name is not found.
        """
        sections = self._client.get_library_sections()
        by_title = {s.title: s.key for s in sections}
        available = ", ".join(by_title.keys())

        if self._movie_lib_name not in by_title:
            raise ValueError(
                f"Library '{self._movie_lib_name}' not found in Plex. "
                f"Available libraries: {available}"
            )
        if self._tv_lib_name not in by_title:
            raise ValueError(
                f"Library '{self._tv_lib_name}' not found in Plex. "
                f"Available libraries: {available}"
            )

        return by_title[self._movie_lib_name], by_title[self._tv_lib_name]
```

**Step 4: Run resolution tests**

```bash
pytest tests/test_plex_service.py -v -k "resolve_library"
```
Expected: All PASSED.

**Step 5: Commit**

```bash
git add app/domain/plex/service.py tests/test_plex_service.py
git commit -m "feat(plex): add PlexSyncService with library name resolution"
```

---

### Task 3: PlexSyncService — match locking

**Files:**
- Modify: `app/domain/plex/service.py`
- Modify: `tests/test_plex_service.py`

**Step 1: Write failing tests**

```python
# append to tests/test_plex_service.py
from app.domain.plex.models import PlexSyncRecord, PlexSyncStatus


def test_lock_match_creates_sync_record_on_success():
    mock_db = MagicMock()
    mock_client = MagicMock()
    mock_client.find_rating_key_by_tmdb_id.return_value = "99"
    mock_client.get_library_sections.return_value = []
    # Simulate no existing record
    mock_db.query.return_value.filter.return_value.first.return_value = None

    svc = PlexSyncService(db=mock_db, client=mock_client,
                          movie_library_name="Movies", tv_library_name="TV Shows")
    svc.lock_match(
        section_id="1",
        item_type=PlexItemType.MOVIE,
        item_id=42,
        tmdb_id="603",
        connection_id=1,
    )

    mock_db.add.assert_called_once()
    record = mock_db.add.call_args[0][0]
    assert record.plex_rating_key == "99"
    assert record.sync_status == PlexSyncStatus.SYNCED


def test_lock_match_marks_not_found_when_no_plex_item():
    mock_db = MagicMock()
    mock_client = MagicMock()
    mock_client.find_rating_key_by_tmdb_id.return_value = None
    mock_db.query.return_value.filter.return_value.first.return_value = None

    svc = PlexSyncService(db=mock_db, client=mock_client,
                          movie_library_name="Movies", tv_library_name="TV Shows")
    svc.lock_match(
        section_id="1",
        item_type=PlexItemType.MOVIE,
        item_id=42,
        tmdb_id="999",
        connection_id=1,
    )

    record = mock_db.add.call_args[0][0]
    assert record.sync_status == PlexSyncStatus.NOT_FOUND
    assert record.plex_rating_key is None
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_plex_service.py -v -k "lock_match"
```
Expected: `AttributeError` — method not found.

**Step 3: Add lock_match to service**

```python
# append to PlexSyncService in app/domain/plex/service.py

    def lock_match(
        self,
        section_id: str,
        item_type: PlexItemType,
        item_id: int,
        tmdb_id: str,
        connection_id: int,
    ) -> PlexSyncRecord:
        """Resolve TMDB ID to Plex ratingKey and upsert sync record.

        Marks NOT_FOUND if Plex has no item with the given TMDB ID.
        Never raises — missing items are skipped, not failures.
        """
        rating_key = self._client.find_rating_key_by_tmdb_id(
            section_id=section_id, tmdb_id=tmdb_id
        )

        record = (
            self._db.query(PlexSyncRecord)
            .filter(
                PlexSyncRecord.item_type == item_type,
                PlexSyncRecord.item_id == item_id,
                PlexSyncRecord.connection_id == connection_id,
            )
            .first()
        )

        if record is None:
            record = PlexSyncRecord(
                connection_id=connection_id,
                item_type=item_type,
                item_id=item_id,
            )
            self._db.add(record)

        if rating_key:
            record.plex_rating_key = rating_key
            record.sync_status = PlexSyncStatus.SYNCED
            record.last_matched_at = datetime.utcnow()
            logger.info("Plex match locked: %s id=%s key=%s", item_type, item_id, rating_key)
        else:
            record.sync_status = PlexSyncStatus.NOT_FOUND
            record.plex_rating_key = None
            logger.warning(
                "Plex match not found: %s id=%s tmdb_id=%s — skipping",
                item_type, item_id, tmdb_id,
            )

        self._db.commit()
        return record
```

**Step 4: Run tests**

```bash
pytest tests/test_plex_service.py -v -k "lock_match"
```
Expected: All PASSED.

**Step 5: Commit**

```bash
git add app/domain/plex/service.py tests/test_plex_service.py
git commit -m "feat(plex): add PlexSyncService.lock_match with not_found handling"
```

---

### Task 4: PlexSyncService — watch status pull

**Files:**
- Modify: `app/domain/plex/service.py`
- Modify: `tests/test_plex_service.py`

**Step 1: Write failing tests**

```python
# append to tests/test_plex_service.py
from app.infrastructure.external_apis.plex.schemas import PlexMediaItem


def test_pull_watched_status_updates_existing_record():
    mock_db = MagicMock()
    mock_client = MagicMock()

    plex_item = PlexMediaItem(
        **{
            "ratingKey": "99",
            "title": "The Matrix",
            "viewCount": 5,
            "lastViewedAt": 1700000000,
            "Guid": [{"id": "tmdb://603"}],
        }
    )
    mock_client.get_all_items.return_value = [plex_item]

    existing_record = MagicMock(spec=PlexSyncRecord)
    existing_record.item_id = 42
    mock_db.query.return_value.filter.return_value.first.return_value = existing_record

    svc = PlexSyncService(db=mock_db, client=mock_client,
                          movie_library_name="Movies", tv_library_name="TV Shows")
    svc.pull_watched_status(section_id="1", media_type=1, connection_id=1)

    assert existing_record.watch_count == 5
    assert existing_record.is_watched is True
    mock_db.commit.assert_called()


def test_pull_watched_status_skips_unmatched_items():
    mock_db = MagicMock()
    mock_client = MagicMock()

    plex_item = PlexMediaItem(
        **{"ratingKey": "99", "title": "Unknown", "Guid": []}
    )
    mock_client.get_all_items.return_value = [plex_item]

    svc = PlexSyncService(db=mock_db, client=mock_client,
                          movie_library_name="Movies", tv_library_name="TV Shows")
    svc.pull_watched_status(section_id="1", media_type=1, connection_id=1)

    # No DB writes for items with no tmdb_id
    mock_db.add.assert_not_called()
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_plex_service.py -v -k "pull_watched"
```
Expected: `AttributeError`

**Step 3: Add pull_watched_status to service**

```python
# append to PlexSyncService in app/domain/plex/service.py

    def pull_watched_status(
        self, section_id: str, media_type: int, connection_id: int
    ) -> None:
        """Pull watch status from Plex for all items in a section.

        Updates existing PlexSyncRecords. Skips items with no tmdb_id.
        Never blocks on a single missing item.
        """
        items = self._client.get_all_items(section_id=section_id, media_type=media_type)
        logger.info("Plex pull: %d items from section %s", len(items), section_id)

        for item in items:
            if not item.tmdb_id:
                continue
            self._update_watch_record(item=item, connection_id=connection_id)

        self._db.commit()

    def _update_watch_record(self, item, connection_id: int) -> None:
        record = (
            self._db.query(PlexSyncRecord)
            .filter(
                PlexSyncRecord.plex_rating_key == item.rating_key,
                PlexSyncRecord.connection_id == connection_id,
            )
            .first()
        )
        if record is None:
            return

        record.watch_count = item.view_count
        record.is_watched = item.view_count > 0
        record.last_pulled_at = datetime.utcnow()
        if item.last_viewed_at:
            record.last_watched_at = datetime.utcfromtimestamp(item.last_viewed_at)
        logger.info(
            "Plex watch update: rating_key=%s views=%d", item.rating_key, item.view_count
        )
```

**Step 4: Run all service tests**

```bash
pytest tests/test_plex_service.py -v
```
Expected: All PASSED.

**Step 5: Lint**

```bash
black app/domain/plex/service.py tests/test_plex_service.py
isort app/domain/plex/service.py tests/test_plex_service.py
flake8 app/domain/plex/service.py tests/test_plex_service.py
mypy app/domain/plex/service.py
```

**Step 6: Commit**

```bash
git add app/domain/plex/service.py tests/test_plex_service.py
git commit -m "feat(plex): add PlexSyncService watch status pull"
```
