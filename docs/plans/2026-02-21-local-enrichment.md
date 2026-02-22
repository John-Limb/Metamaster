# Local Enrichment with Deferred External Metadata — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Decouple ffprobe local scanning from OMDB/TVDB external enrichment so movies and TV shows are always created with technical metadata regardless of API availability, with deferred and retryable external enrichment.

**Architecture:** Add an `enrichment_status` state machine column to `movies` and `tv_shows`. Stage 1 (ffprobe + filename ID parsing) always succeeds. Stage 2 (OMDB/TVDB) runs as a separate Celery task, retried every 2 hours for failed items, with manual override via new API endpoints and UI. Items with no API match are flagged as `not_found` and require a user-supplied external ID.

**Tech Stack:** SQLAlchemy 2.0, Alembic, Celery, FastAPI, React + TypeScript, Vitest, pytest

---

### Task 1: Database migration — enrichment_status enum + new columns

**Files:**
- Create: `alembic/versions/007_add_enrichment_status.py`

**Step 1: Write the migration**

```python
"""Add enrichment_status and related columns to movies and tv_shows

Revision ID: 007
Revises: 006
Create Date: 2026-02-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None

ENUM_NAME = 'enrichmentstatus'
ENUM_VALUES = ('pending_local', 'local_only', 'pending_external', 'fully_enriched', 'external_failed', 'not_found')


def upgrade() -> None:
    enrichment_status_enum = postgresql.ENUM(*ENUM_VALUES, name=ENUM_NAME)
    enrichment_status_enum.create(op.get_bind())

    for table in ('movies', 'tv_shows'):
        op.add_column(table, sa.Column('enrichment_status', sa.Enum(*ENUM_VALUES, name=ENUM_NAME), nullable=False, server_default='pending_local'))
        op.add_column(table, sa.Column('detected_external_id', sa.String(50), nullable=True))
        op.add_column(table, sa.Column('manual_external_id', sa.String(50), nullable=True))
        op.add_column(table, sa.Column('enrichment_error', sa.Text(), nullable=True))


def downgrade() -> None:
    for table in ('tv_shows', 'movies'):
        op.drop_column(table, 'enrichment_error')
        op.drop_column(table, 'manual_external_id')
        op.drop_column(table, 'detected_external_id')
        op.drop_column(table, 'enrichment_status')

    postgresql.ENUM(name=ENUM_NAME).drop(op.get_bind())
```

**Step 2: Run the migration**

```bash
alembic upgrade head
```

Expected output: `Running upgrade 006 -> 007`

**Step 3: Commit**

```bash
git add alembic/versions/007_add_enrichment_status.py
git commit -m "feat: add enrichment_status migration for movies and tv_shows"
```

---

### Task 2: Update domain models with new columns

**Files:**
- Modify: `app/domain/movies/models.py`
- Modify: `app/domain/tv_shows/models.py`

**Step 1: Write tests for new model properties**

Create `tests/domain/test_enrichment_status.py`:

```python
"""Unit tests for enrichment_status on Movie and TVShow models."""
import pytest
from app.domain.movies.models import Movie
from app.domain.tv_shows.models import TVShow


def test_movie_default_enrichment_status():
    movie = Movie(title="Test", year=2020)
    assert movie.enrichment_status == "pending_local"


def test_movie_enrichment_status_assignment():
    movie = Movie(title="Test", year=2020)
    movie.enrichment_status = "local_only"
    assert movie.enrichment_status == "local_only"


def test_movie_detected_external_id_defaults_none():
    movie = Movie(title="Test", year=2020)
    assert movie.detected_external_id is None


def test_movie_manual_external_id_defaults_none():
    movie = Movie(title="Test", year=2020)
    assert movie.manual_external_id is None


def test_tvshow_default_enrichment_status():
    show = TVShow(title="Test Show")
    assert show.enrichment_status == "pending_local"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/domain/test_enrichment_status.py -v
```

Expected: FAIL — `Movie has no attribute enrichment_status`

**Step 3: Update Movie model** (`app/domain/movies/models.py`)

Add these imports and columns after line 4:

```python
from sqlalchemy import BigInteger, Column, Integer, String, Text, Float, DateTime, ForeignKey, Index, Enum as SAEnum
```

Add columns to `Movie` class after `poster_url`:

```python
enrichment_status = Column(
    SAEnum('pending_local', 'local_only', 'pending_external', 'fully_enriched', 'external_failed', 'not_found', name='enrichmentstatus'),
    nullable=False,
    default='pending_local',
)
detected_external_id = Column(String(50), nullable=True)
manual_external_id = Column(String(50), nullable=True)
enrichment_error = Column(Text, nullable=True)
```

**Step 4: Update TVShow model** (`app/domain/tv_shows/models.py`)

Same import addition, and add the same four columns to `TVShow` after `poster_url`.

**Step 5: Run tests**

```bash
pytest tests/domain/test_enrichment_status.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add app/domain/movies/models.py app/domain/tv_shows/models.py tests/domain/test_enrichment_status.py
git commit -m "feat: add enrichment_status fields to Movie and TVShow models"
```

---

### Task 3: Filename/folder ID parser

**Files:**
- Modify: `app/domain/movies/scanner.py`
- Create: `tests/domain/test_id_parser.py`

**Step 1: Write failing tests**

