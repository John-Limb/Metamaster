# CI/CD Pipeline

MetaMaster uses GitHub Actions for CI and Docker builds, with separate workflow sets for backend and frontend.

---

## Backend Workflows (`.github/workflows/`)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push to main | Run tests, linting, type checking |
| `docker.yml` | Push to main, tags | Build and push Docker images to GHCR |
| `release.yml` | Tags (`v*`) | Bump versions, generate changelog, create GitHub Release |
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

---

## Cutting a Release

1. Ensure all changes are merged to `main`
2. Push a semantic version tag:

   ```bash
   git tag v1.2.3
   git push origin v1.2.3
   ```

3. The `release.yml` workflow fires automatically and:
   - Bumps `pyproject.toml` and `frontend/package.json` to match the tag version
   - Regenerates `CHANGELOG.md` from all commits using `git-cliff`
   - Commits those files back to `main` with `[skip ci]`
   - Creates a GitHub Release with notes for this version only

4. The `docker.yml` workflow fires in parallel, building and pushing the Docker image tagged `1.2.3`, `sha-<hash>`, and `latest`

> **Note:** The version-bump commit is pushed directly to `main`. If branch protection requires pull requests, the workflow will fail at that step. In that case, grant the `GITHUB_TOKEN` bypass permissions in your branch protection settings.
