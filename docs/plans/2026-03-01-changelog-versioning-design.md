# Changelog & Version Sync Design

**Date:** 2026-03-01
**Status:** Approved

## Problem

MetaMaster has no changelog, and `frontend/package.json` version (`0.0.0`) is not kept in sync with `pyproject.toml` (`1.0.0`). Releasing is currently just pushing a git tag, with no user-facing release notes.

## Goal

Auto-generate a `CHANGELOG.md` and create a GitHub Release with release notes whenever a `v*` tag is pushed. Keep `pyproject.toml` and `frontend/package.json` in sync automatically as part of the same workflow.

## Design

### Tooling

**`git-cliff`** — Rust binary, understands Conventional Commits natively, configurable via `cliff.toml`. Installed in CI via `taiki-e/install-action`.

### New file: `cliff.toml`

At the repo root. Commit groups:

| Group | Commit types |
|---|---|
| Features | `feat` |
| Bug Fixes | `fix` |
| Refactoring | `refactor` |
| Documentation | `docs` |
| Dependency Updates | `chore(deps)` specifically |
| Other Changes | non-conventional commits |

Skipped (noise): bare `chore:`, `test:`, `style:` commits.

### New workflow: `.github/workflows/release.yml`

Triggers on `push: tags: ['v*']`. Steps:

1. Checkout with `fetch-depth: 0` (git-cliff needs full history)
2. Extract version from tag — strip `v` prefix
3. Patch `pyproject.toml` version with `sed`
4. Patch `frontend/package.json` version with `npm version --no-git-tag-version`
5. Install git-cliff via `taiki-e/install-action`
6. Run `git-cliff -o CHANGELOG.md` — full changelog for all versions
7. Run `git-cliff --latest --strip all` — notes for this release only (saved to `release-notes.md`)
8. Commit `pyproject.toml` + `frontend/package.json` + `CHANGELOG.md` back to `main` with message `chore(release): bump version to X.Y.Z [skip ci]`
9. Create GitHub Release at the tag using `gh release create`, body from `release-notes.md`

Permissions needed: `contents: write`.

### Release workflow (developer)

```bash
git tag v1.2.3
git push origin v1.2.3
```

The Docker build workflow (`docker.yml`) already triggers on the same `v*` tag pattern and runs independently.

## What Is NOT Changed

- `ci.yml` — runs on `main` pushes, unaffected
- `docker.yml` — unchanged, already handles `v*` tags
- How PRs, branches, or merges work
- Commit conventions — already using Conventional Commits
