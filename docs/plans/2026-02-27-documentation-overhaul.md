# Documentation Overhaul Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor README.md into a concise overview with links to four new dedicated docs files, fix all factual inaccuracies across all documentation, and update frontend/README.md.

**Architecture:** Main README becomes a short overview. Architecture, API reference, and CI/CD details move to dedicated files under `docs/`. A troubleshooting guide is created to back the existing frontend README link. No code changes — documentation only.

**Tech Stack:** Markdown. All version numbers sourced from `requirements.txt` and `frontend/package.json`.

---

## Reference: Correct Version Numbers

These must replace the outdated numbers currently in README.md:

### Backend (`requirements.txt`)
| Package | Old (README) | New (actual) |
|---------|-------------|--------------|
| FastAPI | 0.104.1 | 0.132.0 |
| Uvicorn | 0.24.0 | 0.41.0 |
| SQLAlchemy | 2.0.23 | 2.0.46 |
| Alembic | 1.12.1 | 1.18.4 |
| Celery | 5.3.4 | 5.6.2 |
| HTTPX | 0.25.2 | 0.28.1 |
| Watchdog | 3.0.0 | 6.0.0 |
| FFmpeg-Python | 0.2.0 | **REMOVE** (replaced by direct ffprobe subprocess call) |
| structlog | 23.2.0 | **REMOVE** (not in requirements.txt) |
| pytest | 7.4.3 | 8.4.2 |
| pytest-asyncio | 0.21.1 | 1.3.0 |
| pytest-benchmark | 4.0.0 | **REMOVE** (not in requirements.txt) |
| locust | 2.17.0 | **REMOVE** (not in requirements.txt) |
| Black | 23.12.0 | 26.1.0 |
| isort | 5.13.2 | 6.1.0 |
| mypy | 1.7.1 | 1.19.1 |

Add new row to Media Analysis section: `FFprobe | system | Media file analysis (via subprocess)`

### Frontend (`frontend/package.json`) — all versions already correct in README, no changes needed.

---

## Task 1: Create `docs/ARCHITECTURE.md`

**Files:**
- Create: `docs/ARCHITECTURE.md`

**Step 1: Create the file with this exact content**

