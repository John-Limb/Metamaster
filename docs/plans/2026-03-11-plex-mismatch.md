# Plex TMDB Mismatch Detection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Detect when Plex and MetaMaster have matched the same file to different TMDB IDs, surface the conflict in the UI, and let the user resolve it per-item.

**Architecture:** Two-step TMDB ID → title+year lookup during `lock_match`; mismatch stored on `PlexSyncRecord`; two new API endpoints; frontend badge on library cards and a panel on the Plex page.

**Tech Stack:** SQLAlchemy / Alembic, FastAPI, Plex HTTP API, React + Zustand + TypeScript

---

### Task 1: Schema and migration

**Files:**
- Modify: `app/domain/plex/models.py`
- Create: `alembic/versions/013_plex_mismatch.py`

**Background:** `PlexSyncStatus` is both a Python enum and a PostgreSQL native enum (`plexsyncstatus`). Both must be updated together. The new `plex_tmdb_id` column stores what Plex resolved the item to when it differs from ours.

**Step 1: Write the failing test**

Add to `tests/test_plex_models.py`:

```python
@pytest.mark.unit
def test_plex_sync_status_has_mismatch_value():
    from app.domain.plex.models import PlexSyncStatus
    assert PlexSyncStatus.MISMATCH == "mismatch"
```

**Step 2: Run to verify it fails**

```bash
pytest tests/test_plex_models.py::test_plex_sync_status_has_mismatch_value -v
```
Expected: FAIL — `AttributeError: MISMATCH`

**Step 3: Update the Python enum and SAEnum in models.py**

In `app/domain/plex/models.py`, change `PlexSyncStatus`:

```python
class PlexSyncStatus(str, enum.Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    NOT_FOUND = "not_found"
    MISMATCH = "mismatch"
```

Update the `sync_status` column SAEnum string list on `PlexSyncRecord`:

```python
sync_status: Any = Column(
    SAEnum("pending", "synced", "failed", "not_found", "mismatch", name="plexsyncstatus"),
    nullable=False,
    default="pending",
)
```

Add `plex_tmdb_id` column to `PlexSyncRecord` (after `plex_rating_key`):

```python
plex_tmdb_id = Column(String(50), nullable=True)
```

**Step 4: Create the Alembic migration**

Create `alembic/versions/013_plex_mismatch.py`:

```python
"""Add mismatch support to plex_sync_records

Revision ID: 013
Revises: 012
Create Date: 2026-03-11
"""

import sqlalchemy as sa

from alembic import op

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL: ADD VALUE cannot run inside a transaction on older versions.
    # IF NOT EXISTS makes this idempotent.
    op.execute("ALTER TYPE plexsyncstatus ADD VALUE IF NOT EXISTS 'mismatch'")
    op.add_column(
        "plex_sync_records",
        sa.Column("plex_tmdb_id", sa.String(50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("plex_sync_records", "plex_tmdb_id")
    # Note: PostgreSQL cannot remove enum values without recreating the type.
    # The 'mismatch' value is left in place on downgrade.
```

**Step 5: Run the tests to verify they pass**

```bash
pytest tests/test_plex_models.py -v
```
Expected: all PASS

**Step 6: Commit**

```bash
git add app/domain/plex/models.py alembic/versions/013_plex_mismatch.py
git commit -m "feat(plex): add MISMATCH status and plex_tmdb_id column"
```

---

### Task 2: PlexClient.find_by_title_year

**Files:**
- Modify: `app/infrastructure/external_apis/plex/client.py`
- Test: `tests/test_plex_client.py`

**Background:** When `find_rating_key_by_tmdb_id` returns nothing, we fall back to title+year search. Plex supports `?title=...` as a filter on `/library/sections/{id}/all`. The year filter is applied client-side because Plex's title filter is fuzzy. Returns the first `PlexMediaItem` whose `year` matches (or any item if `year` is None).

**Step 1: Write the failing tests**

Add to `tests/test_plex_client.py`:

```python
@pytest.mark.unit
@respx.mock
def test_find_by_title_year_returns_item_when_found():
    respx.get(
        "http://plex:32400/library/sections/1/all",
        params={"type": 1, "title": "The Matrix"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "MediaContainer": {
                    "Metadata": [
                        {
                            "ratingKey": "77",
                            "title": "The Matrix",
                            "year": 1999,
                            "Guid": [{"id": "tmdb://9999"}],
                        }
                    ]
                }
            },
        )
    )
    client = PlexClient(server_url="http://plex:32400", token="fake-token")
    item = client.find_by_title_year(section_id="1", title="The Matrix", year=1999)
    assert item is not None
    assert item.rating_key == "77"
    assert item.tmdb_id == "9999"


@pytest.mark.unit
@respx.mock
def test_find_by_title_year_returns_none_when_year_mismatch():
    respx.get(
        "http://plex:32400/library/sections/1/all",
        params={"type": 1, "title": "The Matrix"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "MediaContainer": {
                    "Metadata": [
                        {"ratingKey": "77", "title": "The Matrix", "year": 2003, "Guid": []}
                    ]
                }
            },
        )
    )
    client = PlexClient(server_url="http://plex:32400", token="fake-token")
    item = client.find_by_title_year(section_id="1", title="The Matrix", year=1999)
    assert item is None


@pytest.mark.unit
@respx.mock
def test_find_by_title_year_returns_item_when_year_is_none():
    """When year is None (e.g. TV show), return the first title match."""
    respx.get(
        "http://plex:32400/library/sections/2/all",
        params={"type": 2, "title": "Breaking Bad"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "MediaContainer": {
                    "Metadata": [
                        {"ratingKey": "55", "title": "Breaking Bad", "year": 2008, "Guid": [{"id": "tmdb://1396"}]}
                    ]
                }
            },
        )
    )
    client = PlexClient(server_url="http://plex:32400", token="fake-token")
    item = client.find_by_title_year(section_id="2", title="Breaking Bad", year=None, media_type=2)
    assert item is not None
    assert item.rating_key == "55"
```

