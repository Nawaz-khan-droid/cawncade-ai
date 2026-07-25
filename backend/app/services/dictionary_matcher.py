import os
import json
import difflib
from typing import Dict, Optional

class PreFlightDictionaryMatcher:
    def __init__(self, storage_path="db/viral_claims_dictionary.json"):
        self.storage_path = storage_path
        # Core structured lookup table: { "normalized_claim": "cached_markdown_verdict" }
        self.claims_lookup: Dict[str, str] = {}
        self._load_dictionary()

    def _normalize_text(self, text: str) -> str:
        """Strips out capitalization, punctuation, and padding to normalize matches."""
        import string
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
        """Runs a near-instant sequence match lookup across known texts under 1ms."""
        normalized_query = self._normalize_text(user_claim)
        
        # Pattern 1: Check for a direct, O(1) hash table hit
        if normalized_query in self.claims_lookup:
            print("[Tier 0] FLASH Hit! Exact matching text intercepted instantly.")
            return self.claims_lookup[normalized_query]

        # Pattern 2: Fall back to a fast character similarity pass for typos or small adjustments
        for cached_claim, stored_verdict in self.claims_lookup.items():
            # difflib.SequenceMatcher is heavily optimized in C/Python for rapid structural string checks
            similarity = difflib.SequenceMatcher(None, normalized_query, cached_claim).ratio()
            if similarity >= ratio_threshold:
                print(f"[Tier 0] Character Hit! Structural Match Score: {similarity:.2f}")
                return stored_verdict

        return None

    def commit_viral_claim(self, raw_claim: str, final_verdict_markdown: str):
        """Saves a fresh resolution straight to the Tier 0 local database volume."""
        normalized_key = self._normalize_text(raw_claim)
        self.claims_lookup[normalized_key] = final_verdict_markdown
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.claims_lookup, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Tier 0 persistent storage sync exception: {e}")

# Global instance
dictionary_matcher = PreFlightDictionaryMatcher()
