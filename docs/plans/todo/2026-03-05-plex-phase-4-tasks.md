# Plex Integration — Phase 4: Celery Tasks

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement Celery tasks for library refresh, match locking, watched status poll, and manual full sync. Wire the poll task into Celery Beat.

**Architecture:** Tasks in `app/tasks/plex.py` are thin wrappers over `PlexSyncService`. They handle DB session lifecycle, retry logic, and logging. The poll task is registered in `celery_beat.py`. All tasks are routed to the `external_api` queue (matching TMDB tasks).

**Tech Stack:** Celery, SQLAlchemy, pytest, unittest.mock

**Prerequisite:** Phases 1–3 complete.

---

### Task 1: Library refresh task

**Files:**
- Create: `app/tasks/plex.py`
- Create: `tests/test_plex_tasks.py`

**Step 1: Write failing test**

```python
# tests/test_plex_tasks.py
import pytest
from unittest.mock import MagicMock, patch
from app.tasks.plex import refresh_plex_library


@patch("app.tasks.plex.PlexClient")
@patch("app.tasks.plex.get_db")
@patch("app.tasks.plex.settings")
def test_refresh_plex_library_calls_client(mock_settings, mock_get_db, mock_client_cls):
    mock_settings.plex_server_url = "http://plex:32400"
    mock_settings.plex_token = "token"
    mock_settings.plex_library_movies = "Movies"
    mock_settings.plex_library_tv = "TV Shows"

    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])

    refresh_plex_library.apply(args=["1"]).get()

    mock_client.refresh_library_section.assert_called_once_with(section_id="1")


@patch("app.tasks.plex.settings")
def test_refresh_plex_library_skips_when_no_server_url(mock_settings):
    mock_settings.plex_server_url = None
    result = refresh_plex_library.apply(args=["1"]).get()
    assert result is None
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_plex_tasks.py -v -k "refresh"
```
Expected: `ImportError`

**Step 3: Implement tasks module**

```python
# app/tasks/plex.py
"""Celery tasks for Plex Media Server integration"""

import logging
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.domain.plex.models import PlexItemType
from app.domain.plex.service import PlexSyncService
from app.infrastructure.external_apis.plex.client import PlexClient
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _make_client() -> Optional[PlexClient]:
    """Return a configured PlexClient, or None if Plex is not configured."""
    if not settings.plex_server_url:
        logger.warning("Plex not configured (PLEX_SERVER_URL not set) — skipping")
        return None
    token = settings.plex_token or ""
    return PlexClient(server_url=settings.plex_server_url, token=token)


@celery_app.task(
    name="app.tasks.plex.refresh_plex_library",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="external_api",
)
def refresh_plex_library(self, section_id: str) -> None:
    """Trigger a Plex library section rescan."""
    client = _make_client()
    if client is None:
        return None

    try:
        logger.info("Plex: refreshing library section %s", section_id)
        client.refresh_library_section(section_id=section_id)
        logger.info("Plex: library section %s refresh triggered", section_id)
    except Exception as exc:
        logger.error("Plex: refresh failed for section %s: %s", section_id, exc)
        raise self.retry(exc=exc)
```

**Step 4: Run test**

```bash
pytest tests/test_plex_tasks.py -v -k "refresh"
```
Expected: PASSED.

**Step 5: Commit**

```bash
git add app/tasks/plex.py tests/test_plex_tasks.py
git commit -m "feat(plex): add refresh_plex_library Celery task"
```

---

### Task 2: Match locking task

**Files:**
- Modify: `app/tasks/plex.py`
- Modify: `tests/test_plex_tasks.py`

**Step 1: Write failing test**

```python
# append to tests/test_plex_tasks.py
from app.tasks.plex import lock_plex_match
from app.domain.plex.models import PlexItemType


@patch("app.tasks.plex.PlexSyncService")
@patch("app.tasks.plex.PlexClient")
@patch("app.tasks.plex.get_db")
@patch("app.tasks.plex.settings")
def test_lock_plex_match_delegates_to_service(
    mock_settings, mock_get_db, mock_client_cls, mock_service_cls
):
    mock_settings.plex_server_url = "http://plex:32400"
    mock_settings.plex_token = "token"
    mock_settings.plex_library_movies = "Movies"
    mock_settings.plex_library_tv = "TV Shows"

    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])
    mock_service = MagicMock()
    mock_service_cls.return_value = mock_service
    mock_service.resolve_library_ids.return_value = ("1", "2")

    lock_plex_match.apply(args=["movie", 42, "603", 1]).get()

    mock_service.lock_match.assert_called_once_with(
        section_id="1",
        item_type=PlexItemType.MOVIE,
        item_id=42,
        tmdb_id="603",
        connection_id=1,
    )
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_plex_tasks.py -v -k "lock_plex_match"
```
Expected: `ImportError` or `AttributeError`

**Step 3: Add task**