**Step 2: Run to verify they fail**

```bash
pytest tests/test_plex_client.py::test_find_by_title_year_returns_item_when_found -v
```
Expected: FAIL — `AttributeError: 'PlexClient' object has no attribute 'find_by_title_year'`

**Step 3: Implement in client.py**

Add to `app/infrastructure/external_apis/plex/client.py` after `find_rating_key_by_tmdb_id`:

```python
def find_by_title_year(
    self,
    section_id: str,
    title: str,
    year: Optional[int],
    media_type: int = 1,
) -> Optional[PlexMediaItem]:
    """Find a Plex item by title and year. Returns first match, or None."""
    data = self._get(
        f"/library/sections/{section_id}/all",
        params={"type": media_type, "title": title},
    )
    for raw in data.get("MediaContainer", {}).get("Metadata", []):
        item = PlexMediaItem(**raw)
        if year is None or item.year == year:
            return item
    return None
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_plex_client.py -v
```
Expected: all PASS

**Step 5: Commit**

```bash
git add app/infrastructure/external_apis/plex/client.py tests/test_plex_client.py
git commit -m "feat(plex): add title+year fallback search to PlexClient"
```

---

### Task 3: PlexClient.fix_match

**Files:**
- Modify: `app/infrastructure/external_apis/plex/client.py`
- Test: `tests/test_plex_client.py`

**Background:** When the user chooses "Trust MetaMaster", we push our TMDB ID directly to Plex. Plex's fix-match endpoint is `PUT /library/metadata/{ratingKey}/match?guid=tmdb://{id}&name={title}`. This skips the interactive candidate-search step and directly sets the match.

**Step 1: Write the failing test**

Add to `tests/test_plex_client.py`:

```python
@pytest.mark.unit
@respx.mock
def test_fix_match_calls_correct_url():
    route = respx.put("http://plex:32400/library/metadata/99/match").mock(
        return_value=httpx.Response(200)
    )
    client = PlexClient(server_url="http://plex:32400", token="fake-token")
    client.fix_match(rating_key="99", tmdb_id="603", title="The Matrix")
    assert route.called
    request = route.calls[0].request
    assert "tmdb%3A%2F%2F603" in str(request.url) or "tmdb://603" in str(request.url)
```

**Step 2: Run to verify it fails**

```bash
pytest tests/test_plex_client.py::test_fix_match_calls_correct_url -v
```
Expected: FAIL — `AttributeError: 'PlexClient' object has no attribute 'fix_match'`

**Step 3: Implement in client.py**

Add `_put` helper and `fix_match` to `PlexClient`. Also add `import urllib.parse` at the top of the file.

```python
import urllib.parse
```

```python
def _put(self, path: str, params: Optional[dict] = None) -> None:
    url = f"{self._base}{path}"
    logger.info("Plex API PUT %s params=%s", url, params)
    with httpx.Client(timeout=10) as http:
        response = http.put(url, headers=self._headers(), params=params)
    response.raise_for_status()

def fix_match(self, rating_key: str, tmdb_id: str, title: str) -> None:
    """Push our TMDB ID to Plex to correct its match."""
    self._put(
        f"/library/metadata/{rating_key}/match",
        params={"guid": f"tmdb://{tmdb_id}", "name": title},
    )
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_plex_client.py -v
```
Expected: all PASS

**Step 5: Commit**

```bash
git add app/infrastructure/external_apis/plex/client.py tests/test_plex_client.py
git commit -m "feat(plex): add fix_match to PlexClient for correcting Plex metadata"
```

---

### Task 4: Mismatch detection in PlexSyncService.lock_match

**Files:**
- Modify: `app/domain/plex/service.py`
- Test: `tests/test_plex_service.py`

**Background:** `lock_match` currently does a single TMDB ID lookup. Add `title` and `year` params and a two-step lookup: TMDB ID first (→ SYNCED), then title+year fallback (→ MISMATCH or NOT_FOUND).

**Step 1: Write the failing tests**

Add to `tests/test_plex_service.py`:

