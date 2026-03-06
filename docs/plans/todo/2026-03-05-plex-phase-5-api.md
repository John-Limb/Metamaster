# Plex Integration — Phase 5: API Endpoints

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expose Plex connection management, OAuth callback, and manual sync trigger via FastAPI router at `/api/v1/plex/`.

**Architecture:** Follows existing router patterns in `app/api/v1/`. Three endpoint groups: connection config (GET/POST/DELETE), OAuth flow (GET initiate, GET callback), manual sync (POST). Auth required on all endpoints (existing JWT dependency).

**Tech Stack:** FastAPI, pytest, httpx TestClient

**Prerequisite:** Phases 1–4 complete.

---

### Task 1: Router skeleton and connection endpoints

**Files:**
- Create: `app/api/v1/plex/__init__.py`
- Create: `app/api/v1/plex/schemas.py`
- Create: `app/api/v1/plex/router.py`
- Create: `tests/test_plex_api.py`
- Modify: `app/main.py` or `app/api/v1/__init__.py` (router registration — check existing pattern)

**Step 1: Check how existing routers are registered**

```bash
grep -n "include_router" app/main.py | head -20
```

Note the pattern (prefix, tags). Match it for the Plex router.

**Step 2: Write failing tests**

```python
# tests/test_plex_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


def auth_headers():
    # Re-use the auth pattern from existing API tests
    # Check tests/test_api_endpoints_integration.py for how tokens are obtained
    return {"Authorization": "Bearer test-token"}


@patch("app.api.v1.plex.router.get_db")
@patch("app.api.v1.plex.router.get_current_user")
def test_get_connection_returns_404_when_none(mock_user, mock_db):
    mock_user.return_value = MagicMock(id=1)
    mock_db.return_value = iter([MagicMock()])
    response = client.get("/api/v1/plex/connection", headers=auth_headers())
    assert response.status_code == 404


@patch("app.api.v1.plex.router.get_db")
@patch("app.api.v1.plex.router.get_current_user")
def test_post_connection_creates_record(mock_user, mock_db):
    mock_user.return_value = MagicMock(id=1)
    mock_session = MagicMock()
    mock_session.query.return_value.first.return_value = None
    mock_db.return_value = iter([mock_session])

    response = client.post(
        "/api/v1/plex/connection",
        headers=auth_headers(),
        json={"server_url": "http://plex:32400", "token": "my-token"},
    )
    assert response.status_code == 201
    mock_session.add.assert_called_once()
```

**Step 3: Run to verify failure**

```bash
pytest tests/test_plex_api.py -v
```
Expected: `ImportError` or 404 on route not registered.

**Step 4: Create API schemas**

```python
# app/api/v1/plex/schemas.py
"""Request/response schemas for Plex API endpoints"""

from typing import Optional
from pydantic import BaseModel


class PlexConnectionCreate(BaseModel):
    server_url: str
    token: str


class PlexSyncTriggerResponse(BaseModel):
    task_id: str
    message: str


class PlexOAuthInitResponse(BaseModel):
    oauth_url: str
    pin_id: int
```

**Step 5: Create router**

```python
# app/api/v1/plex/__init__.py
```

```python
# app/api/v1/plex/router.py
"""FastAPI router for Plex integration endpoints"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.plex.schemas import (
    PlexConnectionCreate,
    PlexOAuthInitResponse,
    PlexSyncTriggerResponse,
)
from app.core.config import settings
from app.core.database import get_db
from app.domain.plex.models import PlexConnection
from app.domain.plex.schemas import PlexConnectionResponse
from app.infrastructure.external_apis.plex.auth import PlexAuth
from app.tasks.plex import lock_plex_match, poll_plex_watched_status

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plex", tags=["plex"])


@router.get("/connection", response_model=PlexConnectionResponse)
def get_connection(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Get the active Plex connection."""
    conn = db.query(PlexConnection).filter(PlexConnection.is_active.is_(True)).first()
    if conn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active Plex connection")
    return conn


@router.post("/connection", response_model=PlexConnectionResponse, status_code=201)
def create_connection(
    payload: PlexConnectionCreate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Create or replace the Plex connection using a manual token."""
    existing = db.query(PlexConnection).first()
    if existing:
        db.delete(existing)
        db.flush()

    conn = PlexConnection(
        server_url=payload.server_url,
        token=payload.token,
        is_active=True,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


@router.delete("/connection", status_code=204)
def delete_connection(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Remove the Plex connection."""
    conn = db.query(PlexConnection).first()
    if conn:
        db.delete(conn)
        db.commit()
```

**Step 6: Register router in main app**

Find where other v1 routers are included (e.g. `app/main.py` or `app/api/v1/__init__.py`) and add:

```python
from app.api.v1.plex.router import router as plex_router
app.include_router(plex_router, prefix="/api/v1")
```

**Step 7: Run tests**

```bash
pytest tests/test_plex_api.py -v -k "connection"
```
Expected: PASSED.

**Step 8: Commit**

```bash
git add app/api/v1/plex/ tests/test_plex_api.py app/main.py
git commit -m "feat(plex): add Plex connection management API endpoints"
```

---

### Task 2: OAuth endpoints

**Files:**
- Modify: `app/api/v1/plex/router.py`
- Modify: `tests/test_plex_api.py`

