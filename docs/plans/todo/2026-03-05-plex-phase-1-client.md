# Plex Integration — Phase 1: HTTP Client & Auth

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the raw Plex HTTP client and OAuth/token auth layer under `app/infrastructure/external_apis/plex/`.

**Architecture:** Thin HTTP wrapper over the Plex API using `httpx`. Auth supports OAuth pin flow (primary) and manual `X-Plex-Token` (fallback). All requests log at INFO to the standard logger (visible in Celery worker console).

**Tech Stack:** Python, httpx, pydantic, pytest, respx (HTTP mocking)

---

### Task 1: Plex API response schemas

**Files:**
- Create: `app/infrastructure/external_apis/plex/__init__.py`
- Create: `app/infrastructure/external_apis/plex/schemas.py`
- Create: `tests/test_plex_client.py`

**Step 1: Create the package init**

```python
# app/infrastructure/external_apis/plex/__init__.py
```

**Step 2: Write failing tests for schemas**

```python
# tests/test_plex_client.py
import pytest
from app.infrastructure.external_apis.plex.schemas import (
    PlexLibrarySection,
    PlexLibrarySectionsResponse,
    PlexMediaItem,
    PlexMediaListResponse,
)


def test_plex_library_section_parses():
    data = {"key": "1", "title": "Movies", "type": "movie"}
    section = PlexLibrarySection(**data)
    assert section.key == "1"
    assert section.title == "Movies"
    assert section.type == "movie"


def test_plex_media_item_parses_with_guid():
    data = {
        "ratingKey": "123",
        "title": "The Matrix",
        "year": 1999,
        "viewCount": 2,
        "lastViewedAt": 1700000000,
        "Guid": [{"id": "tmdb://603"}],
    }
    item = PlexMediaItem(**data)
    assert item.rating_key == "123"
    assert item.tmdb_id == "603"
    assert item.view_count == 2


def test_plex_media_item_missing_guid_returns_none():
    data = {"ratingKey": "456", "title": "Unknown", "Guid": []}
    item = PlexMediaItem(**data)
    assert item.tmdb_id is None
```

**Step 3: Run tests to verify they fail**

```bash
pytest tests/test_plex_client.py -v
```
Expected: `ImportError` — module not found.

**Step 4: Implement schemas**

```python
# app/infrastructure/external_apis/plex/schemas.py
"""Pydantic models for Plex API responses"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PlexGuid(BaseModel):
    id: str  # e.g. "tmdb://603" or "imdb://tt0133093"


class PlexLibrarySection(BaseModel):
    key: str
    title: str
    type: str  # "movie" or "show"


class PlexLibrarySectionsResponse(BaseModel):
    sections: List[PlexLibrarySection] = Field(default_factory=list)


class PlexMediaItem(BaseModel):
    rating_key: str = Field(alias="ratingKey")
    title: str
    year: Optional[int] = None
    view_count: int = Field(alias="viewCount", default=0)
    last_viewed_at: Optional[int] = Field(alias="lastViewedAt", default=None)
    guids: List[PlexGuid] = Field(alias="Guid", default_factory=list)

    model_config = {"populate_by_name": True}

    @property
    def tmdb_id(self) -> Optional[str]:
        for guid in self.guids:
            if guid.id.startswith("tmdb://"):
                return guid.id.removeprefix("tmdb://")
        return None


class PlexMediaListResponse(BaseModel):
    items: List[PlexMediaItem] = Field(default_factory=list)
```

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_plex_client.py -v
```
Expected: 4 PASSED.

**Step 6: Commit**

```bash
git add app/infrastructure/external_apis/plex/ tests/test_plex_client.py
git commit -m "feat(plex): add Plex API response schemas"
```

---

### Task 2: Plex HTTP client

**Files:**
- Create: `app/infrastructure/external_apis/plex/client.py`
- Modify: `tests/test_plex_client.py`

**Step 1: Write failing tests**

```python
# append to tests/test_plex_client.py
import respx
import httpx
from app.infrastructure.external_apis.plex.client import PlexClient


@respx.mock
def test_get_library_sections_returns_sections():
    respx.get("http://plex:32400/library/sections").mock(
        return_value=httpx.Response(
            200,
            json={
                "MediaContainer": {
                    "Directory": [
                        {"key": "1", "title": "Movies", "type": "movie"},
                        {"key": "2", "title": "TV Shows", "type": "show"},
                    ]
                }
            },
        )
    )
    client = PlexClient(server_url="http://plex:32400", token="fake-token")
    sections = client.get_library_sections()
    assert len(sections) == 2
    assert sections[0].title == "Movies"