```python
# append to app/tasks/plex.py

_ITEM_TYPE_MAP = {
    "movie": PlexItemType.MOVIE,
    "tv_show": PlexItemType.TV_SHOW,
    "episode": PlexItemType.EPISODE,
}


@celery_app.task(
    name="app.tasks.plex.lock_plex_match",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="external_api",
)
def lock_plex_match(
    self, item_type_str: str, item_id: int, tmdb_id: str, connection_id: int
) -> None:
    """Resolve TMDB ID to Plex ratingKey and lock the match."""
    client = _make_client()
    if client is None:
        return None

    db = next(get_db())
    try:
        svc = PlexSyncService(
            db=db,
            client=client,
            movie_library_name=settings.plex_library_movies,
            tv_library_name=settings.plex_library_tv,
        )
        movie_section_id, _ = svc.resolve_library_ids()
        item_type = _ITEM_TYPE_MAP[item_type_str]
        svc.lock_match(
            section_id=movie_section_id,
            item_type=item_type,
            item_id=item_id,
            tmdb_id=tmdb_id,
            connection_id=connection_id,
        )
    except Exception as exc:
        logger.error("Plex: lock_match failed for %s id=%s: %s", item_type_str, item_id, exc)
        raise self.retry(exc=exc)
    finally:
        db.close()
```

**Step 4: Run test**

```bash
pytest tests/test_plex_tasks.py -v -k "lock_plex_match"
```
Expected: PASSED.

**Step 5: Commit**

```bash
git add app/tasks/plex.py tests/test_plex_tasks.py
git commit -m "feat(plex): add lock_plex_match Celery task"
```

---

### Task 3: Poll watched status task

**Files:**
- Modify: `app/tasks/plex.py`
- Modify: `tests/test_plex_tasks.py`

**Step 1: Write failing test**

```python
# append to tests/test_plex_tasks.py
from app.tasks.plex import poll_plex_watched_status


@patch("app.tasks.plex.PlexSyncService")
@patch("app.tasks.plex.PlexClient")
@patch("app.tasks.plex.get_db")
@patch("app.tasks.plex.settings")
def test_poll_plex_watched_status_calls_pull_for_movies_and_tv(
    mock_settings, mock_get_db, mock_client_cls, mock_service_cls
):
    mock_settings.plex_server_url = "http://plex:32400"
    mock_settings.plex_token = "token"
    mock_settings.plex_library_movies = "Movies"
    mock_settings.plex_library_tv = "TV Shows"

    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])
    mock_service = MagicMock()
    mock_service_cls.return_value = mock_service
    mock_service.resolve_library_ids.return_value = ("1", "2")

    poll_plex_watched_status.apply(args=[1]).get()

    # type=1 for movies, type=4 for episodes
    calls = mock_service.pull_watched_status.call_args_list
    assert any(c.kwargs.get("media_type") == 1 or c[0][1] == 1 for c in calls)
    assert any(c.kwargs.get("media_type") == 4 or c[0][1] == 4 for c in calls)
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_plex_tasks.py -v -k "poll_plex"
```
Expected: `ImportError` or `AttributeError`

**Step 3: Add task**

```python
# append to app/tasks/plex.py

@celery_app.task(
    name="app.tasks.plex.poll_plex_watched_status",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    queue="external_api",
)
def poll_plex_watched_status(self, connection_id: int) -> None:
    """Pull watch status from Plex for all movies and episodes."""
    client = _make_client()
    if client is None:
        return None

    db = next(get_db())
    try:
        svc = PlexSyncService(
            db=db,
            client=client,
            movie_library_name=settings.plex_library_movies,
            tv_library_name=settings.plex_library_tv,
        )
        movie_section_id, tv_section_id = svc.resolve_library_ids()
        logger.info("Plex: polling watched status for movies and TV")
        svc.pull_watched_status(
            section_id=movie_section_id, media_type=1, connection_id=connection_id
        )
        svc.pull_watched_status(
            section_id=tv_section_id, media_type=4, connection_id=connection_id
        )
        logger.info("Plex: watched status poll complete")
    except Exception as exc:
        logger.error("Plex: poll_watched_status failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()
```

**Step 4: Run all task tests**

```bash
pytest tests/test_plex_tasks.py -v
```
Expected: All PASSED.

**Step 5: Commit**

```bash
git add app/tasks/plex.py tests/test_plex_tasks.py
git commit -m "feat(plex): add poll_plex_watched_status Celery task"
```

---

### Task 4: Register poll task in Celery Beat

**Files:**
- Modify: `app/tasks/celery_beat.py`

**Step 1: Add poll schedule**

In `app/tasks/celery_beat.py`, add to the `beat_schedule` dict:

```python
"poll_plex_watched_status": {
    "task": "app.tasks.plex.poll_plex_watched_status",
    "schedule": settings.plex_sync_poll_interval_seconds,  # default 300s
    "args": [1],  # connection_id=1 (single-server for now)
    "options": {
        "queue": "external_api",
    },
},
```

Note: `celery_beat.py` will need to import `settings`:
```python
from app.core.config import settings
```

**Step 2: Add plex task to celery_app task routes**

In `app/tasks/celery_app.py`, add to `task_routes`:

```python
"app.tasks.plex.*": {"queue": "external_api"},
```

**Step 3: Verify Celery can find the task**

```bash
celery -A app.tasks.celery_app inspect registered 2>/dev/null | grep plex || echo "Start worker to verify"
```

**Step 4: Lint**

```bash
black app/tasks/plex.py app/tasks/celery_beat.py app/tasks/celery_app.py tests/test_plex_tasks.py
isort app/tasks/plex.py app/tasks/celery_beat.py tests/test_plex_tasks.py
flake8 app/tasks/plex.py app/tasks/celery_beat.py tests/test_plex_tasks.py
mypy app/tasks/plex.py
```

**Step 5: Commit**

```bash
git add app/tasks/celery_beat.py app/tasks/celery_app.py app/tasks/plex.py tests/test_plex_tasks.py
git commit -m "feat(plex): register poll_plex_watched_status in Celery Beat"
```
