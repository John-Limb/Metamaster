# TMDB Dual Auth (Read Access Token + API Key) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Support both TMDB Read Access Token (Bearer) and v3 API Key auth, with the token taking priority, and expose the status of each credential on the dashboard External APIs card.

**Architecture:** Add `TMDB_READ_ACCESS_TOKEN` alongside `TMDB_API_KEY` in `.env` and `Settings`. Replace `TMDBService._get_headers()` with `_get_auth()` returning `(headers, params)` so Bearer auth passes an `Authorization` header while API Key auth appends `?api_key=` as a query param. The backend `/config/check` endpoint exposes two separate items — one per credential — with descriptions noting which is active. The dashboard `ExternalApiStatus` component is updated to watch both IDs.

**Tech Stack:** Python/FastAPI backend, Pydantic Settings, httpx, React/TypeScript frontend, Tailwind CSS.

---

### Task 1: Add `TMDB_READ_ACCESS_TOKEN` to `.env` and `Settings`

**Files:**
- Modify: `.env`
- Modify: `app/core/config.py:58-61`

**Step 1: Add the new env var to `.env`**

In `.env`, replace the TMDB block:
```
# TMDB API (The Movie Database — covers both movies and TV shows)
# Get a free API key at https://www.themoviedb.org/settings/api
TMDB_API_KEY=9ce1a8a11e172aa217bf5c28a65f480b
VITE_TMDB_API_KEY=9ce1a8a11e172aa217bf5c28a65f480b
TMDB_RATE_LIMIT=4
TMDB_CACHE_TTL=2592000
```
with:
```
# TMDB API (The Movie Database — covers both movies and TV shows)
# Get credentials at https://www.themoviedb.org/settings/api
#
# TMDB_READ_ACCESS_TOKEN — preferred. Long JWT from the TMDB API settings page
#   under "API Read Access Token (v4 auth)". Used as: Authorization: Bearer <token>
# TMDB_API_KEY — fallback v3 API key. Short alphanumeric string. Used as: ?api_key=<key>
# At least one must be set for enrichment to work.
TMDB_READ_ACCESS_TOKEN=
TMDB_API_KEY=9ce1a8a11e172aa217bf5c28a65f480b
TMDB_RATE_LIMIT=4
TMDB_CACHE_TTL=2592000
```

**Step 2: Add the setting to `Settings` in `app/core/config.py`**

Replace:
```python
    # TMDB API (The Movie Database — covers both movies and TV shows)
    tmdb_api_key: Optional[str] = None
    tmdb_rate_limit: int = 4  # requests per second (~40/10s)
    tmdb_cache_ttl: int = 2592000  # 30 days in seconds
```
with:
```python
    # TMDB API (The Movie Database — covers both movies and TV shows)
    # tmdb_read_access_token: preferred — long JWT Bearer token (v4 auth)
    # tmdb_api_key: fallback — short v3 API key appended as ?api_key=
    tmdb_read_access_token: Optional[str] = None
    tmdb_api_key: Optional[str] = None
    tmdb_rate_limit: int = 4  # requests per second (~40/10s)
    tmdb_cache_ttl: int = 2592000  # 30 days in seconds
```

**Step 3: Commit**
```bash
git add .env app/core/config.py
git commit -m "feat: add TMDB_READ_ACCESS_TOKEN env var and Settings field"
```

---

### Task 2: Refactor `TMDBService` auth — replace `_get_headers` with `_get_auth`

**Files:**
- Modify: `app/services_impl.py:289-295` (`_get_headers`) and all five callers

**Step 1: Write the failing test**

In `tests/test_tmdb_service.py`, add a new section after the existing `_get_cache_key` tests:

```python
# ===========================================================================
# _get_auth
# ===========================================================================


def test_get_auth_prefers_read_access_token():
    """_get_auth returns Bearer header when TMDB_READ_ACCESS_TOKEN is set."""
    with patch.object(settings, "tmdb_read_access_token", "my.jwt.token"), \
         patch.object(settings, "tmdb_api_key", "myapikey"):
        result = TMDBService._get_auth()
    assert result is not None
    headers, params = result
    assert headers["Authorization"] == "Bearer my.jwt.token"
    assert params == {}


def test_get_auth_falls_back_to_api_key():
    """_get_auth returns ?api_key= params when only TMDB_API_KEY is set."""
    with patch.object(settings, "tmdb_read_access_token", None), \
         patch.object(settings, "tmdb_api_key", "myapikey"):
        result = TMDBService._get_auth()
    assert result is not None
    headers, params = result
    assert "Authorization" not in headers
    assert params == {"api_key": "myapikey"}


def test_get_auth_returns_none_when_neither_set():
    """_get_auth returns None when no credentials are configured."""
    with patch.object(settings, "tmdb_read_access_token", None), \
         patch.object(settings, "tmdb_api_key", None):
        result = TMDBService._get_auth()
    assert result is None
```