@respx.mock
def test_refresh_library_section_calls_correct_url():
    respx.get("http://plex:32400/library/sections/1/refresh").mock(
        return_value=httpx.Response(200)
    )
    client = PlexClient(server_url="http://plex:32400", token="fake-token")
    client.refresh_library_section(section_id="1")  # should not raise


@respx.mock
def test_find_item_by_tmdb_id_returns_rating_key():
    respx.get("http://plex:32400/library/sections/1/all").mock(
        return_value=httpx.Response(
            200,
            json={
                "MediaContainer": {
                    "Metadata": [
                        {
                            "ratingKey": "99",
                            "title": "The Matrix",
                            "Guid": [{"id": "tmdb://603"}],
                        }
                    ]
                }
            },
        )
    )
    client = PlexClient(server_url="http://plex:32400", token="fake-token")
    key = client.find_rating_key_by_tmdb_id(section_id="1", tmdb_id="603")
    assert key == "99"


@respx.mock
def test_find_item_by_tmdb_id_returns_none_when_not_found():
    respx.get("http://plex:32400/library/sections/1/all").mock(
        return_value=httpx.Response(
            200,
            json={"MediaContainer": {"Metadata": []}},
        )
    )
    client = PlexClient(server_url="http://plex:32400", token="fake-token")
    key = client.find_rating_key_by_tmdb_id(section_id="1", tmdb_id="999")
    assert key is None


@respx.mock
def test_get_all_items_with_watch_status():
    respx.get("http://plex:32400/library/sections/1/all").mock(
        return_value=httpx.Response(
            200,
            json={
                "MediaContainer": {
                    "Metadata": [
                        {
                            "ratingKey": "1",
                            "title": "Movie A",
                            "viewCount": 3,
                            "lastViewedAt": 1700000000,
                            "Guid": [{"id": "tmdb://100"}],
                        }
                    ]
                }
            },
        )
    )
    client = PlexClient(server_url="http://plex:32400", token="fake-token")
    items = client.get_all_items(section_id="1", media_type=1)
    assert items[0].view_count == 3
    assert items[0].tmdb_id == "100"
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_plex_client.py -v -k "test_get_library"
```
Expected: `ImportError`

**Step 3: Install respx if not present**

```bash
pip show respx || pip install respx
echo "respx" >> requirements.txt
```

**Step 4: Implement client**

```python
# app/infrastructure/external_apis/plex/client.py
"""Plex Media Server HTTP API client"""

import logging
from typing import List, Optional

import httpx

from app.infrastructure.external_apis.plex.schemas import (
    PlexLibrarySection,
    PlexMediaItem,
)

logger = logging.getLogger(__name__)

_PLEX_HEADERS = {
    "Accept": "application/json",
    "X-Plex-Client-Identifier": "metamaster",
    "X-Plex-Product": "MetaMaster",
}


class PlexClient:
    """Raw HTTP client for the Plex Media Server API"""

    def __init__(self, server_url: str, token: str):
        self._base = server_url.rstrip("/")
        self._token = token

    def _headers(self) -> dict:
        return {**_PLEX_HEADERS, "X-Plex-Token": self._token}

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self._base}{path}"
        logger.info("Plex API GET %s params=%s", url, params)
        with httpx.Client(timeout=10) as client:
            response = client.get(url, headers=self._headers(), params=params)
        logger.info("Plex API response %s %s", url, response.status_code)
        response.raise_for_status()
        return response.json()

    def get_library_sections(self) -> List[PlexLibrarySection]:
        data = self._get("/library/sections")
        directories = data.get("MediaContainer", {}).get("Directory", [])
        return [PlexLibrarySection(**d) for d in directories]

    def refresh_library_section(self, section_id: str) -> None:
        self._get(f"/library/sections/{section_id}/refresh")

    def find_rating_key_by_tmdb_id(
        self, section_id: str, tmdb_id: str
    ) -> Optional[str]:
        items = self.get_all_items(section_id=section_id, media_type=1)
        for item in items:
            if item.tmdb_id == tmdb_id:
                return item.rating_key
        return None

    def get_all_items(
        self, section_id: str, media_type: int
    ) -> List[PlexMediaItem]:
        data = self._get(
            f"/library/sections/{section_id}/all",
            params={"type": media_type},
        )
        metadata = data.get("MediaContainer", {}).get("Metadata", [])
        return [PlexMediaItem(**m) for m in metadata]
```

**Step 5: Run all client tests**

```bash
pytest tests/test_plex_client.py -v
```
Expected: All PASSED.

**Step 6: Commit**

```bash
git add app/infrastructure/external_apis/plex/client.py tests/test_plex_client.py requirements.txt
git commit -m "feat(plex): add Plex HTTP client with section and item queries"
```

---

### Task 3: Auth module

**Files:**
- Create: `app/infrastructure/external_apis/plex/auth.py`
- Create: `tests/test_plex_auth.py`

**Step 1: Write failing tests**

```python
# tests/test_plex_auth.py
import respx
import httpx
import pytest
from app.infrastructure.external_apis.plex.auth import PlexAuth


