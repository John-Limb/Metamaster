# Architecture

## Backend

The backend is a layered Python/FastAPI application under `app/`:

- **`api/v1/`** — FastAPI routers by domain: `auth/`, `movies/`, `tv_shows/`, `files/`, `queue/`, `enrichment/`, `storage/`, `organisation/`, `cache/`, `config/`, `health/`, `tasks/`
- **`domain/`** — Core business logic. Core media domains (`movies/`, `tv_shows/`) each have `models.py` (SQLAlchemy ORM), `schemas.py` (Pydantic), `service.py`, and `scanner.py`. The `files/` domain has `models.py` and `service.py`. Other domains (`auth/`, `organisation/`, `storage/`, `settings/`) contain only the files relevant to their scope.
- **`infrastructure/`** — External concerns: `cache/` (Redis), `external_apis/` (reserved for external API clients), `file_system/` (file monitoring, FFprobe wrapper, queue manager), `monitoring/` (Prometheus), `security/` (JWT, password hashing, rate limiting)
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

1. Initialize database (SQLAlchemy `create_all`)
2. Sync media directories
3. Run file scanners
4. Dispatch enrichment tasks for pending items
5. Initialize Celery

### Authentication

JWT-based. Access tokens expire after 15 minutes; refresh tokens after 7 days. `jwt_secret_key` and `internal_api_key` are **auto-generated at startup** and are not persisted — they reset on every restart.

### Media Paths

Fixed container paths: `/media/movies` and `/media/tv`. These are Docker volume mount points configured as constants in `app/core/config.py`, not environment variables.

### Metadata Enrichment

All metadata enrichment uses **TMDB** (The Movie Database). TMDB API calls are made directly from `app/services_impl.py` via HTTPX.

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
- **`hooks/`** — Custom React hooks
- **`utils/`** — Utility functions

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
│   │   ├── external_apis/            # Reserved for external API clients
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
│   │   │   ├── auth/
│   │   │   ├── common/
│   │   │   ├── configuration/
│   │   │   ├── dashboard/
│   │   │   ├── features/             # movies/, tvshows/
│   │   │   ├── file/
│   │   │   ├── layout/
│   │   │   ├── queue/
│   │   │   ├── search/
│   │   │   └── settings/
│   │   ├── assets/
│   │   ├── config/
│   │   ├── context/
│   │   ├── hooks/
│   │   ├── infrastructure/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── stores/
│   │   ├── styles/
│   │   ├── test/
│   │   ├── types/
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
