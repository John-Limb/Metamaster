# Plex Integration — Phase 2: Data Models & Migration

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `PlexConnection` and `PlexSyncRecord` ORM models and generate the Alembic migration.

**Architecture:** Two new tables following the existing SQLAlchemy pattern (`app/domain/*/models.py`). `PlexConnection` stores server config and cached library IDs. `PlexSyncRecord` tracks sync state per item and is the analytics foundation.

**Tech Stack:** SQLAlchemy, Alembic, PostgreSQL, pytest

**Prerequisite:** Phase 1 complete.

---

### Task 1: PlexConnection and PlexSyncRecord models

**Files:**
- Create: `app/domain/plex/__init__.py`
- Create: `app/domain/plex/models.py`
- Create: `tests/test_plex_models.py`

**Step 1: Write failing tests**

```python
# tests/test_plex_models.py
import pytest
from app.domain.plex.models import PlexConnection, PlexSyncRecord, PlexSyncStatus, PlexItemType


def test_plex_connection_tablename():
    assert PlexConnection.__tablename__ == "plex_connections"


def test_plex_sync_record_tablename():
    assert PlexSyncRecord.__tablename__ == "plex_sync_records"


def test_plex_sync_status_values():
    assert PlexSyncStatus.PENDING == "pending"
    assert PlexSyncStatus.SYNCED == "synced"
    assert PlexSyncStatus.FAILED == "failed"
    assert PlexSyncStatus.NOT_FOUND == "not_found"


def test_plex_item_type_values():
    assert PlexItemType.MOVIE == "movie"
    assert PlexItemType.TV_SHOW == "tv_show"
    assert PlexItemType.EPISODE == "episode"
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_plex_models.py -v
```
Expected: `ImportError`

**Step 3: Create package init**

```python
# app/domain/plex/__init__.py
```

**Step 4: Implement models**

```python
# app/domain/plex/models.py
"""SQLAlchemy ORM models for Plex integration"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class PlexSyncStatus(str, enum.Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    NOT_FOUND = "not_found"


class PlexItemType(str, enum.Enum):
    MOVIE = "movie"
    TV_SHOW = "tv_show"
    EPISODE = "episode"


class PlexConnection(Base):
    """Plex server connection configuration"""

    __tablename__ = "plex_connections"

    id = Column(Integer, primary_key=True, index=True)
    server_url = Column(String(500), nullable=False)
    token = Column(String(500), nullable=False)
    movie_library_id = Column(String(20), nullable=True)
    tv_library_id = Column(String(20), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_connected_at = Column(DateTime, nullable=True)

    sync_records = relationship(
        "PlexSyncRecord", back_populates="connection", cascade="all, delete-orphan"
    )


class PlexSyncRecord(Base):
    """Sync state and watch history for a single MetaMaster item"""

    __tablename__ = "plex_sync_records"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(
        Integer, ForeignKey("plex_connections.id", ondelete="CASCADE"), nullable=False
    )
    item_type = Column(
        SAEnum(
            "movie", "tv_show", "episode",
            name="plexitemtype",
        ),
        nullable=False,
    )
    item_id = Column(Integer, nullable=False)
    plex_rating_key = Column(String(50), nullable=True)
    last_matched_at = Column(DateTime, nullable=True)
    last_pulled_at = Column(DateTime, nullable=True)
    watch_count = Column(Integer, default=0)
    last_watched_at = Column(DateTime, nullable=True)
    is_watched = Column(Boolean, default=False)
    sync_status = Column(
        SAEnum(
            "pending", "synced", "failed", "not_found",
            name="plexsyncstatus",
        ),
        nullable=False,
        default="pending",
    )
    last_error = Column(Text, nullable=True)

    connection = relationship("PlexConnection", back_populates="sync_records")

    __table_args__ = (
        Index("idx_plex_sync_item", "item_type", "item_id"),
        Index("idx_plex_sync_connection", "connection_id"),
        Index("idx_plex_sync_status", "sync_status"),
    )
```

**Step 5: Run tests**

```bash
pytest tests/test_plex_models.py -v
```
Expected: All PASSED.

**Step 6: Commit**

```bash
git add app/domain/plex/ tests/test_plex_models.py
git commit -m "feat(plex): add PlexConnection and PlexSyncRecord ORM models"
```

---

### Task 2: Register models with Base and generate Alembic migration

