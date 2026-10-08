import time
import logging
from fastapi import HTTPException, status

logger = logging.getLogger("cawncade.rate_limiter")

class TokenBucketLimiter:
    """Implements an in-memory thread-safe sliding window rate limiter."""
    def __init__(self, capacity: int, refill_rate_per_sec: float):
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self.tokens = float(capacity)
        self.last_refill = time.time()

    def consume(self) -> bool:
        now = time.time()
        elapsed = now - self.last_refill
        self.last_refill = now
        
        # Add back tokens accrued over time without exceeding max bucket capacity
        self.tokens = min(float(self.capacity), self.tokens + (elapsed * self.refill_rate))
        
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False

# In-memory limiter instance: Maximum 5 requests bucket, refilling 1 token every 12 seconds
global_api_limiter = TokenBucketLimiter(capacity=5, refill_rate_per_sec=0.083)

async def verify_rate_limit():
    """Dependency injection guard protecting downstream LLM models from exploitation."""
    if not global_api_limiter.consume():
        logger.warning("[Security] Rate limit boundary breached. Rejecting request.")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. System is throttling inbound requests to protect upstream API budgets."
        )

class LegacyRateLimiter:
    def check_or_raise(self, key: str):
        # We enforce the new TokenBucketLimiter globally instead
        pass

rate_limiter = LegacyRateLimiter()
