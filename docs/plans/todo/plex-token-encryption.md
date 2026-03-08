# TODO: Encrypted Credential Storage for Integrations

## Problem

Third-party tokens and API keys (Plex OAuth token, and future integrations) are stored **plaintext** in the database. Anyone who can read the database gets usable credentials.

The admin password uses Argon2id hashing, but that is one-way — unsuitable here because tokens must be **retrieved and sent** to external services on every API call.

## Proposed Solution

Build a generic `EncryptedCredential` store using **Fernet symmetric encryption** (`cryptography` library — already a project dependency). A single encryption key is generated at first startup, displayed alongside the admin credentials in the startup logs, and stored in `AppSetting`. All integrations encrypt their secrets through the same service.

### Security model

- Attacker with **DB access only**: cannot use any stored credentials (needs the key)
- Attacker with **DB + AppSetting key**: can decrypt (same threat surface as plaintext, but requires reading two things)
- Attacker with **DB + `.env` key** (if env override used): same as above
- For a home server this is a meaningful improvement over plaintext

## Design: Generic Credential Service

`app/infrastructure/security/credential_store.py` — single entry point for all integrations:

```python
class CredentialStore:
    def encrypt(self, plaintext: str) -> str: ...
    def decrypt(self, ciphertext: str) -> str: ...
```

Integrations call this directly — no integration needs to know about Fernet. Future services (Trakt, Jellyfin, TMDB user tokens, etc.) use the same interface.

## Files to Change

| File | Change |
|---|---|
| `app/infrastructure/security/credential_store.py` | **Create** — `CredentialStore` with `encrypt` / `decrypt`; loads key from env or `AppSetting` |
| `app/core/init_db.py` | Generate Fernet key on first run, store as `AppSetting(key="credential_encryption_key")`, log alongside admin password |
| `app/core/config.py` | Add optional `secret_encryption_key: str \| None = None` — if set, takes precedence over DB-stored key |
| `app/domain/plex/models.py` | Rename column `token` → `token_encrypted`; Alembic migration |
| `app/api/v1/plex/router.py` | Encrypt on write, decrypt before use |
| `tests/infrastructure/security/test_credential_store.py` | **Create** — round-trip test, wrong-key test, missing-key startup error test |

## Future Integrations

Any new integration that stores a secret follows the same pattern:

1. Column named `<field>_encrypted` in the model
2. Call `credential_store.encrypt()` before writing, `credential_store.decrypt()` before using
3. Never return the raw ciphertext or plaintext from API responses

Examples: Trakt OAuth token, Jellyfin API key, custom TMDB user token, etc.

## Alembic Migration (Plex)

```
alembic revision --autogenerate -m "encrypt plex token at rest"
```

Column rename (`token` → `token_encrypted`) must be written manually — Alembic can't detect renames. Existing Plex connections will need to reconnect after the migration.

## Key Generation (reference)

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()  # base64url-encoded 32-byte key
```

Stored in `AppSetting` as a plain string. Loaded and cached at app startup.

## Startup Log Output (first run)

```
============================================================
DEFAULT ADMIN USER CREATED
Username: admin
Password: <generated>
Please change this password on first login!

CREDENTIAL ENCRYPTION KEY (store this somewhere safe)
Key: <base64url key>
This key encrypts all third-party tokens stored in the database.
If lost, all connected integrations will need to be reconnected.
============================================================
```

## Notes

- `cryptography` is already in `requirements.txt` (used by `PyJWT`)
- If the key is missing at startup (not in env, not in `AppSetting`), raise a clear error — never fall back to plaintext
- Key rotation is out of scope for now — would require re-encrypting all stored credentials