**Files:**
- Modify: `app/core/init_db.py` (or wherever models are imported to register with Base)
- Create: `alembic/versions/<hash>_add_plex_tables.py` (auto-generated)

**Step 1: Find where models are imported for Alembic to detect**

```bash
grep -r "from app.domain" alembic/env.py
grep -r "import.*models" app/core/init_db.py
```

Look for the pattern where domain models are imported so SQLAlchemy's metadata is populated. This is typically in `alembic/env.py` or `app/core/init_db.py`.

**Step 2: Import new models alongside existing ones**

In whichever file collects model imports (check `alembic/env.py` and `app/core/init_db.py`):

```python
from app.domain.plex.models import PlexConnection, PlexSyncRecord  # noqa: F401
```

**Step 3: Generate migration**

```bash
alembic revision --autogenerate -m "add plex tables"
```

**Step 4: Inspect the generated migration**

```bash
ls alembic/versions/ | sort | tail -3
```

Open the newest file and verify it contains:
- `CREATE TABLE plex_connections`
- `CREATE TABLE plex_sync_records`
- Both enum types: `plexitemtype`, `plexsyncstatus`
- Indexes on `plex_sync_records`

**Step 5: Apply migration to test database**

```bash
alembic upgrade head
```
Expected: No errors.

**Step 6: Verify tables exist**

```bash
python -c "
from app.core.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
print(inspector.get_table_names())
"
```
Expected: `plex_connections` and `plex_sync_records` in the list.

**Step 7: Commit**

```bash
git add app/core/init_db.py alembic/versions/ alembic/env.py
git commit -m "feat(plex): add Alembic migration for plex tables"
```

---

### Task 3: Plex domain schemas (Pydantic)

**Files:**
- Create: `app/domain/plex/schemas.py`
- Modify: `tests/test_plex_models.py`

**Step 1: Write failing tests**

```python
# append to tests/test_plex_models.py
from app.domain.plex.schemas import PlexConnectionResponse, PlexSyncRecordResponse


def test_plex_connection_response_schema():
    data = {
        "id": 1,
        "server_url": "http://plex:32400",
        "is_active": True,
        "movie_library_id": "1",
        "tv_library_id": "2",
        "created_at": "2026-03-05T00:00:00",
        "last_connected_at": None,
    }
    schema = PlexConnectionResponse(**data)
    assert schema.server_url == "http://plex:32400"
    assert schema.is_active is True


def test_plex_sync_record_response_schema():
    data = {
        "id": 1,
        "connection_id": 1,
        "item_type": "movie",
        "item_id": 42,
        "plex_rating_key": "99",
        "sync_status": "synced",
        "watch_count": 3,
        "is_watched": True,
        "last_matched_at": None,
        "last_pulled_at": None,
        "last_watched_at": None,
        "last_error": None,
    }
    schema = PlexSyncRecordResponse(**data)
    assert schema.sync_status == "synced"
    assert schema.watch_count == 3
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_plex_models.py -v -k "schema"
```
Expected: `ImportError`

**Step 3: Implement schemas**

```python
# app/domain/plex/schemas.py
"""Pydantic schemas for Plex domain API responses"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PlexConnectionResponse(BaseModel):
    id: int
    server_url: str
    is_active: bool
    movie_library_id: Optional[str]
    tv_library_id: Optional[str]
    created_at: datetime
    last_connected_at: Optional[datetime]

    model_config = {"from_attributes": True}


class PlexSyncRecordResponse(BaseModel):
    id: int
    connection_id: int
    item_type: str
    item_id: int
    plex_rating_key: Optional[str]
    sync_status: str
    watch_count: int
    is_watched: bool
    last_matched_at: Optional[datetime]
    last_pulled_at: Optional[datetime]
    last_watched_at: Optional[datetime]
    last_error: Optional[str]

    model_config = {"from_attributes": True}
```

**Step 4: Run all plex model tests**

```bash
pytest tests/test_plex_models.py -v
```
Expected: All PASSED.

**Step 5: Lint**

```bash
black app/domain/plex/ tests/test_plex_models.py
isort app/domain/plex/ tests/test_plex_models.py
flake8 app/domain/plex/ tests/test_plex_models.py
mypy app/domain/plex/
```

**Step 6: Commit**

```bash
git add app/domain/plex/schemas.py tests/test_plex_models.py
git commit -m "feat(plex): add Pydantic schemas for Plex domain"
```
