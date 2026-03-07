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
2. Click **Open Plex.tv to Authorise**
3. A Plex.tv authorisation page opens in a new tab — sign in and approve
4. Return to MetaMaster — the connection status should show your server URL

### Option B: Manual token (power users / headless setups)

If you prefer not to use OAuth, you can use a static Plex token:

1. Find your token: sign in to Plex Web → open any media item → click the `···` menu →
   **Get Info** → **View XML**. The token appears as `X-Plex-Token=XXXXX` in the URL.
2. Go to **Settings → Plex Integration** → click **Manual Token** tab
3. Enter your server URL and token → click **Connect**

Alternatively, set `PLEX_TOKEN=your-token-here` in `.env` before connecting.

---

## Step 3: Verify the connection

After connecting, MetaMaster will:
1. Resolve your library names to Plex section IDs
2. Begin matching your enriched media to Plex items via TMDB IDs
3. Start polling for watch status on the configured interval

Check **System Health** (`/system-health`) in MetaMaster to see match progress
and any items that could not be matched.

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

### Items showing as "Not found in Plex" on the health page

The item exists in MetaMaster but Plex hasn't scanned/matched it yet. This happens when:
- The file was recently added and Plex hasn't scanned yet — wait or trigger a manual scan in Plex
- The filename doesn't match Plex naming conventions — check `docs/file-organisation.md`

Once Plex has matched the file, click **Re-sync** on the health page item to retry.

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
