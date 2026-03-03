# Redis Safe Upgrade Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade redis-py from 5.0.1 to the latest version within Kombu's tested constraint (`<6.5`), instead of accepting Dependabot PR #43's jump to 7.0.1.

**Architecture:** Requirements-only change — no application code modifications are needed. All redis-py API calls in the codebase use stable methods (`from_url`, `ping`, `get`, `setex`, `delete`, `keys`, `incr`, `flushdb`, `info`, `pipeline`, sorted-set commands) that are unchanged across 5.x → 6.x → 7.x. The blocker is Kombu 5.6.2 (Celery's broker library, the latest available), which caps its tested redis-py range at `<6.5`. Bumping directly to 7.0.1 is outside that tested range and risks Celery broker instability at runtime.

**Tech Stack:** Python, redis-py, Kombu 5.6.2, Celery 5.6.2

---

## Investigation Findings

### Why Dependabot PR #43 (`redis 5.0.1 → 7.0.1`) should NOT be merged as-is

| Evidence | Detail |
|---|---|
| Kombu 5.6.2 extras constraint | `redis!=4.5.5,!=5.0.2,<6.5,>=4.5.2` |
| Latest available Kombu | 5.6.2 — no newer release supports redis 7.x |
| Latest Celery | 5.6.2 — ships Kombu 5.6.2 |
| redis-py 7.0.1 vs constraint | 7.0.1 > 6.5 → outside Kombu's tested range |
| Pip enforcement | Constraint lives in `extras_require["redis"]`, not `install_requires`. Pip won't error on `pip install -r requirements.txt`, but the Celery Redis broker transport is **untested** with redis-py 7.x by the Kombu team. |

### Why app code needs no changes

All call sites audited. Every method used exists unchanged in redis-py 5.x through 7.x:

| File | Methods used |
|---|---|
| `app/infrastructure/cache/redis_cache.py` | `from_url`, `ping`, `get`, `setex`, `delete`, `keys`, `incr`, `flushdb`, `info` |
| `app/infrastructure/security/rate_limiter.py` | `pipeline`, `execute`, `zremrangebyscore`, `zcard`, `zrange(..., withscores=True)`, `zadd`, `expire`, `delete` |
| `app/infrastructure/monitoring/monitoring_service.py` | `from_url`, `ping` |
| `app/api/v1/health/endpoints.py` | `from_url`, `ping` |

No removed params (`charset`, `errors`) are used. No `rediss://` SSL URLs → the `ssl_check_hostname=True` default change in 6.0.0 is irrelevant.

### Safe target version

`redis==5.2.0` — latest in the 5.x series, fully within Kombu's constraint, contains all 5.x security and bug fixes since 5.0.1.

If you want to also get 6.x improvements (e.g. default retry backoff, RLock deadlock fix), `redis==6.1.0` is the highest confirmed 6.x release and also within the `<6.5` constraint. The 6.0.0 ssl_check_hostname change does not affect this project (plain `redis://` only).

**Recommendation: `redis==5.2.0`** — minimal blast radius, gets bug fixes, zero risk.

---

### Task 1: Pin redis to the safe version

**Files:**
- Modify: `requirements.txt`

**Step 1: Update the pin**

In `requirements.txt`, change:
```
redis==5.0.1
```
to:
```
redis==5.2.0
```

**Step 2: Verify no other pins need changing**

Run:
```bash
grep -n "redis" requirements.txt
```
Expected output — only two lines: the `redis==5.2.0` line and `celery==5.6.2`. No other redis-related pins.

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore(deps): bump redis from 5.0.1 to 5.2.0 (within kombu constraint)"
```

---

### Task 2: Run the test suite to confirm no regressions

**Step 1: Run all unit tests**

```bash
pytest -m "not slow" -x -q
```
Expected: all pass. If redis-related tests fail, see the troubleshooting note below.

**Step 2: Run the full suite**

```bash
pytest -x -q
```
Expected: same pass rate as on `main`. Any new failures are regressions from the version bump and must be diagnosed before proceeding.

**Troubleshooting:** If `tests/test_redis_cache.py` fails with a `ResponseError` or attribute error, check `redis_cache.py:58-65` — the `from_url` kwargs (`decode_responses`, `socket_connect_timeout`, `socket_keepalive`) are all valid in 5.2.0.

**Step 3: Commit (only if all tests pass)**

No code changes needed here — this step is evidence gathering only.

---

### Task 3: Run linting to satisfy CI

**Step 1: Run Black (CI version)**

```bash
pipx run black==26.1.0 --check requirements.txt
```
Expected: `1 file would be left unchanged.`

**Step 2: Run isort**

```bash
isort --check-only requirements.txt
```
Expected: no output (no changes needed for a requirements file).

---

### Task 4: Document the Dependabot PR decision

**Step 1: Add an inline comment to requirements.txt**

In `requirements.txt`, update the redis line to:
```
redis==5.2.0  # Kombu 5.6.2 caps redis-py at <6.5; do not bump above 6.4.x until kombu is updated
```

**Step 2: Commit**

```bash
git add requirements.txt
git commit -m "docs(deps): document redis version ceiling due to kombu constraint"
```

---

### Task 5: Close Dependabot PR #43 with explanation

**Step 1: Comment on the Dependabot PR**

```bash
gh pr comment 43 --body "Closing in favour of a safe intermediate bump (redis 5.0.1 → 5.2.0).

**Root cause:** Kombu 5.6.2 (Celery's broker library) caps its tested redis-py range at \`<6.5\` (\`redis!=4.5.5,!=5.0.2,<6.5,>=4.5.2\`). Jumping directly to 7.0.1 is outside the tested range for the Celery Redis broker transport, even though application-level API calls are compatible.

**No app-code changes were needed** — all call sites use stable APIs unchanged across 5.x–7.x.

**When to revisit:** Once Kombu ships a release with an updated constraint that explicitly includes redis-py ≥ 6.5 or ≥ 7.0, the full jump to 7.x can be made safely."
```

**Step 2: Close the PR**

```bash
gh pr close 43 --comment "Superseded by chore/redis-safe-upgrade — see comment above."
```

---

## Post-merge: When to revisit the full 7.x upgrade

Watch for a Kombu release that bumps its redis extras constraint above `<6.5`. You can check periodically with:

```bash
pip index versions kombu 2>/dev/null | head -5
# or
curl -s https://pypi.org/pypi/kombu/json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['info']['version'])"
```

When a new Kombu ships, re-evaluate whether Celery also needs a bump and re-run the audit above before accepting the 7.x Dependabot PR.