```markdown
# Architecture

## Backend

The backend is a layered Python/FastAPI application under `app/`:

- **`api/v1/`** — FastAPI routers by domain: `auth/`, `movies/`, `tv_shows/`, `files/`, `queue/`, `enrichment/`, `storage/`, `organisation/`, `cache/`, `config/`, `health/`, `tasks/`
- **`domain/`** — Core business logic. Each domain (`movies/`, `tv_shows/`, `files/`, `auth/`, `organisation/`, `storage/`, `settings/`) has `models.py` (SQLAlchemy ORM), `schemas.py` (Pydantic), and `service.py`
- **`infrastructure/`** — External concerns: `cache/` (Redis), `external_apis/` (TMDB client), `file_system/` (file monitoring, FFprobe wrapper, queue manager), `monitoring/` (Prometheus), `security/` (JWT, password hashing, rate limiting)
- **`application/`** — Cross-cutting services: `search/`, `batch_operations/`, `pattern_recognition/`, `db_optimization/`
- **`tasks/`** — Celery: `celery_app.py` (config), `enrichment.py` (TMDB enrichment tasks), `celery_beat.py` (scheduled tasks)
- **`core/`** — App bootstrap: `config.py` (pydantic-settings), `database.py`, `init_db.py`, `logging_config.py`

### Data Model

```
Movie ──────────────── MovieFile  (1:many)
TVShow ─── Season ─── Episode ─── EpisodeFile  (1:many at each level)
```

Both `Movie` and `TVShow` have an `enrichment_status` enum:
`pending_local → local_only → pending_external → fully_enriched / not_found / external_failed`

### Startup Flow (`app/main.py` lifespan)

1. Initialize database (run Alembic migrations)
2. Sync media directories
3. Run file scanners
4. Dispatch enrichment tasks for pending items
5. Initialize Celery

### Authentication

JWT-based. Access tokens expire after 15 minutes; refresh tokens after 7 days. `jwt_secret_key` and `internal_api_key` are **auto-generated at startup** and are not persisted — they reset on every restart.

### Media Paths

Fixed container paths: `/media/movies` and `/media/tv`. These are Docker volume mount points configured as constants in `app/core/config.py`, not environment variables.

### Metadata Enrichment

All metadata enrichment uses **TMDB** (The Movie Database). Legacy stub directories for OMDB and TVDB remain in `app/infrastructure/external_apis/` but contain no active code.

---

## Frontend

The frontend is a React/TypeScript SPA under `frontend/src/`:

- **`App.tsx`** — Route definitions. All routes except `/login` and `/register` are wrapped in `ProtectedRoute` + `MainLayout`. Pages are lazy-loaded.
- **`pages/`** — Top-level page components (one per route)
- **`components/features/`** — `movies/` and `tvshows/` feature modules (handle sub-routing internally)
- **`components/common/`**, **`components/layout/`** — Shared UI components
- **`services/`** — Axios-based API client functions (one file per domain)
- **`stores/`** — Zustand global state: `movieStore`, `tvShowStore`, `fileStore`, `queueStore`, `uiStore`, `searchStore`, `settingsStore`, `authStore`
- **`context/`** — React contexts: `ThemeContext`, `AuthContext`
- **`types/`** — TypeScript types; `api-schema.ts` is generated from `openapi.json` via `npm run typegen`

TanStack Query handles server-state caching on top of Zustand client state.

---

## Project Structure

```
.
├── app/                              # Backend application
│   ├── main.py                       # FastAPI application entry point
│   ├── services_impl.py              # Service implementations (TMDB enrichment)
│   ├── api/                          # API endpoints
│   │   ├── middleware/               # Request middleware
│   │   └── v1/                       # API version 1
│   │       ├── auth/                 # Authentication endpoints (JWT)
│   │       ├── cache/                # Cache management
│   │       ├── config/               # Configuration
│   │       ├── enrichment/           # Metadata enrichment
│   │       ├── files/                # File management
│   │       ├── health/               # Health checks
│   │       ├── movies/               # Movie endpoints
│   │       ├── organisation/         # Organisation management
│   │       ├── queue/                # Queue management
│   │       ├── storage/              # Storage analytics
│   │       ├── tasks/                # Task management
│   │       └── tv_shows/             # TV show endpoints
│   ├── core/                         # App bootstrap
│   │   ├── config.py                 # pydantic-settings configuration
│   │   ├── database.py               # Database setup
│   │   ├── init_db.py                # Database initialization
│   │   └── logging_config.py         # Logging configuration
│   ├── domain/                       # Business logic
│   │   ├── auth/
│   │   ├── common/
│   │   ├── files/
│   │   ├── movies/
│   │   ├── organisation/
│   │   ├── settings/
│   │   ├── storage/
│   │   └── tv_shows/
│   ├── infrastructure/               # External concerns
│   │   ├── cache/                    # Redis caching
│   │   ├── external_apis/            # TMDB client
│   │   ├── file_system/              # File monitoring, FFprobe, queue
│   │   ├── monitoring/               # Prometheus metrics
│   │   └── security/                 # JWT, password hashing, rate limiting
│   ├── application/                  # Cross-cutting services
│   │   ├── batch_operations/
│   │   ├── db_optimization/
│   │   ├── pattern_recognition/
│   │   └── search/
│   └── tasks/                        # Celery task definitions
│       ├── celery_app.py
│       ├── celery_beat.py
│       └── async_helpers.py
├── frontend/                         # Frontend application
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   ├── dashboard/
│   │   │   ├── features/             # movies/, tvshows/
│   │   │   ├── file/
│   │   │   ├── layout/
│   │   │   ├── queue/
│   │   │   ├── search/
│   │   │   └── settings/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── stores/
│   │   ├── types/
│   │   ├── context/
│   │   └── utils/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── vitest.config.ts
│   ├── playwright.config.ts
│   └── tsconfig.json
├── alembic/                          # Database migrations
│   └── versions/
├── .github/workflows/                # CI/CD pipelines
├── docs/                             # Documentation
│   └── plans/
├── requirements.txt
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
└── .env.example
```
```

**Step 2: Verify the file exists**

```bash
ls docs/ARCHITECTURE.md
```
Expected: file listed.

**Step 3: Stage**

```bash
git add docs/ARCHITECTURE.md
```

---

## Task 2: Create `docs/API_REFERENCE.md`

**Files:**
- Create: `docs/API_REFERENCE.md`

**Step 1: Create the file with this exact content**

