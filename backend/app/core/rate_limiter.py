"""
Rate Limiter Module.
In-memory rate limiting for API endpoints.
For production, replace with Redis-backed implementation.
"""
import time
from collections import defaultdict
from fastapi import HTTPException, status
from ..config.settings import get_settings

settings = get_settings()


class RateLimiter:
    """
    Simple in-memory sliding window rate limiter.
    Thread-safe for basic usage.
    """

    def __init__(self):
        self.requests = defaultdict(list)  # key -> list of timestamps
        self.max_requests = settings.RATE_LIMIT_REQUESTS
        self.window_seconds = settings.RATE_LIMIT_WINDOW_SECONDS

    def check(self, key: str) -> bool:
        """
        Check if a request is allowed.
        Returns True if allowed, False if rate-limited.
        """
        if not settings.RATE_LIMIT_ENABLED:
            return True

        now = time.time()
        window_start = now - self.window_seconds

        # Clean old entries
        self.requests[key] = [ts for ts in self.requests[key] if ts > window_start]

        if len(self.requests[key]) >= self.max_requests:
            return False

        self.requests[key].append(now)
        return True

    def check_or_raise(self, key: str):
        """Check rate limit and raise HTTPException if exceeded."""
        if not self.check(key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds}s.",
            )


# Singleton
rate_limiter = RateLimiter()
