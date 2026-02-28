# Single Admin User Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Lock MetaMaster to a single admin user by removing the public registration endpoint and UI, and adding an in-container CLI to reset the admin password.

**Architecture:** Remove `POST /api/v1/auth/register` from the FastAPI router. Create `app/core/reset_password.py` as a standalone CLI script that uses the existing `AuthService` and `init_db` helpers. On the frontend, delete the `RegisterPage`/`RegisterForm` components and strip all registration links and routes.

**Tech Stack:** Python / FastAPI (backend), React / TypeScript / Vitest (frontend), pytest (backend tests).

---

## Context

- Design doc: `docs/plans/2026-02-28-single-admin-user-design.md`
- Worktree: `.worktrees/feat/single-admin-user` (branch `feat/single-admin-user`)
- Baseline: 78 backend tests passing (pre-existing broken imports in `app.services` are unrelated — run `pytest tests/domain/ tests/test_models_unit.py tests/test_schemas_unit.py tests/test_utils_unit.py` to avoid those).
- Frontend tests: `cd frontend && npm run test` — all pass at baseline.
- Password hashing: `hash_password()` from `app.domain.auth.service`
- Random password generation: `generate_random_password()` from `app.core.init_db`
- Token revocation: `AuthService.revoke_all_user_tokens(user_id)` → returns count (int)
- DB session: `SessionLocal` from `app.core.database`
- Admin user in DB: `username == "admin"` (always set by `init_db.py`)

---

## Task 1: Remove the backend register endpoint

**Files:**
- Modify: `app/api/v1/auth/endpoints.py`

### Step 1: Remove the `register` function (lines 92–159) from `endpoints.py`

Delete the entire `@router.post("/register", ...)` block. It starts at line 92 and ends at line 159.

**Step 2: Remove `UserRegisterRequest` from the import block**

Change the schema import at the top of `endpoints.py` from:

```python
from app.domain.auth.schemas import (
    ChangePasswordRequest,
    LoginResponse,
    MessageResponse,
    TokenResponse,
    UpdateProfileRequest,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
```

To:

```python
from app.domain.auth.schemas import (
    ChangePasswordRequest,
    LoginResponse,
    MessageResponse,
    TokenResponse,
    UpdateProfileRequest,
    UserLoginRequest,
    UserResponse,
)
```

**Step 3: Remove the `"register"` rate limit key from the rate limiter if only used here**

Check `app/infrastructure/security/rate_limiter.py` — if `RATE_LIMITS["register"]` is defined there, leave it (no need to clean up the dict entry). Just confirm the import `RATE_LIMITS` still works after removing the endpoint.

**Step 4: Verify the backend still starts cleanly**

```bash
cd /Users/john/Code/Metamaster/.worktrees/feat/single-admin-user
python -c "from app.api.v1.auth.endpoints import router; print('OK')"
```

Expected: `OK`

**Step 5: Run the safe backend test subset**

```bash
pytest tests/domain/ tests/test_models_unit.py tests/test_schemas_unit.py tests/test_utils_unit.py -v
```

Expected: all passing (same count as baseline — 78).

**Step 6: Stage and commit**

```bash
git add app/api/v1/auth/endpoints.py
git commit -m "feat(auth): remove POST /register endpoint"
```

---

## Task 2: Create the password reset CLI

**Files:**
- Create: `app/core/reset_password.py`
- Create: `tests/test_reset_password.py`

### Step 1: Write the failing test first

Create `tests/test_reset_password.py`:

```python
"""Tests for the admin password reset CLI."""
import sys
from unittest.mock import MagicMock, patch

import pytest


def test_reset_admin_password_updates_hash_and_revokes_tokens(capsys):
    """Happy path: admin user found, password_hash updated, tokens revoked."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "admin"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    mock_auth_service = MagicMock()
    mock_auth_service.revoke_all_user_tokens.return_value = 3

    with (
        patch("app.core.reset_password.SessionLocal", return_value=mock_db),
        patch(
            "app.core.reset_password.generate_random_password",
            return_value="TestPass1!",
        ),
        patch("app.core.reset_password.hash_password", return_value="hashed_value"),
        patch("app.core.reset_password.AuthService", return_value=mock_auth_service),
    ):
        from app.core.reset_password import reset_admin_password

        reset_admin_password()

    assert mock_user.password_hash == "hashed_value"
    assert mock_user.requires_password_change is True
    mock_db.commit.assert_called_once()
    mock_auth_service.revoke_all_user_tokens.assert_called_once_with(1)

    captured = capsys.readouterr()
    assert "TestPass1!" in captured.out
    assert "admin" in captured.out


def test_reset_admin_password_exits_when_no_admin(capsys):
    """No admin user in DB: print error and exit with code 1."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with (
        patch("app.core.reset_password.SessionLocal", return_value=mock_db),
        pytest.raises(SystemExit) as exc_info,
    ):
        from app.core.reset_password import reset_admin_password

        reset_admin_password()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "No admin user found" in captured.out


def test_reset_admin_password_closes_db_on_exception(capsys):
    """DB session is always closed, even if an exception occurs mid-reset."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = RuntimeError(
        "DB exploded"
    )

    with (
        patch("app.core.reset_password.SessionLocal", return_value=mock_db),
        pytest.raises(RuntimeError),
    ):
        from app.core.reset_password import reset_admin_password

        reset_admin_password()

    mock_db.close.assert_called_once()
```

**Step 2: Run the tests — verify they FAIL**

```bash
pytest tests/test_reset_password.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.core.reset_password'`

**Step 3: Create `app/core/reset_password.py`**

```python
"""Admin password reset CLI.

Resets the admin password and revokes all existing refresh tokens.
Run inside the container:

    python -m app.core.reset_password
"""

import sys

from app.core.database import SessionLocal
from app.core.init_db import generate_random_password
from app.domain.auth.models import User
from app.domain.auth.service import AuthService, hash_password


def reset_admin_password() -> None:
    """Reset the admin password and revoke all existing refresh tokens.

    Generates a new random password, updates the admin user record,
    sets requires_password_change=True, and revokes all refresh tokens.
    Prints new credentials to stdout.

    Exits with code 1 if the admin user does not exist.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").first()
        if user is None:
            print("No admin user found. Has the application been initialised?")
            sys.exit(1)

        new_password = generate_random_password()
        user.password_hash = hash_password(new_password)
        user.requires_password_change = True
        db.commit()

        auth_service = AuthService(db)
        revoked = auth_service.revoke_all_user_tokens(user.id)

        print("=" * 60)
        print("Admin password reset successfully.")
        print(f"  Username       : admin")
        print(f"  Password       : {new_password}")
        print(f"  Tokens revoked : {revoked}")
        print("You will be prompted to set a new password on next login.")
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    reset_admin_password()
```

**Step 4: Run the tests — verify they PASS**

```bash
pytest tests/test_reset_password.py -v
```

Expected: 3 tests passing.

**Step 5: Run the full safe test suite**

```bash
pytest tests/domain/ tests/test_models_unit.py tests/test_schemas_unit.py tests/test_utils_unit.py tests/test_reset_password.py -v
```

Expected: all passing.

**Step 6: Stage and commit**

```bash
git add app/core/reset_password.py tests/test_reset_password.py
git commit -m "feat(auth): add admin password reset CLI"
```

---

## Task 3: Remove the frontend /register route and delete dead components

**Files:**
- Modify: `frontend/src/App.tsx`
- Delete: `frontend/src/pages/RegisterPage.tsx`
- Delete: `frontend/src/components/auth/RegisterForm.tsx`

### Step 1: Run the frontend tests before touching anything

```bash
cd /Users/john/Code/Metamaster/.worktrees/feat/single-admin-user/frontend
npm run test -- --run
```

Expected: all passing.

**Step 2: Remove the `RegisterPage` import from `App.tsx`**

In `frontend/src/App.tsx`, delete line 13:

```tsx
// DELETE this line:
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
```

**Step 3: Remove the `/register` route block from `App.tsx`**

Delete the entire route block (lines 46–53):

```tsx
// DELETE this entire block:
<Route
  path="/register"
  element={
    <Suspense fallback={<LoadingFallback />}>
      <RegisterPage />
    </Suspense>
  }
/>
```

**Step 4: Delete `RegisterPage.tsx`**

```bash
rm frontend/src/pages/RegisterPage.tsx
```

**Step 5: Delete `RegisterForm.tsx`**

```bash
rm frontend/src/components/auth/RegisterForm.tsx
```