```python
"""Tests for external ID parsing from file paths and folder names."""
import pytest
from app.domain.movies.scanner import extract_external_id_from_path


@pytest.mark.parametrize("path,expected", [
    # Plex/Jellyfin folder convention
    ("/movies/Inception (2010) {imdb-tt1375666}/Inception.mkv", "tt1375666"),
    # Bare ID in folder
    ("/movies/The Matrix (1999) tt0133093/matrix.mkv", "tt0133093"),
    # Parenthesis style
    ("/movies/Dune (tt1160419)/dune.mkv", "tt1160419"),
    # ID in filename itself
    ("/movies/Interstellar {imdb-tt0816692}.mkv", "tt0816692"),
    # TVDB style
    ("/tv/Breaking Bad {tvdb-81189}/S01E01.mkv", "81189"),
    # No ID present
    ("/movies/Some Random Movie (2020)/movie.mkv", None),
    # ID too short — not matched
    ("/movies/Movie tt123/m.mkv", None),
])
def test_extract_external_id_from_path(path, expected):
    assert extract_external_id_from_path(path) == expected
```

**Step 2: Run to verify failure**

```bash
pytest tests/domain/test_id_parser.py -v
```

Expected: FAIL — `cannot import name 'extract_external_id_from_path'`

**Step 3: Implement `extract_external_id_from_path`** in `app/domain/movies/scanner.py`

Add after the existing `title_from_filename` function (after line 39):

```python
# Matches {imdb-ttXXXXXXX}, {tvdb-XXXXX}, (ttXXXXXXX), bare ttXXXXXXX (7-8 digits)
_IMDB_PATTERNS = [
    re.compile(r'\{imdb-(?P<id>tt\d{7,8})\}', re.IGNORECASE),
    re.compile(r'\((?P<id>tt\d{7,8})\)'),
    re.compile(r'\btt(?P<id>\d{7,8})\b'),
]
_TVDB_PATTERN = re.compile(r'\{tvdb-(?P<id>\d{4,7})\}', re.IGNORECASE)


def extract_external_id_from_path(file_path: str) -> str | None:
    """Parse an IMDB or TVDB ID embedded in a file path or parent folder name.

    Checks both the filename stem and the immediate parent directory name.
    Returns the ID string (e.g. 'tt1375666' or '81189'), or None if not found.
    Priority: IMDB patterns > TVDB pattern.
    """
    path = Path(file_path)
    candidates = [path.stem, path.parent.name]
    for text in candidates:
        for pattern in _IMDB_PATTERNS:
            m = pattern.search(text)
            if m:
                return m.group('id') if 'id' in m.groupdict() else m.group(0).lstrip('t')
        m = _TVDB_PATTERN.search(text)
        if m:
            return m.group('id')
    return None
```

> Note: The IMDB bare-tt pattern captures only the digit portion in group `id` — adjust the return to prepend `tt` if needed. Here's the corrected implementation:

```python
_IMDB_BARE_PATTERN = re.compile(r'\b(?P<id>tt\d{7,8})\b')
_IMDB_BRACE_PATTERN = re.compile(r'\{imdb-(?P<id>tt\d{7,8})\}', re.IGNORECASE)
_IMDB_PAREN_PATTERN = re.compile(r'\((?P<id>tt\d{7,8})\)')
_TVDB_PATTERN = re.compile(r'\{tvdb-(?P<id>\d{4,7})\}', re.IGNORECASE)

_IMDB_PATTERNS = [_IMDB_BRACE_PATTERN, _IMDB_PAREN_PATTERN, _IMDB_BARE_PATTERN]


def extract_external_id_from_path(file_path: str) -> str | None:
    """Parse an IMDB or TVDB ID embedded in a file path or parent folder name."""
    path = Path(file_path)
    candidates = [path.stem, path.parent.name]
    for text in candidates:
        for pattern in _IMDB_PATTERNS:
            m = pattern.search(text)
            if m:
                return m.group('id')
        m = _TVDB_PATTERN.search(text)
        if m:
            return m.group('id')
    return None
```

**Step 4: Run tests**

```bash
pytest tests/domain/test_id_parser.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add app/domain/movies/scanner.py tests/domain/test_id_parser.py
git commit -m "feat: add extract_external_id_from_path for embedded IMDB/TVDB IDs"
```

---

### Task 4: Decouple ffprobe (Stage 1) from external enrichment (Stage 2) — movies

**Files:**
- Modify: `app/domain/movies/scanner.py`
- Modify: `tests/domain/` (existing or new test file)

**Step 1: Write failing tests**

Create `tests/domain/test_movie_scanner.py`:

```python
"""Tests for decoupled movie scanning flow."""
import pytest
from unittest.mock import MagicMock, patch
from app.domain.movies.scanner import create_movies_from_files


def make_db_with_file(file_path="/movies/Inception (2010)/inception.mkv"):
    """Build a minimal mock DB that returns one FileItem."""
    fi = MagicMock()
    fi.path = file_path
    fi.name = "inception.mkv"
    fi.size = 1_000_000_000
    fi.type = "file"

    db = MagicMock()
    db.query.return_value.filter.return_value.all.side_effect = [
        [],   # existing MovieFile paths
        [fi], # FileItem results
    ]
    db.query.return_value.all.return_value = []
    return db


@patch("app.domain.movies.scanner.get_ffprobe", return_value=None)
def test_create_movies_sets_local_only_status_when_ffprobe_unavailable(mock_ffprobe):
    db = make_db_with_file()
    movie = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()

    with patch("app.domain.movies.scanner.Movie") as MockMovie:
        MockMovie.return_value = movie
        create_movies_from_files(db)
        # enrichment_status should be set to local_only (ffprobe skipped)
        assert movie.enrichment_status == "local_only"


@patch("app.domain.movies.scanner.get_ffprobe")
def test_create_movies_sets_local_only_status_after_ffprobe(mock_get_ffprobe):
    mock_ffprobe = MagicMock()
    mock_ffprobe.get_metadata.return_value = {}
    mock_get_ffprobe.return_value = mock_ffprobe

    db = make_db_with_file()
    movie = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()

    with patch("app.domain.movies.scanner.Movie") as MockMovie:
        MockMovie.return_value = movie
        create_movies_from_files(db)
        assert movie.enrichment_status == "local_only"


def test_create_movies_does_not_call_omdb():
    """Stage 1 must never call OMDB."""
    db = make_db_with_file()
    with patch("app.domain.movies.scanner.OMDBService") as MockOMDB:
        create_movies_from_files(db)
        MockOMDB.search_movie.assert_not_called()
```

