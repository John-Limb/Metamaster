"""JWT token handling for authentication.

This module provides JWT token generation and validation for access and refresh tokens.
Tokens include proper expiration and type claims for security.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

import jwt

from app.core.config import settings


class JWTHandler:
    """Handle JWT token generation and validation.

    This class provides methods for creating and verifying JWT tokens
    with proper security claims including expiration and token type.

    Attributes:
        secret_key: The secret key used for signing tokens.
        algorithm: The algorithm used for signing (default: HS256).
        access_token_expire_minutes: Access token expiration time.
        refresh_token_expire_days: Refresh token expiration time.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: Optional[str] = None,
        access_token_expire_minutes: Optional[int] = None,
        refresh_token_expire_days: Optional[int] = None,
    ):
        """Initialize the JWT handler.

        Args:
            secret_key: Secret key for signing tokens. Defaults to settings.
            algorithm: Signing algorithm. Defaults to HS256.
            access_token_expire_minutes: Access token expiry in minutes.
            refresh_token_expire_days: Refresh token expiry in days.
        """
        # Use provided values or fall back to settings with secure defaults
        self.secret_key = secret_key or getattr(settings, "jwt_secret_key", None)
        if not self.secret_key:
            raise ValueError(
                "JWT secret key must be provided via settings.jwt_secret_key "
                "or constructor argument"
            )

        self.algorithm = algorithm or getattr(settings, "jwt_algorithm", "HS256")
        self.access_token_expire_minutes = access_token_expire_minutes or getattr(
            settings, "access_token_expire_minutes", 30
        )
        self.refresh_token_expire_days = refresh_token_expire_days or getattr(
            settings, "refresh_token_expire_days", 7
        )

    def create_access_token(
        self,
        user_id: int,
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[dict[str, Any]] = None,
    ) -> str:
        """Create a JWT access token.

        Access tokens are short-lived tokens used for API authentication.

        Args:
            user_id: The user ID to encode in the token subject.
            expires_delta: Optional custom expiration time delta.
            additional_claims: Optional additional claims to include.

        Returns:
            The encoded JWT access token string.

        Example:
            >>> handler = JWTHandler(secret_key="my-secret")
            >>> token = handler.create_access_token(user_id=1)
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode = {
            "sub": str(user_id),
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        if additional_claims:
            to_encode.update(additional_claims)

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        user_id: int,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a JWT refresh token.

        Refresh tokens are long-lived tokens used to obtain new access tokens.

        Args:
            user_id: The user ID to encode in the token subject.
            expires_delta: Optional custom expiration time delta.

        Returns:
            The encoded JWT refresh token string.

        Example:
            >>> handler = JWTHandler(secret_key="my-secret")
            >>> token = handler.create_refresh_token(user_id=1)
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        to_encode = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Optional[dict[str, Any]]:
        """Decode and validate a JWT token.

        This method verifies the signature and checks expiration.

        Args:
            token: The JWT token string to decode.

        Returns:
            The decoded token payload if valid, None if invalid or expired.

        Example:
            >>> handler = JWTHandler(secret_key="my-secret")
            >>> token = handler.create_access_token(user_id=1)
            >>> payload = handler.decode_token(token)
            >>> payload["sub"]
            '1'
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def verify_access_token(self, token: str) -> Optional[int]:
        """Verify an access token and return the user ID.

        This method validates that the token is an access token (not refresh)
        and returns the user ID from the subject claim.

        Args:
            token: The JWT access token string to verify.

        Returns:
            The user ID if valid access token, None otherwise.

        Example:
            >>> handler = JWTHandler(secret_key="my-secret")
            >>> token = handler.create_access_token(user_id=1)
            >>> handler.verify_access_token(token)
            1
        """
        payload = self.decode_token(token)
        if payload and payload.get("type") == "access":
            try:
                return int(payload["sub"])
            except (KeyError, ValueError):
                return None
        return None

    def verify_refresh_token(self, token: str) -> Optional[int]:
        """Verify a refresh token and return the user ID.

        This method validates that the token is a refresh token (not access)
        and returns the user ID from the subject claim.

        Args:
            token: The JWT refresh token string to verify.

        Returns:
            The user ID if valid refresh token, None otherwise.

        Example:
            >>> handler = JWTHandler(secret_key="my-secret")
            >>> token = handler.create_refresh_token(user_id=1)
            >>> handler.verify_refresh_token(token)
            1
        """
        payload = self.decode_token(token)
        if payload and payload.get("type") == "refresh":
            try:
                return int(payload["sub"])
            except (KeyError, ValueError):
                return None
        return None


# Global instance - will be initialized lazily when settings are available
_jwt_handler: Optional[JWTHandler] = None


def get_jwt_handler() -> JWTHandler:
    """Get or create the global JWT handler instance.

    Returns:
        The global JWTHandler instance.
    """
    global _jwt_handler
    if _jwt_handler is None:
        _jwt_handler = JWTHandler()
    return _jwt_handler


# For backwards compatibility, expose as jwt_handler property
class _JWTHandlerProxy:
    """Proxy object that delegates to the global JWT handler."""

    def __getattr__(self, name):
        return getattr(get_jwt_handler(), name)


jwt_handler = _JWTHandlerProxy()
