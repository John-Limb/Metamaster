"""Auth domain service for business logic.

This module provides authentication services including password hashing,
token management, and user authentication operations.
"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.auth.models import RefreshToken, User
from app.domain.auth.schemas import UserRegisterRequest
from app.domain.auth.validators import validate_password_strength
from app.infrastructure.security.password import (
    hash_password as _hash_password,
    needs_rehash,
    verify_password as _verify_password,
)
from app.infrastructure.security.jwt import jwt_handler
from app.infrastructure.security.rate_limiter import RATE_LIMITS, rate_limiter


def hash_password(password: str) -> str:
    """Hash a password using Argon2id.

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed password string.
    """
    return _hash_password(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a hash.

    Args:
        password: The plain text password to verify.
        password_hash: The stored password hash.

    Returns:
        True if the password matches, False otherwise.
    """
    return _verify_password(password, password_hash)


def create_access_token(user_id: int, expires_delta: timedelta) -> str:
    """Create a JWT access token.

    Args:
        user_id: The user ID to encode in the token.
        expires_delta: The time until expiration.

    Returns:
        The encoded JWT access token.
    """
    return jwt_handler.create_access_token(user_id, expires_delta=expires_delta)


def create_refresh_token(user_id: int, expires_delta: timedelta) -> str:
    """Create a JWT refresh token.

    Args:
        user_id: The user ID to encode in the token.
        expires_delta: The time until expiration.

    Returns:
        The encoded JWT refresh token.
    """
    return jwt_handler.create_refresh_token(user_id, expires_delta=expires_delta)


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token.

    Args:
        token: The JWT token to verify.

    Returns:
        The decoded token payload if valid, None otherwise.
    """
    return jwt_handler.decode_token(token)


def hash_token(token: str) -> str:
    """Hash a token for storage.

    Uses SHA-256 for token hashing.

    Args:
        token: The token to hash.

    Returns:
        The hashed token.
    """
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    """Service for authentication operations.

    Provides methods for user authentication, registration, and
    token management.
    """

    def __init__(self, db: Session):
        """Initialize the auth service.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def authenticate_user(
        self, username: str, password: str
    ) -> Optional[User]:
        """Authenticate a user by username/email and password.

        Args:
            username: The username or email.
            password: The plain text password.

        Returns:
            The User object if authentication succeeds, None otherwise.
        """
        # Try to find user by username or email
        user = self.get_user_by_username(username)
        if user is None:
            user = self.get_user_by_email(username)

        if user is None:
            return None

        if not user.is_active:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    def create_user(self, user_data: UserRegisterRequest) -> User:
        """Create a new user.

        Args:
            user_data: The user registration data.

        Returns:
            The created User object.

        Raises:
            ValueError: If username or email already exists.
        """
        # Check for existing username
        existing_user = self.get_user_by_username(user_data.username)
        if existing_user:
            raise ValueError("Username already registered")

        # Check for existing email
        existing_user = self.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError("Email already registered")

        # Validate password strength
        is_valid, missing = validate_password_strength(user_data.password)
        if not is_valid:
            raise ValueError(f"Password requirements not met: {', '.join(missing)}")

        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email.lower(),
            password_hash=hash_password(user_data.password),
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username.

        Args:
            username: The username to search for.

        Returns:
            The User object if found, None otherwise.
        """
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email.

        Args:
            email: The email to search for.

        Returns:
            The User object if found, None otherwise.
        """
        return self.db.query(User).filter(User.email == email.lower()).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID.

        Args:
            user_id: The user ID to search for.

        Returns:
            The User object if found, None otherwise.
        """
        return self.db.query(User).filter(User.id == user_id).first()

    def update_last_login(self, user: User) -> None:
        """Update the user's last login timestamp.

        Args:
            user: The User object to update.
        """
        user.last_login = datetime.utcnow()
        self.db.commit()

    def change_password(
        self, user: User, current_password: str, new_password: str
    ) -> bool:
        """Change a user's password.

        Args:
            user: The User object.
            current_password: The current password for verification.
            new_password: The new password to set.

        Returns:
            True if password change succeeded, False otherwise.

        Raises:
            ValueError: If new password doesn't meet requirements.
        """
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            return False

        # Validate new password strength
        is_valid, missing = validate_password_strength(new_password)
        if not is_valid:
            raise ValueError(f"Password requirements not met: {', '.join(missing)}")

        user.password_hash = hash_password(new_password)
        user.requires_password_change = False
        self.db.commit()

        return True

    def store_refresh_token(
        self, user_id: int, token: str, expires_at: datetime
    ) -> RefreshToken:
        """Store a refresh token for a user.

        Args:
            user_id: The user ID.
            token: The refresh token.
            expires_at: The expiration datetime.

        Returns:
            The created RefreshToken object.
        """
        token_hash = hash_token(token)

        refresh_token = RefreshToken(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
        )

        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)

        return refresh_token

    def revoke_refresh_token(self, token_hash: str) -> bool:
        """Revoke a refresh token.

        Args:
            token_hash: The hash of the token to revoke.

        Returns:
            True if token was revoked, False if not found.
        """
        refresh_token = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )

        if refresh_token is None:
            return False

        refresh_token.revoked = True
        self.db.commit()

        return True

    def get_valid_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        """Get a valid (non-revoked, non-expired) refresh token.

        Args:
            token_hash: The hash of the token to find.

        Returns:
            The RefreshToken object if valid, None otherwise.
        """
        now = datetime.utcnow()

        refresh_token = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > now,
            )
            .first()
        )

        return refresh_token

    def revoke_all_user_tokens(self, user_id: int) -> int:
        """Revoke all refresh tokens for a user.

        Args:
            user_id: The user ID.

        Returns:
            The number of tokens revoked.
        """
        result = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,
            )
            .update({"revoked": True})
        )

        self.db.commit()

        return result
