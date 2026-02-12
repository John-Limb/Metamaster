# Phased Codebase Improvement Plan

## Guiding principles
- Protect the existing UI uplift scope documented in [`docs/UI_REVAMP/README.md`](docs/UI_REVAMP/README.md).
- Keep backend and frontend contracts synchronized via explicit schemas generated from [`app/main.py`](app/main.py:52) OpenAPI metadata.
- Prefer incremental phases so each slice is independently deployable and testable.

## Phase 1 – API contract alignment & critical bug remediation
### Objectives
- Ship fully functional metadata sync endpoints and eliminate 404s coming from mismatched frontend calls.
- Establish a single truth for pagination, search, and health contracts.

### Key workstreams
1. Await async OMDB/TVDB helpers within the FastAPI handlers so `/movies/{id}/sync-metadata` and `/tv-shows/{id}/sync-metadata` actually persist updates [`app/api/v1/movies/endpoints.py`](app/api/v1/movies/endpoints.py:248) [`app/api/v1/tv_shows/endpoints.py`](app/api/v1/tv_shows/endpoints.py:295).
2. Normalize pagination parameters (`limit`/`skip`) or add server support for `page`/`pageSize`, updating both the routers and axios helpers [`app/api/v1/movies/endpoints.py`](app/api/v1/movies/endpoints.py:25) [`frontend/src/services/movieService.ts`](frontend/src/services/movieService.ts:7) [`frontend/src/services/tvShowService.ts`](frontend/src/services/tvShowService.ts:7).
3. Either expose `/movies/genre`, `/movies/popular`, `/tv-shows/top-rated`, etc., or remove those calls from the service layer to prevent persistent 404s [`frontend/src/services/movieService.ts`](frontend/src/services/movieService.ts:43) [`frontend/src/services/tvShowService.ts`](frontend/src/services/tvShowService.ts:43).
4. Realign health endpoints so the dashboard only calls supported routes, or add the richer `/health/system`, `/health/cache`, and `/health/services/:name` endpoints to FastAPI [`frontend/src/services/healthService.ts`](frontend/src/services/healthService.ts:31) [`app/api/v1/health/endpoints.py`](app/api/v1/health/endpoints.py:17).
5. Publish the reconciled OpenAPI schema and generate a typed frontend client (e.g., `openapi-typescript`) so future drift is caught during CI [`pyproject.toml`](pyproject.toml:1) [`frontend/package.json`](frontend/package.json:1).

### Exit criteria
- Frontend smoke tests hit only valid endpoints and all critical API calls succeed end-to-end.
- Metadata sync tasks update DB records successfully and return populated responses.
- Health widget reads real status instead of mock data in [`frontend/src/components/dashboard/Dashboard.tsx`](frontend/src/components/dashboard/Dashboard.tsx:56).

## Phase 2 – Infrastructure hardening & observability
### Objectives
- Remove single-node SQLite bottlenecks and enforce least-privilege networking defaults.
- Capture actionable metrics/logs for Celery, DB, and cache layers.

### Key workstreams
1. Migrate from the shared SQLite file volume to Postgres (or another multi-writer store) and update the deployment manifests plus `.env` samples [`docker-compose.yml`](docker-compose.yml:36) [`app/core/config.py`](app/core/config.py:17).
2. Restrict CORS and TrustedHost origins based on environment variables rather than `*` wildcards [`app/main.py`](app/main.py:117).
3. Refactor Celery tasks to avoid `asyncio.run` per invocation—either reuse a global loop or create synchronous wrappers, preventing worker thread starvation [`app/tasks.py`](app/tasks.py:132).
4. Expand structured logging/metrics exporters so `monitoring_service` feeds Prometheus/OpenTelemetry sinks instead of local JSON only [`app/infrastructure/monitoring/monitoring_service.py`](app/infrastructure/monitoring/monitoring_service.py:1) [`app/core/logging_config.py`](app/core/logging_config.py:1).
5. Add alerting/notification hooks to the TaskError handler (e.g., webhook/email) so critical failures no longer stop at database logging [`app/infrastructure/monitoring/error_handler.py`](app/infrastructure/monitoring/error_handler.py:90).

