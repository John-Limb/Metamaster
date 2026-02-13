"""Redis-based distributed rate limiting.

This module provides rate limiting using the sliding window algorithm
with Redis as the backend for distributed rate limiting across multiple
application instances.
"""

import time
from typing import Optional, Tuple

from app.infrastructure.cache.redis_cache import RedisCacheService


class RateLimiter:
    """Redis-based distributed rate limiter using sliding window algorithm.

    The sliding window algorithm provides more accurate rate limiting than
    fixed window by tracking the exact timestamps of requests within the window.

    Attributes:
        redis: The Redis cache service instance.
    """

    def __init__(self, redis_client: Optional[RedisCacheService] = None):
        """Initialize the rate limiter.

        Args:
            redis_client: Optional Redis cache service instance.
                         Uses the global instance if not provided.
        """
        self.redis = redis_client

    def _get_redis(self) -> RedisCacheService:
        """Get the Redis client, initializing if needed.

        Returns:
            The RedisCacheService instance.
        """
        if self.redis is None:
            from app.infrastructure.cache.redis_cache import get_cache_service

            self.redis = get_cache_service()
        return self.redis

    def is_allowed(
        self, key: str, max_requests: int, window_seconds: int
    ) -> Tuple[bool, int, int]:
        """Check if a request is allowed based on rate limit.

        Uses a sliding window algorithm with Redis sorted sets for accurate
        rate limiting. Each request is stored with its timestamp as the score.

        Args:
            key: Unique identifier for the rate limit (e.g., IP + endpoint).
            max_requests: Maximum number of requests allowed in the window.
            window_seconds: Time window in seconds.

        Returns:
            Tuple of (is_allowed, remaining_requests, retry_after_seconds).
            - is_allowed: True if request should be allowed.
            - remaining_requests: Number of requests remaining in window.
            - retry_after_seconds: Seconds until rate limit resets (0 if allowed).

        Example:
            >>> limiter = RateLimiter()
            >>> allowed, remaining, retry_after = limiter.is_allowed(
            ...     "login:192.168.1.1", max_requests=5, window_seconds=60
            ... )
            >>> if not allowed:
            ...     print(f"Rate limited. Retry after {retry_after} seconds")
        """
        redis = self._get_redis()

        if not redis.is_connected():
            # If Redis is not available, allow the request (fail open)
            return True, max_requests, 0

        current_time = time.time()
        window_start = current_time - window_seconds

        redis_key = f"rate_limit:{key}"

        try:
            # Use Redis pipeline for atomic operations
            client = redis.redis_client
            pipe = client.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(redis_key, 0, window_start)

            # Count current requests in window
            pipe.zcard(redis_key)

            # Get the oldest request time (for retry_after calculation)
            pipe.zrange(redis_key, 0, 0, withscores=True)

            results = pipe.execute()
            current_count = results[1]
            oldest_entries = results[2]

            if current_count >= max_requests:
                # Rate limit exceeded
                if oldest_entries:
                    oldest_time = oldest_entries[0][1]
                    retry_after = int(oldest_time + window_seconds - current_time) + 1
                else:
                    retry_after = window_seconds
                return False, 0, max(1, retry_after)

            # Add current request
            pipe = client.pipeline()
            pipe.zadd(redis_key, {str(current_time): current_time})
            pipe.expire(redis_key, window_seconds)
            pipe.execute()

            remaining = max_requests - current_count - 1
            return True, remaining, 0

        except Exception:
            # On Redis errors, fail open (allow request)
            return True, max_requests, 0

    def reset(self, key: str) -> None:
        """Reset rate limit for a key.

        Args:
            key: The rate limit key to reset.

        Example:
            >>> limiter = RateLimiter()
            >>> limiter.reset("login:192.168.1.1")
        """
        redis = self._get_redis()

        if not redis.is_connected():
            return

        redis_key = f"rate_limit:{key}"

        try:
            redis.redis_client.delete(redis_key)
        except Exception:
            pass  # Silently ignore errors on reset

    def get_remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        """Get the number of remaining requests for a key.

        Args:
            key: The rate limit key to check.
            max_requests: Maximum number of requests allowed.
            window_seconds: Time window in seconds.

        Returns:
            Number of remaining requests in the current window.

        Example:
            >>> limiter = RateLimiter()
            >>> remaining = limiter.get_remaining(
            ...     "login:192.168.1.1", max_requests=5, window_seconds=60
            ... )
            >>> print(f"{remaining} requests remaining")
        """
        redis = self._get_redis()

        if not redis.is_connected():
            return max_requests

        current_time = time.time()
        window_start = current_time - window_seconds
        redis_key = f"rate_limit:{key}"

        try:
            client = redis.redis_client
            pipe = client.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(redis_key, 0, window_start)
            # Count current
            pipe.zcard(redis_key)

            results = pipe.execute()
            current_count = results[1]

            return max(0, max_requests - current_count)
        except Exception:
            return max_requests


# Rate limit configurations for different endpoints
RATE_LIMITS = {
    "login": {"max_requests": 5, "window_seconds": 60},  # 5 per minute
    "register": {"max_requests": 3, "window_seconds": 3600},  # 3 per hour
    "refresh": {"max_requests": 20, "window_seconds": 60},  # 20 per minute
    "password_reset": {"max_requests": 3, "window_seconds": 3600},  # 3 per hour
    "email_verification": {"max_requests": 5, "window_seconds": 3600},  # 5 per hour
}


# Global instance
rate_limiter = RateLimiter()