```python
@pytest.mark.unit
def test_lock_match_detects_mismatch_via_title_year_fallback():
    """If TMDB lookup fails but title+year finds a different TMDB ID, mark MISMATCH."""
    from app.infrastructure.external_apis.plex.schemas import PlexMediaItem

    mock_db = MagicMock()
    mock_client = MagicMock()
    mock_client.find_rating_key_by_tmdb_id.return_value = None  # our tmdb_id not found
    plex_item = PlexMediaItem(**{
        "ratingKey": "77",
        "title": "The Matrix",
        "year": 1999,
        "Guid": [{"id": "tmdb://9999"}],  # Plex has a different tmdb_id
    })
    mock_client.find_by_title_year.return_value = plex_item
    mock_db.query.return_value.filter.return_value.first.return_value = None

    svc = PlexSyncService(
        db=mock_db, client=mock_client,
        movie_library_name="Movies", tv_library_name="TV Shows",
    )
    svc.lock_match(
        section_id="1",
        item_type=PlexItemType.MOVIE,
        item_id=42,
        tmdb_id="603",
        connection_id=1,
        title="The Matrix",
        year=1999,
    )

    record = mock_db.add.call_args[0][0]
    assert record.sync_status == PlexSyncStatus.MISMATCH
    assert record.plex_tmdb_id == "9999"
    assert record.plex_rating_key == "77"


@pytest.mark.unit
def test_lock_match_skips_title_fallback_when_no_title_provided():
    """If title is not provided, fall straight through to NOT_FOUND."""
    mock_db = MagicMock()
    mock_client = MagicMock()
    mock_client.find_rating_key_by_tmdb_id.return_value = None
    mock_db.query.return_value.filter.return_value.first.return_value = None

    svc = PlexSyncService(
        db=mock_db, client=mock_client,
        movie_library_name="Movies", tv_library_name="TV Shows",
    )
    svc.lock_match(
        section_id="1",
        item_type=PlexItemType.MOVIE,
        item_id=42,
        tmdb_id="603",
        connection_id=1,
        # no title/year
    )

    record = mock_db.add.call_args[0][0]
    assert record.sync_status == PlexSyncStatus.NOT_FOUND
    mock_client.find_by_title_year.assert_not_called()


@pytest.mark.unit
def test_lock_match_not_found_when_title_fallback_finds_nothing():
    mock_db = MagicMock()
    mock_client = MagicMock()
    mock_client.find_rating_key_by_tmdb_id.return_value = None
    mock_client.find_by_title_year.return_value = None
    mock_db.query.return_value.filter.return_value.first.return_value = None

    svc = PlexSyncService(
        db=mock_db, client=mock_client,
        movie_library_name="Movies", tv_library_name="TV Shows",
    )
    svc.lock_match(
        section_id="1",
        item_type=PlexItemType.MOVIE,
        item_id=42,
        tmdb_id="603",
        connection_id=1,
        title="The Matrix",
        year=1999,
    )

    record = mock_db.add.call_args[0][0]
    assert record.sync_status == PlexSyncStatus.NOT_FOUND
```

**Step 2: Run to verify they fail**

```bash
pytest tests/test_plex_service.py::test_lock_match_detects_mismatch_via_title_year_fallback -v
```
Expected: FAIL — `lock_match() got an unexpected keyword argument 'title'`

**Step 3: Rewrite lock_match in service.py**

Replace the `lock_match` method in `app/domain/plex/service.py`:

```python
def lock_match(
    self,
    section_id: str,
    item_type: PlexItemType,
    item_id: int,
    tmdb_id: str,
    connection_id: int,
    title: Optional[str] = None,
    year: Optional[int] = None,
) -> PlexSyncRecord:
    """Resolve TMDB ID to Plex ratingKey and upsert sync record.

    Two-step lookup:
    1. Search by our tmdb_id → SYNCED
    2. Fallback title+year search → MISMATCH (different tmdb_id) or NOT_FOUND
    """
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

    rating_key = self._client.find_rating_key_by_tmdb_id(
        section_id=section_id, tmdb_id=tmdb_id
    )
    if rating_key:
        record.plex_rating_key = rating_key  # type: ignore[assignment]
        record.plex_tmdb_id = None  # type: ignore[assignment]
        record.sync_status = PlexSyncStatus.SYNCED  # type: ignore[assignment]
        record.last_matched_at = datetime.utcnow()  # type: ignore[assignment]
        logger.info("Plex match locked: %s id=%s key=%s", item_type, item_id, rating_key)
        self._db.commit()
        return record

    if title:
        plex_item = self._client.find_by_title_year(
            section_id=section_id, title=title, year=year
        )
        if plex_item and plex_item.tmdb_id and plex_item.tmdb_id != tmdb_id:
            record.plex_rating_key = plex_item.rating_key  # type: ignore[assignment]
            record.plex_tmdb_id = plex_item.tmdb_id  # type: ignore[assignment]
            record.sync_status = PlexSyncStatus.MISMATCH  # type: ignore[assignment]
            record.last_matched_at = datetime.utcnow()  # type: ignore[assignment]
            logger.warning(
                "Plex TMDB mismatch: %s id=%s ours=%s plex=%s",
                item_type, item_id, tmdb_id, plex_item.tmdb_id,
            )
            self._db.commit()
            return record

    record.sync_status = PlexSyncStatus.NOT_FOUND  # type: ignore[assignment]
    record.plex_rating_key = None  # type: ignore[assignment]
    record.plex_tmdb_id = None  # type: ignore[assignment]
    logger.warning("Plex match not found: %s id=%s tmdb_id=%s", item_type, item_id, tmdb_id)
    self._db.commit()
    return record
```

**Step 4: Run all service tests**

```bash
pytest tests/test_plex_service.py -v
```
Expected: all PASS

**Step 5: Commit**