**Step 1: Write failing tests**

```python
# append to tests/test_plex_api.py

@patch("app.api.v1.plex.router.PlexAuth")
@patch("app.api.v1.plex.router.get_current_user")
def test_oauth_initiate_returns_url_and_pin(mock_user, mock_auth_cls):
    mock_user.return_value = MagicMock(id=1)
    mock_auth = MagicMock()
    mock_auth_cls.return_value = mock_auth
    mock_auth.create_pin.return_value = (42, "ABCD1234")
    mock_auth.build_oauth_url.return_value = "https://app.plex.tv/auth#?code=ABCD1234"

    response = client.get(
        "/api/v1/plex/oauth/initiate",
        headers=auth_headers(),
        params={"redirect_uri": "http://localhost:5173/plex/callback"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pin_id"] == 42
    assert "plex.tv" in data["oauth_url"]
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_plex_api.py -v -k "oauth"
```
Expected: 404 (route not yet defined)

**Step 3: Add OAuth endpoints to router**

```python
# append to app/api/v1/plex/router.py

@router.get("/oauth/initiate", response_model=PlexOAuthInitResponse)
def oauth_initiate(
    redirect_uri: str,
    _: object = Depends(get_current_user),
):
    """Begin OAuth pin flow. Returns URL for user to visit and pin_id to poll."""
    auth = PlexAuth()
    pin_id, pin_code = auth.create_pin()
    oauth_url = auth.build_oauth_url(pin_code=pin_code, redirect_uri=redirect_uri)
    logger.info("Plex OAuth: initiated pin_id=%s", pin_id)
    return PlexOAuthInitResponse(oauth_url=oauth_url, pin_id=pin_id)


@router.get("/oauth/callback")
def oauth_callback(
    pin_id: int,
    server_url: str,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Poll for OAuth token after user authorises. Creates PlexConnection on success."""
    auth = PlexAuth()
    token = auth.poll_pin(pin_id=pin_id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Authorisation pending — user has not approved yet",
        )

    existing = db.query(PlexConnection).first()
    if existing:
        db.delete(existing)
        db.flush()

    conn = PlexConnection(server_url=server_url, token=token, is_active=True)
    db.add(conn)
    db.commit()
    db.refresh(conn)
    logger.info("Plex OAuth: connection established server=%s", server_url)
    return PlexConnectionResponse.model_validate(conn)
```

**Step 4: Run tests**

```bash
pytest tests/test_plex_api.py -v -k "oauth"
```
Expected: PASSED.

**Step 5: Commit**

```bash
git add app/api/v1/plex/router.py tests/test_plex_api.py
git commit -m "feat(plex): add Plex OAuth initiate and callback endpoints"
```

---

### Task 3: Manual sync endpoint

**Files:**
- Modify: `app/api/v1/plex/router.py`
- Modify: `tests/test_plex_api.py`

**Step 1: Write failing test**

```python
# append to tests/test_plex_api.py
from unittest.mock import patch


@patch("app.api.v1.plex.router.poll_plex_watched_status")
@patch("app.api.v1.plex.router.get_db")
@patch("app.api.v1.plex.router.get_current_user")
def test_post_sync_dispatches_celery_task(mock_user, mock_db, mock_poll):
    mock_user.return_value = MagicMock(id=1)
    mock_session = MagicMock()
    mock_conn = MagicMock(id=1)
    mock_session.query.return_value.filter.return_value.first.return_value = mock_conn
    mock_db.return_value = iter([mock_session])
    mock_poll.delay.return_value = MagicMock(id="task-abc")

    response = client.post("/api/v1/plex/sync", headers=auth_headers())
    assert response.status_code == 202
    mock_poll.delay.assert_called_once_with(1)
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_plex_api.py -v -k "sync"
```
Expected: 404

**Step 3: Add sync endpoint**

```python
# append to app/api/v1/plex/router.py

@router.post("/sync", response_model=PlexSyncTriggerResponse, status_code=202)
def trigger_full_sync(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Dispatch a full Plex sync (match locking + watch status pull)."""
    conn = db.query(PlexConnection).filter(PlexConnection.is_active.is_(True)).first()
    if conn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active Plex connection")

    task = poll_plex_watched_status.delay(conn.id)
    logger.info("Plex: manual sync dispatched task_id=%s", task.id)
    return PlexSyncTriggerResponse(task_id=task.id, message="Plex sync dispatched")
```

**Step 4: Run all API tests**

```bash
pytest tests/test_plex_api.py -v
```
Expected: All PASSED.

**Step 5: Lint**

```bash
black app/api/v1/plex/ tests/test_plex_api.py
isort app/api/v1/plex/ tests/test_plex_api.py
flake8 app/api/v1/plex/ tests/test_plex_api.py
mypy app/api/v1/plex/
```

**Step 6: Commit**

```bash
git add app/api/v1/plex/ tests/test_plex_api.py
git commit -m "feat(plex): add manual Plex sync trigger endpoint"
```

---

### Task 4: Run full backend test suite

**Step 1:**

```bash
pytest --tb=short -q
```
Expected: No regressions. New Plex tests all PASS.

**Step 2: If failures exist**, investigate before continuing to Phase 6.

**Step 3: Commit any fixes**

```bash
git add -u
git commit -m "fix(plex): resolve test regressions from API integration"
```
