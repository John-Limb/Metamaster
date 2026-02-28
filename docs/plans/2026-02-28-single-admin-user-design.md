# Single Admin User Design

**Date:** 2026-02-28
**Status:** Approved

## Problem

MetaMaster currently exposes a public `/register` endpoint and a "Create account" link on the login page. For a self-hosted single-user media manager this is unnecessary and a security risk — any visitor can create an account.

## Goal

Lock the system to a single admin user. Remove all self-registration paths. Provide a secure in-container CLI to reset the admin password when access is lost.

## Design

### Backend

**Remove registration endpoint:**
- Delete `POST /api/v1/auth/register` from `app/api/v1/auth/endpoints.py`
- Remove unused `UserRegisterRequest` import from `endpoints.py`
  (schema stays — `create_user` in `AuthService` and `init_db.py` still use it internally)

**Add password reset CLI (`app/core/reset_password.py`):**
- Runnable as `python -m app.core.reset_password` inside the container
- Generates a new 16-char random password (same `generate_random_password` from `init_db.py`)
- Updates admin's `password_hash`, sets `requires_password_change=True`
- Revokes all existing refresh tokens (`revoke_all_user_tokens`)
- Prints new credentials prominently to stdout
- Exits with code 1 if no admin user exists

### Frontend

- Remove `/register` route from `App.tsx`; delete the lazy import for `RegisterPage`
- Remove "Create one" link (`to="/register"`) from `LoginForm.tsx`
- Delete `frontend/src/pages/RegisterPage.tsx`
- Delete `frontend/src/components/auth/RegisterForm.tsx`
- Update `LoginForm.test.tsx`: remove assertion that register link exists

### Documentation

**New file `docs/ADMIN.md`:**
- How admin account is bootstrapped (auto-created on first run, password printed to docker logs)
- How to reset the admin password: `docker exec MetaMaster_app python -m app.core.reset_password`
- The `requires_password_change` flow (forced password change on first/reset login)
- Security notes (single-user only, no self-registration)

**Updates to existing docs:**
- `docs/ARCHITECTURE.md` — auth section: note single-user/admin-only model
- `README.md` — add `ADMIN.md` to the Documentation table
- `docs/API_REFERENCE.md` — remove `POST /api/v1/auth/register` row

## What Is NOT Changed

- Login, logout, refresh token, change-password, profile endpoints — all stay
- `AuthService.create_user` — stays (used by `init_db.py` seeding only)
- `UserRegisterRequest` schema — stays (used internally)
- Admin auto-creation on first run in `init_db.py` — stays as-is