Also add the import at the top of the test file:
```python
from app.core.config import settings
```

**Step 2: Run tests to confirm they fail**
```bash
pytest tests/test_tmdb_service.py::test_get_auth_prefers_read_access_token tests/test_tmdb_service.py::test_get_auth_falls_back_to_api_key tests/test_tmdb_service.py::test_get_auth_returns_none_when_neither_set -v
```
Expected: FAIL — `TMDBService` has no `_get_auth` attribute.

**Step 3: Replace `_get_headers` with `_get_auth` in `app/services_impl.py`**

Replace the `_get_headers` classmethod (lines ~289-295):
```python
    @classmethod
    def _get_headers(cls) -> Optional[Dict[str, str]]:
        """Return Authorization headers, or None if API key is not configured."""
        if not settings.tmdb_api_key:
            logger.error("TMDB_API_KEY not configured")
            return None
        return {"Authorization": f"Bearer {settings.tmdb_api_key}", "accept": "application/json"}
```
with:
```python
    @classmethod
    def _get_auth(cls) -> Optional[tuple]:
        """Return (headers, query_params) for TMDB authentication.

        Priority: TMDB_READ_ACCESS_TOKEN (Bearer) > TMDB_API_KEY (?api_key=).
        Returns None if neither is configured.
        """
        if settings.tmdb_read_access_token:
            return (
                {"Authorization": f"Bearer {settings.tmdb_read_access_token}", "accept": "application/json"},
                {},
            )
        if settings.tmdb_api_key:
            return (
                {"accept": "application/json"},
                {"api_key": settings.tmdb_api_key},
            )
        logger.error("No TMDB credentials configured — set TMDB_READ_ACCESS_TOKEN or TMDB_API_KEY")
        return None
```

**Step 4: Update `_make_request_with_retry` to accept `params`**

Change the signature and the `client.get` call:
```python
    @staticmethod
    async def _make_request_with_retry(
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> Optional[Dict[str, Any]]:
```
And inside the method, change the `client.get` call from:
```python
                    response = await client.get(url, headers=headers)
```
to:
```python
                    response = await client.get(url, headers=headers, params=params or {})
```

**Step 5: Update all five callers to use `_get_auth`**

Each of `search_movie`, `get_movie_details`, `search_show`, `get_series_details`, `get_season_details` currently does:
```python
        headers = cls._get_headers()
        if not headers:
            return None
        ...
        result = await cls._make_request_with_retry(url, headers)
```

Replace every instance with:
```python
        auth = cls._get_auth()
        if not auth:
            return None
        headers, params = auth
        ...
        result = await cls._make_request_with_retry(url, headers, params)
```

**Step 6: Update existing tests that patch `_get_headers`**

In `tests/test_tmdb_service.py`, every occurrence of:
```python
patch.object(TMDBService, "_get_headers", return_value={"Authorization": "Bearer test"})
```
must become:
```python
patch.object(TMDBService, "_get_auth", return_value=({"Authorization": "Bearer test"}, {}))
```

There are 8 such patches — in tests:
`test_search_movie_cache_hit`, `test_search_movie_no_api_key`, `test_search_movie_network_call`,
`test_get_movie_details_cache_hit`, `test_get_movie_details_no_api_key`,
`test_search_show_cache_hit`, `test_search_show_no_api_key`,
`test_get_series_details_cache_hit`, `test_get_series_details_no_api_key`,
`test_get_season_details_cache_hit`, `test_get_season_details_no_api_key`.

For the "no api key" tests, the return value must also change to `None`:
```python
patch.object(TMDBService, "_get_auth", return_value=None)
```

**Step 7: Run all TMDB tests**
```bash
pytest tests/test_tmdb_service.py -v
```
Expected: All PASS.

**Step 8: Commit**
```bash
git add app/services_impl.py tests/test_tmdb_service.py
git commit -m "feat: replace _get_headers with _get_auth supporting Bearer token and API Key fallback"
```

---

### Task 3: Update `/config/check` to expose two TMDB credential items

**Files:**
- Modify: `app/api/v1/config/endpoints.py:68-78`