### Exit criteria
- Celery/worker containers pass load tests without event-loop contention.
- Security review confirms CORS/host policies meet deployment requirements.
- Metrics/alerts visible in the existing monitoring stack.

## Phase 3 – Frontend data realism & UI uplift enablement
### Objectives
- Replace mocked dashboard data with live queries and align with the UI revamp program.
- Ensure state management (Zustand/TanStack Query) reflects backend truth.

### Key workstreams
1. Wire dashboard stats/activities to real APIs (movies count, queue status, storage metrics) once Phase 1 endpoints ship [`frontend/src/components/dashboard/Dashboard.tsx`](frontend/src/components/dashboard/Dashboard.tsx:53).
2. Create reusable hooks/stores for health, queue, and search data so other UI surfaces can consume the same cached responses [`frontend/src/stores`](frontend/src/stores:1) [`frontend/src/hooks`](frontend/src/hooks:1).
3. Sync the UI uplift documentation with the new backend contracts, referencing shared components and tokens defined in [`docs/UI_REVAMP/01_DESIGN_SYSTEM.md`](docs/UI_REVAMP/01_DESIGN_SYSTEM.md:1).
4. Add Storybook stories/e2e tests for the real data states (loading, empty, error) to keep regressions from reintroducing mock fallbacks [`frontend/.storybook`](frontend/.storybook:1).

### Exit criteria
- Dashboard visuals reflect live data and degrade gracefully under API failures.
- UI uplift checkpoints reference the same components/services used in production code.

## Phase 4 – Platform readiness & automation
### Objectives
- Bake the improvements into CI/CD and operational playbooks.

### Key workstreams
1. Extend CI to run generated-client drift checks plus contract tests comparing frontend fixtures to FastAPI responses [`frontend/package.json`](frontend/package.json:1) [`pyproject.toml`](pyproject.toml:1).
2. Add load/soak tests for Celery tasks and metadata sync workflows using the new Postgres backend [`app/tasks.py`](app/tasks.py:274).
3. Update disaster-recovery and deployment docs to match the hardened architecture while keeping the dedicated UI uplift documentation untouched [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md:1) [`docs/UI_REVAMP/README.md`](docs/UI_REVAMP/README.md:1).

### Exit criteria
- Pipelines fail fast on API contract drift and regenerated clients stay in sync.
- Runbooks accurately describe the new infra path and on-call teams rely on alerting hooks.

## Current bug tracker (carried into Phase 1)
1. Metadata sync endpoints return coroutine objects and never persist data [`app/api/v1/movies/endpoints.py`](app/api/v1/movies/endpoints.py:248) [`app/api/v1/tv_shows/endpoints.py`](app/api/v1/tv_shows/endpoints.py:295).
2. Frontend health service calls unsupported routes (`/health/system`, `/health/cache`, etc.) and always fails [`frontend/src/services/healthService.ts`](frontend/src/services/healthService.ts:31).
3. Pagination/search parameter mismatch between frontend services and backend routers causes silent fallback to defaults [`frontend/src/services/movieService.ts`](frontend/src/services/movieService.ts:7) [`app/api/v1/movies/endpoints.py`](app/api/v1/movies/endpoints.py:25).
4. React services invoke nonexistent `/popular`, `/top-rated`, and `/genre/:name` endpoints, producing 404s [`frontend/src/services/movieService.ts`](frontend/src/services/movieService.ts:43) [`frontend/src/services/tvShowService.ts`](frontend/src/services/tvShowService.ts:43).
5. Dashboard still depends on mocked data even when backend is reachable, hiding regressions [`frontend/src/components/dashboard/Dashboard.tsx`](frontend/src/components/dashboard/Dashboard.tsx:56).
6. Cache warmup endpoint imports methods that do not exist on the re-exported TV show service, leading to runtime AttributeErrors [`app/api/v1/cache/endpoints.py`](app/api/v1/cache/endpoints.py:225) [`app/services_impl.py`](app/services_impl.py:1).

---
This plan supersedes previous review documents (other than the UI uplift materials) and should be treated as the authoritative roadmap for remediation.
