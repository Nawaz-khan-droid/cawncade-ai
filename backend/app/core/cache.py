"""
In-Memory Cache with TTL support.
Phase 1: In-memory dict (zero dependencies).
Upgrade path: Replace with Upstash Redis when needed.
"""
import time
import threading
import hashlib
from ..utils.logger import log


class InMemoryCache:
    def __init__(self, default_ttl: int = 21600):
        self._store: dict[str, dict] = {}
        self._default_ttl = default_ttl
        self._lock = threading.Lock()

    def _make_key(self, key: str) -> str:
        # REFACTOR-05 FIX: Use SHA-256 instead of MD5 (MD5 is cryptographically broken
        # and triggers security scanners). Truncate to 32 chars to keep keys compact.
        return hashlib.sha256(key.encode()).hexdigest()[:32] if len(key) > 200 else key

    def get(self, key: str):
        key = self._make_key(key)
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            if time.time() > item["expires"]:
                del self._store[key]
                return None
            return item["value"]

    def set(self, key: str, value, ttl: int = None):
        key = self._make_key(key)
        ttl = ttl or self._default_ttl
        with self._lock:
            self._store[key] = {
                "value": value,
                "expires": time.time() + ttl,
                "created": time.time(),
            }

    def delete(self, key: str):
        key = self._make_key(key)
        with self._lock:
            self._store.pop(key, None)

    def has(self, key: str) -> bool:
        return self.get(key) is not None

    def clear(self):
        with self._lock:
            self._store.clear()
            log.info("[Cache] All entries cleared.")

    def cleanup(self):
        now = time.time()
        with self._lock:
            expired = [k for k, v in self._store.items() if now > v["expires"]]
            for k in expired:
                del self._store[k]
            if expired:
                log.info(f"[Cache] Cleaned up {len(expired)} expired entries.")

    def stats(self) -> dict:
        with self._lock:
            total = len(self._store)
            now = time.time()
            active = sum(1 for v in self._store.values() if now <= v["expires"])
            return {"total_entries": total, "active_entries": active, "expired": total - active}


cache = InMemoryCache(default_ttl=21600)