**Step 2: Run to verify failures**

```bash
pytest tests/domain/test_movie_scanner.py -v
```

Expected: FAIL

**Step 3: Update `create_movies_from_files`** in `app/domain/movies/scanner.py`

Replace the current `create_movies_from_files` function body (lines 110–170):

- After `title, year = title_from_filename(fi.name)`, add:
  ```python
  detected_id = extract_external_id_from_path(fi.path)
  ```
- Change `movie = Movie(title=title, year=year)` to:
  ```python
  movie = Movie(title=title, year=year, enrichment_status='local_only', detected_external_id=detected_id)
  ```
- Remove the call to `OMDBService` (it was not in this function, but ensure no import side-effects dispatch enrichment here)
- The rest of the ffprobe logic stays the same

**Step 4: Remove `OMDBService` import** from scanner.py (line 13) — it is no longer needed here. The enrichment will be done by a separate Celery task (Task 5).

**Step 5: Run tests**

```bash
pytest tests/domain/test_movie_scanner.py -v
```

Expected: PASS

**Step 6: Run full backend test suite to check for regressions**

```bash
pytest -x -q
```

Expected: All pass (or existing failures unrelated to this change)

**Step 7: Commit**

```bash
git add app/domain/movies/scanner.py tests/domain/test_movie_scanner.py
git commit -m "feat: decouple ffprobe Stage 1 from external enrichment in movie scanner"
```

---

### Task 5: Decouple TV show scanner (Stage 1)

**Files:**
- Modify: `app/domain/tv_shows/scanner.py`

**Step 1: Write failing tests**

Create `tests/domain/test_tvshow_scanner.py`:

```python
"""Tests for decoupled TV show scanning flow."""
import pytest
from unittest.mock import MagicMock, patch
from app.domain.tv_shows.scanner import create_tv_shows_from_files


def test_create_tv_shows_does_not_call_tvdb():
    """Stage 1 must never call TVDB."""
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.all.return_value = []

    with patch("app.domain.tv_shows.scanner.TVDBService") as MockTVDB:
        create_tv_shows_from_files(db)
        MockTVDB.search_show.assert_not_called()
```

**Step 2: Run to verify failure**

```bash
pytest tests/domain/test_tvshow_scanner.py::test_create_tv_shows_does_not_call_tvdb -v
```

**Step 3: Update `create_tv_shows_from_files`** in `app/domain/tv_shows/scanner.py`

- In the loop where `TVShow` is created, add `enrichment_status='local_only'`
- Call `extract_external_id_from_path` (import it from `app.domain.movies.scanner`) on the episode file path to populate `detected_external_id` on the TVShow if it's a new show
- Remove any direct TVDB calls from the scanner (move to Task 6 Celery task)
- Remove `TVDBService` import from tv_shows/scanner.py

**Step 4: Run tests**

```bash
pytest tests/domain/test_tvshow_scanner.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add app/domain/tv_shows/scanner.py tests/domain/test_tvshow_scanner.py
git commit -m "feat: decouple ffprobe Stage 1 from external enrichment in TV show scanner"
```

---

### Task 6: External enrichment Celery task

**Files:**
- Create: `app/tasks/enrichment.py`
- Modify: `app/tasks/__init__.py`
- Modify: `app/tasks/celery_beat.py`
- Modify: `app/tasks/celery_app.py`
- Create: `tests/tasks/test_enrichment_task.py`

**Step 1: Write failing tests**

```python
"""Tests for the external enrichment Celery task."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


def make_movie(id=1, title="Inception", year=2010, enrichment_status="local_only",
               detected_external_id=None, manual_external_id=None):
    m = MagicMock()
    m.id = id
    m.title = title
    m.year = year
    m.enrichment_status = enrichment_status
    m.detected_external_id = detected_external_id
    m.manual_external_id = manual_external_id
    m.omdb_id = None
    return m


@patch("app.tasks.enrichment.SessionLocal")
@patch("app.tasks.enrichment.OMDBService")
def test_enrich_movie_uses_manual_id_first(MockOMDB, MockSession):
    """manual_external_id takes priority over search."""
    movie = make_movie(manual_external_id="tt9999999")
    db = MagicMock()
    MockSession.return_value.__enter__.return_value = db
    db.query.return_value.filter.return_value.first.return_value = movie

    MockOMDB.get_movie_details = AsyncMock(return_value={"Response": "True", "Title": "Inception"})
    MockOMDB.parse_omdb_response = MagicMock(return_value={"omdb_id": "tt9999999", "plot": "A dream"})

    from app.tasks.enrichment import enrich_movie_external
    enrich_movie_external(1)

    # Should NOT call search_movie — went straight to get_movie_details
    MockOMDB.search_movie.assert_not_called()
    assert movie.enrichment_status == "fully_enriched"


@patch("app.tasks.enrichment.SessionLocal")
@patch("app.tasks.enrichment.OMDBService")
def test_enrich_movie_sets_external_failed_on_api_error(MockOMDB, MockSession):
    """API unavailability sets status to external_failed."""
    import httpx
    movie = make_movie()
    db = MagicMock()
    MockSession.return_value.__enter__.return_value = db
    db.query.return_value.filter.return_value.first.return_value = movie

    MockOMDB.search_movie = AsyncMock(side_effect=httpx.ConnectError("unreachable"))

    from app.tasks.enrichment import enrich_movie_external
    enrich_movie_external(1)

    assert movie.enrichment_status == "external_failed"
    assert movie.enrichment_error is not None


@patch("app.tasks.enrichment.SessionLocal")
@patch("app.tasks.enrichment.OMDBService")
def test_enrich_movie_sets_not_found_when_no_results(MockOMDB, MockSession):
    """Empty search result sets status to not_found."""
    movie = make_movie()
    db = MagicMock()
    MockSession.return_value.__enter__.return_value = db
    db.query.return_value.filter.return_value.first.return_value = movie

    MockOMDB.search_movie = AsyncMock(return_value=None)
    MockOMDB.parse_omdb_response = MagicMock(return_value=None)

    from app.tasks.enrichment import enrich_movie_external
    enrich_movie_external(1)

    assert movie.enrichment_status == "not_found"
```

