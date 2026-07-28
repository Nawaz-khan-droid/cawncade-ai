"""
Circuit Breaker Pattern.
Prevents cascading failures by temporarily disabling unhealthy services.
"""
import time
from ..utils.logger import log


class CircuitBreaker:
    """
    States: CLOSED (normal) -> OPEN (failing) -> HALF_OPEN (testing recovery) -> CLOSED
    """

    def __init__(self, name: str, failure_threshold: int = 3, reset_timeout: int = 600):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "closed"
        self.total_calls = 0
        self.successful_calls = 0

    async def call(self, func, *args, **kwargs):
        self.total_calls += 1
        if self.state == "open":
            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.reset_timeout:
                self.state = "half_open"
                log.info(f"[CircuitBreaker] '{self.name}' -> HALF_OPEN (retrying after {elapsed:.0f}s)")
            else:
                log.warning(f"[CircuitBreaker] '{self.name}' -> OPEN (skipping, {self.reset_timeout - elapsed:.0f}s remaining)")
                return None
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(str(e))
            return None

    def _on_success(self):
        if self.state == "half_open":
            log.info(f"[CircuitBreaker] '{self.name}' -> CLOSED (recovered)")
        self.failure_count = 0
        self.state = "closed"
        self.successful_calls += 1

    def _on_failure(self, error: str):
        self.failure_count += 1
        self.last_failure_time = time.time()
        log.error(f"[CircuitBreaker] '{self.name}' failure #{self.failure_count}: {error[:100]}")
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            log.warning(
                f"[CircuitBreaker] '{self.name}' -> OPEN "
                f"(after {self.failure_threshold} failures, waiting {self.reset_timeout}s)"
            )

    def is_available(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "half_open":
            return True
        return time.time() - self.last_failure_time >= self.reset_timeout

    def force_reset(self):
        self.failure_count = 0
        self.state = "closed"
        log.info(f"[CircuitBreaker] '{self.name}' -> CLOSED (manual reset)")

    def status(self) -> dict:
        return {
            "name": self.name,
            "state": self.state,
            "failures": self.failure_count,
            "threshold": self.failure_threshold,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
        }


circuit_google_search = CircuitBreaker("google_search", failure_threshold=3, reset_timeout=600)
circuit_tavily = CircuitBreaker("tavily", failure_threshold=3, reset_timeout=600)
circuit_fact_check = CircuitBreaker("fact_check", failure_threshold=3, reset_timeout=600)
circuit_safe_browsing = CircuitBreaker("safe_browsing", failure_threshold=5, reset_timeout=900)
circuit_newsapi = CircuitBreaker("newsapi", failure_threshold=3, reset_timeout=600)
circuit_newsdata = CircuitBreaker("newsdata", failure_threshold=3, reset_timeout=600)
circuit_youtube = CircuitBreaker("youtube", failure_threshold=5, reset_timeout=900)
circuit_vision = CircuitBreaker("vision", failure_threshold=3, reset_timeout=600)
circuit_gdelt = CircuitBreaker("gdelt", failure_threshold=5, reset_timeout=600)
circuit_google_news = CircuitBreaker("google_news", failure_threshold=5, reset_timeout=600)
circuit_agent = CircuitBreaker("llm_agent", failure_threshold=3, reset_timeout=600)

def get_all_circuit_breaker_telemetry() -> dict:
    """Returns real-time status & error telemetry across all search & LLM provider circuit breakers."""
    breakers = [
        circuit_google_search, circuit_tavily, circuit_fact_check,
        circuit_newsdata, circuit_youtube, circuit_gdelt,
        circuit_google_news, circuit_agent
    ]
    return {b.name: b.status() for b in breakers}