**Step 6: Check for any remaining references**

```bash
grep -r "RegisterPage\|RegisterForm\|/register" frontend/src --include="*.tsx" --include="*.ts"
```

Expected: no matches (the LoginForm register link will be removed in Task 4).

**Step 7: Run TypeScript check**

```bash
npm run type-check
```

Expected: no errors.

**Step 8: Run frontend tests**

```bash
npm run test -- --run
```

Expected: all passing. (The `LoginForm.test.tsx` register link test still passes here because we haven't touched `LoginForm.tsx` yet — it will fail after Task 4, which is intentional TDD order.)

**Step 9: Stage and commit**

```bash
cd /Users/john/Code/Metamaster/.worktrees/feat/single-admin-user
git add frontend/src/App.tsx
git rm frontend/src/pages/RegisterPage.tsx
git rm frontend/src/components/auth/RegisterForm.tsx
git commit -m "feat(frontend): remove /register route and delete registration components"
```

---

## Task 4: Remove the register link from LoginForm and update its test

**Files:**
- Modify: `frontend/src/components/auth/LoginForm.tsx`
- Modify: `frontend/src/components/auth/__tests__/LoginForm.test.tsx`

### Step 1: Delete the register link test (make the test file accurate first)

In `frontend/src/components/auth/__tests__/LoginForm.test.tsx`, delete the test at lines 67–72:

```tsx
// DELETE this entire test:
it('should render link to registration page', () => {
  renderWithRouter(<LoginForm />)

  expect(screen.getByText(/don't have an account/i)).toBeInTheDocument()
  expect(screen.getByRole('link', { name: /create one/i })).toHaveAttribute('href', '/register')
})
```

**Step 2: Run the tests — verify they FAIL**

```bash
cd /Users/john/Code/Metamaster/.worktrees/feat/single-admin-user/frontend
npm run test -- --run
```

Expected: the deleted test is gone but the remaining tests still pass. (The register link still exists in `LoginForm.tsx` at this point so the file currently passes. This step just removes the outdated test assertion.)

Actually — re-check: since we deleted the test, they should still pass. Now we make them test the correct behaviour.

**Step 3: Remove the register link section from `LoginForm.tsx`**

In `frontend/src/components/auth/LoginForm.tsx`, delete the entire footer section (lines 179–189):

```tsx
// DELETE this entire block:
<div className="mt-6 text-center">
  <p className="text-sm text-secondary-600 dark:text-secondary-400">
    Don't have an account?{' '}
    <Link
      to="/register"
      className="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300 focus:outline-none focus:underline"
    >
      Create one
    </Link>
  </p>
</div>
```

**Step 4: Remove the unused `Link` import from `LoginForm.tsx`**

Change line 5 from:

```tsx
import { Link, useNavigate, useLocation } from 'react-router-dom'
```

To:

```tsx
import { useNavigate, useLocation } from 'react-router-dom'
```

**Step 5: Run TypeScript check**

```bash
npm run type-check
```

Expected: no errors.

**Step 6: Run frontend tests**

```bash
npm run test -- --run
```

Expected: all passing. The register link test is gone; remaining tests confirm login form fields and error display still work.

**Step 7: Stage and commit**

```bash
cd /Users/john/Code/Metamaster/.worktrees/feat/single-admin-user
git add frontend/src/components/auth/LoginForm.tsx
git add frontend/src/components/auth/__tests__/LoginForm.test.tsx
git commit -m "feat(frontend): remove register link from LoginForm"
```

---

## Task 5: Create docs/ADMIN.md

**Files:**
- Create: `docs/ADMIN.md`

### Step 1: Create the file

```bash
cat > /Users/john/Code/Metamaster/.worktrees/feat/single-admin-user/docs/ADMIN.md << 'EOF'
# Admin Guide

MetaMaster is a single-admin application. There is exactly one user account. Self-registration is disabled.

---

## First Login

The admin account is created automatically on first startup. The generated password is printed to the container logs:

```bash
docker-compose logs app | grep -A3 "Admin user created"
```

You will be prompted to set a new password immediately after your first login.

---

## Resetting the Admin Password

If you lose access to the admin account, reset the password from inside the container:

```bash
docker exec MetaMaster_app python -m app.core.reset_password
```

The command will:

1. Generate a new 16-character random password
2. Update the admin's password in the database
3. Revoke all existing refresh tokens (forcing re-login on all active sessions)
4. Set `requires_password_change = true` (you will be prompted to set a permanent password on next login)
5. Print the new credentials to stdout

Example output:

```
============================================================
Admin password reset successfully.
  Username       : admin
  Password       : xK9mP2qR7vL4nJ8w
  Tokens revoked : 2
You will be prompted to set a new password on next login.
============================================================
```

---

## Forced Password Change

When `requires_password_change` is `true` (after first login or a reset), the UI redirects to `/change-password` immediately after login. You cannot access any other page until the password is changed.

The backend enforces this via the `requires_password_change` flag on the `User` model; the frontend reads `requiresPasswordChange` from the login response.

---

## Security Notes

- Self-registration is permanently disabled — the `POST /api/v1/auth/register` endpoint does not exist
- JWT access tokens expire after 15 minutes; refresh tokens expire after 7 days
- `jwt_secret_key` and `internal_api_key` are regenerated on every container restart — all sessions are invalidated on restart
- To revoke all sessions without changing the password, run the reset CLI and immediately log in with the new password to set it back to your preferred one
EOF
```

**Step 2: Verify the file looks right**

```bash
cat docs/ADMIN.md
```

Expected: readable markdown with the correct container exec command.

**Step 3: Stage and commit**

```bash
git add docs/ADMIN.md
git commit -m "docs: add ADMIN.md with password reset and first-login guide"
```

---

## Task 6: Update existing documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/API_REFERENCE.md`
- Modify: `docs/ARCHITECTURE.md`

### Step 1: Add ADMIN.md to README.md's Documentation table

Find the Documentation table in `README.md`. It currently looks like:

```markdown
| [Architecture](docs/ARCHITECTURE.md) | System design, component overview |
| [API Reference](docs/API_REFERENCE.md) | REST endpoint reference |
```

Add a row for ADMIN.md:

```markdown
| [Admin Guide](docs/ADMIN.md) | Admin account, password reset |
```

Insert it as the first row of the Documentation table (before Architecture), since it is the most operationally important doc for a first-time user.

**Step 2: Remove the `POST /api/v1/auth/register` row from `docs/API_REFERENCE.md`**

Find the auth endpoints table. The register row reads:

```markdown
| `POST` | `/api/v1/auth/register` | Register a new user | No |
```

Delete that entire row.

**Step 3: Update the auth section in `docs/ARCHITECTURE.md`**

Find the Auth section (search for `## Auth` or `### Auth`). It currently describes JWT details. Add a sentence making the single-admin model explicit.

Add after the JWT description:

```markdown
MetaMaster is a **single-admin application**. Self-registration is disabled — the `POST /auth/register` endpoint is not exposed. The admin account is bootstrapped automatically on first run (see [Admin Guide](ADMIN.md)).
```

**Step 4: Run the TypeScript and backend checks to confirm docs-only changes didn't break anything**

```bash
cd /Users/john/Code/Metamaster/.worktrees/feat/single-admin-user
python -c "from app.api.v1.auth.endpoints import router; print('Backend OK')"
cd frontend && npm run type-check && echo "Frontend OK"
```

Expected: `Backend OK` then `Frontend OK`.

**Step 5: Stage and commit**

```bash
cd /Users/john/Code/Metamaster/.worktrees/feat/single-admin-user
git add README.md docs/API_REFERENCE.md docs/ARCHITECTURE.md
git commit -m "docs: update README, API_REFERENCE, and ARCHITECTURE for single-admin model"
```

---

## Done — Verify Everything

**Backend:**

```bash
pytest tests/domain/ tests/test_models_unit.py tests/test_schemas_unit.py tests/test_utils_unit.py tests/test_reset_password.py -v
```

Expected: all passing.

**Frontend:**

```bash
cd frontend && npm run test -- --run && npm run type-check
```

Expected: all passing, no type errors.

**Smoke check — register route is gone:**

```bash
python -c "
from app.api.v1.auth.endpoints import router
routes = [r.path for r in router.routes]
assert '/register' not in routes, 'register route still present!'
print('register route absent — OK')
print('Remaining auth routes:', routes)
"
```

Expected: `register route absent — OK` and list of remaining routes (login, refresh, logout, me, change-password, profile).