**Step 2: Run to verify failures**

```bash
pytest tests/tasks/test_enrichment_task.py -v
```

Expected: FAIL — `cannot import name 'enrich_movie_external'`

**Step 3: Create `app/tasks/enrichment.py`**

```python
"""Celery tasks for external metadata enrichment (OMDB / TVDB)."""

import logging
import httpx
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.domain.movies.models import Movie
from app.domain.tv_shows.models import TVShow
from app.services_impl import OMDBService, TVDBService
from app.tasks.async_helpers import run_async
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

RETRYABLE_STATUSES = ("local_only", "external_failed")


def _resolve_movie_id(movie: Movie) -> str | None:
    """Return the best external ID available for a movie, or None to trigger search."""
    return movie.manual_external_id or movie.detected_external_id


def enrich_movie_external(movie_id: int) -> None:
    """Fetch OMDB metadata for a single movie. Sets enrichment_status accordingly.

    Priority: manual_external_id > detected_external_id > title search.
    """
    with SessionLocal() as db:
        movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if not movie:
            logger.warning(f"Movie {movie_id} not found for enrichment")
            return

        existing_ids = {
            row[0] for row in db.query(Movie.omdb_id).filter(Movie.omdb_id.isnot(None)).all()
        }

        try:
            movie.enrichment_status = "pending_external"
            db.commit()

            external_id = _resolve_movie_id(movie)

            if external_id:
                # Direct fetch by ID
                raw = run_async(OMDBService.get_movie_details(db, external_id))
            else:
                # Search by title + year
                raw = run_async(OMDBService.search_movie(db, movie.title, movie.year))
                if raw:
                    parsed_search = OMDBService.parse_omdb_response(raw)
                    results = parsed_search.get("search_results", []) if parsed_search else []
                    external_id = results[0].get("omdb_id") if results else None
                    if not external_id:
                        movie.enrichment_status = "not_found"
                        movie.enrichment_error = "No match found in OMDB"
                        db.commit()
                        return
                    raw = run_async(OMDBService.get_movie_details(db, external_id))
                else:
                    movie.enrichment_status = "not_found"
                    movie.enrichment_error = "No match found in OMDB"
                    db.commit()
                    return

            if not raw:
                movie.enrichment_status = "not_found"
                movie.enrichment_error = "OMDB returned no data for this ID"
                db.commit()
                return

            detail = OMDBService.parse_omdb_response(raw)
            if not detail:
                movie.enrichment_status = "not_found"
                movie.enrichment_error = "Could not parse OMDB response"
                db.commit()
                return

            omdb_id = detail.get("omdb_id") or external_id
            if omdb_id and omdb_id not in existing_ids:
                movie.omdb_id = omdb_id
            movie.plot = detail.get("plot", movie.plot)
            movie.rating = detail.get("rating", movie.rating)
            movie.runtime = detail.get("runtime", movie.runtime)
            movie.genres = detail.get("genres", movie.genres)
            poster = detail.get("poster")
            if poster and poster != "N/A":
                movie.poster_url = poster
            movie.enrichment_status = "fully_enriched"
            movie.enrichment_error = None
            db.commit()
            logger.info(f"Enriched movie {movie_id} ({movie.title}) successfully")

        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            movie.enrichment_status = "external_failed"
            movie.enrichment_error = f"API unreachable: {exc}"
            db.commit()
            logger.warning(f"External API unavailable for movie {movie_id}: {exc}")
        except Exception as exc:
            movie.enrichment_status = "external_failed"
            movie.enrichment_error = str(exc)
            db.commit()
            logger.error(f"Unexpected error enriching movie {movie_id}: {exc}", exc_info=True)


def enrich_tv_show_external(show_id: int) -> None:
    """Fetch TVDB metadata for a single TV show. Sets enrichment_status accordingly."""
    with SessionLocal() as db:
        show = db.query(TVShow).filter(TVShow.id == show_id).first()
        if not show:
            logger.warning(f"TVShow {show_id} not found for enrichment")
            return

        external_id = show.manual_external_id or show.detected_external_id

        try:
            show.enrichment_status = "pending_external"
            db.commit()

            if external_id:
                raw = run_async(TVDBService.get_show_details(db, external_id))
            else:
                raw = run_async(TVDBService.search_show(db, show.title))
                if raw:
                    parsed = TVDBService.parse_tvdb_response(raw)
                    results = parsed.get("search_results", []) if parsed else []
                    external_id = results[0].get("tvdb_id") if results else None
                    if not external_id:
                        show.enrichment_status = "not_found"
                        show.enrichment_error = "No match found in TVDB"
                        db.commit()
                        return
                    raw = run_async(TVDBService.get_show_details(db, external_id))
                else:
                    show.enrichment_status = "not_found"
                    show.enrichment_error = "No match found in TVDB"
                    db.commit()
                    return

            if not raw:
                show.enrichment_status = "not_found"
                show.enrichment_error = "TVDB returned no data for this ID"
                db.commit()
                return

            detail = TVDBService.parse_tvdb_response(raw) if raw else None
            if not detail:
                show.enrichment_status = "not_found"
                show.enrichment_error = "Could not parse TVDB response"
                db.commit()
                return

            tvdb_id = detail.get("tvdb_id") or external_id
            if tvdb_id:
                show.tvdb_id = tvdb_id
            show.plot = detail.get("plot", show.plot)
            show.rating = detail.get("rating", show.rating)
            show.genres = detail.get("genres", show.genres)
            show.status = detail.get("status", show.status)
            poster = detail.get("poster_url")
            if poster:
                show.poster_url = poster
            show.enrichment_status = "fully_enriched"
            show.enrichment_error = None
            db.commit()
            logger.info(f"Enriched TV show {show_id} ({show.title}) successfully")

        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            show.enrichment_status = "external_failed"
            show.enrichment_error = f"API unreachable: {exc}"
            db.commit()
            logger.warning(f"External API unavailable for TV show {show_id}: {exc}")
        except Exception as exc:
            show.enrichment_status = "external_failed"
            show.enrichment_error = str(exc)
            db.commit()
            logger.error(f"Unexpected error enriching TV show {show_id}: {exc}", exc_info=True)


@celery_app.task(name="app.tasks.retry_failed_enrichment", bind=True, max_retries=0)
def retry_failed_enrichment(self):
    """Periodic task: re-attempt external enrichment for local_only and external_failed items."""
    with SessionLocal() as db:
        movies = db.query(Movie).filter(
            Movie.enrichment_status.in_(RETRYABLE_STATUSES)
        ).all()
        tv_shows = db.query(TVShow).filter(
            TVShow.enrichment_status.in_(RETRYABLE_STATUSES)
        ).all()

    logger.info(f"retry_failed_enrichment: {len(movies)} movies, {len(tv_shows)} TV shows to retry")

    for movie in movies:
        enrich_movie_external(movie.id)

    for show in tv_shows:
        enrich_tv_show_external(show.id)
```