```bash
git add app/domain/plex/service.py tests/test_plex_service.py
git commit -m "feat(plex): detect TMDB mismatch via title+year fallback in lock_match"
```

---

### Task 5: Update Celery task to pass title and year

**Files:**
- Modify: `app/tasks/plex.py`
- Test: `tests/test_plex_tasks.py`

**Background:** `lock_plex_match` must load the `Movie` or `TVShow` from the DB to get title and year, then pass them to `lock_match`. TV shows have no `year` field — pass `None`.

**Step 1: Read the existing task tests**

Open `tests/test_plex_tasks.py` and note the existing test for `lock_plex_match`. We need to update it so the mock also provides title and year.

**Step 2: Write the failing test**

Add to `tests/test_plex_tasks.py`:

```python
@pytest.mark.unit
@patch("app.tasks.plex._make_client")
@patch("app.tasks.plex.get_db")
def test_lock_plex_match_passes_title_and_year_to_service(mock_get_db, mock_make_client):
    from unittest.mock import MagicMock, patch
    from app.tasks.plex import lock_plex_match

    mock_client = MagicMock()
    mock_make_client.return_value = mock_client

    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])

    # Mock the Movie loaded from db
    mock_movie = MagicMock()
    mock_movie.title = "The Matrix"
    mock_movie.year = 1999

    mock_svc = MagicMock()
    mock_svc.resolve_library_ids.return_value = ("1", "2")

    with patch("app.tasks.plex.PlexSyncService", return_value=mock_svc), \
         patch("app.tasks.plex.Movie") as mock_movie_cls:
        mock_movie_cls.id = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_movie

        lock_plex_match("movie", 42, "603", 1)

    call_kwargs = mock_svc.lock_match.call_args[1]
    assert call_kwargs["title"] == "The Matrix"
    assert call_kwargs["year"] == 1999
```

**Step 3: Run to verify it fails**

```bash
pytest tests/test_plex_tasks.py::test_lock_plex_match_passes_title_and_year_to_service -v
```
Expected: FAIL

**Step 4: Update lock_plex_match in app/tasks/plex.py**

Add imports at the top of the file (after existing imports):

```python
from app.domain.movies.models import Movie
from app.domain.tv_shows.models import TVShow
```

Add a helper function before `lock_plex_match`:

```python
def _get_title_year(db, item_type_str: str, item_id: int):
    """Return (title, year) for the given item, or (None, None) if not found."""
    if item_type_str == "movie":
        item = db.query(Movie).filter(Movie.id == item_id).first()
        return (item.title, item.year) if item else (None, None)
    if item_type_str == "tv_show":
        item = db.query(TVShow).filter(TVShow.id == item_id).first()
        return (item.title, None) if item else (None, None)
    return (None, None)
```

Update the `lock_plex_match` task body to call `_get_title_year` and pass to `lock_match`:

```python
@celery_app.task(
    name="app.tasks.plex.lock_plex_match",
    queue="external_api",
)
def lock_plex_match(item_type_str: str, item_id: int, tmdb_id: str, connection_id: int) -> None:
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
        movie_section_id, tv_section_id = svc.resolve_library_ids()
        item_type = _ITEM_TYPE_MAP[item_type_str]
        section_id = movie_section_id if item_type == PlexItemType.MOVIE else tv_section_id
        title, year = _get_title_year(db, item_type_str, item_id)
        svc.lock_match(
            section_id=section_id,
            item_type=item_type,
            item_id=item_id,
            tmdb_id=tmdb_id,
            connection_id=connection_id,
            title=title,
            year=year,
        )
    finally:
        db.close()
```

**Step 5: Run all plex task tests**

```bash
pytest tests/test_plex_tasks.py -v
```
Expected: all PASS

**Step 6: Commit**

```bash
git add app/tasks/plex.py tests/test_plex_tasks.py
git commit -m "feat(plex): pass title and year to lock_match for mismatch detection"
```

---

### Task 6: Mismatch API endpoints

**Files:**
- Modify: `app/api/v1/plex/schemas.py`
- Modify: `app/api/v1/plex/router.py`
- Test: `tests/test_plex_api.py`

**Background:** Two new endpoints. `GET /mismatches` returns all MISMATCH records. `POST /mismatches/{record_id}/resolve` resolves with `trust=metamaster` (push our ID to Plex) or `trust=plex` (update our DB + re-enrich). The router already has `_get_tmdb_id_for_record` — reuse it.

**Step 1: Write the failing tests**

Add to `tests/test_plex_api.py`:

```python
@pytest.mark.unit
def test_get_mismatches_returns_mismatch_records():
    from app.domain.plex.models import PlexSyncStatus

    mock_session = MagicMock()
    mismatch_records = [
        MagicMock(
            id=10,
            item_type="movie",
            item_id=42,
            plex_rating_key="77",
            plex_tmdb_id="9999",
        ),
    ]
    mock_session.query.return_value.filter.return_value.all.return_value = mismatch_records

    def _override_db():
        yield mock_session

    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_db] = _override_db
    try:
        response = client.get("/api/v1/plex/mismatches", headers=auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["plex_tmdb_id"] == "9999"
        assert data[0]["item_type"] == "movie"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.unit
@patch("app.api.v1.plex.router.PlexClient")
def test_resolve_mismatch_trust_metamaster(mock_client_cls):
    mock_session = MagicMock()
    mock_record = MagicMock(
        id=10, item_type="movie", item_id=42,
        plex_rating_key="77", plex_tmdb_id="9999", connection_id=1,
    )
    mock_conn = MagicMock(server_url="http://plex:32400", token="tok")
    mock_movie = MagicMock(tmdb_id="603", title="The Matrix")
    mock_session.query.return_value.filter.return_value.first.side_effect = [
        mock_record, mock_conn, mock_movie,
    ]
    mock_plex = MagicMock()
    mock_client_cls.return_value = mock_plex

    def _override_db():
        yield mock_session

    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_db] = _override_db
    try:
        response = client.post(
            "/api/v1/plex/mismatches/10/resolve",
            headers=auth_headers(),
            json={"trust": "metamaster"},
        )
        assert response.status_code == 200
        mock_plex.fix_match.assert_called_once_with(
            rating_key="77", tmdb_id="603", title="The Matrix"
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.unit
@patch("app.api.v1.plex.router.enrich_movie")
def test_resolve_mismatch_trust_plex_updates_tmdb_id(mock_enrich):
    mock_session = MagicMock()
    mock_record = MagicMock(
        id=10, item_type="movie", item_id=42,
        plex_rating_key="77", plex_tmdb_id="9999", connection_id=1,
    )
    mock_movie = MagicMock(id=42, tmdb_id="603")
    mock_session.query.return_value.filter.return_value.first.side_effect = [
        mock_record, mock_movie,
    ]
    mock_enrich.delay.return_value = MagicMock(id="task-enrich")

    def _override_db():
        yield mock_session

    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_db] = _override_db
    try:
        response = client.post(
            "/api/v1/plex/mismatches/10/resolve",
            headers=auth_headers(),
            json={"trust": "plex"},
        )
        assert response.status_code == 200
        assert mock_movie.tmdb_id == "9999"
        mock_enrich.delay.assert_called_once_with(42)
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
```

**Step 2: Run to verify they fail**

```bash
pytest tests/test_plex_api.py::test_get_mismatches_returns_mismatch_records -v
```
Expected: FAIL — 404 (route not registered)

**Step 3: Add schemas to app/api/v1/plex/schemas.py**

```python
class PlexMismatchItem(BaseModel):
    id: int
    item_type: str
    item_id: int
    plex_rating_key: str
    plex_tmdb_id: str


class PlexResolveRequest(BaseModel):
    trust: str  # "metamaster" or "plex"
```

**Step 4: Add endpoints to app/api/v1/plex/router.py**

Add to the imports at the top:

```python
from app.api.v1.plex.schemas import (
    PlexConnectionCreate,
    PlexMismatchItem,
    PlexOAuthInitResponse,
    PlexResolveRequest,
    PlexSyncTriggerResponse,
)
from app.domain.movies.models import Movie
from app.infrastructure.external_apis.plex.client import PlexClient
from app.tasks.enrichment import enrich_movie
```

Also add `TVShow` import:
```python
from app.domain.tv_shows.models import TVShow
```

Add the two new route handlers at the end of the router file:

```python
@router.get("/mismatches", response_model=list[PlexMismatchItem])
def list_mismatches(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Return all sync records with TMDB mismatch between MetaMaster and Plex."""
    records = (
        db.query(PlexSyncRecord)
        .filter(PlexSyncRecord.sync_status == PlexSyncStatus.MISMATCH)
        .all()
    )
    return [
        PlexMismatchItem(
            id=r.id,
            item_type=r.item_type,
            item_id=r.item_id,
            plex_rating_key=r.plex_rating_key,
            plex_tmdb_id=r.plex_tmdb_id,
        )
        for r in records
    ]


@router.post("/mismatches/{record_id}/resolve")
def resolve_mismatch(
    record_id: int,
    payload: PlexResolveRequest,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Resolve a TMDB mismatch. trust='metamaster' pushes our ID to Plex;
    trust='plex' updates our DB and re-triggers enrichment."""
    record = db.query(PlexSyncRecord).filter(PlexSyncRecord.id == record_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Sync record not found")
    if record.sync_status != PlexSyncStatus.MISMATCH:
        raise HTTPException(status_code=400, detail="Record is not in MISMATCH state")

    if payload.trust == "metamaster":
        _resolve_trust_metamaster(db, record)
    elif payload.trust == "plex":
        _resolve_trust_plex(db, record)
    else:
        raise HTTPException(status_code=422, detail="trust must be 'metamaster' or 'plex'")

    return {"status": "resolved"}


def _resolve_trust_metamaster(db: Session, record: PlexSyncRecord) -> None:
    """Push our TMDB ID to Plex to fix their match."""
    conn = db.query(PlexConnection).filter(PlexConnection.id == record.connection_id).first()
    our_tmdb_id = _get_tmdb_id_for_record(db, record.item_type, record.item_id)
    title = _get_title_for_record(db, record.item_type, record.item_id)
    if conn and our_tmdb_id and title:
        plex = PlexClient(server_url=conn.server_url, token=conn.token)
        plex.fix_match(rating_key=record.plex_rating_key, tmdb_id=our_tmdb_id, title=title)
    record.plex_tmdb_id = None  # type: ignore[assignment]
    record.sync_status = PlexSyncStatus.SYNCED  # type: ignore[assignment]
    db.commit()


def _resolve_trust_plex(db: Session, record: PlexSyncRecord) -> None:
    """Accept Plex's TMDB ID: update our item and re-trigger enrichment."""
    plex_tmdb_id = record.plex_tmdb_id
    item_type: str = record.item_type  # type: ignore[assignment]
    item_id: int = record.item_id  # type: ignore[assignment]

    if item_type == "movie":
        item = db.query(Movie).filter(Movie.id == item_id).first()
        if item:
            item.tmdb_id = plex_tmdb_id  # type: ignore[assignment]
            db.flush()
            enrich_movie.delay(item_id)
    elif item_type == "tv_show":
        item = db.query(TVShow).filter(TVShow.id == item_id).first()
        if item:
            item.tmdb_id = plex_tmdb_id  # type: ignore[assignment]
            db.flush()

    record.plex_tmdb_id = None  # type: ignore[assignment]
    record.sync_status = PlexSyncStatus.SYNCED  # type: ignore[assignment]
    db.commit()


def _get_title_for_record(db: Session, item_type: str, item_id: int) -> Optional[str]:
    """Look up the title from the source model for the given item."""
    if item_type == "movie":
        item = db.query(Movie).filter(Movie.id == item_id).first()
        return item.title if item else None
    if item_type == "tv_show":
        item = db.query(TVShow).filter(TVShow.id == item_id).first()
        return item.title if item else None
    return None
```

