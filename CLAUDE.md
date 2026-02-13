# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MetaMaster is a full-stack media metadata management system. FastAPI backend with PostgreSQL/Redis, React frontend with TypeScript/Vite. It monitors directories for media files, enriches metadata from OMDB (movies) and TVDB (TV shows), and analyzes files with FFprobe.

## Common Commands

### Frontend (run from `frontend/`)

| Task | Command |
|------|---------|
| Dev server | `npm run dev` (port 5173) |
| Build | `npm run build` |
| Lint | `npm run lint` |
| Lint fix | `npm run lint:fix` |
| Format | `npm run format` |
| Type check | `npm run type-check` |
| Run all tests | `npm test` |
| Run single test | `npx vitest run path/to/file.test.ts` |
| Watch mode | `npm run test:watch` |
| Coverage | `npm run test:coverage` |
| E2E tests | `npm run test:e2e` |
| Regenerate API types | `npm run typegen` |

### Backend (run from project root)

| Task | Command |
|------|---------|
| Dev server | `uvicorn app.main:app --reload` |
| Run all tests | `pytest` |
| Run single test | `pytest tests/path/to/test_file.py::test_name` |
| Run by marker | `pytest -m unit` / `pytest -m integration` |
| Format | `black .` |
| Sort imports | `isort .` |
| Lint | `flake8` |
| Type check | `mypy app/` |
| DB migrations | `alembic upgrade head` |

### Docker

- Full stack: `docker-compose up -d`
- Dev with debug ports: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d`

## Architecture

### Backend (`app/`)

Clean architecture with four layers:

- **`api/v1/`** — FastAPI route handlers organized by domain (auth, movies, tv_shows, files, cache, health, tasks, config)
- **`domain/`** — Business logic and models (common, files, movies, tv_shows, auth)
- **`application/`** — Application services (batch_operations, db_optimization, pattern_recognition, search)
- **`infrastructure/`** — External integrations (cache via Redis, external_apis for OMDB/TVDB, file_system via Watchdog, monitoring via Prometheus)
- **`core/`** — Config (Pydantic settings), database setup (SQLAlchemy 2.0), logging (structlog)
- **`tasks/`** — Celery task definitions with Redis as broker

Auth: JWT access tokens (15 min) + refresh tokens (7 day) in httpOnly cookies. Argon2 password hashing. Rate limiting on auth endpoints.

### Frontend (`frontend/src/`)

- **`pages/`** — Route-level page components
- **`components/`** — Organized by feature area (auth, file, settings, layout, features)
- **`services/`** — API service layer (authService, fileService, movieService, tvShowService)
- **`stores/`** — Zustand stores for client state (fileStore, movieStore, tvShowStore, uiStore)
- **`context/`** — React Context providers (AuthContext, ThemeContext, ConfigurationContext)
- **`hooks/`** — Custom React hooks
- **`types/`** — TypeScript type definitions; `api-schema.ts` is auto-generated from OpenAPI spec
- **`utils/api.ts`** — Axios client singleton with interceptors for auth headers, retry logic, and request ID tracking

State management pattern: Zustand for client/UI state, TanStack Query for server state caching. React Router v7 with lazy-loaded routes.

### Key Integration Points

- Frontend API base URL configured via `VITE_API_BASE_URL` (defaults to `http://localhost:8000/api/v1`)
- Backend settings driven by environment variables via Pydantic `Settings` in `app/core/config.py`
- Path alias `@/` maps to `frontend/src/` (configured in vite.config.ts and tsconfig)

## Code Style

- **Backend**: Black formatter (line length 100), isort with black profile, Python 3.9+
- **Frontend**: ESLint 9 flat config + Prettier, TypeScript strict mode, Husky pre-commit hooks with lint-staged
- **Commits**: Conventional Commits format (`feat:`, `fix:`, `chore:`, etc.)
- **Coverage threshold**: 80% minimum (frontend via Vitest config)

## Testing

- **Backend markers**: `unit`, `integration`, `e2e`, `slow`, `performance`, `database`, `redis`, `external_api`, `docker`
- **Frontend**: Vitest + Testing Library (unit/component), Playwright (E2E)
- **Backend**: pytest + pytest-asyncio (async tests auto mode)

<!-- WEDNESDAY_SKILLS_START -->
## Wednesday Agent Skills

This project uses Wednesday Solutions agent skills for consistent code quality and design standards.

### Available Skills

<available_skills>
  <skill>
    <name>wednesday-design</name>
    <description>Design and UX guidelines for Wednesday Solutions projects. Covers visual design tokens, animation patterns, component standards, accessibility, and user experience best practices for React/Next.js applications. ENFORCES use of approved component libraries only.</description>
    <location>.wednesday/skills/wednesday-design/SKILL.md</location>
  </skill>
  <skill>
    <name>wednesday-dev</name>
    <description>Technical development guidelines for Wednesday Solutions projects. Enforces import ordering, complexity limits, naming conventions, TypeScript best practices, and code quality standards for React/Next.js applications.</description>
    <location>.wednesday/skills/wednesday-dev/SKILL.md</location>
  </skill>
</available_skills>

### How to Use Skills

When working on tasks, check if a relevant skill is available above. To activate a skill, read its SKILL.md file to load the full instructions.

For example:
- For code quality and development guidelines, read: .wednesday/skills/wednesday-dev/SKILL.md
- For design and UI component guidelines, read: .wednesday/skills/wednesday-design/SKILL.md

### Important

- The wednesday-design skill contains 492+ approved UI components. Always check the component library before creating custom components.
- The wednesday-dev skill enforces import ordering, complexity limits (max 8), and naming conventions.

<!-- WEDNESDAY_SKILLS_END -->