**Step 1: Replace the single TMDB item with two items**

Replace the existing TMDB check block:
```python
    # Check TMDB API Key (covers both movies and TV shows)
    tmdb_configured = bool(settings.tmdb_api_key and settings.tmdb_api_key != "your_tmdb_api_key_here")
    items.append(ConfigurationItem(
        id="api-keys-tmdb",
        name="TMDB API Key",
        description="API key for fetching movie and TV show metadata from The Movie Database",
        severity="important",
        status="valid" if tmdb_configured else "invalid",
        actionLabel="Configure API Key",
        actionPath="/settings?section=api-keys",
    ))
```
with:
```python
    # Check TMDB credentials — Read Access Token (preferred) and v3 API Key (fallback)
    token_set = bool(settings.tmdb_read_access_token)
    key_set = bool(settings.tmdb_api_key and settings.tmdb_api_key != "your_tmdb_api_key_here")

    token_desc = "Long JWT for Bearer auth — get from TMDB Settings → API Read Access Token (v4 auth)"
    if token_set:
        token_desc += " — active"

    items.append(ConfigurationItem(
        id="api-keys-tmdb-token",
        name="TMDB Access Token",
        description=token_desc,
        severity="important",
        status="valid" if token_set else "invalid",
        actionLabel="Configure Token",
        actionPath="/settings?section=api-keys",
    ))

    if key_set and token_set:
        key_desc = "v3 API Key — present but not active (Access Token takes priority)"
    elif key_set:
        key_desc = "v3 API Key — active (set TMDB_READ_ACCESS_TOKEN to use Bearer auth instead)"
    else:
        key_desc = "v3 API Key — not set"

    items.append(ConfigurationItem(
        id="api-keys-tmdb-key",
        name="TMDB API Key",
        description=key_desc,
        severity="optional" if token_set else "important",
        status="valid" if key_set else "invalid",
        actionLabel="Configure API Key",
        actionPath="/settings?section=api-keys",
    ))
```

Also update the `metadata_configured` line further down from:
```python
    metadata_configured = tmdb_configured
```
to:
```python
    metadata_configured = token_set or key_set
```

**Step 2: Verify the endpoint manually**
```bash
curl -s http://localhost/api/v1/config/check | python3 -m json.tool | grep -A6 "tmdb"
```
Expected: two items — `api-keys-tmdb-token` and `api-keys-tmdb-key` — with correct statuses.

**Step 3: Commit**
```bash
git add app/api/v1/config/endpoints.py
git commit -m "feat: expose TMDB Read Access Token and API Key as separate config check items"
```

---

### Task 4: Update dashboard `ExternalApiStatus` component

**Files:**
- Modify: `frontend/src/components/dashboard/Dashboard/Dashboard.tsx:21-30`

**Step 1: Update `API_STATUS_IDS` and `labels`**

Replace:
```typescript
const API_STATUS_IDS = ['api-keys-tmdb']

function ExternalApiStatus({ items }: { items: ConfigurationItem[] }) {
  const apiItems = items.filter(i => API_STATUS_IDS.includes(i.id))
  const allValid = apiItems.length > 0 && apiItems.every(i => i.status === 'valid')
  const hasInvalid = apiItems.some(i => i.status === 'invalid')

  const labels: Record<string, string> = {
    'api-keys-tmdb': 'TMDB',
  }
```
with:
```typescript
const API_STATUS_IDS = ['api-keys-tmdb-token', 'api-keys-tmdb-key']

function ExternalApiStatus({ items }: { items: ConfigurationItem[] }) {
  const apiItems = items.filter(i => API_STATUS_IDS.includes(i.id))
  const allValid = apiItems.length > 0 && apiItems.every(i => i.status === 'valid')
  const hasInvalid = apiItems.some(i => i.status === 'invalid')

  const labels: Record<string, string> = {
    'api-keys-tmdb-token': 'TMDB Access Token',
    'api-keys-tmdb-key': 'TMDB API Key',
  }
```

**Step 2: Verify in browser**

Open the dashboard at `http://localhost`. The External APIs card should now show two rows:
- **TMDB Access Token** — red dot + "Missing" if `TMDB_READ_ACCESS_TOKEN` is empty, green + "Connected" if set
- **TMDB API Key** — green dot + "Connected" if `TMDB_API_KEY` is set

**Step 3: Commit**
```bash
git add frontend/src/components/dashboard/Dashboard/Dashboard.tsx
git commit -m "feat: show TMDB Access Token and API Key separately in dashboard External APIs card"
```