**Step 5: Run all plex API tests**

```bash
pytest tests/test_plex_api.py -v
```
Expected: all PASS

**Step 6: Run full lint check**

```bash
black app/api/v1/plex/ && isort app/api/v1/plex/ && flake8 app/api/v1/plex/
```
Expected: no errors

**Step 7: Commit**

```bash
git add app/api/v1/plex/schemas.py app/api/v1/plex/router.py tests/test_plex_api.py
git commit -m "feat(plex): add mismatch list and resolve endpoints"
```

---

### Task 7: Frontend service and store

**Files:**
- Modify: `frontend/src/services/plexService.ts`
- Modify: `frontend/src/stores/plexStore.ts`
- Test: `frontend/src/services/__tests__/plexService.test.ts`

**Background:** Add `getMismatches()` and `resolveMismatch()` to the service, then expose `mismatches`, `fetchMismatches`, and `resolveMismatch` from the store.

**Step 1: Write failing tests**

Add to `frontend/src/services/__tests__/plexService.test.ts`:

```typescript
describe('getMismatches', () => {
  it('returns mismatch items from the API', async () => {
    const mockData = [
      { id: 10, item_type: 'movie', item_id: 42, plex_rating_key: '77', plex_tmdb_id: '9999' },
    ]
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockData })
    const result = await getMismatches()
    expect(result).toEqual(mockData)
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/plex/mismatches')
  })
})

describe('resolveMismatch', () => {
  it('posts resolve request to the API', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: { status: 'resolved' } })
    await resolveMismatch(10, 'metamaster')
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/plex/mismatches/10/resolve', {
      trust: 'metamaster',
    })
  })
})
```

**Step 2: Run to verify they fail**

```bash
cd frontend && npm run test -- --reporter=verbose 2>&1 | grep -A5 "getMismatches\|resolveMismatch"
```
Expected: FAIL — `getMismatches is not a function`

**Step 3: Add types and functions to plexService.ts**

Add to `frontend/src/services/plexService.ts`:

```typescript
export interface PlexMismatchItem {
  id: number
  item_type: string
  item_id: number
  plex_rating_key: string
  plex_tmdb_id: string
}

export async function getMismatches(): Promise<PlexMismatchItem[]> {
  const { data } = await apiClient.get<PlexMismatchItem[]>('/api/v1/plex/mismatches')
  return data
}

export async function resolveMismatch(
  recordId: number,
  trust: 'metamaster' | 'plex'
): Promise<void> {
  await apiClient.post(`/api/v1/plex/mismatches/${recordId}/resolve`, { trust })
}
```

**Step 4: Update plexStore.ts**

Add `mismatches` state and actions to `plexStore.ts`:

```typescript
import { create } from 'zustand'
import type { PlexConnection, PlexMismatchItem } from '../services/plexService'
import {
  deletePlexConnection,
  getMismatches,
  getPlexConnection,
  resolveMismatch,
  triggerPlexSync,
} from '../services/plexService'

interface PlexState {
  connection: PlexConnection | null
  isLoading: boolean
  error: string | null
  mismatches: PlexMismatchItem[]
  fetchConnection: () => Promise<void>
  disconnect: () => Promise<void>
  sync: () => Promise<string>
  fetchMismatches: () => Promise<void>
  resolveMismatch: (recordId: number, trust: 'metamaster' | 'plex') => Promise<void>
}

export const usePlexStore = create<PlexState>((set, get) => ({
  connection: null,
  isLoading: false,
  error: null,
  mismatches: [],

  fetchConnection: async () => {
    set({ isLoading: true, error: null })
    try {
      const connection = await getPlexConnection()
      set({ connection, isLoading: false })
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status: number } }
      if (axiosErr?.response?.status === 404) {
        set({ connection: null, isLoading: false })
      } else {
        set({ error: 'Failed to load Plex connection', isLoading: false })
      }
    }
  },

  disconnect: async () => {
    await deletePlexConnection()
    set({ connection: null })
  },

  sync: async () => {
    const result = await triggerPlexSync()
    return result.task_id
  },

  fetchMismatches: async () => {
    try {
      const mismatches = await getMismatches()
      set({ mismatches })
    } catch {
      // silently fail — mismatches are supplementary
    }
  },

  resolveMismatch: async (recordId, trust) => {
    await resolveMismatch(recordId, trust)
    // Remove the resolved item from local state immediately
    set((state) => ({
      mismatches: state.mismatches.filter((m) => m.id !== recordId),
    }))
  },
}))
```