**Step 4: Register the task in `app/tasks/celery_beat.py`**

Add to the `beat_schedule` dict:

```python
"retry_failed_enrichment": {
    "task": "app.tasks.retry_failed_enrichment",
    "schedule": crontab(minute=0, hour="*/2"),  # every 2 hours
    "options": {
        "queue": "external_api",
    },
},
```

**Step 5: Register task route in `app/tasks/celery_app.py`**

In `task_routes`, add:
```python
"app.tasks.retry_failed_enrichment": {"queue": "external_api"},
"app.tasks.enrich_movie_external": {"queue": "external_api"},
"app.tasks.enrich_tv_show_external": {"queue": "external_api"},
```

**Step 6: Add import in `app/tasks/__init__.py`**

```python
from app.tasks.enrichment import enrich_movie_external, enrich_tv_show_external, retry_failed_enrichment
```

**Step 7: Run enrichment tests**

```bash
pytest tests/tasks/test_enrichment_task.py -v
```

Expected: PASS

**Step 8: Commit**

```bash
git add app/tasks/enrichment.py app/tasks/__init__.py app/tasks/celery_beat.py app/tasks/celery_app.py tests/tasks/test_enrichment_task.py
git commit -m "feat: add external enrichment Celery tasks with status state machine"
```

---

### Task 7: Update startup flow to use new two-stage approach

**Files:**
- Modify: `app/main.py`
- Modify: `app/api/v1/movies/endpoints.py`
- Modify: `app/api/v1/tv_shows/endpoints.py`

**Step 1: Find the startup enrichment calls in `app/main.py`**

```bash
grep -n "enrich_new" app/main.py
```

**Step 2: Replace `enrich_new_movies(db)` and `enrich_new_tv_shows(db)` calls**

In `app/main.py`, after `create_movies_from_files(db)` and `create_tv_shows_from_files(db)`, replace the enrich calls with the new Celery task dispatch:

```python
# Dispatch enrichment as background tasks instead of blocking startup
from app.tasks.enrichment import enrich_movie_external, enrich_tv_show_external
from app.domain.movies.models import Movie
from app.domain.tv_shows.models import TVShow

with SessionLocal() as db:
    pending_movies = db.query(Movie).filter(
        Movie.enrichment_status.in_(["local_only", "external_failed"])
    ).all()
    for m in pending_movies:
        enrich_movie_external.delay(m.id)

    pending_shows = db.query(TVShow).filter(
        TVShow.enrichment_status.in_(["local_only", "external_failed"])
    ).all()
    for s in pending_shows:
        enrich_tv_show_external.delay(s.id)
```

**Step 3: Update `scan-directory` endpoint** in `app/api/v1/movies/endpoints.py`

In the `scan_movie_directory` handler, replace `movies_enriched = enrich_new_movies(db)` with dispatching the task asynchronously:

```python
from app.tasks.enrichment import enrich_movie_external
from app.domain.movies.models import Movie as MovieModel

# Dispatch enrichment tasks for newly created/unenriched movies
pending = db.query(MovieModel).filter(
    MovieModel.enrichment_status.in_(["local_only", "external_failed"])
).all()
for m in pending:
    enrich_movie_external.delay(m.id)
movies_enriched = len(pending)
```

**Step 4: Do the same in `app/api/v1/tv_shows/endpoints.py`** for the TV show scan-directory endpoint.

**Step 5: Run backend tests**

```bash
pytest -x -q
```

Expected: All pass

**Step 6: Commit**

```bash
git add app/main.py app/api/v1/movies/endpoints.py app/api/v1/tv_shows/endpoints.py
git commit -m "feat: dispatch enrichment as async tasks from startup and scan endpoints"
```

---

### Task 8: New API endpoints — external-id override and enrichment trigger

**Files:**
- Modify: `app/api/v1/movies/endpoints.py`
- Modify: `app/api/v1/tv_shows/endpoints.py`
- Create: `app/api/v1/enrichment/` (new router)
- Create: `tests/api/test_enrichment_endpoints.py`

