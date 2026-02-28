# CI/CD Pipeline

MetaMaster uses GitHub Actions for CI and Docker builds, with separate workflow sets for backend and frontend.

---

## Backend Workflows (`.github/workflows/`)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push to main | Run tests, linting, type checking |
| `docker.yml` | Push to main, tags | Build and push Docker images to GHCR |
| `lint.yml` | Push, PRs | Fast linting feedback |

## Frontend Workflows (`frontend/.github/workflows/`)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `FrontEndTest-Lint.yml` | Push to main, PRs | Build, test, lint, coverage reporting |
| `FrontEndsecurity.yml` | Push, schedule | npm audit, CodeQL scanning |

---

## Required GitHub Secrets

Configure these in your repository **Settings → Secrets and variables → Actions**:

| Secret | Purpose |
|--------|---------|
| `CODECOV_TOKEN` | Coverage reporting (codecov.io) — used in `FrontEndTest-Lint.yml` |

---

## Dependabot

Automated dependency updates are configured for:

- Python dependencies (pip)
- Docker base images
- GitHub Actions