**Step 5: Run frontend tests**

```bash
cd frontend && npm run test
```
Expected: all PASS

**Step 6: Run type check**

```bash
cd frontend && npm run type-check
```
Expected: no errors

**Step 7: Commit**

```bash
git add frontend/src/services/plexService.ts frontend/src/stores/plexStore.ts \
  "frontend/src/services/__tests__/plexService.test.ts"
git commit -m "feat(plex): add mismatch service functions and store state"
```

---

### Task 8: Library card mismatch badge and resolve modal

**Files:**
- Identify the movie card component with: `grep -r "MovieCard\|movie-card" frontend/src --include="*.tsx" -l`
- Create: `frontend/src/components/features/plex/MismatchResolveModal.tsx`
- Modify: movie and TV show card components

**Background:** The library needs to show a small warning badge on cards where a MISMATCH exists. Clicking opens a modal. The mismatch data comes from `usePlexStore` — it's fetched once at app startup or on the library page mount.

**Step 1: Find the card components**

```bash
grep -r "poster\|MovieCard\|TVShowCard" frontend/src --include="*.tsx" -l
```

Note the exact file paths — you'll add the badge to those components.

**Step 2: Write the failing test for MismatchResolveModal**

Create `frontend/src/components/features/plex/__tests__/MismatchResolveModal.test.tsx`:

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MismatchResolveModal } from '../MismatchResolveModal'

describe('MismatchResolveModal', () => {
  const mismatch = {
    id: 10,
    item_type: 'movie',
    item_id: 42,
    plex_rating_key: '77',
    plex_tmdb_id: '9999',
  }

  it('shows our tmdb id and plex tmdb id', () => {
    render(
      <MismatchResolveModal
        mismatch={mismatch}
        ourTmdbId="603"
        onResolve={vi.fn()}
        onClose={vi.fn()}
      />
    )
    expect(screen.getByText(/603/)).toBeInTheDocument()
    expect(screen.getByText(/9999/)).toBeInTheDocument()
  })

  it('calls onResolve with metamaster when that button is clicked', () => {
    const onResolve = vi.fn()
    render(
      <MismatchResolveModal
        mismatch={mismatch}
        ourTmdbId="603"
        onResolve={onResolve}
        onClose={vi.fn()}
      />
    )
    fireEvent.click(screen.getByText(/Trust MetaMaster/i))
    expect(onResolve).toHaveBeenCalledWith(10, 'metamaster')
  })

  it('calls onResolve with plex when that button is clicked', () => {
    const onResolve = vi.fn()
    render(
      <MismatchResolveModal
        mismatch={mismatch}
        ourTmdbId="603"
        onResolve={onResolve}
        onClose={vi.fn()}
      />
    )
    fireEvent.click(screen.getByText(/Trust Plex/i))
    expect(onResolve).toHaveBeenCalledWith(10, 'plex')
  })
})
```

**Step 3: Run to verify they fail**

```bash
cd frontend && npm run test -- MismatchResolveModal
```
Expected: FAIL — module not found

**Step 4: Create MismatchResolveModal.tsx**

Create `frontend/src/components/features/plex/MismatchResolveModal.tsx`:

```tsx
import React from 'react'
import type { PlexMismatchItem } from '../../../services/plexService'

interface Props {
  mismatch: PlexMismatchItem
  ourTmdbId: string
  onResolve: (recordId: number, trust: 'metamaster' | 'plex') => void
  onClose: () => void
}

const BTN =
  'px-4 py-2 rounded-lg text-sm font-medium transition disabled:opacity-50'

