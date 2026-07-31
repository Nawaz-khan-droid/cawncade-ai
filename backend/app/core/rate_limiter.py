"""
Rate Limiter Module.
In-memory rate limiting for API endpoints.
"""
import time
from collections import defaultdict
from fastapi import HTTPException, status
from ..config.settings import get_settings

settings = get_settings()


class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.max_requests = settings.RATE_LIMIT_REQUESTS
        self.window_seconds = settings.RATE_LIMIT_WINDOW_SECONDS

    def check(self, key: str) -> bool:
        if not settings.RATE_LIMIT_ENABLED:
            return True
        now = time.time()
        window_start = now - self.window_seconds
        # Prune expired timestamps
        self.requests[key] = [ts for ts in self.requests[key] if ts > window_start]
        # EDGE-07 FIX: Remove empty keys to prevent memory bloat from unique-IP floods
        if not self.requests[key]:
            del self.requests[key]
            self.requests[key].append(now)  # defaultdict recreates it cleanly
            return True
        if len(self.requests[key]) >= self.max_requests:
            return False
        self.requests[key].append(now)
        return True

    def check_or_raise(self, key: str):
        if not self.check(key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds}s.",
            )


rate_limiter = RateLimiter()
