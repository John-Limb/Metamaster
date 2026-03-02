# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MetaMaster is a full-stack media metadata management system. It scans local directories for movies and TV shows, enriches them with metadata from **TMDB** (The Movie Database), and provides a web UI to browse and manage your library.

> Note: The README mentions OMDB/TVDB but the active enrichment code (`app/tasks/enrichment.py`, `app/services_impl.py`) uses TMDB. Legacy client stubs remain in `app/infrastructure/external_apis/omdb/` and `app/infrastructure/external_apis/tvdb/`.

## Hard limits
1. ≤80 lines/function, cyclomatic complexity ≤8
2. ≤5 positional params, ≤12 branches, ≤6 returns

## Architecture

### Backend (Python / FastAPI)

Layered architecture under `app/`:

- **`api/v1/`** — FastAPI routers organized by domain (`movies/`, `tv_shows/`, `files/`, `auth/`, `queue/`, `enrichment/`, `storage/`, `organisation/`)
- **`domain/`** — Core business logic. Each domain (`movies/`, `tv_shows/`, `files/`) has `models.py` (SQLAlchemy ORM), `schemas.py` (Pydantic), `service.py`, and `scanner.py`
- **`infrastructure/`** — External concerns: `cache/` (Redis), `external_apis/` (TMDB/OMDB/TVDB clients), `file_system/` (file monitoring, FFPROBE wrapper), `monitoring/` (Prometheus)
- **`application/`** — Cross-cutting services: `search/`, `batch_operations/`, `pattern_recognition/`, `db_optimization/`
- **`tasks/`** — Celery: `celery_app.py` (config), `enrichment.py` (TMDB enrichment tasks), `celery_beat.py` (scheduled tasks)
- **`core/`** — App bootstrap: `config.py` (pydantic-settings), `database.py`, `init_db.py`, `logging_config.py`

**Data model:** `Movie` → `MovieFile` (1:many); `TVShow` → `Season` → `Episode` → `EpisodeFile` (nested 1:many). Both movies and TV shows have an `enrichment_status` enum: `pending_local → local_only → pending_external → fully_enriched / not_found / external_failed`.

**Startup flow** (`app/main.py` lifespan): init DB → sync media directories → run scanners → dispatch enrichment for pending items → init Celery.

**Media paths** are fixed container paths (`/media/movies`, `/media/tv`) bound via Docker volume mounts. Configured in `app/core/config.py` as constants, not env vars.

**Auth:** JWT (access 15 min / refresh 7 days). `jwt_secret_key` and `internal_api_key` are auto-generated at startup — they are not persisted and reset on restart.

### Frontend (React / TypeScript)

Under `frontend/src/`:

- **`App.tsx`** — Route definitions. All routes except `/login` and `/register` are wrapped in `ProtectedRoute` + `MainLayout`. Pages are lazy-loaded.
- **`pages/`** — Top-level page components (one per route)
- **`components/features/`** — `movies/` and `tvshows/` feature modules (handle sub-routing internally with `/*`)
- **`components/common/`**, **`components/layout/`** — Shared UI
- **`services/`** — API client functions (axios-based, one file per domain)
- **`stores/`** — Zustand global state stores (`movieStore`, `tvShowStore`, `fileStore`, `queueStore`, `uiStore`, `searchStore`, `settingsStore`/`authStore`)
- **`context/`** — React contexts: `ThemeContext`, `AuthContext`
- **`types/`** — TypeScript types; `api-schema.ts` is generated from `openapi.json` via `npm run typegen`

TanStack Query handles server-state caching on top of the Zustand client state.

## Development Commands

### Backend

```bash
# Run dev server
uvicorn app.main:app --reload

# Run all tests
pytest

# Run a single test file
pytest tests/test_models_unit.py

# Run tests by marker
pytest -m unit
pytest -m "not slow"

# With coverage
pytest --cov=app

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "Description"
alembic downgrade -1

# Code quality (run before committing)
black app/ && isort app/ && flake8 app/ && mypy app/

# Celery worker (required for enrichment tasks)
celery -A app.tasks.celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend

npm run dev             # Dev server at http://localhost:5173
npm run build           # Production build
npm run type-check      # TypeScript check

npm run test            # Run unit tests (Vitest)
npm run test:watch      # Watch mode
npm run test:coverage   # With coverage

npm run lint            # ESLint
npm run lint:fix        # Auto-fix lint issues
npm run format          # Prettier

npm run typegen         # Regenerate API types from openapi.json
```

### Docker

```bash
docker-compose up -d           # Start all services
docker-compose up -d --build   # Rebuild and start
docker-compose logs -f app     # Backend logs
docker-compose down            # Stop
```

## Key Configuration

- Config is loaded via `pydantic-settings` from `.env` (see `app/core/config.py`)
- **TMDB:** Set `TMDB_READ_ACCESS_TOKEN` (preferred, Bearer JWT) or `TMDB_API_KEY` (v3 fallback)
- **Database:** `DATABASE_URL` defaults to PostgreSQL. Tests also use PostgreSQL via `TEST_DATABASE_URL` env var (defaults to `postgresql+psycopg2://test:test@localhost:5432/metamaster_test`; set automatically in CI)
- **CORS/Trusted Hosts:** Extend `allowed_origins` and `trusted_hosts` in `.env` for non-local deployments (comma-separated strings)

## Git Workflow

**Always stage changes (`git add`), never commit.** Commits require a GPG password that only the user can provide — stage the files and let the user commit.

**All changes must pass linting locally before being staged, regardless of branch.**

- Backend: `black app/ && isort app/ && flake8 app/ && mypy app/`
- Frontend: `cd frontend && npm run lint`

Do not stage files that introduce new lint errors. If existing lint debt is present in a file you haven't touched, it does not need to be fixed as part of an unrelated change — but any code you write or modify must be clean.

## Commit Convention

Follows Conventional Commits: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example: `feat(api): add batch movie import endpoint`
