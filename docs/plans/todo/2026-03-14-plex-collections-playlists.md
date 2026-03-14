# Plex Collections & Playlists Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bi-directionally sync Plex collections and playlists from definitions stored in MetaMaster, using a Kometa-inspired builder YAML schema (stored in DB, importable/exportable as YAML).

**Architecture:** Definitions (name, description, builder config) live in the MetaMaster DB. A builder resolver translates each definition into a list of Plex `ratingKey`s using existing `PlexSyncRecord` data. Push sync creates/reconciles Plex collections and playlists from DB definitions; pull sync imports Plex-managed collections/playlists into the DB. A new Plex client module handles collections/playlist HTTP calls (separate from the existing `client.py` to keep files focused). Celery tasks orchestrate both directions on demand and on schedule.

**Tech Stack:** SQLAlchemy / Alembic, FastAPI, Pydantic v2, PyYAML, React + Zustand + TypeScript, existing `PlexClient` / `PlexSyncRecord` infrastructure.

---

## Chunk 1: Data Layer

### Task 1: Builder Pydantic schemas (YAML-compatible)

**Files:**
- Create: `app/infrastructure/external_apis/plex/collection_schemas.py`
- Test: `tests/test_plex_collection_schemas.py`

**Background:** These Pydantic models describe the builder DSL — the same shape as the YAML the user sees. Two builder types for now: `tmdb_collection` (resolve all MetaMaster movies that belong to a given TMDB collection ID) and `static_items` (explicit list of `{tmdb_id, type}` pairs). Collections support both; playlists support `static_items` only (playlists mix movies and TV, which TMDB collections don't model).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_plex_collection_schemas.py
import pytest
from app.infrastructure.external_apis.plex.collection_schemas import (
    StaticItem,
    StaticItemsBuilder,
    TmdbCollectionBuilder,
    CollectionDefinition,
    PlaylistDefinition,
    CollectionsYaml,
)


@pytest.mark.unit
def test_static_item_defaults_type_to_movie():
    item = StaticItem(tmdb_id="123")
    assert item.item_type == "movie"


@pytest.mark.unit
def test_static_items_builder_roundtrip():
    b = StaticItemsBuilder(items=[StaticItem(tmdb_id="1"), StaticItem(tmdb_id="2", item_type="tv_show")])
    assert len(b.items) == 2
    assert b.builder_type == "static_items"


@pytest.mark.unit
def test_tmdb_collection_builder():
    b = TmdbCollectionBuilder(tmdb_collection_id="131292")
    assert b.builder_type == "tmdb_collection"
    assert b.tmdb_collection_id == "131292"


@pytest.mark.unit
def test_collection_definition_requires_name():
    with pytest.raises(Exception):
        CollectionDefinition()


@pytest.mark.unit
def test_playlist_definition_only_accepts_static_items():
    b = StaticItemsBuilder(items=[StaticItem(tmdb_id="1")])
    p = PlaylistDefinition(name="My List", builder=b)
    assert p.name == "My List"


@pytest.mark.unit
def test_collections_yaml_parses_both_sections():
    raw = {
        "collections": {
            "MCU": {
                "description": "Marvel",
                "sort_title": "!001",
                "builder": {"builder_type": "tmdb_collection", "tmdb_collection_id": "131292"},
            }
        },
        "playlists": {
            "Weekend": {
                "builder": {
                    "builder_type": "static_items",
                    "items": [{"tmdb_id": "1"}],
                }
            }
        },
    }
    parsed = CollectionsYaml.model_validate(raw)
    assert "MCU" in parsed.collections
    assert "Weekend" in parsed.playlists
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_plex_collection_schemas.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement the schemas**

```python
# app/infrastructure/external_apis/plex/collection_schemas.py
"""Pydantic models for the Kometa-inspired collection/playlist builder DSL."""

from __future__ import annotations

from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class StaticItem(BaseModel):
    tmdb_id: str
    item_type: Literal["movie", "tv_show"] = Field(default="movie", alias="type")

    model_config = {"populate_by_name": True}


class StaticItemsBuilder(BaseModel):
    builder_type: Literal["static_items"] = "static_items"
    items: List[StaticItem] = Field(default_factory=list)


class TmdbCollectionBuilder(BaseModel):
    builder_type: Literal["tmdb_collection"] = "tmdb_collection"
    tmdb_collection_id: str


AnyBuilder = Union[TmdbCollectionBuilder, StaticItemsBuilder]


class CollectionDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    sort_title: Optional[str] = None
    builder: AnyBuilder = Field(discriminator="builder_type")


class PlaylistDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    builder: StaticItemsBuilder


class CollectionsYaml(BaseModel):
    """Root of the Kometa-inspired YAML config."""
    collections: Dict[str, CollectionDefinition] = Field(default_factory=dict)
    playlists: Dict[str, PlaylistDefinition] = Field(default_factory=dict)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_plex_collection_schemas.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/infrastructure/external_apis/plex/collection_schemas.py tests/test_plex_collection_schemas.py
git commit -m "feat(plex): add Kometa-inspired collection/playlist builder schemas"
```

---

### Task 2: ORM models

**Files:**
- Create: `app/domain/plex/collection_models.py`
- Test: `tests/test_plex_collection_models.py`

**Background:** Four new tables: `plex_collections`, `plex_collection_items`, `plex_playlists`, `plex_playlist_items`. Both `PlexCollection` and `PlexPlaylist` store the resolved builder config as JSON. `plex_rating_key` on the parent rows is nullable until the first push sync creates the object in Plex.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_plex_collection_models.py
import pytest
from app.domain.plex.collection_models import (
    PlexCollection,
    PlexCollectionItem,
    PlexPlaylist,
    PlexPlaylistItem,
    BuilderType,
)


@pytest.mark.unit
def test_builder_type_enum_values():
    assert BuilderType.TMDB_COLLECTION == "tmdb_collection"
    assert BuilderType.STATIC_ITEMS == "static_items"


@pytest.mark.unit
def test_plex_collection_has_required_columns():
    cols = {c.name for c in PlexCollection.__table__.columns}
    assert {"id", "connection_id", "name", "builder_type", "builder_config",
            "plex_rating_key", "last_synced_at"}.issubset(cols)


@pytest.mark.unit
def test_plex_playlist_has_required_columns():
    cols = {c.name for c in PlexPlaylist.__table__.columns}
    assert {"id", "connection_id", "name", "builder_config",
            "plex_rating_key", "last_synced_at"}.issubset(cols)


@pytest.mark.unit
def test_plex_collection_item_has_position():
    cols = {c.name for c in PlexCollectionItem.__table__.columns}
    assert "position" in cols


@pytest.mark.unit
def test_plex_playlist_item_has_position():
    cols = {c.name for c in PlexPlaylistItem.__table__.columns}
    assert "position" in cols
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_plex_collection_models.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement the models**

```python
# app/domain/plex/collection_models.py
"""ORM models for Plex collections and playlists."""

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.core.database import Base


class BuilderType(str, enum.Enum):
    TMDB_COLLECTION = "tmdb_collection"
    STATIC_ITEMS = "static_items"


class PlexCollection(Base):
    __tablename__ = "plex_collections"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(
        Integer, ForeignKey("plex_connections.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    sort_title = Column(String(500), nullable=True)
    builder_type: Any = Column(
        SAEnum("tmdb_collection", "static_items", name="plexbuildertype"),
        nullable=False,
    )
    builder_config = Column(JSON, nullable=False, default=dict)
    plex_rating_key = Column(String(50), nullable=True)
    last_synced_at = Column(DateTime, nullable=True)

    items = relationship(
        "PlexCollectionItem", back_populates="collection", cascade="all, delete-orphan"
    )
    __table_args__ = (
        Index("idx_plex_collection_connection", "connection_id"),
        Index("idx_plex_collection_key", "plex_rating_key"),
    )


class PlexCollectionItem(Base):
    __tablename__ = "plex_collection_items"

    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(
        Integer, ForeignKey("plex_collections.id", ondelete="CASCADE"), nullable=False
    )
    plex_rating_key = Column(String(50), nullable=False)
    item_type = Column(String(20), nullable=False)  # movie / tv_show
    item_id = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False, default=0)

    collection = relationship("PlexCollection", back_populates="items")


class PlexPlaylist(Base):
    __tablename__ = "plex_playlists"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(
        Integer, ForeignKey("plex_connections.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    builder_config = Column(JSON, nullable=False, default=dict)
    plex_rating_key = Column(String(50), nullable=True)
    last_synced_at = Column(DateTime, nullable=True)

    items = relationship(
        "PlexPlaylistItem", back_populates="playlist", cascade="all, delete-orphan"
    )
    __table_args__ = (
        Index("idx_plex_playlist_connection", "connection_id"),
        Index("idx_plex_playlist_key", "plex_rating_key"),
    )


class PlexPlaylistItem(Base):
    __tablename__ = "plex_playlist_items"

    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(
        Integer, ForeignKey("plex_playlists.id", ondelete="CASCADE"), nullable=False
    )
    plex_rating_key = Column(String(50), nullable=False)
    item_type = Column(String(20), nullable=False)
    item_id = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False, default=0)

    playlist = relationship("PlexPlaylist", back_populates="items")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_plex_collection_models.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/domain/plex/collection_models.py tests/test_plex_collection_models.py
git commit -m "feat(plex): add PlexCollection and PlexPlaylist ORM models"
```

---

### Task 3: Alembic migration

**Files:**
- Create: `alembic/versions/014_plex_collections.py`

**Background:** Creates four new tables and a new `plexbuildertype` enum. The enum must be created before the table that uses it. Check the existing migration `012_add_plex_tables.py` for the enum creation pattern used in this codebase.

- [ ] **Step 1: Generate a blank migration**

```bash
alembic revision -m "add plex collections and playlists"
```

- [ ] **Step 2: Fill in the migration** (rename the generated file to `014_plex_collections.py`)

```python
"""add plex collections and playlists

Revision ID: 014
Revises: 013
"""
from alembic import op
import sqlalchemy as sa

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    builder_type_enum = sa.Enum(
        "tmdb_collection", "static_items", name="plexbuildertype"
    )
    builder_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "plex_collections",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("connection_id", sa.Integer,
                  sa.ForeignKey("plex_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("sort_title", sa.String(500), nullable=True),
        sa.Column("builder_type", sa.Enum("tmdb_collection", "static_items",
                  name="plexbuildertype"), nullable=False),
        sa.Column("builder_config", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("plex_rating_key", sa.String(50), nullable=True),
        sa.Column("last_synced_at", sa.DateTime, nullable=True),
    )
    op.create_index("idx_plex_collection_connection", "plex_collections", ["connection_id"])
    op.create_index("idx_plex_collection_key", "plex_collections", ["plex_rating_key"])

    op.create_table(
        "plex_collection_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("collection_id", sa.Integer,
                  sa.ForeignKey("plex_collections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plex_rating_key", sa.String(50), nullable=False),
        sa.Column("item_type", sa.String(20), nullable=False),
        sa.Column("item_id", sa.Integer, nullable=False),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
    )

    op.create_table(
        "plex_playlists",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("connection_id", sa.Integer,
                  sa.ForeignKey("plex_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("builder_config", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("plex_rating_key", sa.String(50), nullable=True),
        sa.Column("last_synced_at", sa.DateTime, nullable=True),
    )
    op.create_index("idx_plex_playlist_connection", "plex_playlists", ["connection_id"])
    op.create_index("idx_plex_playlist_key", "plex_playlists", ["plex_rating_key"])

    op.create_table(
        "plex_playlist_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("playlist_id", sa.Integer,
                  sa.ForeignKey("plex_playlists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plex_rating_key", sa.String(50), nullable=False),
        sa.Column("item_type", sa.String(20), nullable=False),
        sa.Column("item_id", sa.Integer, nullable=False),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("plex_playlist_items")
    op.drop_table("plex_playlists")
    op.drop_table("plex_collection_items")
    op.drop_table("plex_collections")
    op.execute("DROP TYPE IF EXISTS plexbuildertype")
```

- [ ] **Step 3: Run migration and verify**

```bash
alembic upgrade head
alembic current
```
Expected: `014 (head)`

- [ ] **Step 4: Commit**

```bash
git add alembic/versions/014_plex_collections.py
git commit -m "feat(plex): migration 014 — add collections and playlists tables"
```

---

## Chunk 2: Plex Client Extension

### Task 4: Collection client methods

**Files:**
- Create: `app/infrastructure/external_apis/plex/collection_client.py`
- Modify: `app/infrastructure/external_apis/plex/client.py` (add `get_machine_identifier()`)
- Test: `tests/test_plex_collection_client.py`

**Background:** Plex uses a URI format for item references: `server://{machineIdentifier}/com.plexapp.plugins.library/library/metadata/{ratingKey}`. The machine identifier comes from `GET /`. Collections live under a library section.

Key API calls:
- `GET /library/sections/{sectionId}/collections` → list
- `POST /library/collections?type=18&title=...&smart=0&sectionId=...&uri=...` → create (type 18 = collection)
- `PUT /library/metadata/{key}?title=...&summary=...&titleSort=...` → update metadata
- `GET /library/metadata/{key}/children` → get items
- `PUT /library/metadata/{key}/items?uri={uri}` → add single item
- `DELETE /library/metadata/{key}/items/{childKey}` → remove single item
- `DELETE /library/metadata/{key}` → delete collection

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_plex_collection_client.py
import pytest
from unittest.mock import MagicMock, patch

from app.infrastructure.external_apis.plex.collection_client import PlexCollectionClient
from app.infrastructure.external_apis.plex.client import PlexClient


@pytest.mark.unit
def test_get_machine_identifier_parses_response():
    client = PlexClient(server_url="http://plex:32400", token="tok")
    with patch.object(client, "_get", return_value={"MediaContainer": {"machineIdentifier": "abc123"}}):
        result = client.get_machine_identifier()
    assert result == "abc123"


@pytest.mark.unit
def test_build_item_uri():
    cc = PlexCollectionClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    assert cc._item_uri("99") == "server://abc/com.plexapp.plugins.library/library/metadata/99"


@pytest.mark.unit
def test_get_collections_returns_list():
    cc = PlexCollectionClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    payload = {"MediaContainer": {"Metadata": [
        {"ratingKey": "10", "title": "MCU", "summary": "Marvel"},
    ]}}
    with patch.object(cc, "_get", return_value=payload):
        result = cc.get_collections(section_id="1")
    assert len(result) == 1
    assert result[0]["ratingKey"] == "10"


@pytest.mark.unit
def test_get_collection_item_keys():
    cc = PlexCollectionClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    payload = {"MediaContainer": {"Metadata": [
        {"ratingKey": "5"}, {"ratingKey": "6"},
    ]}}
    with patch.object(cc, "_get", return_value=payload):
        result = cc.get_collection_item_keys("10")
    assert result == ["5", "6"]


@pytest.mark.unit
def test_create_collection_posts_and_returns_key():
    cc = PlexCollectionClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    payload = {"MediaContainer": {"Metadata": [{"ratingKey": "99"}]}}
    with patch.object(cc, "_post", return_value=payload) as mock_post:
        key = cc.create_collection(section_id="1", title="MCU", rating_keys=["5", "6"])
    assert key == "99"
    mock_post.assert_called_once()


@pytest.mark.unit
def test_delete_collection_calls_correct_path():
    cc = PlexCollectionClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    with patch.object(cc, "_delete") as mock_del:
        cc.delete_collection("10")
    mock_del.assert_called_once_with("/library/metadata/10")
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_plex_collection_client.py -v
```
Expected: FAIL

- [ ] **Step 3: Add `get_machine_identifier()` to `client.py`**

In `app/infrastructure/external_apis/plex/client.py` add after the existing `_put` method:

```python
def get_machine_identifier(self) -> str:
    """Return the Plex server machine identifier (needed for item URIs)."""
    data = self._get("/")
    return data["MediaContainer"]["machineIdentifier"]
```

- [ ] **Step 4: Implement `PlexCollectionClient`**

```python
# app/infrastructure/external_apis/plex/collection_client.py
"""Plex HTTP client methods for collections."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.infrastructure.external_apis.plex.client import _PLEX_HEADERS

logger = logging.getLogger(__name__)

_COLLECTION_TYPE = "18"  # Plex media type for collections


class PlexCollectionClient:
    """HTTP client for Plex collection management."""

    def __init__(self, server_url: str, token: str, machine_id: str):
        self._base = server_url.rstrip("/")
        self._token = token
        self._machine_id = machine_id

    def _headers(self) -> dict:
        return {**_PLEX_HEADERS, "X-Plex-Token": self._token}

    def _item_uri(self, rating_key: str) -> str:
        return (
            f"server://{self._machine_id}"
            "/com.plexapp.plugins.library"
            f"/library/metadata/{rating_key}"
        )

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self._base}{path}"
        with httpx.Client(timeout=15) as http:
            r = http.get(url, headers=self._headers(), params=params)
        r.raise_for_status()
        return r.json() if r.content else {}

    def _post(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self._base}{path}"
        with httpx.Client(timeout=15) as http:
            r = http.post(url, headers=self._headers(), params=params)
        r.raise_for_status()
        return r.json() if r.content else {}

    def _put(self, path: str, params: Optional[dict] = None) -> None:
        url = f"{self._base}{path}"
        with httpx.Client(timeout=15) as http:
            r = http.put(url, headers=self._headers(), params=params)
        r.raise_for_status()

    def _delete(self, path: str) -> None:
        url = f"{self._base}{path}"
        with httpx.Client(timeout=15) as http:
            r = http.delete(url, headers=self._headers())
        r.raise_for_status()

    def get_collections(self, section_id: str) -> List[Dict[str, Any]]:
        """Return raw Plex collection metadata dicts for a library section."""
        data = self._get(f"/library/sections/{section_id}/collections")
        return data.get("MediaContainer", {}).get("Metadata", [])

    def get_collection_item_keys(self, collection_key: str) -> List[str]:
        """Return ratingKeys of all items in a collection."""
        data = self._get(f"/library/metadata/{collection_key}/children")
        items = data.get("MediaContainer", {}).get("Metadata", [])
        return [item["ratingKey"] for item in items]

    def create_collection(
        self, section_id: str, title: str, rating_keys: List[str]
    ) -> str:
        """Create a Plex collection with the given items. Returns its ratingKey."""
        first_uri = self._item_uri(rating_keys[0]) if rating_keys else ""
        data = self._post(
            "/library/collections",
            params={
                "type": _COLLECTION_TYPE,
                "title": title,
                "smart": "0",
                "sectionId": section_id,
                "uri": first_uri,
            },
        )
        key: str = data["MediaContainer"]["Metadata"][0]["ratingKey"]
        for rk in rating_keys[1:]:
            self.add_item_to_collection(collection_key=key, rating_key=rk)
        return key

    def update_collection_metadata(
        self,
        collection_key: str,
        title: str,
        description: Optional[str],
        sort_title: Optional[str],
    ) -> None:
        params: dict = {"title": title, "type": _COLLECTION_TYPE}
        if description is not None:
            params["summary"] = description
        if sort_title is not None:
            params["titleSort"] = sort_title
        self._put(f"/library/metadata/{collection_key}", params=params)

    def add_item_to_collection(self, collection_key: str, rating_key: str) -> None:
        self._put(
            f"/library/metadata/{collection_key}/items",
            params={"uri": self._item_uri(rating_key)},
        )

    def remove_item_from_collection(
        self, collection_key: str, item_key: str
    ) -> None:
        self._delete(f"/library/metadata/{collection_key}/items/{item_key}")

    def delete_collection(self, collection_key: str) -> None:
        self._delete(f"/library/metadata/{collection_key}")
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_plex_collection_client.py -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/infrastructure/external_apis/plex/collection_client.py \
        app/infrastructure/external_apis/plex/client.py \
        tests/test_plex_collection_client.py
git commit -m "feat(plex): add collection client and machine identifier lookup"
```

---

### Task 5: Playlist client methods

**Files:**
- Create: `app/infrastructure/external_apis/plex/playlist_client.py`
- Test: `tests/test_plex_playlist_client.py`

**Background:** Plex playlists are created with `POST /playlists?type=video&smart=0&uri=...&title=...`. Items are added via `PUT /playlists/{key}/items?uri=...` and removed via `DELETE /playlists/{key}/items/{itemId}`. Playlists are cross-library so no sectionId is needed for creation beyond the initial uri.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_plex_playlist_client.py
import pytest
from unittest.mock import patch

from app.infrastructure.external_apis.plex.playlist_client import PlexPlaylistClient


@pytest.mark.unit
def test_get_playlists_returns_list():
    pc = PlexPlaylistClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    payload = {"MediaContainer": {"Metadata": [
        {"ratingKey": "20", "title": "Weekend"},
    ]}}
    with patch.object(pc, "_get", return_value=payload):
        result = pc.get_playlists()
    assert len(result) == 1
    assert result[0]["ratingKey"] == "20"


@pytest.mark.unit
def test_get_playlist_item_keys():
    pc = PlexPlaylistClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    payload = {"MediaContainer": {"Metadata": [{"ratingKey": "3"}, {"ratingKey": "4"}]}}
    with patch.object(pc, "_get", return_value=payload):
        result = pc.get_playlist_item_keys("20")
    assert result == ["3", "4"]


@pytest.mark.unit
def test_create_playlist_returns_key():
    pc = PlexPlaylistClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    payload = {"MediaContainer": {"Metadata": [{"ratingKey": "99"}]}}
    with patch.object(pc, "_post", return_value=payload):
        key = pc.create_playlist(title="Weekend", rating_keys=["3"])
    assert key == "99"


@pytest.mark.unit
def test_delete_playlist_calls_correct_path():
    pc = PlexPlaylistClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    with patch.object(pc, "_delete") as mock_del:
        pc.delete_playlist("20")
    mock_del.assert_called_once_with("/playlists/20")
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_plex_playlist_client.py -v
```

- [ ] **Step 3: Implement `PlexPlaylistClient`**

```python
# app/infrastructure/external_apis/plex/playlist_client.py
"""Plex HTTP client methods for playlists."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.infrastructure.external_apis.plex.client import _PLEX_HEADERS

logger = logging.getLogger(__name__)


class PlexPlaylistClient:
    """HTTP client for Plex playlist management."""

    def __init__(self, server_url: str, token: str, machine_id: str):
        self._base = server_url.rstrip("/")
        self._token = token
        self._machine_id = machine_id

    def _headers(self) -> dict:
        return {**_PLEX_HEADERS, "X-Plex-Token": self._token}

    def _item_uri(self, rating_key: str) -> str:
        return (
            f"server://{self._machine_id}"
            "/com.plexapp.plugins.library"
            f"/library/metadata/{rating_key}"
        )

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self._base}{path}"
        with httpx.Client(timeout=15) as http:
            r = http.get(url, headers=self._headers(), params=params)
        r.raise_for_status()
        return r.json() if r.content else {}

    def _post(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self._base}{path}"
        with httpx.Client(timeout=15) as http:
            r = http.post(url, headers=self._headers(), params=params)
        r.raise_for_status()
        return r.json() if r.content else {}

    def _put(self, path: str, params: Optional[dict] = None) -> None:
        url = f"{self._base}{path}"
        with httpx.Client(timeout=15) as http:
            r = http.put(url, headers=self._headers(), params=params)
        r.raise_for_status()

    def _delete(self, path: str) -> None:
        url = f"{self._base}{path}"
        with httpx.Client(timeout=15) as http:
            r = http.delete(url, headers=self._headers())
        r.raise_for_status()

    def get_playlists(self) -> List[Dict[str, Any]]:
        data = self._get("/playlists", params={"playlistType": "video"})
        return data.get("MediaContainer", {}).get("Metadata", [])

    def get_playlist_item_keys(self, playlist_key: str) -> List[str]:
        data = self._get(f"/playlists/{playlist_key}/items")
        items = data.get("MediaContainer", {}).get("Metadata", [])
        return [item["ratingKey"] for item in items]

    def create_playlist(self, title: str, rating_keys: List[str]) -> str:
        """Create a video playlist with the given items. Returns its ratingKey."""
        first_uri = self._item_uri(rating_keys[0]) if rating_keys else ""
        data = self._post(
            "/playlists",
            params={"type": "video", "smart": "0", "title": title, "uri": first_uri},
        )
        key: str = data["MediaContainer"]["Metadata"][0]["ratingKey"]
        for rk in rating_keys[1:]:
            self.add_item_to_playlist(playlist_key=key, rating_key=rk)
        return key

    def update_playlist_metadata(
        self, playlist_key: str, title: str, description: Optional[str]
    ) -> None:
        params: dict = {"title": title}
        if description is not None:
            params["summary"] = description
        self._put(f"/playlists/{playlist_key}", params=params)

    def add_item_to_playlist(self, playlist_key: str, rating_key: str) -> None:
        self._put(
            f"/playlists/{playlist_key}/items",
            params={"uri": self._item_uri(rating_key)},
        )

    def remove_item_from_playlist(self, playlist_key: str, item_key: str) -> None:
        self._delete(f"/playlists/{playlist_key}/items/{item_key}")

    def delete_playlist(self, playlist_key: str) -> None:
        self._delete(f"/playlists/{playlist_key}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_plex_playlist_client.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/infrastructure/external_apis/plex/playlist_client.py \
        tests/test_plex_playlist_client.py
git commit -m "feat(plex): add playlist client"
```

---

## Chunk 3: Service Layer

### Task 6: Builder resolver

**Files:**
- Create: `app/domain/plex/collection_builder.py`
- Test: `tests/test_plex_collection_builder.py`

**Background:** The resolver's job is: given a builder config from the DB, return a list of `(plex_rating_key, item_type, item_id)` tuples by querying `PlexSyncRecord` and the TMDB data we already have. It never calls Plex API — it works entirely from our DB state.

For `tmdb_collection`: query `Movie.tmdb_collection_id == builder_config["tmdb_collection_id"]`, then look up each movie's `PlexSyncRecord` to get the `plex_rating_key`. Skip items without a synced record.

For `static_items`: for each item in `builder_config["items"]`, find the matching `Movie`/`TVShow` by `tmdb_id`, then look up their `PlexSyncRecord`. Skip items without a synced record.

Check `app/domain/movies/models.py` to confirm the `tmdb_collection_id` column name before implementing.

- [ ] **Step 1: Verify the Movie model has `tmdb_collection_id`**

```bash
grep -n "tmdb_collection" app/domain/movies/models.py
```

If the column is named differently, adjust the implementation accordingly.

- [ ] **Step 2: Write the failing tests**

```python
# tests/test_plex_collection_builder.py
import pytest
from unittest.mock import MagicMock

from app.domain.plex.collection_builder import BuilderResolver, ResolvedItem


@pytest.mark.unit
def test_resolved_item_dataclass():
    item = ResolvedItem(plex_rating_key="5", item_type="movie", item_id=1)
    assert item.plex_rating_key == "5"


@pytest.mark.unit
def test_static_items_resolver_returns_empty_when_no_sync_record(db_session):
    """Items without a SYNCED PlexSyncRecord are skipped."""
    resolver = BuilderResolver(db=db_session, connection_id=1)
    config = {"items": [{"tmdb_id": "99999", "item_type": "movie"}]}
    result = resolver.resolve_static_items(config)
    assert result == []


@pytest.mark.unit
def test_tmdb_collection_resolver_returns_empty_when_no_movies(db_session):
    resolver = BuilderResolver(db=db_session, connection_id=1)
    config = {"tmdb_collection_id": "0000"}
    result = resolver.resolve_tmdb_collection(config)
    assert result == []
```

Note: `db_session` fixture is the existing PostgreSQL test fixture. Check `tests/conftest.py` for its name.

- [ ] **Step 3: Run to verify it fails**

```bash
pytest tests/test_plex_collection_builder.py -v
```

- [ ] **Step 4: Implement the resolver**

```python
# app/domain/plex/collection_builder.py
"""Resolve builder configs to lists of Plex rating keys using local DB state."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.domain.movies.models import Movie
from app.domain.plex.models import PlexSyncRecord, PlexSyncStatus
from app.domain.tv_shows.models import TVShow

logger = logging.getLogger(__name__)


@dataclass
class ResolvedItem:
    plex_rating_key: str
    item_type: str  # "movie" or "tv_show"
    item_id: int


class BuilderResolver:
    """Resolve builder configs → ResolvedItem lists from local DB state."""

    def __init__(self, db: Session, connection_id: int):
        self._db = db
        self._connection_id = connection_id

    def resolve_static_items(self, config: Dict[str, Any]) -> List[ResolvedItem]:
        results: List[ResolvedItem] = []
        for entry in config.get("items", []):
            tmdb_id = str(entry["tmdb_id"])
            item_type = entry.get("item_type", "movie")
            resolved = self._resolve_single(tmdb_id=tmdb_id, item_type=item_type)
            if resolved:
                results.append(resolved)
        return results

    def resolve_tmdb_collection(self, config: Dict[str, Any]) -> List[ResolvedItem]:
        collection_id = str(config["tmdb_collection_id"])
        movies = (
            self._db.query(Movie)
            .filter(Movie.tmdb_collection_id == collection_id)
            .all()
        )
        results: List[ResolvedItem] = []
        for movie in movies:
            record = self._get_synced_record(item_type="movie", item_id=movie.id)
            if record and record.plex_rating_key:
                results.append(ResolvedItem(
                    plex_rating_key=record.plex_rating_key,
                    item_type="movie",
                    item_id=movie.id,
                ))
        return results

    def _resolve_single(self, tmdb_id: str, item_type: str) -> ResolvedItem | None:
        item_id = self._find_item_id(tmdb_id=tmdb_id, item_type=item_type)
        if item_id is None:
            logger.debug("Builder: no %s found for tmdb_id=%s", item_type, tmdb_id)
            return None
        record = self._get_synced_record(item_type=item_type, item_id=item_id)
        if not record or not record.plex_rating_key:
            logger.debug("Builder: no synced record for %s id=%s", item_type, item_id)
            return None
        return ResolvedItem(
            plex_rating_key=record.plex_rating_key,
            item_type=item_type,
            item_id=item_id,
        )

    def _find_item_id(self, tmdb_id: str, item_type: str) -> int | None:
        if item_type == "movie":
            movie = self._db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
            return movie.id if movie else None
        if item_type == "tv_show":
            show = self._db.query(TVShow).filter(TVShow.tmdb_id == tmdb_id).first()
            return show.id if show else None
        return None

    def _get_synced_record(
        self, item_type: str, item_id: int
    ) -> PlexSyncRecord | None:
        return (
            self._db.query(PlexSyncRecord)
            .filter(
                PlexSyncRecord.item_type == item_type,
                PlexSyncRecord.item_id == item_id,
                PlexSyncRecord.connection_id == self._connection_id,
                PlexSyncRecord.sync_status == PlexSyncStatus.SYNCED,
            )
            .first()
        )
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_plex_collection_builder.py -v
```

- [ ] **Step 6: Commit**

```bash
git add app/domain/plex/collection_builder.py tests/test_plex_collection_builder.py
git commit -m "feat(plex): add builder resolver for collections and playlists"
```

---

### Task 7: Collection sync service

**Files:**
- Create: `app/domain/plex/collection_service.py`
- Test: `tests/test_plex_collection_service.py`

**Background:** `PlexCollectionService` handles both push and pull directions for collections.

- **Push** (`push_collection`): resolve the builder → get target `rating_keys` → compare to current Plex state → add/remove items → create the collection if it doesn't exist yet → update `PlexCollectionItem` rows and `last_synced_at`.
- **Pull** (`pull_collections`): list all collections in both library sections from Plex → for each, upsert a `PlexCollection` record (using `plex_rating_key` as the key) → populate `PlexCollectionItem` rows from Plex item listing.

Reconciliation (set difference) keeps `push_collection` under 80 lines: add items in `target - current`, remove items in `current - target`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_plex_collection_service.py
import pytest
from unittest.mock import MagicMock, patch

from app.domain.plex.collection_service import PlexCollectionService


@pytest.fixture
def mock_cc():
    return MagicMock()


@pytest.fixture
def mock_resolver():
    return MagicMock()


@pytest.fixture
def svc(db_session, mock_cc, mock_resolver):
    return PlexCollectionService(
        db=db_session,
        collection_client=mock_cc,
        resolver=mock_resolver,
        movie_section_id="1",
        tv_section_id="2",
    )


@pytest.mark.unit
def test_push_creates_collection_when_missing(svc, mock_cc, mock_resolver, db_session):
    from app.domain.plex.collection_models import PlexCollection, BuilderType
    from app.domain.plex.models import PlexConnection
    conn = PlexConnection(server_url="http://plex", token="t", is_active=True)
    db_session.add(conn)
    db_session.flush()

    coll = PlexCollection(
        connection_id=conn.id,
        name="MCU",
        builder_type=BuilderType.STATIC_ITEMS,
        builder_config={"items": [{"tmdb_id": "1", "item_type": "movie"}]},
    )
    db_session.add(coll)
    db_session.flush()

    from app.domain.plex.collection_builder import ResolvedItem
    mock_resolver.resolve_static_items.return_value = [
        ResolvedItem(plex_rating_key="5", item_type="movie", item_id=1)
    ]
    mock_cc.create_collection.return_value = "99"
    mock_cc.get_collection_item_keys.return_value = []

    svc.push_collection(coll)

    mock_cc.create_collection.assert_called_once()
    assert coll.plex_rating_key == "99"


@pytest.mark.unit
def test_push_reconciles_items(svc, mock_cc, mock_resolver, db_session):
    from app.domain.plex.collection_models import PlexCollection, BuilderType
    from app.domain.plex.models import PlexConnection
    conn = PlexConnection(server_url="http://plex", token="t", is_active=True)
    db_session.add(conn)
    db_session.flush()

    coll = PlexCollection(
        connection_id=conn.id,
        name="MCU",
        builder_type=BuilderType.STATIC_ITEMS,
        builder_config={"items": []},
        plex_rating_key="99",
    )
    db_session.add(coll)
    db_session.flush()

    from app.domain.plex.collection_builder import ResolvedItem
    mock_resolver.resolve_static_items.return_value = [
        ResolvedItem(plex_rating_key="5", item_type="movie", item_id=1),
    ]
    mock_cc.get_collection_item_keys.return_value = ["6"]  # "6" not in target → remove

    svc.push_collection(coll)

    mock_cc.add_item_to_collection.assert_called_once_with(
        collection_key="99", rating_key="5"
    )
    mock_cc.remove_item_from_collection.assert_called_once_with(
        collection_key="99", item_key="6"
    )
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_plex_collection_service.py -v
```

- [ ] **Step 3: Implement the service**

```python
# app/domain/plex/collection_service.py
"""Bi-directional sync service for Plex collections."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.domain.plex.collection_builder import BuilderResolver, ResolvedItem
from app.domain.plex.collection_models import (
    BuilderType,
    PlexCollection,
    PlexCollectionItem,
)
from app.infrastructure.external_apis.plex.collection_client import PlexCollectionClient

logger = logging.getLogger(__name__)


class PlexCollectionService:
    def __init__(
        self,
        db: Session,
        collection_client: PlexCollectionClient,
        resolver: BuilderResolver,
        movie_section_id: str,
        tv_section_id: str,
    ):
        self._db = db
        self._cc = collection_client
        self._resolver = resolver
        self._movie_section = movie_section_id
        self._tv_section = tv_section_id

    def push_collection(self, collection: PlexCollection) -> None:
        """Push a single collection definition to Plex, reconciling items."""
        target_items = self._resolve(collection)
        target_keys = {item.plex_rating_key for item in target_items}

        if not collection.plex_rating_key:
            self._create_and_set_key(collection, target_items)
        else:
            self._reconcile_items(collection.plex_rating_key, target_keys)
            self._cc.update_collection_metadata(
                collection_key=collection.plex_rating_key,
                title=collection.name,
                description=collection.description,
                sort_title=collection.sort_title,
            )

        self._upsert_item_records(collection, target_items)
        collection.last_synced_at = datetime.utcnow()
        self._db.commit()
        logger.info("Plex: pushed collection '%s' key=%s", collection.name, collection.plex_rating_key)

    def pull_collections(self, connection_id: int) -> None:
        """Import all Plex-managed collections into the DB."""
        for section_id in (self._movie_section, self._tv_section):
            for raw in self._cc.get_collections(section_id=section_id):
                self._upsert_pulled_collection(raw, connection_id, section_id)
        self._db.commit()
        logger.info("Plex: pull collections complete")

    def _resolve(self, collection: PlexCollection) -> List[ResolvedItem]:
        config = collection.builder_config
        if collection.builder_type == BuilderType.TMDB_COLLECTION:
            return self._resolver.resolve_tmdb_collection(config)
        return self._resolver.resolve_static_items(config)

    def _create_and_set_key(
        self, collection: PlexCollection, items: List[ResolvedItem]
    ) -> None:
        rating_keys = [i.plex_rating_key for i in items]
        key = self._cc.create_collection(
            section_id=self._movie_section,
            title=collection.name,
            rating_keys=rating_keys,
        )
        collection.plex_rating_key = key

    def _reconcile_items(self, collection_key: str, target_keys: set) -> None:
        current_keys = set(self._cc.get_collection_item_keys(collection_key))
        for key in target_keys - current_keys:
            self._cc.add_item_to_collection(collection_key=collection_key, rating_key=key)
        for key in current_keys - target_keys:
            self._cc.remove_item_from_collection(collection_key=collection_key, item_key=key)

    def _upsert_item_records(
        self, collection: PlexCollection, items: List[ResolvedItem]
    ) -> None:
        self._db.query(PlexCollectionItem).filter(
            PlexCollectionItem.collection_id == collection.id
        ).delete()
        for pos, item in enumerate(items):
            self._db.add(PlexCollectionItem(
                collection_id=collection.id,
                plex_rating_key=item.plex_rating_key,
                item_type=item.item_type,
                item_id=item.item_id,
                position=pos,
            ))

    def _upsert_pulled_collection(
        self, raw: dict, connection_id: int, section_id: str
    ) -> None:
        plex_key = raw["ratingKey"]
        existing = (
            self._db.query(PlexCollection)
            .filter(PlexCollection.plex_rating_key == plex_key)
            .first()
        )
        if existing is None:
            existing = PlexCollection(
                connection_id=connection_id,
                builder_type=BuilderType.STATIC_ITEMS,
                builder_config={"items": []},
                plex_rating_key=plex_key,
            )
            self._db.add(existing)

        existing.name = raw.get("title", plex_key)
        existing.description = raw.get("summary")
        existing.last_synced_at = datetime.utcnow()

        item_keys = self._cc.get_collection_item_keys(plex_key)
        self._db.query(PlexCollectionItem).filter(
            PlexCollectionItem.collection_id == existing.id
        ).delete()
        for pos, rk in enumerate(item_keys):
            self._db.add(PlexCollectionItem(
                collection_id=existing.id,
                plex_rating_key=rk,
                item_type="movie",
                item_id=0,
                position=pos,
            ))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_plex_collection_service.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/domain/plex/collection_service.py tests/test_plex_collection_service.py
git commit -m "feat(plex): add collection bi-di sync service"
```

---

### Task 8: Playlist sync service

**Files:**
- Create: `app/domain/plex/playlist_service.py`
- Test: `tests/test_plex_playlist_service.py`

**Background:** Mirrors `PlexCollectionService` but for playlists. Playlists only use `static_items` builder. Pull sync imports existing Plex playlists. Reconciliation is identical (set difference on rating keys).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_plex_playlist_service.py
import pytest
from unittest.mock import MagicMock

from app.domain.plex.playlist_service import PlexPlaylistService


@pytest.fixture
def mock_pc():
    return MagicMock()


@pytest.fixture
def mock_resolver():
    return MagicMock()


@pytest.fixture
def svc(db_session, mock_pc, mock_resolver):
    return PlexPlaylistService(
        db=db_session,
        playlist_client=mock_pc,
        resolver=mock_resolver,
    )


@pytest.mark.unit
def test_push_creates_playlist_when_missing(svc, mock_pc, mock_resolver, db_session):
    from app.domain.plex.collection_models import PlexPlaylist
    from app.domain.plex.models import PlexConnection
    from app.domain.plex.collection_builder import ResolvedItem

    conn = PlexConnection(server_url="http://plex", token="t", is_active=True)
    db_session.add(conn)
    db_session.flush()

    pl = PlexPlaylist(
        connection_id=conn.id,
        name="Weekend",
        builder_config={"items": [{"tmdb_id": "1", "item_type": "movie"}]},
    )
    db_session.add(pl)
    db_session.flush()

    mock_resolver.resolve_static_items.return_value = [
        ResolvedItem(plex_rating_key="5", item_type="movie", item_id=1)
    ]
    mock_pc.create_playlist.return_value = "99"
    mock_pc.get_playlist_item_keys.return_value = []

    svc.push_playlist(pl)

    mock_pc.create_playlist.assert_called_once()
    assert pl.plex_rating_key == "99"
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_plex_playlist_service.py -v
```

- [ ] **Step 3: Implement the service**

```python
# app/domain/plex/playlist_service.py
"""Bi-directional sync service for Plex playlists."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.domain.plex.collection_builder import BuilderResolver, ResolvedItem
from app.domain.plex.collection_models import PlexPlaylist, PlexPlaylistItem
from app.infrastructure.external_apis.plex.playlist_client import PlexPlaylistClient

logger = logging.getLogger(__name__)


class PlexPlaylistService:
    def __init__(
        self,
        db: Session,
        playlist_client: PlexPlaylistClient,
        resolver: BuilderResolver,
    ):
        self._db = db
        self._pc = playlist_client
        self._resolver = resolver

    def push_playlist(self, playlist: PlexPlaylist) -> None:
        items = self._resolver.resolve_static_items(playlist.builder_config)
        target_keys = {i.plex_rating_key for i in items}

        if not playlist.plex_rating_key:
            key = self._pc.create_playlist(
                title=playlist.name,
                rating_keys=[i.plex_rating_key for i in items],
            )
            playlist.plex_rating_key = key
        else:
            self._reconcile(playlist.plex_rating_key, target_keys)
            self._pc.update_playlist_metadata(
                playlist_key=playlist.plex_rating_key,
                title=playlist.name,
                description=playlist.description,
            )

        self._upsert_item_records(playlist, items)
        playlist.last_synced_at = datetime.utcnow()
        self._db.commit()
        logger.info("Plex: pushed playlist '%s' key=%s", playlist.name, playlist.plex_rating_key)

    def pull_playlists(self, connection_id: int) -> None:
        for raw in self._pc.get_playlists():
            self._upsert_pulled_playlist(raw, connection_id)
        self._db.commit()

    def _reconcile(self, playlist_key: str, target_keys: set) -> None:
        current_keys = set(self._pc.get_playlist_item_keys(playlist_key))
        for key in target_keys - current_keys:
            self._pc.add_item_to_playlist(playlist_key=playlist_key, rating_key=key)
        for key in current_keys - target_keys:
            self._pc.remove_item_from_playlist(playlist_key=playlist_key, item_key=key)

    def _upsert_item_records(
        self, playlist: PlexPlaylist, items: List[ResolvedItem]
    ) -> None:
        self._db.query(PlexPlaylistItem).filter(
            PlexPlaylistItem.playlist_id == playlist.id
        ).delete()
        for pos, item in enumerate(items):
            self._db.add(PlexPlaylistItem(
                playlist_id=playlist.id,
                plex_rating_key=item.plex_rating_key,
                item_type=item.item_type,
                item_id=item.item_id,
                position=pos,
            ))

    def _upsert_pulled_playlist(self, raw: dict, connection_id: int) -> None:
        plex_key = raw["ratingKey"]
        existing = (
            self._db.query(PlexPlaylist)
            .filter(PlexPlaylist.plex_rating_key == plex_key)
            .first()
        )
        if existing is None:
            existing = PlexPlaylist(
                connection_id=connection_id,
                builder_config={"items": []},
                plex_rating_key=plex_key,
            )
            self._db.add(existing)
        existing.name = raw.get("title", plex_key)
        existing.description = raw.get("summary")
        existing.last_synced_at = datetime.utcnow()
```

- [ ] **Step 4: Run all service tests**

```bash
pytest tests/test_plex_collection_service.py tests/test_plex_playlist_service.py -v
```
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add app/domain/plex/playlist_service.py tests/test_plex_playlist_service.py
git commit -m "feat(plex): add playlist bi-di sync service"
```

---

## Chunk 4: API Layer

### Task 9: API schemas + collection endpoints

**Files:**
- Create: `app/api/v1/plex/collection_schemas.py`
- Create: `app/api/v1/plex/collection_router.py`
- Modify: `app/main.py` (register `collection_router`)
- Test: `tests/test_plex_collection_api.py`

**Background:** Collection endpoints follow the same auth pattern as `router.py` (use `get_current_user`). The router prefix is `/plex/collections`. Endpoints:
- `GET /` — list all collections for the active connection
- `POST /` — create a collection definition
- `DELETE /{id}` — delete a collection definition (and remove from Plex)
- `POST /{id}/push` — trigger a push sync for a single collection (202)
- `POST /push-all` — push all collections (202, returns task_id)
- `POST /pull` — pull all collections from Plex (202, returns task_id)
- `GET /export` — export all collection definitions as YAML text

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_plex_collection_api.py
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_list_collections_requires_auth(client: TestClient):
    r = client.get("/api/v1/plex/collections/")
    assert r.status_code == 401


@pytest.mark.integration
def test_create_collection(auth_client: TestClient, plex_connection):
    payload = {
        "name": "MCU",
        "description": "Marvel",
        "builder": {
            "builder_type": "static_items",
            "items": [{"tmdb_id": "299536", "item_type": "movie"}],
        },
    }
    r = auth_client.post("/api/v1/plex/collections/", json=payload)
    assert r.status_code == 201
    assert r.json()["name"] == "MCU"


@pytest.mark.integration
def test_list_collections_returns_created(auth_client: TestClient, plex_connection):
    payload = {
        "name": "Test",
        "builder": {"builder_type": "static_items", "items": []},
    }
    auth_client.post("/api/v1/plex/collections/", json=payload)
    r = auth_client.get("/api/v1/plex/collections/")
    assert r.status_code == 200
    names = [c["name"] for c in r.json()]
    assert "Test" in names


@pytest.mark.integration
def test_delete_collection(auth_client: TestClient, plex_connection):
    payload = {
        "name": "ToDelete",
        "builder": {"builder_type": "static_items", "items": []},
    }
    create_r = auth_client.post("/api/v1/plex/collections/", json=payload)
    coll_id = create_r.json()["id"]

    r = auth_client.delete(f"/api/v1/plex/collections/{coll_id}")
    assert r.status_code == 204


@pytest.mark.integration
def test_export_yaml(auth_client: TestClient, plex_connection):
    payload = {
        "name": "MCU",
        "description": "Marvel",
        "builder": {
            "builder_type": "tmdb_collection",
            "tmdb_collection_id": "131292",
        },
    }
    auth_client.post("/api/v1/plex/collections/", json=payload)
    r = auth_client.get("/api/v1/plex/collections/export")
    assert r.status_code == 200
    assert "MCU" in r.text
    assert "131292" in r.text
```

Check `tests/conftest.py` for the `auth_client` and `plex_connection` fixtures — add `plex_connection` if it doesn't exist (creates a `PlexConnection` row and returns it).

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_plex_collection_api.py -v
```

- [ ] **Step 3: Implement API schemas**

```python
# app/api/v1/plex/collection_schemas.py
"""Request/response schemas for collection and playlist API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.infrastructure.external_apis.plex.collection_schemas import (
    StaticItemsBuilder,
    TmdbCollectionBuilder,
)


class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sort_title: Optional[str] = None
    builder: Union[TmdbCollectionBuilder, StaticItemsBuilder] = Field(
        discriminator="builder_type"
    )


class CollectionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: Optional[str]
    sort_title: Optional[str]
    builder_type: str
    builder_config: Dict[str, Any]
    plex_rating_key: Optional[str]
    last_synced_at: Optional[datetime]


class PlaylistCreate(BaseModel):
    name: str
    description: Optional[str] = None
    builder: StaticItemsBuilder


class PlaylistResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: Optional[str]
    builder_config: Dict[str, Any]
    plex_rating_key: Optional[str]
    last_synced_at: Optional[datetime]


class SyncTriggered(BaseModel):
    task_id: Optional[str]
    message: str
```

- [ ] **Step 4: Implement collection router**

```python
# app/api/v1/plex/collection_router.py
"""FastAPI endpoints for Plex collections and playlists."""

import logging
from typing import List

import yaml
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.v1.auth.endpoints import get_current_user
from app.api.v1.plex.collection_schemas import (
    CollectionCreate,
    CollectionResponse,
    PlaylistCreate,
    PlaylistResponse,
    SyncTriggered,
)
from app.core.database import get_db
from app.domain.plex.collection_models import BuilderType, PlexCollection, PlexPlaylist
from app.domain.plex.models import PlexConnection
from app.tasks.plex_collections import push_all_collections, pull_all_collections
from app.tasks.plex_collections import push_all_playlists, pull_all_playlists

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plex/collections", tags=["plex-collections"])
playlist_router = APIRouter(prefix="/plex/playlists", tags=["plex-playlists"])


def _get_active_connection(db: Session) -> PlexConnection:
    conn = db.query(PlexConnection).filter(PlexConnection.is_active.is_(True)).first()
    if conn is None:
        raise HTTPException(status_code=404, detail="No active Plex connection")
    return conn


@router.get("/", response_model=List[CollectionResponse])
def list_collections(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    conn = _get_active_connection(db)
    return db.query(PlexCollection).filter(PlexCollection.connection_id == conn.id).all()


@router.post("/", response_model=CollectionResponse, status_code=201)
def create_collection(
    payload: CollectionCreate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    conn = _get_active_connection(db)
    coll = PlexCollection(
        connection_id=conn.id,
        name=payload.name,
        description=payload.description,
        sort_title=payload.sort_title,
        builder_type=payload.builder.builder_type,
        builder_config=payload.builder.model_dump(),
    )
    db.add(coll)
    db.commit()
    db.refresh(coll)
    return coll


@router.delete("/{collection_id}", status_code=204)
def delete_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    coll = db.query(PlexCollection).filter(PlexCollection.id == collection_id).first()
    if coll is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    db.delete(coll)
    db.commit()


@router.post("/push-all", response_model=SyncTriggered, status_code=202)
def push_all(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    conn = _get_active_connection(db)
    task = push_all_collections.delay(conn.id)
    return SyncTriggered(task_id=task.id, message="Collection push dispatched")


@router.post("/pull", response_model=SyncTriggered, status_code=202)
def pull(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    conn = _get_active_connection(db)
    task = pull_all_collections.delay(conn.id)
    return SyncTriggered(task_id=task.id, message="Collection pull dispatched")


@router.get("/export")
def export_yaml(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    conn = _get_active_connection(db)
    colls = db.query(PlexCollection).filter(PlexCollection.connection_id == conn.id).all()
    data = {"collections": {}, "playlists": {}}
    for c in colls:
        data["collections"][c.name] = {
            "description": c.description,
            "sort_title": c.sort_title,
            "builder": c.builder_config,
        }
    return Response(content=yaml.dump(data, allow_unicode=True), media_type="text/yaml")


# --- Playlist endpoints (same file, different router) ---

@playlist_router.get("/", response_model=List[PlaylistResponse])
def list_playlists(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    conn = _get_active_connection(db)
    return db.query(PlexPlaylist).filter(PlexPlaylist.connection_id == conn.id).all()


@playlist_router.post("/", response_model=PlaylistResponse, status_code=201)
def create_playlist(
    payload: PlaylistCreate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    conn = _get_active_connection(db)
    pl = PlexPlaylist(
        connection_id=conn.id,
        name=payload.name,
        description=payload.description,
        builder_config=payload.builder.model_dump(),
    )
    db.add(pl)
    db.commit()
    db.refresh(pl)
    return pl


@playlist_router.delete("/{playlist_id}", status_code=204)
def delete_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    pl = db.query(PlexPlaylist).filter(PlexPlaylist.id == playlist_id).first()
    if pl is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    db.delete(pl)
    db.commit()


@playlist_router.post("/push-all", response_model=SyncTriggered, status_code=202)
def push_playlists(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    conn = _get_active_connection(db)
    task = push_all_playlists.delay(conn.id)
    return SyncTriggered(task_id=task.id, message="Playlist push dispatched")


@playlist_router.post("/pull", response_model=SyncTriggered, status_code=202)
def pull_playlists(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    conn = _get_active_connection(db)
    task = pull_all_playlists.delay(conn.id)
    return SyncTriggered(task_id=task.id, message="Playlist pull dispatched")
```

- [ ] **Step 5: Register routers in `main.py`**

In `app/main.py`, add after the existing `plex_router` import:

```python
from app.api.v1.plex.collection_router import router as plex_collection_router
from app.api.v1.plex.collection_router import playlist_router as plex_playlist_router
```

And in the router registration section (wherever `app.include_router(plex_router, ...)` is), add:

```python
app.include_router(plex_collection_router, prefix="/api/v1")
app.include_router(plex_playlist_router, prefix="/api/v1")
```

- [ ] **Step 6: Install PyYAML if not present**

```bash
grep -q "pyyaml\|PyYAML" requirements.txt || echo "pyyaml" >> requirements.txt
pip install pyyaml
```

- [ ] **Step 7: Run API tests**

```bash
pytest tests/test_plex_collection_api.py -v
```
Expected: all PASS

- [ ] **Step 8: Commit**

```bash
git add app/api/v1/plex/collection_schemas.py \
        app/api/v1/plex/collection_router.py \
        app/main.py requirements.txt
git commit -m "feat(plex): add collections and playlists API endpoints"
```

---

## Chunk 5: Celery Tasks

### Task 10: Collection and playlist Celery tasks

**Files:**
- Create: `app/tasks/plex_collections.py`
- Test: `tests/test_plex_collection_tasks.py`

**Background:** Four tasks: `push_all_collections`, `pull_all_collections`, `push_all_playlists`, `pull_all_playlists`. All run on the `external_api` queue. Each task instantiates the relevant client, resolver, and service, then iterates through DB records. Uses the same `get_or_cache_library_ids` helper from `plex.service` to get section IDs.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_plex_collection_tasks.py
import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.unit
def test_push_all_collections_skips_when_no_connection():
    with patch("app.tasks.plex_collections.get_db") as mock_db:
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = None
        mock_db.return_value = iter([session])

        from app.tasks.plex_collections import push_all_collections
        push_all_collections(connection_id=999)


@pytest.mark.unit
def test_pull_all_collections_skips_when_no_connection():
    with patch("app.tasks.plex_collections.get_db") as mock_db:
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = None
        mock_db.return_value = iter([session])

        from app.tasks.plex_collections import pull_all_collections
        pull_all_collections(connection_id=999)
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_plex_collection_tasks.py -v
```

- [ ] **Step 3: Implement the tasks**

```python
# app/tasks/plex_collections.py
"""Celery tasks for Plex collection and playlist sync."""

import logging

from app.core.config import settings
from app.core.database import get_db
from app.domain.plex.collection_builder import BuilderResolver
from app.domain.plex.collection_models import PlexCollection, PlexPlaylist
from app.domain.plex.collection_service import PlexCollectionService
from app.domain.plex.models import PlexConnection
from app.domain.plex.playlist_service import PlexPlaylistService
from app.domain.plex.service import get_or_cache_library_ids
from app.infrastructure.external_apis.plex.client import PlexClient
from app.infrastructure.external_apis.plex.collection_client import PlexCollectionClient
from app.infrastructure.external_apis.plex.playlist_client import PlexPlaylistClient
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _make_clients(conn: PlexConnection):
    """Return (PlexClient, machine_id, PlexCollectionClient, PlexPlaylistClient)."""
    base_client = PlexClient(server_url=conn.server_url, token=conn.token)
    machine_id = base_client.get_machine_identifier()
    cc = PlexCollectionClient(
        server_url=conn.server_url, token=conn.token, machine_id=machine_id
    )
    pc = PlexPlaylistClient(
        server_url=conn.server_url, token=conn.token, machine_id=machine_id
    )
    return base_client, machine_id, cc, pc


@celery_app.task(name="app.tasks.plex_collections.push_all_collections", queue="external_api")
def push_all_collections(connection_id: int) -> None:
    db = next(get_db())
    try:
        conn = db.query(PlexConnection).filter(PlexConnection.id == connection_id).first()
        if conn is None:
            logger.warning("push_all_collections: connection %s not found", connection_id)
            return
        movie_section, tv_section = get_or_cache_library_ids(db, conn)
        _, _, cc, _ = _make_clients(conn)
        resolver = BuilderResolver(db=db, connection_id=connection_id)
        svc = PlexCollectionService(
            db=db,
            collection_client=cc,
            resolver=resolver,
            movie_section_id=movie_section,
            tv_section_id=tv_section,
        )
        colls = db.query(PlexCollection).filter(PlexCollection.connection_id == connection_id).all()
        for coll in colls:
            svc.push_collection(coll)
        logger.info("push_all_collections: pushed %d collections", len(colls))
    finally:
        db.close()


@celery_app.task(name="app.tasks.plex_collections.pull_all_collections", queue="external_api")
def pull_all_collections(connection_id: int) -> None:
    db = next(get_db())
    try:
        conn = db.query(PlexConnection).filter(PlexConnection.id == connection_id).first()
        if conn is None:
            logger.warning("pull_all_collections: connection %s not found", connection_id)
            return
        movie_section, tv_section = get_or_cache_library_ids(db, conn)
        _, _, cc, _ = _make_clients(conn)
        resolver = BuilderResolver(db=db, connection_id=connection_id)
        svc = PlexCollectionService(
            db=db,
            collection_client=cc,
            resolver=resolver,
            movie_section_id=movie_section,
            tv_section_id=tv_section,
        )
        svc.pull_collections(connection_id=connection_id)
    finally:
        db.close()


@celery_app.task(name="app.tasks.plex_collections.push_all_playlists", queue="external_api")
def push_all_playlists(connection_id: int) -> None:
    db = next(get_db())
    try:
        conn = db.query(PlexConnection).filter(PlexConnection.id == connection_id).first()
        if conn is None:
            logger.warning("push_all_playlists: connection %s not found", connection_id)
            return
        _, _, _, pc = _make_clients(conn)
        resolver = BuilderResolver(db=db, connection_id=connection_id)
        svc = PlexPlaylistService(db=db, playlist_client=pc, resolver=resolver)
        playlists = db.query(PlexPlaylist).filter(PlexPlaylist.connection_id == connection_id).all()
        for pl in playlists:
            svc.push_playlist(pl)
        logger.info("push_all_playlists: pushed %d playlists", len(playlists))
    finally:
        db.close()


@celery_app.task(name="app.tasks.plex_collections.pull_all_playlists", queue="external_api")
def pull_all_playlists(connection_id: int) -> None:
    db = next(get_db())
    try:
        conn = db.query(PlexConnection).filter(PlexConnection.id == connection_id).first()
        if conn is None:
            logger.warning("pull_all_playlists: connection %s not found", connection_id)
            return
        _, _, _, pc = _make_clients(conn)
        resolver = BuilderResolver(db=db, connection_id=connection_id)
        svc = PlexPlaylistService(db=db, playlist_client=pc, resolver=resolver)
        svc.pull_playlists(connection_id=connection_id)
    finally:
        db.close()
```

- [ ] **Step 4: Run all backend tests**

```bash
pytest tests/ -v --tb=short
```
Expected: all PASS (or pre-existing failures only)

- [ ] **Step 5: Run linting**

```bash
black app/ tests/ && isort app/ tests/ && flake8 app/ tests/ && mypy app/
```

Fix any issues before committing.

- [ ] **Step 6: Commit**

```bash
git add app/tasks/plex_collections.py tests/test_plex_collection_tasks.py
git commit -m "feat(plex): add Celery tasks for collection and playlist bi-di sync"
```

---

## Chunk 6: Frontend

### Task 11: API service layer

**Files:**
- Create: `frontend/src/services/plexCollectionService.ts`
- Test: `frontend/src/services/__tests__/plexCollectionService.test.ts`

**Background:** Thin axios wrappers. Follow the pattern in `frontend/src/services/plexService.ts` — each function calls the API and returns typed data. Types come from the OpenAPI schema via `npm run typegen` (run after backend is deployed) or are defined inline for now.

- [ ] **Step 1: Write the failing tests**

```typescript
// frontend/src/services/__tests__/plexCollectionService.test.ts
import { vi, describe, it, expect, beforeEach } from 'vitest';
import axios from 'axios';

vi.mock('axios');
const mockedAxios = vi.mocked(axios, true);

import {
  listCollections,
  createCollection,
  deleteCollection,
  pushAllCollections,
  pullCollections,
  exportCollectionsYaml,
  listPlaylists,
  createPlaylist,
  deletePlaylist,
  pushAllPlaylists,
  pullPlaylists,
} from '../plexCollectionService';

beforeEach(() => vi.clearAllMocks());

describe('listCollections', () => {
  it('GETs /api/v1/plex/collections/', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: [] });
    await listCollections();
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/plex/collections/');
  });
});

describe('createCollection', () => {
  it('POSTs with payload', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({ data: { id: 1 } });
    const payload = { name: 'MCU', builder: { builder_type: 'static_items', items: [] } };
    const result = await createCollection(payload as any);
    expect(result.id).toBe(1);
  });
});

describe('exportCollectionsYaml', () => {
  it('GETs export endpoint', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: 'collections: {}' });
    const result = await exportCollectionsYaml();
    expect(result).toContain('collections');
  });
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd frontend && npm run test -- services/__tests__/plexCollectionService.test.ts
```

- [ ] **Step 3: Implement the service**

```typescript
// frontend/src/services/plexCollectionService.ts
import axios from 'axios';

export interface StaticItem {
  tmdb_id: string;
  item_type: 'movie' | 'tv_show';
}

export interface StaticItemsBuilder {
  builder_type: 'static_items';
  items: StaticItem[];
}

export interface TmdbCollectionBuilder {
  builder_type: 'tmdb_collection';
  tmdb_collection_id: string;
}

export type AnyBuilder = StaticItemsBuilder | TmdbCollectionBuilder;

export interface CollectionCreate {
  name: string;
  description?: string;
  sort_title?: string;
  builder: AnyBuilder;
}

export interface CollectionResponse {
  id: number;
  name: string;
  description: string | null;
  sort_title: string | null;
  builder_type: string;
  builder_config: Record<string, unknown>;
  plex_rating_key: string | null;
  last_synced_at: string | null;
}

export interface PlaylistCreate {
  name: string;
  description?: string;
  builder: StaticItemsBuilder;
}

export interface PlaylistResponse {
  id: number;
  name: string;
  description: string | null;
  builder_config: Record<string, unknown>;
  plex_rating_key: string | null;
  last_synced_at: string | null;
}

export interface SyncTriggered {
  task_id: string | null;
  message: string;
}

const BASE = '/api/v1/plex';

export async function listCollections(): Promise<CollectionResponse[]> {
  const { data } = await axios.get<CollectionResponse[]>(`${BASE}/collections/`);
  return data;
}

export async function createCollection(payload: CollectionCreate): Promise<CollectionResponse> {
  const { data } = await axios.post<CollectionResponse>(`${BASE}/collections/`, payload);
  return data;
}

export async function deleteCollection(id: number): Promise<void> {
  await axios.delete(`${BASE}/collections/${id}`);
}

export async function pushAllCollections(): Promise<SyncTriggered> {
  const { data } = await axios.post<SyncTriggered>(`${BASE}/collections/push-all`);
  return data;
}

export async function pullCollections(): Promise<SyncTriggered> {
  const { data } = await axios.post<SyncTriggered>(`${BASE}/collections/pull`);
  return data;
}

export async function exportCollectionsYaml(): Promise<string> {
  const { data } = await axios.get<string>(`${BASE}/collections/export`);
  return data;
}

export async function listPlaylists(): Promise<PlaylistResponse[]> {
  const { data } = await axios.get<PlaylistResponse[]>(`${BASE}/playlists/`);
  return data;
}

export async function createPlaylist(payload: PlaylistCreate): Promise<PlaylistResponse> {
  const { data } = await axios.post<PlaylistResponse>(`${BASE}/playlists/`, payload);
  return data;
}

export async function deletePlaylist(id: number): Promise<void> {
  await axios.delete(`${BASE}/playlists/${id}`);
}

export async function pushAllPlaylists(): Promise<SyncTriggered> {
  const { data } = await axios.post<SyncTriggered>(`${BASE}/playlists/push-all`);
  return data;
}

export async function pullPlaylists(): Promise<SyncTriggered> {
  const { data } = await axios.post<SyncTriggered>(`${BASE}/playlists/pull`);
  return data;
}
```

- [ ] **Step 4: Run tests**

```bash
cd frontend && npm run test -- services/__tests__/plexCollectionService.test.ts
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/plexCollectionService.ts \
        frontend/src/services/__tests__/plexCollectionService.test.ts
git commit -m "feat(plex): add frontend collection/playlist service layer"
```

---

### Task 12: Zustand store

**Files:**
- Create: `frontend/src/stores/plexCollectionStore.ts`
- Test: `frontend/src/stores/__tests__/plexCollectionStore.test.ts`

**Background:** Follows the pattern in `frontend/src/stores/plexStore.ts`. Tracks `collections`, `playlists`, loading states, and error strings. Actions call the service functions.

- [ ] **Step 1: Write the failing tests**

```typescript
// frontend/src/stores/__tests__/plexCollectionStore.test.ts
import { vi, describe, it, expect, beforeEach } from 'vitest';

vi.mock('../../services/plexCollectionService', () => ({
  listCollections: vi.fn().mockResolvedValue([{ id: 1, name: 'MCU' }]),
  listPlaylists: vi.fn().mockResolvedValue([]),
  createCollection: vi.fn().mockResolvedValue({ id: 2, name: 'Test' }),
  deleteCollection: vi.fn().mockResolvedValue(undefined),
  pushAllCollections: vi.fn().mockResolvedValue({ task_id: 'abc', message: 'ok' }),
  pullCollections: vi.fn().mockResolvedValue({ task_id: 'def', message: 'ok' }),
  createPlaylist: vi.fn().mockResolvedValue({ id: 1, name: 'Weekend' }),
  deletePlaylist: vi.fn().mockResolvedValue(undefined),
  pushAllPlaylists: vi.fn().mockResolvedValue({ task_id: 'ghi', message: 'ok' }),
  pullPlaylists: vi.fn().mockResolvedValue({ task_id: 'jkl', message: 'ok' }),
}));

import { usePlexCollectionStore } from '../plexCollectionStore';

beforeEach(() => {
  usePlexCollectionStore.setState({ collections: [], playlists: [], loading: false, error: null });
});

describe('fetchCollections', () => {
  it('loads collections into state', async () => {
    await usePlexCollectionStore.getState().fetchCollections();
    expect(usePlexCollectionStore.getState().collections).toHaveLength(1);
  });
});

describe('pushAll', () => {
  it('calls pushAllCollections without error', async () => {
    await usePlexCollectionStore.getState().pushAll();
    expect(usePlexCollectionStore.getState().error).toBeNull();
  });
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd frontend && npm run test -- stores/__tests__/plexCollectionStore.test.ts
```

- [ ] **Step 3: Implement the store**

```typescript
// frontend/src/stores/plexCollectionStore.ts
import { create } from 'zustand';
import {
  CollectionCreate,
  CollectionResponse,
  PlaylistCreate,
  PlaylistResponse,
  createCollection,
  createPlaylist,
  deleteCollection,
  deletePlaylist,
  listCollections,
  listPlaylists,
  pullCollections,
  pullPlaylists,
  pushAllCollections,
  pushAllPlaylists,
} from '../services/plexCollectionService';

interface PlexCollectionState {
  collections: CollectionResponse[];
  playlists: PlaylistResponse[];
  loading: boolean;
  error: string | null;
  fetchCollections: () => Promise<void>;
  fetchPlaylists: () => Promise<void>;
  addCollection: (payload: CollectionCreate) => Promise<void>;
  removeCollection: (id: number) => Promise<void>;
  pushAll: () => Promise<void>;
  pullAll: () => Promise<void>;
  addPlaylist: (payload: PlaylistCreate) => Promise<void>;
  removePlaylist: (id: number) => Promise<void>;
  pushAllPl: () => Promise<void>;
  pullAllPl: () => Promise<void>;
}

export const usePlexCollectionStore = create<PlexCollectionState>((set, get) => ({
  collections: [],
  playlists: [],
  loading: false,
  error: null,

  fetchCollections: async () => {
    set({ loading: true, error: null });
    try {
      const collections = await listCollections();
      set({ collections, loading: false });
    } catch (e: unknown) {
      set({ error: String(e), loading: false });
    }
  },

  fetchPlaylists: async () => {
    set({ loading: true, error: null });
    try {
      const playlists = await listPlaylists();
      set({ playlists, loading: false });
    } catch (e: unknown) {
      set({ error: String(e), loading: false });
    }
  },

  addCollection: async (payload) => {
    const created = await createCollection(payload);
    set((s) => ({ collections: [...s.collections, created] }));
  },

  removeCollection: async (id) => {
    await deleteCollection(id);
    set((s) => ({ collections: s.collections.filter((c) => c.id !== id) }));
  },

  pushAll: async () => {
    set({ error: null });
    try {
      await pushAllCollections();
    } catch (e: unknown) {
      set({ error: String(e) });
    }
  },

  pullAll: async () => {
    set({ error: null });
    try {
      await pullCollections();
      await get().fetchCollections();
    } catch (e: unknown) {
      set({ error: String(e) });
    }
  },

  addPlaylist: async (payload) => {
    const created = await createPlaylist(payload);
    set((s) => ({ playlists: [...s.playlists, created] }));
  },

  removePlaylist: async (id) => {
    await deletePlaylist(id);
    set((s) => ({ playlists: s.playlists.filter((p) => p.id !== id) }));
  },

  pushAllPl: async () => {
    set({ error: null });
    try {
      await pushAllPlaylists();
    } catch (e: unknown) {
      set({ error: String(e) });
    }
  },

  pullAllPl: async () => {
    set({ error: null });
    try {
      await pullPlaylists();
      await get().fetchPlaylists();
    } catch (e: unknown) {
      set({ error: String(e) });
    }
  },
}));
```

- [ ] **Step 4: Run tests**

```bash
cd frontend && npm run test -- stores/__tests__/plexCollectionStore.test.ts
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/stores/plexCollectionStore.ts \
        frontend/src/stores/__tests__/plexCollectionStore.test.ts
git commit -m "feat(plex): add Zustand store for collections and playlists"
```

---

### Task 13: UI components and page

**Files:**
- Create: `frontend/src/pages/PlexCollectionsPage.tsx`
- Create: `frontend/src/components/features/plex/CollectionCard.tsx`
- Create: `frontend/src/components/features/plex/PlaylistCard.tsx`
- Create: `frontend/src/components/features/plex/CollectionForm.tsx`
- Modify: `frontend/src/App.tsx` (add route)

**Background:** A single page at `/plex/collections` with two tabs — Collections and Playlists. Each tab shows a list of cards (name, builder type, last synced, sync status badge, delete button) plus push/pull action buttons in the header. A "New Collection/Playlist" modal triggers `CollectionForm`.

Check `frontend/src/App.tsx` for the route registration pattern (lazy-loaded pages wrapped in `ProtectedRoute` + `MainLayout`).

- [ ] **Step 1: Implement `CollectionCard`**

```tsx
// frontend/src/components/features/plex/CollectionCard.tsx
import React from 'react';
import { CollectionResponse } from '../../../services/plexCollectionService';

interface Props {
  collection: CollectionResponse;
  onDelete: (id: number) => void;
}

export function CollectionCard({ collection, onDelete }: Props) {
  const synced = collection.last_synced_at
    ? new Date(collection.last_synced_at).toLocaleString()
    : 'Never';

  return (
    <div className="card border rounded p-4 flex justify-between items-start">
      <div>
        <h3 className="font-semibold text-lg">{collection.name}</h3>
        {collection.description && (
          <p className="text-sm text-gray-500">{collection.description}</p>
        )}
        <div className="flex gap-2 mt-1 text-xs text-gray-400">
          <span className="badge">{collection.builder_type}</span>
          {collection.plex_rating_key ? (
            <span className="text-green-600">Synced to Plex</span>
          ) : (
            <span className="text-yellow-600">Not pushed yet</span>
          )}
          <span>Last sync: {synced}</span>
        </div>
      </div>
      <button
        onClick={() => onDelete(collection.id)}
        className="text-red-500 hover:text-red-700 text-sm"
        aria-label={`Delete collection ${collection.name}`}
      >
        Delete
      </button>
    </div>
  );
}
```

- [ ] **Step 2: Implement `PlaylistCard`** (mirrors CollectionCard for PlaylistResponse)

```tsx
// frontend/src/components/features/plex/PlaylistCard.tsx
import React from 'react';
import { PlaylistResponse } from '../../../services/plexCollectionService';

interface Props {
  playlist: PlaylistResponse;
  onDelete: (id: number) => void;
}

export function PlaylistCard({ playlist, onDelete }: Props) {
  const synced = playlist.last_synced_at
    ? new Date(playlist.last_synced_at).toLocaleString()
    : 'Never';

  return (
    <div className="card border rounded p-4 flex justify-between items-start">
      <div>
        <h3 className="font-semibold text-lg">{playlist.name}</h3>
        {playlist.description && (
          <p className="text-sm text-gray-500">{playlist.description}</p>
        )}
        <div className="flex gap-2 mt-1 text-xs text-gray-400">
          {playlist.plex_rating_key ? (
            <span className="text-green-600">Synced to Plex</span>
          ) : (
            <span className="text-yellow-600">Not pushed yet</span>
          )}
          <span>Last sync: {synced}</span>
        </div>
      </div>
      <button
        onClick={() => onDelete(playlist.id)}
        className="text-red-500 hover:text-red-700 text-sm"
        aria-label={`Delete playlist ${playlist.name}`}
      >
        Delete
      </button>
    </div>
  );
}
```

- [ ] **Step 3: Implement `CollectionForm`**

```tsx
// frontend/src/components/features/plex/CollectionForm.tsx
import React, { useState } from 'react';
import { CollectionCreate, PlaylistCreate, StaticItem } from '../../../services/plexCollectionService';

type Mode = 'collection' | 'playlist';

interface Props {
  mode: Mode;
  onSubmit: (payload: CollectionCreate | PlaylistCreate) => void;
  onCancel: () => void;
}

export function CollectionForm({ mode, onSubmit, onCancel }: Props) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [builderType, setBuilderType] = useState<'static_items' | 'tmdb_collection'>('static_items');
  const [tmdbCollectionId, setTmdbCollectionId] = useState('');
  const [staticItems, setStaticItems] = useState<StaticItem[]>([]);
  const [newTmdbId, setNewTmdbId] = useState('');
  const [newItemType, setNewItemType] = useState<'movie' | 'tv_show'>('movie');

  function addItem() {
    if (!newTmdbId.trim()) return;
    setStaticItems((prev) => [...prev, { tmdb_id: newTmdbId.trim(), item_type: newItemType }]);
    setNewTmdbId('');
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const builder =
      builderType === 'tmdb_collection'
        ? { builder_type: 'tmdb_collection' as const, tmdb_collection_id: tmdbCollectionId }
        : { builder_type: 'static_items' as const, items: staticItems };
    onSubmit({ name, description: description || undefined, builder } as CollectionCreate);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium">Name</label>
        <input
          className="input w-full"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
      </div>
      <div>
        <label className="block text-sm font-medium">Description</label>
        <input className="input w-full" value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>
      {mode === 'collection' && (
        <div>
          <label className="block text-sm font-medium">Builder type</label>
          <select
            className="select w-full"
            value={builderType}
            onChange={(e) => setBuilderType(e.target.value as typeof builderType)}
          >
            <option value="static_items">Static items</option>
            <option value="tmdb_collection">TMDB collection</option>
          </select>
        </div>
      )}
      {builderType === 'tmdb_collection' && (
        <div>
          <label className="block text-sm font-medium">TMDB Collection ID</label>
          <input
            className="input w-full"
            value={tmdbCollectionId}
            onChange={(e) => setTmdbCollectionId(e.target.value)}
            placeholder="e.g. 131292"
            required
          />
        </div>
      )}
      {builderType === 'static_items' && (
        <div>
          <label className="block text-sm font-medium">Items</label>
          <div className="flex gap-2 mb-2">
            <input
              className="input flex-1"
              value={newTmdbId}
              onChange={(e) => setNewTmdbId(e.target.value)}
              placeholder="TMDB ID"
            />
            <select
              className="select"
              value={newItemType}
              onChange={(e) => setNewItemType(e.target.value as 'movie' | 'tv_show')}
            >
              <option value="movie">Movie</option>
              <option value="tv_show">TV Show</option>
            </select>
            <button type="button" onClick={addItem} className="btn btn-secondary">Add</button>
          </div>
          <ul className="text-sm space-y-1">
            {staticItems.map((item, i) => (
              <li key={i} className="flex justify-between">
                <span>{item.tmdb_id} ({item.item_type})</span>
                <button
                  type="button"
                  onClick={() => setStaticItems((prev) => prev.filter((_, j) => j !== i))}
                  className="text-red-500 text-xs"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="flex gap-2 justify-end">
        <button type="button" onClick={onCancel} className="btn btn-ghost">Cancel</button>
        <button type="submit" className="btn btn-primary">Create</button>
      </div>
    </form>
  );
}
```

- [ ] **Step 4: Implement `PlexCollectionsPage`**

```tsx
// frontend/src/pages/PlexCollectionsPage.tsx
import React, { useEffect, useState } from 'react';
import { CollectionCard } from '../components/features/plex/CollectionCard';
import { PlaylistCard } from '../components/features/plex/PlaylistCard';
import { CollectionForm } from '../components/features/plex/CollectionForm';
import { usePlexCollectionStore } from '../stores/plexCollectionStore';
import { CollectionCreate, PlaylistCreate } from '../services/plexCollectionService';

type Tab = 'collections' | 'playlists';

export default function PlexCollectionsPage() {
  const {
    collections, playlists, loading, error,
    fetchCollections, fetchPlaylists,
    addCollection, removeCollection, pushAll, pullAll,
    addPlaylist, removePlaylist, pushAllPl, pullAllPl,
  } = usePlexCollectionStore();

  const [tab, setTab] = useState<Tab>('collections');
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    fetchCollections();
    fetchPlaylists();
  }, [fetchCollections, fetchPlaylists]);

  async function handleSubmit(payload: CollectionCreate | PlaylistCreate) {
    if (tab === 'collections') {
      await addCollection(payload as CollectionCreate);
    } else {
      await addPlaylist(payload as PlaylistCreate);
    }
    setShowForm(false);
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Plex Collections & Playlists</h1>
        <div className="flex gap-2">
          {tab === 'collections' ? (
            <>
              <button onClick={pullAll} className="btn btn-secondary">Pull from Plex</button>
              <button onClick={pushAll} className="btn btn-secondary">Push to Plex</button>
            </>
          ) : (
            <>
              <button onClick={pullAllPl} className="btn btn-secondary">Pull from Plex</button>
              <button onClick={pushAllPl} className="btn btn-secondary">Push to Plex</button>
            </>
          )}
          <button onClick={() => setShowForm(true)} className="btn btn-primary">New</button>
        </div>
      </div>

      {error && <div className="alert alert-error mb-4">{error}</div>}

      <div className="tabs mb-4">
        <button
          className={`tab ${tab === 'collections' ? 'tab-active' : ''}`}
          onClick={() => setTab('collections')}
        >
          Collections ({collections.length})
        </button>
        <button
          className={`tab ${tab === 'playlists' ? 'tab-active' : ''}`}
          onClick={() => setTab('playlists')}
        >
          Playlists ({playlists.length})
        </button>
      </div>

      {loading && <p className="text-gray-400">Loading…</p>}

      {tab === 'collections' && (
        <div className="space-y-3">
          {collections.map((c) => (
            <CollectionCard key={c.id} collection={c} onDelete={removeCollection} />
          ))}
          {collections.length === 0 && !loading && (
            <p className="text-gray-400">No collections yet. Create one or pull from Plex.</p>
          )}
        </div>
      )}

      {tab === 'playlists' && (
        <div className="space-y-3">
          {playlists.map((p) => (
            <PlaylistCard key={p.id} playlist={p} onDelete={removePlaylist} />
          ))}
          {playlists.length === 0 && !loading && (
            <p className="text-gray-400">No playlists yet. Create one or pull from Plex.</p>
          )}
        </div>
      )}

      {showForm && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h2 className="text-lg font-bold mb-4">
              New {tab === 'collections' ? 'Collection' : 'Playlist'}
            </h2>
            <CollectionForm
              mode={tab === 'collections' ? 'collection' : 'playlist'}
              onSubmit={handleSubmit}
              onCancel={() => setShowForm(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Add route to `App.tsx`**

In `frontend/src/App.tsx`, add a lazy import:

```typescript
const PlexCollectionsPage = lazy(() => import('./pages/PlexCollectionsPage'));
```

And add the route inside the protected routes section:

```tsx
<Route path="/plex/collections" element={<PlexCollectionsPage />} />
```

- [ ] **Step 6: Run frontend checks**

```bash
cd frontend && npm run type-check && npm run lint
```

Fix any type or lint errors before committing.

- [ ] **Step 7: Run all frontend tests**

```bash
cd frontend && npm run test
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/pages/PlexCollectionsPage.tsx \
        frontend/src/components/features/plex/CollectionCard.tsx \
        frontend/src/components/features/plex/PlaylistCard.tsx \
        frontend/src/components/features/plex/CollectionForm.tsx \
        frontend/src/App.tsx
git commit -m "feat(plex): add collections and playlists management UI"
```

---

---

## Chunk 7: Franchise Support — Movie Schema & Enrichment

### Task 14: Add `tmdb_collection_id` / `tmdb_collection_name` to Movie + enrichment

**Files:**
- Modify: `app/domain/movies/models.py`
- Modify: `app/services_impl.py` (`parse_movie_details_response`)
- Modify: `app/tasks/enrichment.py` (`enrich_movie_external`)
- Create: `alembic/versions/015_movie_tmdb_collection.py`
- Test: `tests/test_models_unit.py` (or nearest movie model test file)

**Background:** TMDB's `/movie/{id}` response contains a `belongs_to_collection` key: `{"id": 131292, "name": "The Avengers Collection", "poster_path": ..., "backdrop_path": ...}`. `parse_movie_details_response` currently ignores it. We store the `id` (as string) and `name` on `Movie` so the franchise auto-discovery can query them without hitting TMDB again. Existing movies will get these fields populated the next time they are re-enriched; a one-off task can trigger re-enrichment for the whole library if needed.

- [ ] **Step 1: Write the failing tests**

Add to the nearest movie model or enrichment test file (check `tests/test_models_unit.py`):

```python
@pytest.mark.unit
def test_movie_has_tmdb_collection_columns():
    from app.domain.movies.models import Movie
    cols = {c.name for c in Movie.__table__.columns}
    assert "tmdb_collection_id" in cols
    assert "tmdb_collection_name" in cols


@pytest.mark.unit
def test_parse_movie_details_extracts_collection():
    from app.services_impl import TMDBService
    raw = {
        "id": 603,
        "title": "The Matrix",
        "release_date": "1999-03-31",
        "genres": [],
        "belongs_to_collection": {"id": 2344, "name": "The Matrix Collection"},
    }
    result = TMDBService.parse_movie_details_response(raw)
    assert result["tmdb_collection_id"] == "2344"
    assert result["tmdb_collection_name"] == "The Matrix Collection"


@pytest.mark.unit
def test_parse_movie_details_collection_none_when_absent():
    from app.services_impl import TMDBService
    raw = {"id": 603, "title": "Solo Film", "release_date": "2000-01-01", "genres": []}
    result = TMDBService.parse_movie_details_response(raw)
    assert result["tmdb_collection_id"] is None
    assert result["tmdb_collection_name"] is None
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_models_unit.py -k "tmdb_collection" -v
```
Expected: FAIL

- [ ] **Step 3: Add columns to Movie model**

In `app/domain/movies/models.py`, add after `poster_url`:

```python
tmdb_collection_id = Column(String(50), nullable=True, index=True)
tmdb_collection_name = Column(String(500), nullable=True)
```

Also add to `__table_args__`:

```python
Index("idx_movies_tmdb_collection", "tmdb_collection_id"),
```

- [ ] **Step 4: Update `parse_movie_details_response` in `app/services_impl.py`**

Inside the `return { ... }` dict (around line 474), add:

```python
"tmdb_collection_id": str(collection["id"]) if (collection := data.get("belongs_to_collection")) else None,
"tmdb_collection_name": collection.get("name") if data.get("belongs_to_collection") else None,
```

Or without walrus (Python 3.8 compat):

```python
_collection = data.get("belongs_to_collection")
# then in the dict:
"tmdb_collection_id": str(_collection["id"]) if _collection else None,
"tmdb_collection_name": _collection.get("name") if _collection else None,
```

- [ ] **Step 5: Update `enrich_movie_external` in `app/tasks/enrichment.py`**

After `movie.genres = detail.get("genres", movie.genres)` (around line 80), add:

```python
movie.tmdb_collection_id = detail.get("tmdb_collection_id", movie.tmdb_collection_id)
movie.tmdb_collection_name = detail.get("tmdb_collection_name", movie.tmdb_collection_name)
```

- [ ] **Step 6: Create migration**

```bash
alembic revision -m "add tmdb collection fields to movies"
```

Rename to `015_movie_tmdb_collection.py` and fill in:

```python
"""add tmdb collection fields to movies

Revision ID: 015
Revises: 014
"""
from alembic import op
import sqlalchemy as sa

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("movies", sa.Column("tmdb_collection_id", sa.String(50), nullable=True))
    op.add_column("movies", sa.Column("tmdb_collection_name", sa.String(500), nullable=True))
    op.create_index("idx_movies_tmdb_collection", "movies", ["tmdb_collection_id"])


def downgrade() -> None:
    op.drop_index("idx_movies_tmdb_collection", table_name="movies")
    op.drop_column("movies", "tmdb_collection_name")
    op.drop_column("movies", "tmdb_collection_id")
```

- [ ] **Step 7: Run migration**

```bash
alembic upgrade head && alembic current
```
Expected: `015 (head)`

- [ ] **Step 8: Run tests**

```bash
pytest tests/test_models_unit.py -k "tmdb_collection" -v
```
Expected: PASS

- [ ] **Step 9: Run linting**

```bash
black app/ tests/ && isort app/ tests/ && flake8 app/ tests/ && mypy app/
```

- [ ] **Step 10: Commit**

```bash
git add app/domain/movies/models.py app/services_impl.py app/tasks/enrichment.py \
        alembic/versions/015_movie_tmdb_collection.py
git commit -m "feat(movies): store tmdb_collection_id and name from TMDB enrichment"
```

---

## Chunk 8: Default Collection Sets

### Task 15: Extend collection schema — `enabled`, `is_default`, new builder types, CollectionSet model

**Files:**
- Modify: `app/domain/plex/collection_models.py`
- Modify: `app/infrastructure/external_apis/plex/collection_schemas.py`
- Create: `alembic/versions/016_plex_collection_sets.py`
- Test: `tests/test_plex_collection_models.py`

**Background:** Three additions in one migration:

1. `plex_collections` gets `enabled` (bool, default `True`) and `is_default` (bool, default `False`). Only `enabled=True` collections are pushed to Plex during sync.

2. `plexbuildertype` PostgreSQL enum gets two new values: `genre` and `decade`. Adding values to a native PostgreSQL enum requires `ALTER TYPE ... ADD VALUE`.

3. New table `plex_collection_sets` — one row per auto-generation category (franchise, genre, decade). `enabled` controls whether that category runs during sync. Rows are seeded at startup; the table is never user-created.

`SetType` enum values:
- `franchise` — one collection per unique `tmdb_collection_id` in the Movie table
- `genre` — one collection per unique genre tag across movies and TV shows
- `decade` — one collection per decade represented in the movie library

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_plex_collection_models.py`:

```python
@pytest.mark.unit
def test_plex_collection_has_enabled_and_is_default_columns():
    from app.domain.plex.collection_models import PlexCollection
    cols = {c.name for c in PlexCollection.__table__.columns}
    assert "enabled" in cols
    assert "is_default" in cols


@pytest.mark.unit
def test_plex_collection_set_model_exists():
    from app.domain.plex.collection_models import PlexCollectionSet, SetType
    assert SetType.FRANCHISE == "franchise"
    assert SetType.GENRE == "genre"
    assert SetType.DECADE == "decade"


@pytest.mark.unit
def test_genre_builder_schema():
    from app.infrastructure.external_apis.plex.collection_schemas import GenreBuilder
    b = GenreBuilder(genre="Action")
    assert b.builder_type == "genre"
    assert b.genre == "Action"


@pytest.mark.unit
def test_decade_builder_schema():
    from app.infrastructure.external_apis.plex.collection_schemas import DecadeBuilder
    b = DecadeBuilder(decade=2000)
    assert b.builder_type == "decade"
    assert b.decade == 2000
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_plex_collection_models.py -v
```

- [ ] **Step 3: Add `enabled` / `is_default` to `PlexCollection`**

In `app/domain/plex/collection_models.py`, add to `PlexCollection` after `last_synced_at`:

```python
enabled = Column(Boolean, nullable=False, default=True, server_default="true")
is_default = Column(Boolean, nullable=False, default=False, server_default="false")
```

Add `Boolean` to the SQLAlchemy imports.

- [ ] **Step 4: Add `SetType` enum and `PlexCollectionSet` model**

Append to `app/domain/plex/collection_models.py`:

```python
class SetType(str, enum.Enum):
    FRANCHISE = "franchise"
    GENRE = "genre"
    DECADE = "decade"


class PlexCollectionSet(Base):
    """One row per auto-generation category; seeded at startup."""

    __tablename__ = "plex_collection_sets"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(
        Integer, ForeignKey("plex_connections.id", ondelete="CASCADE"), nullable=False
    )
    set_type: Any = Column(
        SAEnum("franchise", "genre", "decade", name="plexsettype"),
        nullable=False,
    )
    enabled = Column(Boolean, nullable=False, default=True, server_default="true")
    last_run_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_plex_set_connection", "connection_id"),
    )
```

- [ ] **Step 5: Add `GenreBuilder` and `DecadeBuilder` to collection_schemas.py**

In `app/infrastructure/external_apis/plex/collection_schemas.py`, add:

```python
class GenreBuilder(BaseModel):
    builder_type: Literal["genre"] = "genre"
    genre: str


class DecadeBuilder(BaseModel):
    builder_type: Literal["decade"] = "decade"
    decade: int  # e.g. 2000 means 2000–2009
```

Update `AnyBuilder`:

```python
AnyBuilder = Union[TmdbCollectionBuilder, StaticItemsBuilder, GenreBuilder, DecadeBuilder]
```

Update `CollectionDefinition.builder` field discriminator — it already uses `discriminator="builder_type"` so no change needed there.

- [ ] **Step 6: Extend `BuilderType` enum**

In `app/domain/plex/collection_models.py`, update `BuilderType`:

```python
class BuilderType(str, enum.Enum):
    TMDB_COLLECTION = "tmdb_collection"
    STATIC_ITEMS = "static_items"
    GENRE = "genre"
    DECADE = "decade"
```

- [ ] **Step 7: Create migration 016**

```bash
alembic revision -m "plex collection sets and enabled flag"
```

Rename to `016_plex_collection_sets.py`:

```python
"""plex collection sets and enabled flag

Revision ID: 016
Revises: 015
"""
from alembic import op
import sqlalchemy as sa

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add enabled/is_default to plex_collections
    op.add_column("plex_collections",
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"))
    op.add_column("plex_collections",
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"))

    # Extend plexbuildertype enum (PostgreSQL native enum)
    op.execute("ALTER TYPE plexbuildertype ADD VALUE IF NOT EXISTS 'genre'")
    op.execute("ALTER TYPE plexbuildertype ADD VALUE IF NOT EXISTS 'decade'")

    # Create plexsettype enum and plex_collection_sets table
    set_type_enum = sa.Enum("franchise", "genre", "decade", name="plexsettype")
    set_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "plex_collection_sets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("connection_id", sa.Integer,
                  sa.ForeignKey("plex_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("set_type",
                  sa.Enum("franchise", "genre", "decade", name="plexsettype"), nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_run_at", sa.DateTime, nullable=True),
    )
    op.create_index("idx_plex_set_connection", "plex_collection_sets", ["connection_id"])


def downgrade() -> None:
    op.drop_table("plex_collection_sets")
    op.execute("DROP TYPE IF EXISTS plexsettype")
    op.drop_column("plex_collections", "is_default")
    op.drop_column("plex_collections", "enabled")
    # Note: PostgreSQL does not support removing enum values — downgrade leaves genre/decade in plexbuildertype
```

- [ ] **Step 8: Run migration**

```bash
alembic upgrade head && alembic current
```
Expected: `016 (head)`

- [ ] **Step 9: Run tests**

```bash
pytest tests/test_plex_collection_models.py tests/test_plex_collection_schemas.py -v
```
Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add app/domain/plex/collection_models.py \
        app/infrastructure/external_apis/plex/collection_schemas.py \
        alembic/versions/016_plex_collection_sets.py
git commit -m "feat(plex): add enabled/is_default to collections, genre/decade builders, CollectionSet model"
```

---

### Task 16: CollectionSet seeding at startup

**Files:**
- Create: `app/domain/plex/collection_set_seeder.py`
- Modify: `app/main.py` (call seeder in lifespan)
- Test: `tests/test_plex_collection_set_seeder.py`

**Background:** `PlexCollectionSet` rows must exist before the user can toggle them. The seeder runs at app startup (inside `lifespan`) and creates the three rows (franchise, genre, decade) for the active connection if they don't already exist. It is idempotent — safe to run on every startup.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_plex_collection_set_seeder.py
import pytest
from app.domain.plex.collection_set_seeder import seed_collection_sets
from app.domain.plex.collection_models import PlexCollectionSet, SetType
from app.domain.plex.models import PlexConnection


@pytest.mark.integration
def test_seed_creates_all_three_set_types(db_session):
    conn = PlexConnection(server_url="http://plex", token="t", is_active=True)
    db_session.add(conn)
    db_session.flush()

    seed_collection_sets(db=db_session, connection_id=conn.id)

    sets = db_session.query(PlexCollectionSet).filter(
        PlexCollectionSet.connection_id == conn.id
    ).all()
    set_types = {s.set_type for s in sets}
    assert SetType.FRANCHISE in set_types
    assert SetType.GENRE in set_types
    assert SetType.DECADE in set_types


@pytest.mark.integration
def test_seed_is_idempotent(db_session):
    conn = PlexConnection(server_url="http://plex", token="t", is_active=True)
    db_session.add(conn)
    db_session.flush()

    seed_collection_sets(db=db_session, connection_id=conn.id)
    seed_collection_sets(db=db_session, connection_id=conn.id)

    count = db_session.query(PlexCollectionSet).filter(
        PlexCollectionSet.connection_id == conn.id
    ).count()
    assert count == 3
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_plex_collection_set_seeder.py -v
```

- [ ] **Step 3: Implement the seeder**

```python
# app/domain/plex/collection_set_seeder.py
"""Seed default PlexCollectionSet rows for a connection."""

import logging

from sqlalchemy.orm import Session

from app.domain.plex.collection_models import PlexCollectionSet, SetType

logger = logging.getLogger(__name__)

_DEFAULT_SET_TYPES = [SetType.FRANCHISE, SetType.GENRE, SetType.DECADE]


def seed_collection_sets(db: Session, connection_id: int) -> None:
    """Create PlexCollectionSet rows for all default set types if not present.

    Safe to call on every startup — skips types that already exist.
    """
    existing = {
        row.set_type
        for row in db.query(PlexCollectionSet.set_type).filter(
            PlexCollectionSet.connection_id == connection_id
        ).all()
    }
    for set_type in _DEFAULT_SET_TYPES:
        if set_type not in existing:
            db.add(PlexCollectionSet(connection_id=connection_id, set_type=set_type, enabled=True))
            logger.info("Seeded CollectionSet type=%s for connection_id=%s", set_type, connection_id)
    db.commit()
```

- [ ] **Step 4: Call seeder in `app/main.py` lifespan**

In `app/main.py`, import the seeder and add a call after `_seed_plex_connection`:

```python
from app.domain.plex.collection_set_seeder import seed_collection_sets
```

Inside the lifespan function, after `_seed_plex_connection(db)`:

```python
from app.domain.plex.models import PlexConnection as _PlexConn
_active_conn = db.query(_PlexConn).filter(_PlexConn.is_active.is_(True)).first()
if _active_conn:
    seed_collection_sets(db=db, connection_id=_active_conn.id)
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_plex_collection_set_seeder.py -v
```

- [ ] **Step 6: Commit**

```bash
git add app/domain/plex/collection_set_seeder.py app/main.py \
        tests/test_plex_collection_set_seeder.py
git commit -m "feat(plex): seed default collection sets (franchise, genre, decade) on startup"
```

---

### Task 17: Builder resolver extensions — genre and decade

**Files:**
- Modify: `app/domain/plex/collection_builder.py`
- Test: `tests/test_plex_collection_builder.py`

**Background:** `genres` on `Movie` and `TVShow` is a JSON-encoded string (e.g., `'["Action", "Adventure"]'`). Parse with `json.loads`. `decade` is derived from `Movie.year`: decade 2000 matches years 2000–2009. Both resolvers return `ResolvedItem` lists using the same `_get_synced_record` helper already on `BuilderResolver`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_plex_collection_builder.py`:

```python
@pytest.mark.unit
def test_resolve_genre_returns_empty_when_no_movies(db_session):
    from app.domain.plex.collection_builder import BuilderResolver
    resolver = BuilderResolver(db=db_session, connection_id=1)
    result = resolver.resolve_genre({"genre": "Action"})
    assert result == []


@pytest.mark.unit
def test_resolve_decade_returns_empty_when_no_movies(db_session):
    from app.domain.plex.collection_builder import BuilderResolver
    resolver = BuilderResolver(db=db_session, connection_id=1)
    result = resolver.resolve_decade({"decade": 2000})
    assert result == []
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_plex_collection_builder.py -v
```

- [ ] **Step 3: Implement the new resolver methods**

In `app/domain/plex/collection_builder.py`, add `import json` at the top and add to `BuilderResolver`:

```python
def resolve_genre(self, config: Dict[str, Any]) -> List[ResolvedItem]:
    """Return synced movies and TV shows matching the given genre."""
    genre = config["genre"]
    results: List[ResolvedItem] = []
    results.extend(self._resolve_genre_for_model(genre, Movie, "movie"))
    results.extend(self._resolve_genre_for_model(genre, TVShow, "tv_show"))
    return results

def resolve_decade(self, config: Dict[str, Any]) -> List[ResolvedItem]:
    """Return synced movies from the given decade (e.g. decade=2000 → 2000–2009)."""
    decade = int(config["decade"])
    movies = (
        self._db.query(Movie)
        .filter(Movie.year >= decade, Movie.year < decade + 10)
        .all()
    )
    results: List[ResolvedItem] = []
    for movie in movies:
        record = self._get_synced_record(item_type="movie", item_id=movie.id)
        if record and record.plex_rating_key:
            results.append(ResolvedItem(
                plex_rating_key=record.plex_rating_key,
                item_type="movie",
                item_id=movie.id,
            ))
    return results

def _resolve_genre_for_model(
    self, genre: str, model: type, item_type: str
) -> List[ResolvedItem]:
    items = self._db.query(model).filter(model.genres.isnot(None)).all()
    results: List[ResolvedItem] = []
    for item in items:
        try:
            genres = json.loads(item.genres or "[]")
        except (ValueError, TypeError):
            continue
        if genre not in genres:
            continue
        record = self._get_synced_record(item_type=item_type, item_id=item.id)
        if record and record.plex_rating_key:
            results.append(ResolvedItem(
                plex_rating_key=record.plex_rating_key,
                item_type=item_type,
                item_id=item.id,
            ))
    return results
```

Also update `resolve_static_items` to route correctly — and update the service's `_resolve` method to handle the new builder types. In `app/domain/plex/collection_service.py`, update `_resolve`:

```python
def _resolve(self, collection: PlexCollection) -> List[ResolvedItem]:
    config = collection.builder_config
    if collection.builder_type == BuilderType.TMDB_COLLECTION:
        return self._resolver.resolve_tmdb_collection(config)
    if collection.builder_type == BuilderType.GENRE:
        return self._resolver.resolve_genre(config)
    if collection.builder_type == BuilderType.DECADE:
        return self._resolver.resolve_decade(config)
    return self._resolver.resolve_static_items(config)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_plex_collection_builder.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/domain/plex/collection_builder.py app/domain/plex/collection_service.py \
        tests/test_plex_collection_builder.py
git commit -m "feat(plex): add genre and decade builder resolvers"
```

---

### Task 18: DefaultCollectionManager — auto-discover and generate

**Files:**
- Create: `app/domain/plex/default_collection_manager.py`
- Test: `tests/test_plex_default_collection_manager.py`

**Background:** `DefaultCollectionManager` reads the enabled `PlexCollectionSet` rows and auto-generates `PlexCollection` rows for each enabled set type. It never deletes user-created collections — only creates or updates rows where `is_default=True` and `set_type` matches.

- `franchise`: query all distinct `(tmdb_collection_id, tmdb_collection_name)` pairs from Movie where `tmdb_collection_id IS NOT NULL`. Create one `PlexCollection` per pair with `builder_type=TMDB_COLLECTION`, `builder_config={"tmdb_collection_id": "..."}`.

- `genre`: query all distinct genre values from Movie.genres and TVShow.genres (parse JSON strings). Create one `PlexCollection` per genre with `builder_type=GENRE`, `builder_config={"genre": "Action"}`.

- `decade`: query all distinct decades from Movie.year. Create one `PlexCollection` per decade with `builder_type=DECADE`, `builder_config={"decade": 2000}`.

In all cases, upsert by `(connection_id, builder_type, builder_config)` — do not create duplicates.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_plex_default_collection_manager.py
import pytest
from app.domain.plex.default_collection_manager import DefaultCollectionManager
from app.domain.plex.collection_models import PlexCollection, BuilderType
from app.domain.plex.models import PlexConnection
from app.domain.movies.models import Movie


@pytest.mark.integration
def test_discover_franchise_creates_collection(db_session):
    conn = PlexConnection(server_url="http://plex", token="t", is_active=True)
    db_session.add(conn)
    movie = Movie(
        title="The Matrix",
        year=1999,
        tmdb_collection_id="2344",
        tmdb_collection_name="The Matrix Collection",
        enrichment_status="fully_enriched",
    )
    db_session.add(movie)
    db_session.flush()

    mgr = DefaultCollectionManager(db=db_session, connection_id=conn.id)
    mgr.discover_franchises()

    colls = db_session.query(PlexCollection).filter(
        PlexCollection.connection_id == conn.id,
        PlexCollection.builder_type == BuilderType.TMDB_COLLECTION,
        PlexCollection.is_default.is_(True),
    ).all()
    assert any(c.name == "The Matrix Collection" for c in colls)


@pytest.mark.integration
def test_discover_franchise_is_idempotent(db_session):
    conn = PlexConnection(server_url="http://plex", token="t", is_active=True)
    db_session.add(conn)
    movie = Movie(
        title="The Matrix",
        year=1999,
        tmdb_collection_id="2344",
        tmdb_collection_name="The Matrix Collection",
        enrichment_status="fully_enriched",
    )
    db_session.add(movie)
    db_session.flush()

    mgr = DefaultCollectionManager(db=db_session, connection_id=conn.id)
    mgr.discover_franchises()
    mgr.discover_franchises()

    count = db_session.query(PlexCollection).filter(
        PlexCollection.connection_id == conn.id,
        PlexCollection.is_default.is_(True),
    ).count()
    assert count == 1


@pytest.mark.integration
def test_discover_decades_creates_collection(db_session):
    conn = PlexConnection(server_url="http://plex", token="t", is_active=True)
    db_session.add(conn)
    db_session.add(Movie(title="Old Film", year=1985, enrichment_status="fully_enriched"))
    db_session.flush()

    mgr = DefaultCollectionManager(db=db_session, connection_id=conn.id)
    mgr.discover_decades()

    colls = db_session.query(PlexCollection).filter(
        PlexCollection.connection_id == conn.id,
        PlexCollection.builder_type == BuilderType.DECADE,
    ).all()
    assert any(c.name == "1980s" for c in colls)
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_plex_default_collection_manager.py -v
```

- [ ] **Step 3: Implement `DefaultCollectionManager`**

```python
# app/domain/plex/default_collection_manager.py
"""Auto-generate PlexCollection rows from library metadata."""

from __future__ import annotations

import json
import logging
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.domain.movies.models import Movie
from app.domain.plex.collection_models import BuilderType, PlexCollection
from app.domain.tv_shows.models import TVShow

logger = logging.getLogger(__name__)


class DefaultCollectionManager:
    def __init__(self, db: Session, connection_id: int):
        self._db = db
        self._connection_id = connection_id

    def discover_franchises(self) -> int:
        """Create default collections for each TMDB franchise found in library."""
        rows = (
            self._db.query(Movie.tmdb_collection_id, Movie.tmdb_collection_name)
            .filter(Movie.tmdb_collection_id.isnot(None))
            .distinct()
            .all()
        )
        created = 0
        for tmdb_coll_id, tmdb_coll_name in rows:
            name = tmdb_coll_name or f"Collection {tmdb_coll_id}"
            config = {"tmdb_collection_id": tmdb_coll_id}
            if not self._exists(BuilderType.TMDB_COLLECTION, config):
                self._create(name=name, builder_type=BuilderType.TMDB_COLLECTION, config=config)
                created += 1
        self._db.commit()
        logger.info("Franchise discovery: created %d new collection(s)", created)
        return created

    def discover_genres(self) -> int:
        """Create default collections for each genre found in library."""
        genres = self._collect_genres()
        created = 0
        for genre in sorted(genres):
            config = {"genre": genre}
            if not self._exists(BuilderType.GENRE, config):
                self._create(name=genre, builder_type=BuilderType.GENRE, config=config)
                created += 1
        self._db.commit()
        logger.info("Genre discovery: created %d new collection(s)", created)
        return created

    def discover_decades(self) -> int:
        """Create default collections for each decade represented in movie library."""
        decades = self._collect_decades()
        created = 0
        for decade in sorted(decades):
            name = f"{decade}s"
            config = {"decade": decade}
            if not self._exists(BuilderType.DECADE, config):
                self._create(name=name, builder_type=BuilderType.DECADE, config=config)
                created += 1
        self._db.commit()
        logger.info("Decade discovery: created %d new collection(s)", created)
        return created

    def _exists(self, builder_type: BuilderType, config: dict) -> bool:
        return (
            self._db.query(PlexCollection)
            .filter(
                PlexCollection.connection_id == self._connection_id,
                PlexCollection.builder_type == builder_type,
                PlexCollection.builder_config == config,
                PlexCollection.is_default.is_(True),
            )
            .first()
        ) is not None

    def _create(self, name: str, builder_type: BuilderType, config: dict) -> None:
        self._db.add(PlexCollection(
            connection_id=self._connection_id,
            name=name,
            builder_type=builder_type,
            builder_config=config,
            is_default=True,
            enabled=True,
        ))

    def _collect_genres(self) -> set:
        genres: set = set()
        for model in (Movie, TVShow):
            rows = self._db.query(model.genres).filter(model.genres.isnot(None)).all()
            for (raw,) in rows:
                try:
                    genres.update(json.loads(raw or "[]"))
                except (ValueError, TypeError):
                    pass
        return genres

    def _collect_decades(self) -> List[int]:
        rows = (
            self._db.query(Movie.year)
            .filter(Movie.year.isnot(None))
            .distinct()
            .all()
        )
        return list({(year // 10) * 10 for (year,) in rows if year})
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_plex_default_collection_manager.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/domain/plex/default_collection_manager.py \
        tests/test_plex_default_collection_manager.py
git commit -m "feat(plex): add DefaultCollectionManager for franchise/genre/decade auto-discovery"
```

---

### Task 19: Update push sync to respect `enabled` and add discovery task

**Files:**
- Modify: `app/tasks/plex_collections.py`
- Modify: `app/domain/plex/collection_service.py`
- Test: `tests/test_plex_collection_tasks.py`

**Background:** Two changes:

1. `push_all_collections` must filter by `enabled=True`. Disabled collections are not pushed.

2. New task `run_collection_discovery(connection_id)` runs all three discovery methods for enabled `PlexCollectionSet` rows, then immediately calls `push_all_collections`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_plex_collection_tasks.py`:

```python
@pytest.mark.unit
def test_push_all_collections_only_pushes_enabled():
    """Verify the query filter includes enabled=True."""
    with patch("app.tasks.plex_collections.get_db") as mock_db, \
         patch("app.tasks.plex_collections.get_or_cache_library_ids") as mock_libs, \
         patch("app.tasks.plex_collections._make_clients") as mock_clients, \
         patch("app.tasks.plex_collections.BuilderResolver"), \
         patch("app.tasks.plex_collections.PlexCollectionService") as mock_svc_cls:

        session = MagicMock()
        conn = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = conn
        session.query.return_value.filter.return_value.all.return_value = []
        mock_db.return_value = iter([session])
        mock_libs.return_value = ("1", "2")
        mock_clients.return_value = (MagicMock(), "mid", MagicMock(), MagicMock())
        mock_svc_cls.return_value = MagicMock()

        from app.tasks.plex_collections import push_all_collections
        push_all_collections(connection_id=1)

        # Verify that .filter was called (i.e., query was filtered — exact filter tested in service tests)
        session.query.assert_called()
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_plex_collection_tasks.py -v
```

- [ ] **Step 3: Update `push_all_collections` in `app/tasks/plex_collections.py`**

Change the query from:

```python
colls = db.query(PlexCollection).filter(PlexCollection.connection_id == connection_id).all()
```

To:

```python
colls = (
    db.query(PlexCollection)
    .filter(
        PlexCollection.connection_id == connection_id,
        PlexCollection.enabled.is_(True),
    )
    .all()
)
```

- [ ] **Step 4: Add `run_collection_discovery` task**

Append to `app/tasks/plex_collections.py`:

```python
from app.domain.plex.collection_models import PlexCollectionSet, SetType
from app.domain.plex.default_collection_manager import DefaultCollectionManager


@celery_app.task(
    name="app.tasks.plex_collections.run_collection_discovery",
    queue="external_api",
)
def run_collection_discovery(connection_id: int) -> None:
    """Discover franchises/genres/decades for enabled sets, then push to Plex."""
    db = next(get_db())
    try:
        conn = db.query(PlexConnection).filter(PlexConnection.id == connection_id).first()
        if conn is None:
            logger.warning("run_collection_discovery: connection %s not found", connection_id)
            return
        mgr = DefaultCollectionManager(db=db, connection_id=connection_id)
        enabled_sets = (
            db.query(PlexCollectionSet)
            .filter(
                PlexCollectionSet.connection_id == connection_id,
                PlexCollectionSet.enabled.is_(True),
            )
            .all()
        )
        for coll_set in enabled_sets:
            _run_discovery_for_set(mgr, coll_set.set_type)
            coll_set.last_run_at = __import__("datetime").datetime.utcnow()
        db.commit()
    finally:
        db.close()
    push_all_collections.delay(connection_id)


def _run_discovery_for_set(mgr: DefaultCollectionManager, set_type: str) -> None:
    if set_type == SetType.FRANCHISE:
        mgr.discover_franchises()
    elif set_type == SetType.GENRE:
        mgr.discover_genres()
    elif set_type == SetType.DECADE:
        mgr.discover_decades()
```

- [ ] **Step 5: Run all task tests**

```bash
pytest tests/test_plex_collection_tasks.py -v
```

- [ ] **Step 6: Commit**

```bash
git add app/tasks/plex_collections.py tests/test_plex_collection_tasks.py
git commit -m "feat(plex): filter disabled collections from push, add discovery Celery task"
```

---

### Task 20: API endpoints — collection set toggle + discovery trigger

**Files:**
- Modify: `app/api/v1/plex/collection_router.py`
- Modify: `app/api/v1/plex/collection_schemas.py`
- Test: `tests/test_plex_collection_api.py`

**Background:** New endpoints:
- `GET /plex/collections/sets` — list all `PlexCollectionSet` rows for the active connection (returns set_type, enabled, last_run_at)
- `PATCH /plex/collections/sets/{set_type}` — toggle `enabled` on a set
- `POST /plex/collections/discover` — trigger `run_collection_discovery` task (202)
- `PATCH /plex/collections/{id}` — toggle `enabled` on an individual collection

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_plex_collection_api.py`:

```python
@pytest.mark.integration
def test_list_collection_sets(auth_client: TestClient, plex_connection):
    """Sets are seeded at connection creation — list should return 3 rows."""
    from app.domain.plex.collection_set_seeder import seed_collection_sets
    from app.core.database import SessionLocal
    db = SessionLocal()
    seed_collection_sets(db=db, connection_id=plex_connection.id)
    db.close()

    r = auth_client.get("/api/v1/plex/collections/sets")
    assert r.status_code == 200
    assert len(r.json()) == 3


@pytest.mark.integration
def test_toggle_collection_set(auth_client: TestClient, plex_connection):
    from app.domain.plex.collection_set_seeder import seed_collection_sets
    from app.core.database import SessionLocal
    db = SessionLocal()
    seed_collection_sets(db=db, connection_id=plex_connection.id)
    db.close()

    r = auth_client.patch(
        "/api/v1/plex/collections/sets/genre",
        json={"enabled": False},
    )
    assert r.status_code == 200
    assert r.json()["enabled"] is False


@pytest.mark.integration
def test_toggle_individual_collection_enabled(auth_client: TestClient, plex_connection):
    payload = {
        "name": "Toggleable",
        "builder": {"builder_type": "static_items", "items": []},
    }
    create_r = auth_client.post("/api/v1/plex/collections/", json=payload)
    coll_id = create_r.json()["id"]

    r = auth_client.patch(f"/api/v1/plex/collections/{coll_id}", json={"enabled": False})
    assert r.status_code == 200
    assert r.json()["enabled"] is False
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_plex_collection_api.py -k "set" -v
```

- [ ] **Step 3: Add schemas for set responses**

Append to `app/api/v1/plex/collection_schemas.py`:

```python
from datetime import datetime as _dt

class CollectionSetResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    set_type: str
    enabled: bool
    last_run_at: Optional[_dt]


class CollectionSetToggle(BaseModel):
    enabled: bool


class CollectionToggle(BaseModel):
    enabled: bool
```

- [ ] **Step 4: Add endpoints to `collection_router.py`**

Add imports at the top of `app/api/v1/plex/collection_router.py`:

```python
from app.api.v1.plex.collection_schemas import (
    ...,  # existing imports
    CollectionSetResponse,
    CollectionSetToggle,
    CollectionToggle,
)
from app.domain.plex.collection_models import PlexCollectionSet
from app.tasks.plex_collections import run_collection_discovery
```

Add after existing collection endpoints:

```python
@router.get("/sets", response_model=List[CollectionSetResponse])
def list_sets(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    conn = _get_active_connection(db)
    return db.query(PlexCollectionSet).filter(
        PlexCollectionSet.connection_id == conn.id
    ).all()


@router.patch("/sets/{set_type}", response_model=CollectionSetResponse)
def toggle_set(
    set_type: str,
    payload: CollectionSetToggle,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    conn = _get_active_connection(db)
    coll_set = db.query(PlexCollectionSet).filter(
        PlexCollectionSet.connection_id == conn.id,
        PlexCollectionSet.set_type == set_type,
    ).first()
    if coll_set is None:
        raise HTTPException(status_code=404, detail="Collection set not found")
    coll_set.enabled = payload.enabled
    db.commit()
    db.refresh(coll_set)
    return coll_set


@router.patch("/{collection_id}", response_model=CollectionResponse)
def toggle_collection(
    collection_id: int,
    payload: CollectionToggle,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    coll = db.query(PlexCollection).filter(PlexCollection.id == collection_id).first()
    if coll is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    coll.enabled = payload.enabled
    db.commit()
    db.refresh(coll)
    return coll


@router.post("/discover", response_model=SyncTriggered, status_code=202)
def trigger_discovery(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    conn = _get_active_connection(db)
    task = run_collection_discovery.delay(conn.id)
    return SyncTriggered(task_id=task.id, message="Collection discovery dispatched")
```

- [ ] **Step 5: Run API tests**

```bash
pytest tests/test_plex_collection_api.py -v
```
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add app/api/v1/plex/collection_router.py app/api/v1/plex/collection_schemas.py \
        tests/test_plex_collection_api.py
git commit -m "feat(plex): add collection set toggle API and per-collection enabled toggle"
```

---

### Task 21: Frontend — Default Collections toggle panel

**Files:**
- Create: `frontend/src/components/features/plex/CollectionSetToggles.tsx`
- Modify: `frontend/src/stores/plexCollectionStore.ts`
- Modify: `frontend/src/services/plexCollectionService.ts`
- Modify: `frontend/src/pages/PlexCollectionsPage.tsx`

**Background:** A new panel above the collections list shows the three default collection sets (Franchise, Genre, Decade) as toggle switches. Toggling one calls `PATCH /plex/collections/sets/{set_type}`. A "Discover" button triggers `POST /plex/collections/discover`. Individual collection cards get an enable/disable toggle (replacing the binary delete-only UX).

- [ ] **Step 1: Add service functions**

Append to `frontend/src/services/plexCollectionService.ts`:

```typescript
export interface CollectionSetResponse {
  id: number;
  set_type: string;
  enabled: boolean;
  last_run_at: string | null;
}

export async function listCollectionSets(): Promise<CollectionSetResponse[]> {
  const { data } = await axios.get<CollectionSetResponse[]>(`${BASE}/collections/sets`);
  return data;
}

export async function toggleCollectionSet(
  set_type: string,
  enabled: boolean
): Promise<CollectionSetResponse> {
  const { data } = await axios.patch<CollectionSetResponse>(
    `${BASE}/collections/sets/${set_type}`,
    { enabled }
  );
  return data;
}

export async function toggleCollection(
  id: number,
  enabled: boolean
): Promise<CollectionResponse> {
  const { data } = await axios.patch<CollectionResponse>(
    `${BASE}/collections/${id}`,
    { enabled }
  );
  return data;
}

export async function triggerDiscovery(): Promise<SyncTriggered> {
  const { data } = await axios.post<SyncTriggered>(`${BASE}/collections/discover`);
  return data;
}
```

- [ ] **Step 2: Update the store**

In `frontend/src/stores/plexCollectionStore.ts`, add state and actions:

```typescript
// Add to interface:
sets: CollectionSetResponse[];
fetchSets: () => Promise<void>;
toggleSet: (set_type: string, enabled: boolean) => Promise<void>;
toggleCollectionEnabled: (id: number, enabled: boolean) => Promise<void>;
discover: () => Promise<void>;

// Add to initial state:
sets: [],

// Add implementations:
fetchSets: async () => {
  const sets = await listCollectionSets();
  set({ sets });
},

toggleSet: async (set_type, enabled) => {
  const updated = await toggleCollectionSet(set_type, enabled);
  set((s) => ({
    sets: s.sets.map((st) => (st.set_type === set_type ? updated : st)),
  }));
},

toggleCollectionEnabled: async (id, enabled) => {
  const updated = await toggleCollection(id, enabled);
  set((s) => ({
    collections: s.collections.map((c) => (c.id === id ? updated : c)),
  }));
},

discover: async () => {
  set({ error: null });
  try {
    await triggerDiscovery();
  } catch (e: unknown) {
    set({ error: String(e) });
  }
},
```

Import the new service functions at the top of the store file.

- [ ] **Step 3: Implement `CollectionSetToggles` component**

```tsx
// frontend/src/components/features/plex/CollectionSetToggles.tsx
import React from 'react';
import { CollectionSetResponse } from '../../../services/plexCollectionService';

const SET_LABELS: Record<string, string> = {
  franchise: 'Franchise Collections',
  genre: 'Genre Collections',
  decade: 'Decade Collections',
};

const SET_DESCRIPTIONS: Record<string, string> = {
  franchise: 'One collection per TMDB franchise found in your library (e.g. "The Matrix Collection")',
  genre: 'One collection per genre tag across movies and TV shows',
  decade: 'One collection per decade represented in your movie library',
};

interface Props {
  sets: CollectionSetResponse[];
  onToggle: (set_type: string, enabled: boolean) => void;
  onDiscover: () => void;
}

export function CollectionSetToggles({ sets, onToggle, onDiscover }: Props) {
  return (
    <div className="card border rounded p-4 mb-6">
      <div className="flex justify-between items-center mb-3">
        <h2 className="font-semibold text-lg">Default Collection Sets</h2>
        <button onClick={onDiscover} className="btn btn-sm btn-secondary">
          Run Discovery
        </button>
      </div>
      <p className="text-sm text-gray-500 mb-4">
        Enable a set to auto-generate collections from your library metadata.
        Discovery runs the enabled sets and pushes results to Plex.
      </p>
      <div className="space-y-3">
        {sets.map((s) => (
          <div key={s.set_type} className="flex items-start gap-3">
            <input
              type="checkbox"
              id={`set-${s.set_type}`}
              checked={s.enabled}
              onChange={(e) => onToggle(s.set_type, e.target.checked)}
              className="checkbox mt-1"
            />
            <label htmlFor={`set-${s.set_type}`} className="cursor-pointer">
              <div className="font-medium">{SET_LABELS[s.set_type] ?? s.set_type}</div>
              <div className="text-xs text-gray-400">
                {SET_DESCRIPTIONS[s.set_type]}
                {s.last_run_at && (
                  <span className="ml-2">
                    Last run: {new Date(s.last_run_at).toLocaleString()}
                  </span>
                )}
              </div>
            </label>
          </div>
        ))}
        {sets.length === 0 && (
          <p className="text-gray-400 text-sm">No sets found — connect Plex to see defaults.</p>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Update `CollectionCard` to include enable/disable toggle**

In `frontend/src/components/features/plex/CollectionCard.tsx`, add an enabled toggle alongside the delete button:

```tsx
interface Props {
  collection: CollectionResponse;
  onDelete: (id: number) => void;
  onToggleEnabled: (id: number, enabled: boolean) => void;  // new
}

// Inside the component, add next to the delete button:
<input
  type="checkbox"
  checked={collection.enabled !== false}
  onChange={(e) => onToggleEnabled(collection.id, e.target.checked)}
  className="checkbox"
  title={collection.enabled !== false ? 'Disable (skip on push)' : 'Enable'}
/>
```

- [ ] **Step 5: Update `PlexCollectionsPage` to wire everything together**

In `frontend/src/pages/PlexCollectionsPage.tsx`:

- Import `CollectionSetToggles` and `usePlexCollectionStore` additions
- Call `fetchSets()` in the `useEffect` alongside `fetchCollections`
- Render `<CollectionSetToggles>` above the tabs
- Pass `onToggleEnabled` to `<CollectionCard>`

```tsx
// Add to useEffect:
fetchSets();

// Add to destructured store:
sets, fetchSets, toggleSet, toggleCollectionEnabled, discover,

// Add above the tabs div:
<CollectionSetToggles
  sets={sets}
  onToggle={toggleSet}
  onDiscover={discover}
/>

// Update CollectionCard usage:
<CollectionCard
  key={c.id}
  collection={c}
  onDelete={removeCollection}
  onToggleEnabled={toggleCollectionEnabled}
/>
```

- [ ] **Step 6: Run frontend checks**

```bash
cd frontend && npm run type-check && npm run lint && npm run test
```
Fix any errors before committing.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/services/plexCollectionService.ts \
        frontend/src/stores/plexCollectionStore.ts \
        frontend/src/components/features/plex/CollectionSetToggles.tsx \
        frontend/src/components/features/plex/CollectionCard.tsx \
        frontend/src/pages/PlexCollectionsPage.tsx
git commit -m "feat(plex): add default collection set toggles and per-collection enable/disable UI"
```

---

## Final verification

- [ ] **Run all backend tests**

```bash
pytest tests/ --tb=short -q
```

- [ ] **Run full backend lint**

```bash
black app/ tests/ && isort app/ tests/ && flake8 app/ tests/ && mypy app/
```

- [ ] **Run all frontend tests**

```bash
cd frontend && npm run test && npm run type-check && npm run lint
```

- [ ] **Verify migration applies cleanly from scratch**

```bash
alembic downgrade base && alembic upgrade head
```

- [ ] **Stage all changes for review**

```bash
git status
```

---

## Key design notes for the implementer

1. **`tmdb_collection_id` on Movie**: Verify the column name with `grep -n tmdb_collection app/domain/movies/models.py` before implementing the builder resolver. Adjust `resolve_tmdb_collection` accordingly.

2. **Section ID for collection creation**: `create_collection` uses `movie_section_id` as the default section. Collections that contain only TV shows would need `tv_section_id`. For now, the service always uses `movie_section_id`; this can be refined once item types are tracked.

3. **Pull sync item type**: When pulling collections from Plex, `PlexCollectionItem.item_type` is set to `"movie"` as a placeholder. A proper implementation would cross-reference `PlexSyncRecord` by `plex_rating_key` to determine the true type.

4. **YAML export only (no import)**: Import from YAML is out of scope — users define collections via the API/UI and export to YAML for reference. Adding a `POST /collections/import` endpoint that accepts YAML text is a natural follow-on.

5. **`plex_connection` test fixture**: If `tests/conftest.py` doesn't have a `plex_connection` fixture, add one that creates a `PlexConnection` row using the test DB session.
