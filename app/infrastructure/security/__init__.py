"""Security infrastructure module.

This module provides security utilities for:
- Password hashing using Argon2id (OWASP recommended)
- JWT token generation and validation
- Distributed rate limiting with Redis

Example usage:

    from app.infrastructure.security import (
        hash_password,
        verify_password,
        jwt_handler,
        rate_limiter,
        RATE_LIMITS,
    )

    # Password hashing
    hashed = hash_password("secure_password")
    if verify_password("secure_password", hashed):
        print("Password verified")

    # JWT tokens
    access_token = jwt_handler.create_access_token(user_id=1)
    refresh_token = jwt_handler.create_refresh_token(user_id=1)
    user_id = jwt_handler.verify_access_token(access_token)

    # Rate limiting
    allowed, remaining, retry_after = rate_limiter.is_allowed(
        "login:192.168.1.1",
        max_requests=5,
        window_seconds=60,
    )
"""

from app.infrastructure.security.password import (
    hash_password,
    needs_rehash,
    verify_password,
)
from app.infrastructure.security.jwt import (
    JWTHandler,
    get_jwt_handler,
    jwt_handler,
)
from app.infrastructure.security.rate_limiter import (
    RATE_LIMITS,
    RateLimiter,
    rate_limiter,
)

__all__ = [
    # Password utilities
    "hash_password",
    "verify_password",
    "needs_rehash",
    # JWT utilities
    "JWTHandler",
    "jwt_handler",
    "get_jwt_handler",
    # Rate limiting
    "RateLimiter",
    "rate_limiter",
    "RATE_LIMITS",
]
