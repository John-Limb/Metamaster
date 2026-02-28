# Documentation Overhaul Design

**Date:** 2026-02-27
**Status:** Approved

## Overview

Refactor and update all project documentation. The main README becomes a shorter overview with links to dedicated docs files. Four new docs are created covering architecture, API reference, CI/CD, and troubleshooting.

## Files Changed/Created

| Action | File |
|--------|------|
| Update (refactor shorter) | `README.md` |
| Update (fix inaccuracies) | `frontend/README.md` |
| Create new | `docs/ARCHITECTURE.md` |
| Create new | `docs/API_REFERENCE.md` |
| Create new | `docs/CICD.md` |
| Create new | `docs/USER_TROUBLESHOOTING.md` |

## README.md Changes

### Sections Kept (updated in place)
- Intro/description — remove OMDB, TMDB only
- Features list — remove OMDB reference on line 14
- Tech stack tables — update all versions to match requirements.txt/package.json; remove ffmpeg-python row; remove structlog row
- Prerequisites — remove OMDB API key row
- Installation & Setup (Quick Start + Manual)
- Environment config — remove OMDB_API_KEY and OMDB_RATE_LIMIT vars
- Available Commands — fix `ß` on line 301, fix `å` on line 322
- Contributing guidelines
- License
- New "Documentation" section with links to all four new docs

### Sections Removed (extracted)
- Full architecture + folder tree → docs/ARCHITECTURE.md
- API endpoint table → docs/API_REFERENCE.md
- CI/CD workflow details → docs/CICD.md

## docs/ARCHITECTURE.md

- Backend layered architecture description
- Frontend structure description
- Data models: Movie → MovieFile, TVShow → Season → Episode → EpisodeFile
- Startup flow (init DB → sync dirs → scanners → enrichment → Celery)
- Auth details (JWT 15min access / 7-day refresh, auto-generated secrets)
- Detailed project folder tree

## docs/API_REFERENCE.md

- Swagger/ReDoc links at top
- Endpoint tables organized by category: auth, movies, tv-shows, files, storage, organisation, cache, config, enrichment, queue, tasks, health

## docs/CICD.md

- Backend workflow table (ci.yml, docker.yml, code-quality.yml, deploy.yml, lint.yml, scheduled-tests.yml)
- Frontend workflow table (ci.yml, lighthouse.yml, security.yml, storybook.yml)
- Required GitHub secrets table
- Dependabot configuration note

## docs/USER_TROUBLESHOOTING.md

- Common issues from both READMEs consolidated
- API not reachable / CORS errors
- TypeScript errors
- Dependency install issues
- Test failures
- Backend-specific: DB connectivity, Celery worker not running, Redis connection

## frontend/README.md Changes

- Fix `npm format` → `npm run format` (line 269)
- Fix broken links: `../docs/API_REFERENCE.md` and `../docs/USER_TROUBLESHOOTING.md` (these will now exist)
- Remove broken link to `../docs/USER_TROUBLESHOOTING.md` issue template fallback