**Step 1: Write failing tests**

```python
"""Tests for enrichment API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


def test_patch_movie_external_id(client):
    """PATCH /movies/{id}/external-id sets manual_external_id and dispatches task."""
    with patch("app.api.v1.movies.endpoints.enrich_movie_external") as mock_task:
        mock_task.delay = MagicMock()
        response = client.patch("/api/v1/movies/1/external-id", json={"external_id": "tt1234567"})
    assert response.status_code == 200
    assert response.json()["manual_external_id"] == "tt1234567"


def test_post_movie_enrich(client):
    """POST /movies/{id}/enrich dispatches the enrichment task."""
    with patch("app.api.v1.movies.endpoints.enrich_movie_external") as mock_task:
        mock_task.delay = MagicMock()
        response = client.post("/api/v1/movies/1/enrich")
    assert response.status_code == 202


def test_get_enrichment_pending(client):
    """GET /enrichment/pending returns movies and shows awaiting enrichment."""
    response = client.get("/api/v1/enrichment/pending")
    assert response.status_code == 200
    data = response.json()
    assert "movies" in data
    assert "tv_shows" in data
```

**Step 2: Run to verify failure**

```bash
pytest tests/api/test_enrichment_endpoints.py -v
```

**Step 3: Add endpoints to `app/api/v1/movies/endpoints.py`**

```python
from pydantic import BaseModel

class ExternalIdPayload(BaseModel):
    external_id: str


@router.patch("/{movie_id}/external-id", response_model=MovieResponse)
async def set_movie_external_id(
    movie_id: int,
    payload: ExternalIdPayload,
    db: Session = Depends(get_db),
):
    """Set a manual OMDB/IMDB ID and trigger enrichment immediately."""
    from app.tasks.enrichment import enrich_movie_external
    movie = MovieService.get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    movie.manual_external_id = payload.external_id
    movie.enrichment_status = "local_only"
    movie.enrichment_error = None
    db.commit()
    db.refresh(movie)
    enrich_movie_external.delay(movie_id)
    cache_service = get_cache_service()
    cache_service.invalidate_movie(movie_id)
    return movie


@router.post("/{movie_id}/enrich", status_code=202)
async def trigger_movie_enrichment(
    movie_id: int,
    db: Session = Depends(get_db),
):
    """Manually trigger external enrichment for a movie."""
    from app.tasks.enrichment import enrich_movie_external
    movie = MovieService.get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    enrich_movie_external.delay(movie_id)
    return {"message": "Enrichment task dispatched", "movie_id": movie_id}
```

**Step 4: Add filter support to existing movie list endpoint**

In `app/api/v1/movies/endpoints.py`, add `enrichment_status` query param to `list_movies`:

```python
enrichment_status: str = Query(None, description="Filter by enrichment status"),
```

Pass it to `SearchFilters` and update `MovieSearchService.search` to filter by it when provided.

**Step 5: Create `app/api/v1/enrichment/` router**

Create `app/api/v1/enrichment/__init__.py` (empty).

Create `app/api/v1/enrichment/endpoints.py`:

```python
"""Enrichment status dashboard endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.domain.movies.models import Movie
from app.domain.tv_shows.models import TVShow

router = APIRouter(prefix="/enrichment", tags=["Enrichment"])

PENDING_STATUSES = ("local_only", "external_failed", "not_found", "pending_local")


@router.get("/pending")
async def get_pending_enrichment(db: Session = Depends(get_db)):
    """Return all movies and TV shows that need enrichment attention."""
    movies = db.query(Movie).filter(Movie.enrichment_status.in_(PENDING_STATUSES)).all()
    tv_shows = db.query(TVShow).filter(TVShow.enrichment_status.in_(PENDING_STATUSES)).all()
    return {
        "movies": [
            {
                "id": m.id,
                "title": m.title,
                "year": m.year,
                "enrichment_status": m.enrichment_status,
                "enrichment_error": m.enrichment_error,
                "detected_external_id": m.detected_external_id,
                "manual_external_id": m.manual_external_id,
            }
            for m in movies
        ],
        "tv_shows": [
            {
                "id": s.id,
                "title": s.title,
                "enrichment_status": s.enrichment_status,
                "enrichment_error": s.enrichment_error,
                "detected_external_id": s.detected_external_id,
                "manual_external_id": s.manual_external_id,
            }
            for s in tv_shows
        ],
        "total": len(movies) + len(tv_shows),
    }
```

**Step 6: Register the new router** in `app/api/v1/__init__.py` (or wherever routers are mounted in `app/main.py`):

```python
from app.api.v1.enrichment.endpoints import router as enrichment_router
app.include_router(enrichment_router, prefix="/api/v1")
```

**Step 7: Run tests**

```bash
pytest tests/api/test_enrichment_endpoints.py -v
```

Expected: PASS

**Step 8: Commit**

```bash
git add app/api/v1/movies/endpoints.py app/api/v1/tv_shows/endpoints.py app/api/v1/enrichment/ tests/api/test_enrichment_endpoints.py
git commit -m "feat: add external-id override, manual enrich trigger, and enrichment dashboard endpoints"
```

---

### Task 9: Regenerate frontend API types

**Files:**
- Modify: `frontend/src/types/api-schema.ts` (auto-generated)

**Step 1: Ensure backend dev server is running**

```bash
uvicorn app.main:app --reload
```

**Step 2: Regenerate types**

```bash
cd frontend && npm run typegen
```

**Step 3: Verify new types exist**

```bash
grep -n "enrichment_status\|manual_external_id\|detected_external_id" frontend/src/types/api-schema.ts
```

Expected: lines showing the new fields in Movie/TVShow schemas.

**Step 4: Commit**