@respx.mock
def test_create_pin_returns_pin_id_and_code():
    respx.post("https://plex.tv/api/v2/pins").mock(
        return_value=httpx.Response(201, json={"id": 42, "code": "ABCD1234"})
    )
    auth = PlexAuth()
    pin_id, pin_code = auth.create_pin()
    assert pin_id == 42
    assert pin_code == "ABCD1234"


@respx.mock
def test_poll_pin_returns_token_when_authenticated():
    respx.get("https://plex.tv/api/v2/pins/42").mock(
        return_value=httpx.Response(200, json={"authToken": "my-secret-token"})
    )
    auth = PlexAuth()
    token = auth.poll_pin(pin_id=42)
    assert token == "my-secret-token"


@respx.mock
def test_poll_pin_returns_none_when_pending():
    respx.get("https://plex.tv/api/v2/pins/42").mock(
        return_value=httpx.Response(200, json={"authToken": None})
    )
    auth = PlexAuth()
    token = auth.poll_pin(pin_id=42)
    assert token is None


def test_build_oauth_url_contains_pin_code():
    auth = PlexAuth()
    url = auth.build_oauth_url(pin_code="ABCD1234", redirect_uri="http://localhost/callback")
    assert "ABCD1234" in url
    assert "forwardUrl" in url
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_plex_auth.py -v
```
Expected: `ImportError`

**Step 3: Implement auth**

```python
# app/infrastructure/external_apis/plex/auth.py
"""Plex OAuth pin flow and manual token helpers"""

import logging
from typing import Optional, Tuple
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

_PLEX_TV_BASE = "https://plex.tv/api/v2"
_PLEX_HEADERS = {
    "Accept": "application/json",
    "X-Plex-Client-Identifier": "metamaster",
    "X-Plex-Product": "MetaMaster",
}


class PlexAuth:
    """Handles Plex OAuth pin flow for token acquisition"""

    def create_pin(self) -> Tuple[int, str]:
        """Request a new OAuth pin. Returns (pin_id, pin_code)."""
        logger.info("Plex OAuth: creating pin")
        with httpx.Client(timeout=10) as client:
            response = client.post(
                f"{_PLEX_TV_BASE}/pins",
                headers=_PLEX_HEADERS,
                json={"strong": True},
            )
        response.raise_for_status()
        data = response.json()
        logger.info("Plex OAuth: pin created id=%s", data["id"])
        return data["id"], data["code"]

    def poll_pin(self, pin_id: int) -> Optional[str]:
        """Check if the pin has been authenticated. Returns token or None."""
        logger.info("Plex OAuth: polling pin id=%s", pin_id)
        with httpx.Client(timeout=10) as client:
            response = client.get(
                f"{_PLEX_TV_BASE}/pins/{pin_id}",
                headers=_PLEX_HEADERS,
            )
        response.raise_for_status()
        token = response.json().get("authToken")
        if token:
            logger.info("Plex OAuth: pin %s authenticated", pin_id)
        return token or None

    def build_oauth_url(self, pin_code: str, redirect_uri: str) -> str:
        """Build the plex.tv OAuth redirect URL for the user to visit."""
        params = urlencode({"code": pin_code, "forwardUrl": redirect_uri})
        return f"https://app.plex.tv/auth#?{params}"
```

**Step 4: Run tests**

```bash
pytest tests/test_plex_auth.py -v
```
Expected: All PASSED.

**Step 5: Run full plex test suite**

```bash
pytest tests/test_plex_client.py tests/test_plex_auth.py -v
```
Expected: All PASSED.

**Step 6: Commit**

```bash
git add app/infrastructure/external_apis/plex/auth.py tests/test_plex_auth.py
git commit -m "feat(plex): add Plex OAuth pin flow auth"
```

---

### Task 4: Lint & verify

**Step 1: Run backend linters**

```bash
black app/infrastructure/external_apis/plex/ tests/test_plex_client.py tests/test_plex_auth.py
isort app/infrastructure/external_apis/plex/ tests/test_plex_client.py tests/test_plex_auth.py
flake8 app/infrastructure/external_apis/plex/ tests/test_plex_client.py tests/test_plex_auth.py
mypy app/infrastructure/external_apis/plex/
```
Expected: No errors.

**Step 2: Commit**

```bash
git add -u
git commit -m "style(plex): lint client and auth modules"
```