```markdown
# API Reference

Interactive documentation is available when the application is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register new user |
| `POST` | `/api/v1/auth/login` | Login (returns JWT access + refresh tokens) |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `POST` | `/api/v1/auth/logout` | Logout |
| `GET` | `/api/v1/auth/me` | Get current user |
| `PUT` | `/api/v1/auth/password` | Change password |

### Movies

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/movies` | List movies |
| `POST` | `/api/v1/movies` | Create movie |
| `GET` | `/api/v1/movies/{id}` | Get movie details |
| `PUT` | `/api/v1/movies/{id}` | Update movie |
| `DELETE` | `/api/v1/movies/{id}` | Delete movie |
| `POST` | `/api/v1/movies/{id}/enrich` | Trigger TMDB metadata enrichment |

### TV Shows

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/tv-shows` | List TV shows |
| `POST` | `/api/v1/tv-shows` | Create TV show |
| `GET` | `/api/v1/tv-shows/{id}` | Get TV show details |
| `PUT` | `/api/v1/tv-shows/{id}` | Update TV show |
| `DELETE` | `/api/v1/tv-shows/{id}` | Delete TV show |
| `POST` | `/api/v1/tv-shows/{id}/enrich` | Trigger TMDB metadata enrichment |

### Files

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/files` | List files |
| `GET` | `/api/v1/files/{id}` | Get file details |
| `POST` | `/api/v1/files/scan` | Trigger directory scan |

### Storage

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/storage/analytics` | Storage analytics |
| `GET` | `/api/v1/storage/usage` | Storage usage by media type |

### Organisation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/organisation` | Get organisation settings |
| `PUT` | `/api/v1/organisation` | Update organisation settings |

### Cache

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/cache` | Cache info |
| `DELETE` | `/api/v1/cache` | Clear all cache |
| `GET` | `/api/v1/cache/{key}` | Get cache value by key |
| `DELETE` | `/api/v1/cache/{key}` | Delete cache key |

### Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/config` | Get configuration |
| `PUT` | `/api/v1/config` | Update configuration |

### Enrichment

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/enrichment/status` | Enrichment queue status |
| `POST` | `/api/v1/enrichment/retry` | Retry failed enrichments |

### Queue

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/queue` | List queue tasks |
| `GET` | `/api/v1/queue/{id}` | Get task details |
| `DELETE` | `/api/v1/queue/{id}` | Cancel task |

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/tasks` | List tasks |
| `GET` | `/api/v1/tasks/{id}` | Get task details |
| `DELETE` | `/api/v1/tasks/{id}` | Delete task |
| `POST` | `/api/v1/tasks/{id}/retry` | Retry failed task |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health/` | Basic health check |
| `GET` | `/health/db` | Database connectivity check |
```

**Step 2: Verify the file exists**

```bash
ls docs/API_REFERENCE.md
```
Expected: file listed.

**Step 3: Stage**

```bash
git add docs/API_REFERENCE.md
```

---

## Task 3: Create `docs/CICD.md`

**Files:**
- Create: `docs/CICD.md`

**Step 1: Create the file with this exact content**

```markdown
# CI/CD Pipeline

MetaMaster uses GitHub Actions for CI and Docker builds, with separate workflow sets for backend and frontend.

---

## Backend Workflows (`.github/workflows/`)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push to main, PRs | Run tests, linting, type checking |
| `docker.yml` | Push to main, tags | Build and push Docker images to GHCR |
| `code-quality.yml` | Push to main, PRs | Codacy code analysis |
| `deploy.yml` | Push to main | Deploy to production |
| `lint.yml` | Push, PRs | Fast linting feedback |
| `scheduled-tests.yml` | Cron (nightly/weekly) | Nightly tests, weekly benchmarks |

## Frontend Workflows (`frontend/.github/workflows/`)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push to main, PRs | Build, test, lint |
| `lighthouse.yml` | Push to main | Performance auditing |
| `security.yml` | Push, schedule | npm audit, CodeQL scanning |
| `storybook.yml` | Push to main | Deploy Storybook to GitHub Pages |

---

## Required GitHub Secrets

Configure these in your repository **Settings → Secrets and variables → Actions**:

| Secret | Purpose |
|--------|---------|
| `SONAR_TOKEN` | SonarQube/Codacy analysis |
| `DOCKER_USERNAME` | Container registry login |
| `DOCKER_PASSWORD` | Container registry password |
| `CODECOV_TOKEN` | Coverage reporting (codecov.io) |

---

## Dependabot