```bash
git add frontend/src/types/api-schema.ts
git commit -m "chore: regenerate API types with enrichment status fields"
```

---

### Task 10: EnrichmentBadge component

**Files:**
- Create: `frontend/src/components/features/media/EnrichmentBadge/EnrichmentBadge.tsx`
- Create: `frontend/src/components/features/media/EnrichmentBadge/EnrichmentBadge.test.tsx`

**Step 1: Write failing tests**

```typescript
import { render, screen } from '@testing-library/react';
import { EnrichmentBadge } from './EnrichmentBadge';

test('shows green tick for fully_enriched', () => {
  render(<EnrichmentBadge status="fully_enriched" />);
  expect(screen.getByTitle('Fully enriched')).toBeInTheDocument();
});

test('shows amber badge for local_only', () => {
  render(<EnrichmentBadge status="local_only" />);
  expect(screen.getByText('Local only')).toBeInTheDocument();
});

test('shows red badge for not_found', () => {
  render(<EnrichmentBadge status="not_found" />);
  expect(screen.getByText('Manual needed')).toBeInTheDocument();
});

test('shows spinner for pending states', () => {
  render(<EnrichmentBadge status="pending_external" />);
  expect(screen.getByRole('status')).toBeInTheDocument();
});

test('renders nothing for undefined status', () => {
  const { container } = render(<EnrichmentBadge status={undefined} />);
  expect(container.firstChild).toBeNull();
});
```

**Step 2: Run to verify failure**

```bash
cd frontend && npx vitest run src/components/features/media/EnrichmentBadge/EnrichmentBadge.test.tsx
```

**Step 3: Implement `EnrichmentBadge.tsx`**

