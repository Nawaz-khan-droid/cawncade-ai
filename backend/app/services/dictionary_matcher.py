import os
import json
import difflib
from typing import Dict, Optional

# EDGE-01 FIX: Cap the dictionary size to prevent O(n*avg_len) fuzzy scan from
# growing unboundedly. Beyond MAX_DICT_SIZE entries, only exact-match O(1) lookup is used.
MAX_DICT_SIZE = 1000

# PERF-04 FIX: Batch writes — only flush to disk every N additions to avoid
# rewriting the entire JSON file on every single request.
WRITE_BATCH_SIZE = 10


class PreFlightDictionaryMatcher:
    def __init__(self, storage_path="db/viral_claims_dictionary.json"):
        self.storage_path = storage_path
        # Core structured lookup table: { "normalized_claim": "cached_markdown_verdict" }
        self.claims_lookup: Dict[str, str] = {}
        self._pending_writes = 0
        self._load_dictionary()

    def _normalize_text(self, text: str) -> str:
        """Strips out capitalization, punctuation, padding, and appended prompt instructions."""
        import string
        # Strip out any appended prompt instructions or user context overrides
        text = text.split("\n\nUSER SPECIFIC CONTEXT")[0]
        text = text.split("Make sure formatting matches")[0]
        text = text.lower().strip()
        # Remove trailing question marks or punctuation marks
        text = text.translate(str.maketrans('', '', string.punctuation))
        return " ".join(text.split())

    def _load_dictionary(self):
        """Loads known viral records instantly from local JSON flat-file storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.claims_lookup = json.load(f)
                print(f"[Tier 0] Active: Loaded {len(self.claims_lookup)} viral hot-links from disk.")
            except Exception as e:
                print(f"Tier 0 initialization warning: {e}. Starting fresh.")

    def lookup_viral_claim(self, user_claim: str, ratio_threshold: float = 0.92) -> Optional[str]:
        """Runs a near-instant sequence match lookup across known texts."""
        normalized_query = self._normalize_text(user_claim)

        # Pattern 1: Check for a direct, O(1) hash table hit
        if normalized_query in self.claims_lookup:
            print("[Tier 0] FLASH Hit! Exact matching text intercepted instantly.")
            return self.claims_lookup[normalized_query]

        # EDGE-01 FIX: Only run the O(n * str_len) fuzzy scan if the dictionary is
        # small enough. Large dictionaries skip fuzzy matching to keep response times safe.
        if len(self.claims_lookup) > MAX_DICT_SIZE:
            return None

        # Pattern 2: Fall back to fast character similarity pass for typos or small edits.
        # difflib.SequenceMatcher is heavily optimized in C/Python for rapid structural checks.
        for cached_claim, stored_verdict in self.claims_lookup.items():
            # Quick pre-filter: skip if string lengths differ too much (impossible to hit threshold)
            if abs(len(normalized_query) - len(cached_claim)) > 50:
                continue
            similarity = difflib.SequenceMatcher(None, normalized_query, cached_claim).ratio()
            if similarity >= ratio_threshold:
                print(f"[Tier 0] Character Hit! Structural Match Score: {similarity:.2f}")
                return stored_verdict

        return None

    def commit_viral_claim(self, raw_claim: str, final_verdict_markdown: str):
        """Saves a fresh resolution to the Tier 0 local database volume.

        PERF-04 FIX: Writes are batched — the JSON file is only flushed to disk
        every WRITE_BATCH_SIZE additions, not on every single request.
        """
        normalized_key = self._normalize_text(raw_claim)
        self.claims_lookup[normalized_key] = final_verdict_markdown
        self._pending_writes += 1

        if self._pending_writes >= WRITE_BATCH_SIZE:
            self._flush_to_disk()
            self._pending_writes = 0

    def _flush_to_disk(self):
        """Writes the full dictionary to the JSON file atomically."""
        try:
            os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
            # Write to a temp file first, then rename — prevents partial-write corruption
            tmp_path = self.storage_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.claims_lookup, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, self.storage_path)
        except Exception as e:
            print(f"Tier 0 persistent storage sync exception: {e}")

    def force_flush(self):
        """Explicitly persist any pending writes (call on graceful shutdown)."""
        if self._pending_writes > 0:
            self._flush_to_disk()
            self._pending_writes = 0


# Global instance
dictionary_matcher = PreFlightDictionaryMatcher()