Automated dependency updates are configured for:

- Python dependencies (pip)
- Node.js dependencies (npm)
- Docker base images
- GitHub Actions
```

**Step 2: Verify the file exists**

```bash
ls docs/CICD.md
```
Expected: file listed.

**Step 3: Stage**

```bash
git add docs/CICD.md
```

---

## Task 4: Create `docs/USER_TROUBLESHOOTING.md`

**Files:**
- Create: `docs/USER_TROUBLESHOOTING.md`

**Step 1: Create the file with this exact content**

```markdown
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
2. Check file extensions — only `.mp4 .mkv .avi .mov .flv .wmv .webm .m4v` are scanned
3. Trigger a manual scan: `POST /api/v1/files/scan`
```

**Step 2: Verify the file exists**

```bash
ls docs/USER_TROUBLESHOOTING.md
```
Expected: file listed.

**Step 3: Stage**

```bash
git add docs/USER_TROUBLESHOOTING.md
```

---

## Task 5: Update `README.md`

**Files:**
- Modify: `README.md`

This task has multiple steps. Make each change, then verify, then stage at the end.

**Step 1: Fix the description line (line 8)**

Change:
```
A comprehensive web-based media metadata management system for organizing and managing your movie and TV show library with automatic metadata enrichment from OMDB and TMDB APIs.
```
To:
```
A comprehensive web-based media metadata management system for organizing and managing your movie and TV show library with automatic metadata enrichment from TMDB (The Movie Database).
```

**Step 2: Fix the Features list — remove OMDB reference (line 14)**

Change:
```
- **Metadata Enrichment**: Automatic metadata lookup from OMDB (movies) and TMDB (TV shows)
```
To:
```
- **Metadata Enrichment**: Automatic metadata lookup from TMDB for movies and TV shows
```

**Step 3: Update backend tech stack table (lines 34–48)**

Replace the entire backend tech stack table with:

```markdown
| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Framework** | FastAPI | 0.132.0 | ASGI web framework |
| **ASGI Server** | Uvicorn | 0.41.0 | Production server |
| **Database** | PostgreSQL | 15 | Primary data store |
| **ORM** | SQLAlchemy | 2.0.46 | Database abstraction |
| **Migrations** | Alembic | 1.18.4 | Schema migrations |
| **Task Queue** | Celery | 5.6.2 | Background job processing |
| **Message Broker** | Redis | 7 | Celery broker & caching |
| **HTTP Client** | HTTPX | 0.28.1 | Async HTTP requests |
| **File Monitoring** | Watchdog | 6.0.0 | Directory monitoring |
| **Media Analysis** | FFprobe | system | File metadata extraction |
| **Monitoring** | Prometheus Client | 0.17.1 | Metrics collection |
```

**Step 4: Update the Code Quality — Backend table (lines 97–101)**

Replace with:

```markdown
| Tool | Version | Purpose |
|------|---------|---------|
| Black | 26.1.0 | Code formatter |
| isort | 6.1.0 | Import sorter |
| mypy | 1.19.1 | Static type checker |
| flake8 | 6.1.0 | Linter |
```

**Step 5: Update the Testing — Backend table (lines 113–122)**

Replace with:

```markdown
| Tool | Version | Purpose |
|------|---------|---------|
| pytest | 8.4.2 | Test framework |
| pytest-asyncio | 1.3.0 | Async test support |
| pytest-cov | 4.1.0 | Coverage reporting |
```

**Step 6: Remove the OMDB API key from External API Keys table (lines 163–169)**

Replace the entire External API Keys section with:

```markdown
### External API Keys

