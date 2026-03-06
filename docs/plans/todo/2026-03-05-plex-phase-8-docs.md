# Plex Integration — Phase 8: User Documentation

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Write the `docs/plex-setup.md` user guide covering setup, configuration, troubleshooting, and what MetaMaster reads vs writes to Plex.

**Architecture:** Single markdown file in `docs/`. No code changes. Reviewed against actual implementation from Phases 1–7 before publishing.

**Prerequisite:** Phases 1–7 complete and working.

---

### Task 1: Write plex-setup.md

**Files:**
- Create: `docs/plex-setup.md`

**Step 1: Create the doc**

```markdown
# Plex Integration Setup

MetaMaster integrates with Plex Media Server to:
- Trigger Plex library rescans when files are moved or renamed
- Lock Plex's media matches to the correct TMDB entry
- Pull watch status and play counts back for analytics and enrichment prioritisation

MetaMaster does **not** overwrite Plex's own metadata (titles, descriptions, posters, ratings).
Plex manages these via its native agents.

---

## Prerequisites

- Plex Media Server running and accessible from MetaMaster (local or network URL)
- MetaMaster running (Docker or local)
- Your Plex libraries named consistently (you will reference these names in config)

---

## Step 1: Configure your .env file

Add the following to your `.env` file (copy from `.env.example`):

```
PLEX_SERVER_URL=http://192.168.1.x:32400
PLEX_LIBRARY_MOVIES=Movies
PLEX_LIBRARY_TV=TV Shows
PLEX_SYNC_POLL_INTERVAL_SECONDS=300
```

**`PLEX_SERVER_URL`** — the full URL of your Plex Media Server including port.
Use `http://localhost:32400` if Plex runs on the same machine as MetaMaster.

**`PLEX_LIBRARY_MOVIES`** — the exact name of your Plex movie library.
To find it: open Plex → left sidebar → hover over your library name.
This value is **case-sensitive**.

**`PLEX_LIBRARY_TV`** — the exact name of your Plex TV show library.
Same rules as above.

**`PLEX_SYNC_POLL_INTERVAL_SECONDS`** — how often MetaMaster polls Plex for
watch status updates. Default is 300 (5 minutes).

Restart MetaMaster after editing `.env`:
```bash
docker-compose up -d --build
```

---

## Step 2: Connect MetaMaster to Plex

### Option A: Connect via Plex.tv (recommended)

1. Go to **Settings → Plex Integration** in MetaMaster
2. Click **Connect via Plex.tv**
3. A Plex.tv authorisation page opens in a new tab — sign in and approve
4. Return to MetaMaster — the connection status should show your server URL

### Option B: Manual token (power users / headless setups)

If you prefer not to use OAuth, you can use a static Plex token:

1. Find your token: sign in to Plex Web → open any media item → click the `···` menu →
   **Get Info** → **View XML**. The token appears as `X-Plex-Token=XXXXX` in the URL.
2. Add to `.env`:
   ```
   PLEX_TOKEN=your-token-here
   ```
3. Go to **Settings → Plex Integration** → **Manual Token** tab
4. Enter your server URL and token → click **Connect**

---

## Step 3: Verify the connection

After connecting, MetaMaster will:
1. Resolve your library names to Plex section IDs
2. Begin matching your enriched media to Plex items via TMDB IDs
3. Start polling for watch status on the configured interval

Check **Health → Plex Sync** in MetaMaster to see match progress.

---

## What MetaMaster reads vs writes to Plex

| Action | Direction | Notes |
|---|---|---|
| Library rescan trigger | MetaMaster → Plex | After any file move/rename/delete |
| TMDB match lock | MetaMaster → Plex | Prevents Plex misidentifying edge cases |
| Watch count / last watched | Plex → MetaMaster | Used for UI display and enrichment priority |
| Titles, descriptions, ratings | Neither | Plex manages these via its own agents |
| Posters (individual items) | Neither | Plex manages these natively |

---

## Troubleshooting

### "Library mismatch" alert in MetaMaster

MetaMaster cannot find a Plex library matching `PLEX_LIBRARY_MOVIES` or `PLEX_LIBRARY_TV`.

The alert will show available library names. Update `.env` to match exactly
(case-sensitive) and restart.

### Items showing as "Not found in Plex" on the health page

The item exists in MetaMaster but Plex hasn't scanned/matched it yet. This happens when:
- The file was recently added and Plex hasn't scanned yet — wait or trigger a manual scan in Plex
- The filename doesn't match Plex naming conventions — check `docs/file-organisation.md`

Once Plex has matched the file, click **Re-sync** on the health page item.

### Watch status not updating

- Check `PLEX_SYNC_POLL_INTERVAL_SECONDS` — lower it if you want more frequent updates
- Check the Celery worker logs: `docker-compose logs -f celery`
  Look for `Plex API GET` and `Plex pull:` log lines
- Verify the Plex token hasn't expired (Settings → Plex Integration → reconnect)

### OAuth flow not completing

If the Plex.tv popup closes but MetaMaster doesn't show as connected:
- Try the **Manual Token** method instead
- Check browser console for errors
- Check `docker-compose logs -f app` for OAuth callback errors

---

## Celery worker logs

All Plex API calls are logged to the Celery worker console at INFO level.
To view them:

```bash
docker-compose logs -f celery | grep -i plex
```

You will see lines like:
```
INFO Plex API GET http://plex:32400/library/sections params=None
INFO Plex API response http://plex:32400/library/sections 200
INFO Plex match locked: movie id=42 key=99
WARNING Plex match not found: movie id=55 tmdb_id=12345 — skipping
```
```

**Step 2: Review doc against implementation**

Before committing, cross-check each section against the actual implemented behaviour from Phases 1–7:
- Verify env var names match `app/core/config.py`
- Verify UI paths match actual frontend routes and labels
- Verify log message strings match `app/tasks/plex.py` and `app/domain/plex/service.py`

**Step 3: Commit**

```bash
git add docs/plex-setup.md
git commit -m "docs(plex): add Plex integration setup guide"
```

---

### Task 2: Final integration check

**Step 1: Run full backend test suite**

```bash
pytest --tb=short -q
```
Expected: All PASSED, no regressions.

**Step 2: Run full frontend test suite**

```bash
cd frontend && npm run test --run
```
Expected: All PASSED.

**Step 3: Run all linters**

```bash
black app/ tests/ && isort app/ tests/ && flake8 app/ tests/ && mypy app/
cd frontend && npm run lint
```
Expected: No errors.

**Step 4: Stage all changes**

```bash
git status
```

Review and stage any unstaged files:

```bash
git add <any remaining files>
git commit -m "chore(plex): final lint and test pass for Plex integration"
```

**Step 5: Integration complete**

All 8 phases done. The Plex integration is ready for review.
Invoke `superpowers:finishing-a-development-branch` to decide on merge strategy.
```