```tsx
import React from 'react';

type EnrichmentStatus =
  | 'pending_local'
  | 'local_only'
  | 'pending_external'
  | 'fully_enriched'
  | 'external_failed'
  | 'not_found'
  | undefined;

interface EnrichmentBadgeProps {
  status: EnrichmentStatus;
  className?: string;
}

export const EnrichmentBadge: React.FC<EnrichmentBadgeProps> = ({ status, className = '' }) => {
  if (!status) return null;

  if (status === 'fully_enriched') {
    return (
      <span
        title="Fully enriched"
        className={`inline-flex items-center justify-center w-5 h-5 rounded-full bg-green-500 text-white text-xs ${className}`}
      >
        ✓
      </span>
    );
  }

  if (status === 'not_found') {
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 ${className}`}>
        Manual needed
      </span>
    );
  }

  if (status === 'local_only' || status === 'external_failed') {
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800 ${className}`}>
        Local only
      </span>
    );
  }

  // pending_local or pending_external
  return (
    <span role="status" className={`inline-block w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin ${className}`} />
  );
};
```

**Step 4: Run tests**

```bash
cd frontend && npx vitest run src/components/features/media/EnrichmentBadge/EnrichmentBadge.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/features/media/EnrichmentBadge/
git commit -m "feat: add EnrichmentBadge component with status-based visual states"
```

---

### Task 11: Add badge to MovieCard and TVShowCard

**Files:**
- Modify: `frontend/src/components/features/movies/MovieCard/MovieCard.tsx`
- Modify: `frontend/src/components/features/tvshows/TVShowCard/TVShowCard.tsx`

**Step 1: Read the existing MovieCard**

```bash
# Read MovieCard.tsx to see current poster/overlay structure
```

**Step 2: Add `EnrichmentBadge` overlay to MovieCard**

Import `EnrichmentBadge` and add it as an absolute-positioned element over the poster corner:

```tsx
import { EnrichmentBadge } from '@/components/features/media/EnrichmentBadge/EnrichmentBadge';

// Inside the poster container div, add:
<div className="absolute top-2 right-2">
  <EnrichmentBadge status={movie.enrichment_status} />
</div>
```

**Step 3: Do the same for TVShowCard**

**Step 4: Run frontend tests**

```bash
cd frontend && npm test
```

Expected: All pass

**Step 5: Commit**

```bash
git add frontend/src/components/features/movies/MovieCard/ frontend/src/components/features/tvshows/TVShowCard/
git commit -m "feat: show enrichment status badge on movie and TV show cards"
```

---

### Task 12: Needs Attention page

**Files:**
- Create: `frontend/src/pages/NeedsAttention/NeedsAttentionPage.tsx`
- Create: `frontend/src/pages/NeedsAttention/NeedsAttentionPage.test.tsx`
- Create: `frontend/src/services/enrichmentService.ts`
- Modify: Router config (wherever routes are defined)
- Modify: `frontend/src/components/layout/Sidebar/Sidebar.tsx`

**Step 1: Create `enrichmentService.ts`**

```typescript
import { apiClient } from '@/utils/api';

export interface PendingEnrichmentItem {
  id: number;
  title: string;
  year?: number;
  enrichment_status: string;
  enrichment_error?: string;
  detected_external_id?: string;
  manual_external_id?: string;
}

export interface PendingEnrichmentResponse {
  movies: PendingEnrichmentItem[];
  tv_shows: PendingEnrichmentItem[];
  total: number;
}

export const enrichmentService = {
  getPending: async (): Promise<PendingEnrichmentResponse> => {
    const { data } = await apiClient.get('/enrichment/pending');
    return data;
  },

  setMovieExternalId: async (id: number, externalId: string) => {
    const { data } = await apiClient.patch(`/movies/${id}/external-id`, { external_id: externalId });
    return data;
  },

  setTvShowExternalId: async (id: number, externalId: string) => {
    const { data } = await apiClient.patch(`/tv-shows/${id}/external-id`, { external_id: externalId });
    return data;
  },

  triggerMovieEnrich: async (id: number) => {
    const { data } = await apiClient.post(`/movies/${id}/enrich`);
    return data;
  },

  triggerTvShowEnrich: async (id: number) => {
    const { data } = await apiClient.post(`/tv-shows/${id}/enrich`);
    return data;
  },
};
```

**Step 2: Write a failing test for the page**

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { NeedsAttentionPage } from './NeedsAttentionPage';

vi.mock('@/services/enrichmentService', () => ({
  enrichmentService: {
    getPending: vi.fn().mockResolvedValue({
      movies: [{ id: 1, title: 'Inception', enrichment_status: 'not_found', enrichment_error: 'No match found' }],
      tv_shows: [],
      total: 1,
    }),
  },
}));

test('shows not_found movies with external ID input', async () => {
  render(<NeedsAttentionPage />);
  await waitFor(() => expect(screen.getByText('Inception')).toBeInTheDocument());
  expect(screen.getByPlaceholderText(/OMDB.*IMDB.*ID/i)).toBeInTheDocument();
});

test('shows empty state when nothing pending', async () => {
  vi.mocked(enrichmentService.getPending).mockResolvedValueOnce({ movies: [], tv_shows: [], total: 0 });
  render(<NeedsAttentionPage />);
  await waitFor(() => expect(screen.getByText(/all media.*enriched/i)).toBeInTheDocument());
});
```

**Step 3: Implement `NeedsAttentionPage.tsx`**

The page should have three sections:
1. **Manual needed** — items with `not_found`, inline form for external ID input + submit button
2. **Failed** — items with `external_failed`, "Retry now" per item + "Retry all" bulk action
3. **Pending** — items with `local_only` or `pending_local`, informational list

Each row shows: title, status badge, error message (if any), detected ID (if any).

**Step 4: Add route and sidebar link**

Add `/needs-attention` route in the router. Add a "Needs Attention" link in the Sidebar with a red dot indicator when `total > 0`.

**Step 5: Run tests**

```bash
cd frontend && npm test
```

Expected: All pass

**Step 6: Commit**

```bash
git add frontend/src/pages/NeedsAttention/ frontend/src/services/enrichmentService.ts
git commit -m "feat: add Needs Attention page for enrichment status management"
```

---

### Task 13: Enrichment status section on detail pages

**Files:**
- Modify: `frontend/src/components/features/movies/MovieDetailPage/MovieDetailPage.tsx`
- Modify: `frontend/src/components/features/tvshows/TVShowDetailPage/TVShowDetailPage.tsx`

**Step 1: Add enrichment info section to MovieDetailPage**

After the main metadata section, add a small card showing:
- Current `enrichment_status` (with `EnrichmentBadge`)
- `enrichment_error` if present
- `detected_external_id` if set (read-only, labeled "Detected from filename")
- `manual_external_id` if set (read-only, labeled "Manual override")
- "Set External ID" button → inline form for `PATCH /{id}/external-id`
- "Trigger Enrichment" button → calls `POST /{id}/enrich`

**Step 2: Do the same for TVShowDetailPage**

**Step 3: Run frontend tests**

```bash
cd frontend && npm test
```

**Step 4: Commit**

```bash
git add frontend/src/components/features/movies/MovieDetailPage/ frontend/src/components/features/tvshows/TVShowDetailPage/
git commit -m "feat: add enrichment status panel to movie and TV show detail pages"
```

---

### Task 14: Update existing movies/shows to local_only status (data backfill)

**Files:**
- Create: `alembic/versions/008_backfill_enrichment_status.py`

**Step 1: Write the migration**

```python
"""Backfill enrichment_status for existing movies and tv_shows

Revision ID: 008
Revises: 007
Create Date: 2026-02-21
"""
from alembic import op

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Movies with omdb_id are fully enriched; without are local_only
    op.execute("""
        UPDATE movies
        SET enrichment_status = 'fully_enriched'
        WHERE omdb_id IS NOT NULL AND enrichment_status = 'pending_local'
    """)
    op.execute("""
        UPDATE movies
        SET enrichment_status = 'local_only'
        WHERE omdb_id IS NULL AND enrichment_status = 'pending_local'
    """)
    # TV shows with tvdb_id are fully enriched; without are local_only
    op.execute("""
        UPDATE tv_shows
        SET enrichment_status = 'fully_enriched'
        WHERE tvdb_id IS NOT NULL AND enrichment_status = 'pending_local'
    """)
    op.execute("""
        UPDATE tv_shows
        SET enrichment_status = 'local_only'
        WHERE tvdb_id IS NULL AND enrichment_status = 'pending_local'
    """)


def downgrade() -> None:
    op.execute("UPDATE movies SET enrichment_status = 'pending_local'")
    op.execute("UPDATE tv_shows SET enrichment_status = 'pending_local'")
```

**Step 2: Run the migration**

```bash
alembic upgrade head
```

Expected: `Running upgrade 007 -> 008`

**Step 3: Commit**

```bash
git add alembic/versions/008_backfill_enrichment_status.py
git commit -m "feat: backfill enrichment_status for existing media records"
```

---

### Task 15: Final verification

**Step 1: Run full backend test suite**

```bash
pytest -v --tb=short
```

Expected: All pass, 80%+ coverage maintained.

**Step 2: Run frontend tests**

```bash
cd frontend && npm test
```

Expected: All pass.

**Step 3: Run linting**

```bash
# Backend
black . && isort . && flake8

# Frontend
cd frontend && npm run lint
```

Expected: No errors.

**Step 4: Manual smoke test (if docker available)**

```bash
docker-compose up -d
# Add a test movie file with {imdb-tt0133093} in its folder name
# Check /api/v1/enrichment/pending
# Check /api/v1/movies — verify enrichment_status badge in UI
```

**Step 5: Commit any lint fixes, then tag as ready**

```bash
git commit -m "chore: lint and type fixes for enrichment feature"
```
