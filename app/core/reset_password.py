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
        print("  Username       : admin")
        print(f"  Password       : {new_password}")
        print(f"  Tokens revoked : {revoked}")
        print("You will be prompted to set a new password on next login.")
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    reset_admin_password()
