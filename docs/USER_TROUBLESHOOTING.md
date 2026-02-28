# Troubleshooting

---

## Frontend Issues

### API not reachable

**Symptoms:** `Network Error` or CORS error in browser console.

**Fix:**
1. Verify the backend is running: `curl http://localhost:8000/health/`
2. Check `VITE_API_URL` in `frontend/.env` — it should be `http://localhost:8000/api/v1`
3. If running in Docker, verify CORS settings: `allowed_origins` in `.env` must include the frontend origin

### Dependencies not installing

**Symptoms:** `package.json not found` or `Invalid package name`

**Fix:**
```bash
cd frontend
rm -rf node_modules
npm cache clean --force
npm install
```

### TypeScript errors

**Symptoms:** Type errors in IDE or `npm run type-check` fails

**Fix:**
```bash
npm run lint:fix          # auto-fix common issues
npm run type-check        # verify remaining errors
```

If errors persist, regenerate API types from the current OpenAPI schema:
```bash
npm run typegen
```

### Tests failing

**Symptoms:** `npm run test` reports failures

**Fix:**
1. For unit tests: no backend required — run `npm run test:ui` for visual debugging
2. For E2E tests: ensure backend services are running and `VITE_API_URL` is set
3. Verify test environment: `cp .env.example .env` if `.env` is missing

---

## Backend Issues

### Database connection failed

**Symptoms:** `sqlalchemy.exc.OperationalError` on startup

**Fix:**
1. Verify PostgreSQL is running: `docker-compose ps db`
2. Check `DATABASE_URL` in `.env`
3. Apply migrations: `alembic upgrade head`

### Celery worker not processing tasks

**Symptoms:** Enrichment never completes; tasks stuck in queue

**Fix:**
1. Verify Redis is running: `docker-compose ps redis`
2. Start the worker: `celery -A app.tasks.celery_app worker --loglevel=info`
3. Check `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` in `.env`

### Redis connection refused

**Symptoms:** `redis.exceptions.ConnectionError`

**Fix:**
```bash
docker-compose up -d redis    # start Redis container
# or for local Redis:
brew services start redis     # macOS
sudo systemctl start redis    # Linux
```

### TMDB enrichment not working

**Symptoms:** Movies/shows stuck at `external_failed` enrichment status

**Fix:**
1. Verify `TMDB_READ_ACCESS_TOKEN` is set in `.env` (preferred) or `TMDB_API_KEY`
2. Test the token: `curl -H "Authorization: Bearer $TMDB_READ_ACCESS_TOKEN" "https://api.themoviedb.org/3/configuration"`
3. Check Celery worker logs for specific errors

### FFprobe not found

**Symptoms:** `FileNotFoundError: ffprobe` when scanning media files

**Fix:**
Install FFmpeg (which includes FFprobe):
```bash
# macOS
brew install ffmpeg

# Debian/Ubuntu
sudo apt install ffmpeg

# Docker (already included in the backend Dockerfile)
```

### Media files not detected

**Symptoms:** Scanned directories show no files

**Fix:**
1. Verify Docker volume mounts in `docker-compose.yml` map your local directories to `/media/movies` and `/media/tv`
2. Check file extensions — only `.mp4 .mkv .avi .mov .flv .wmv .webm .m4v .mpg .mpeg .3gp` are scanned
3. Trigger a manual scan: `POST /api/v1/files/scan`