export function MismatchResolveModal({ mismatch, ourTmdbId, onResolve, onClose }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 max-w-md w-full mx-4 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          TMDB ID Mismatch
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          MetaMaster and Plex have matched this item to different TMDB IDs. Which is correct?
        </p>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="p-3 rounded-lg bg-gray-100 dark:bg-gray-700">
            <p className="font-medium text-gray-700 dark:text-gray-300">MetaMaster</p>
            <p className="text-gray-900 dark:text-white">TMDB #{ourTmdbId}</p>
          </div>
          <div className="p-3 rounded-lg bg-gray-100 dark:bg-gray-700">
            <p className="font-medium text-gray-700 dark:text-gray-300">Plex</p>
            <p className="text-gray-900 dark:text-white">TMDB #{mismatch.plex_tmdb_id}</p>
          </div>
        </div>
        <div className="flex gap-3 pt-2">
          <button
            onClick={() => onResolve(mismatch.id, 'metamaster')}
            className={`${BTN} bg-primary-600 text-white hover:bg-primary-700 flex-1`}
          >
            Trust MetaMaster
          </button>
          <button
            onClick={() => onResolve(mismatch.id, 'plex')}
            className={`${BTN} bg-orange-500 text-white hover:bg-orange-600 flex-1`}
          >
            Trust Plex
          </button>
        </div>
        <button
          onClick={onClose}
          className="w-full text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
```

**Step 5: Add the mismatch badge to movie/TV show cards**

In the card component(s) you found in Step 1, add:
1. Import `usePlexStore` and `MismatchResolveModal`
2. Add `const { mismatches, fetchMismatches, resolveMismatch } = usePlexStore()` — call `fetchMismatches()` in a `useEffect` on the parent page if not already called
3. Compute `const mismatch = mismatches.find(m => m.item_type === 'movie' && m.item_id === movie.id)`
4. Render a warning badge when `mismatch` exists; clicking sets `activeMismatch` state which renders `<MismatchResolveModal>`

**Step 6: Run all frontend tests**

```bash
cd frontend && npm run test
```
Expected: all PASS

**Step 7: Run type check and lint**

```bash
cd frontend && npm run type-check && npm run lint
```
Expected: no errors

**Step 8: Commit**

```bash
git add frontend/src/components/features/plex/
git commit -m "feat(plex): add mismatch badge to library cards with resolve modal"
```

---

### Task 9: Plex page mismatches panel

**Files:**
- Create: `frontend/src/components/features/plex/MismatchesPanel.tsx`
- Modify: The Plex page (see `docs/plans/2026-03-07-plex-page.md` — if not yet built, add panel to `PlexSettings.tsx` as a fallback)

**Step 1: Write the failing test**

Create `frontend/src/components/features/plex/__tests__/MismatchesPanel.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MismatchesPanel } from '../MismatchesPanel'

const mismatches = [
  { id: 10, item_type: 'movie', item_id: 42, plex_rating_key: '77', plex_tmdb_id: '9999' },
]

describe('MismatchesPanel', () => {
  it('renders nothing when there are no mismatches', () => {
    const { container } = render(
      <MismatchesPanel mismatches={[]} onResolve={vi.fn()} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('shows mismatch count and items when mismatches exist', () => {
    render(<MismatchesPanel mismatches={mismatches} onResolve={vi.fn()} />)
    expect(screen.getByText(/1 TMDB mismatch/i)).toBeInTheDocument()
    expect(screen.getByText(/movie #42/i)).toBeInTheDocument()
  })
})
```

**Step 2: Run to verify they fail**

```bash
cd frontend && npm run test -- MismatchesPanel
```
Expected: FAIL

**Step 3: Create MismatchesPanel.tsx**

```tsx
import React, { useState } from 'react'
import type { PlexMismatchItem } from '../../../services/plexService'
import { MismatchResolveModal } from './MismatchResolveModal'

interface Props {
  mismatches: PlexMismatchItem[]
  onResolve: (recordId: number, trust: 'metamaster' | 'plex') => void
}

export function MismatchesPanel({ mismatches, onResolve }: Props) {
  const [active, setActive] = useState<PlexMismatchItem | null>(null)

  if (mismatches.length === 0) return null

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-orange-600 dark:text-orange-400">
        {mismatches.length} TMDB mismatch{mismatches.length !== 1 ? 'es' : ''} detected
      </h3>
      <ul className="space-y-2">
        {mismatches.map((m) => (
          <li
            key={m.id}
            className="flex items-center justify-between text-sm p-3 rounded-lg bg-orange-50 dark:bg-orange-900/20"
          >
            <span className="text-gray-700 dark:text-gray-300">
              {m.item_type} #{m.item_id} — MetaMaster vs Plex #{m.plex_tmdb_id}
            </span>
            <button
              onClick={() => setActive(m)}
              className="ml-3 px-3 py-1 text-xs bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition"
            >
              Resolve
            </button>
          </li>
        ))}
      </ul>

      {active && (
        <MismatchResolveModal
          mismatch={active}
          ourTmdbId={active.plex_tmdb_id}  // placeholder — parent should pass real tmdb_id
          onResolve={(id, trust) => {
            onResolve(id, trust)
            setActive(null)
          }}
          onClose={() => setActive(null)}
        />
      )}
    </div>
  )
}
```

**Step 4: Add MismatchesPanel to the Plex page**

In `frontend/src/pages/PlexPage.tsx` (or `PlexSettings.tsx` if the page isn't built yet), import and render `<MismatchesPanel>`:

```tsx
const { mismatches, fetchMismatches, resolveMismatch } = usePlexStore()

useEffect(() => {
  fetchMismatches()
}, [fetchMismatches])

// In JSX, after the connection/Now Playing section:
<MismatchesPanel mismatches={mismatches} onResolve={resolveMismatch} />
```

**Step 5: Run all frontend tests**

```bash
cd frontend && npm run test
```
Expected: all PASS

**Step 6: Run type check and lint**

```bash
cd frontend && npm run type-check && npm run lint
```
Expected: no errors

**Step 7: Final backend lint + tests**

```bash
black app/ tests/ && isort app/ tests/ && flake8 app/ tests/ && mypy app/
pytest -m unit -q
```
Expected: all clean, all PASS

**Step 8: Commit**

```bash
git add frontend/src/components/features/plex/MismatchesPanel.tsx \
  "frontend/src/components/features/plex/__tests__/MismatchesPanel.test.tsx"
git commit -m "feat(plex): add MismatchesPanel to Plex page"
```