| API | Purpose | Get Key |
|-----|---------|---------|
| TMDB API | Movie & TV show metadata | [themoviedb.org](https://www.themoviedb.org/settings/api) |
```

**Step 7: Fix unicode artifacts in Available Commands section**

Change line 301 (the `ß` character before `### Backend Commands`):
```
ß### Backend Commands
```
To:
```
### Backend Commands
```

Change line 322 (the `å` character after "Sort imports"):
```
isort app/                        # Sort importså
```
To:
```
isort app/                        # Sort imports
```

**Step 8: Update environment configuration example (lines 267–295)**

Remove the OMDB section from the env block. Replace the full env block with:

```
# Application
APP_NAME=MetaMaster
DEBUG=False
LOG_LEVEL=INFO

# Database (PostgreSQL for production)
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/metamaster

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# TMDB API (preferred: Bearer JWT token)
TMDB_READ_ACCESS_TOKEN=your_tmdb_read_access_token_here
# TMDB_API_KEY=your_tmdb_v3_api_key_here  # fallback if READ_ACCESS_TOKEN not set
TMDB_RATE_LIMIT=3

# File Monitoring
MOVIE_DIR=/path/to/your/movies
TV_DIR=/path/to/your/tv/shows
WATCH_EXTENSIONS=.mp4,.mkv,.avi,.mov,.flv,.wmv,.webm,.m4v
```

**Step 9: Replace the Project Structure section**

Remove the full "Project Structure" section (the large code block with the folder tree, lines 380–478) and replace with a link to the architecture doc:

```markdown
## Project Structure

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full project structure and architecture details.
```

**Step 10: Replace the CI/CD Pipeline section**

Remove the full "CI/CD Pipeline" section (lines 482–527) and replace with a link:

```markdown
## CI/CD Pipeline

See [docs/CICD.md](docs/CICD.md) for workflow details, required secrets, and Dependabot configuration.
```

**Step 11: Replace the API Documentation section**

Remove the full "Available API Endpoints" section (lines 529–588) and replace with:

```markdown
## API Documentation

Once the application is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

See [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for the full endpoint reference.
```

**Step 12: Add a Documentation section before Contributing**

Insert a new section after the API Documentation section and before Contributing:

```markdown
## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | Backend/frontend architecture, data models, startup flow |
| [API Reference](docs/API_REFERENCE.md) | All REST endpoints |
| [CI/CD](docs/CICD.md) | GitHub Actions workflows, secrets, Dependabot |
| [Troubleshooting](docs/USER_TROUBLESHOOTING.md) | Common issues and fixes |
```

**Step 13: Verify no remaining OMDB references**

```bash
grep -i omdb README.md
```
Expected: no output.

**Step 14: Verify no remaining ffmpeg-python references**

```bash
grep -i "ffmpeg-python\|FFmpeg-Python" README.md
```
Expected: no output.

**Step 15: Stage**

```bash
git add README.md
```

---

## Task 6: Update `frontend/README.md`

**Files:**
- Modify: `frontend/README.md`

**Step 1: Fix `npm format` typo (line 269)**

Change:
```bash
npm format
```
To:
```bash
npm run format
```

**Step 2: Fix broken doc links in the "Getting Help" section (lines 369–371)**

Change:
```markdown
- Check existing [issues](../.github/ISSUE_TEMPLATE/)
- Review [API documentation](../docs/API_REFERENCE.md)
- Consult the [troubleshooting section in the main docs](../docs/USER_TROUBLESHOOTING.md)
```
To:
```markdown
- Check existing [issues](../.github/ISSUE_TEMPLATE/)
- Review [API documentation](../docs/API_REFERENCE.md)
- Consult the [troubleshooting guide](../docs/USER_TROUBLESHOOTING.md)
```

(The links are now valid since those files are being created in Tasks 2 and 4.)

**Step 3: Verify no broken relative links**

```bash
grep -n "\.\./docs/" frontend/README.md
```
Expected: lines referencing `../docs/API_REFERENCE.md` and `../docs/USER_TROUBLESHOOTING.md` (both now exist).

**Step 4: Stage**

```bash
git add frontend/README.md
```

---

## Task 7: Final verification and commit

**Step 1: Verify all new docs exist**

```bash
ls docs/ARCHITECTURE.md docs/API_REFERENCE.md docs/CICD.md docs/USER_TROUBLESHOOTING.md
```
Expected: all four files listed.

**Step 2: Verify no OMDB references remain in any doc**

```bash
grep -ri "omdb" docs/ README.md frontend/README.md
```
Expected: no output.

**Step 3: Verify no ffmpeg-python references remain**

```bash
grep -ri "ffmpeg-python" docs/ README.md frontend/README.md
```
Expected: no output.

**Step 4: Check git status**

```bash
git status
```
Expected: `README.md`, `frontend/README.md`, and all four `docs/*.md` files staged.

**Step 5: Stage the design and plan docs too**

```bash
git add docs/plans/2026-02-27-documentation-overhaul-design.md docs/plans/2026-02-27-documentation-overhaul.md
```

**Step 6: Review staged diff**

```bash
git diff --staged --stat
```
Expected: 6 files changed (4 new docs + 2 updated READMEs + plan files).
