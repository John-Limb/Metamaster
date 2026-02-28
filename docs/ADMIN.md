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
