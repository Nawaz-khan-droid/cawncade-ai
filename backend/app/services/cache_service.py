import os
import json
import faiss
import numpy as np
# PERF-01 FIX: Use the shared embedding singleton instead of loading a second
# all-MiniLM-L6-v2 instance here. evidence_ranker.py loads the same model;
# this singleton ensures both share one ~90MB in-memory instance.
from app.services.embedding_singleton import get_embedding_model
from app.utils.logger import log

# We store the cache index and metadata locally to survive app restarts
INDEX_FILE = os.path.join(os.path.dirname(__file__), "..", "db", "semantic_cache.index")
METADATA_FILE = os.path.join(os.path.dirname(__file__), "..", "db", "cache_metadata.json")

class SemanticFactCache:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        """Initializes a local, ultra-lightweight CPU vector cache."""
        log.info("[CacheService] Initializing semantic cache (using shared embedding singleton)...")

        # Dimensions for all-MiniLM-L6-v2 is 384
        self.dimension = 384

        # Ensure the DB directory exists
        os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)

        self.index, self.cached_claims, self.cached_verdicts = self.load_cache_from_disk()

    @property
    def encoder(self):
        """Returns the shared embedding model (lazy-loaded singleton)."""
        return get_embedding_model()

    def load_cache_from_disk(self):
        """Restores the database state from files if they exist on the container."""
        if os.path.exists(INDEX_FILE) and os.path.exists(METADATA_FILE):
            try:
                index = faiss.read_index(INDEX_FILE)
                with open(METADATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                log.info(f"[CacheService] [RESTORED] Restored {index.ntotal} cached claims from persistent disk storage.")
                return index, data.get("claims", []), data.get("verdicts", [])
            except Exception as e:
                log.error(f"[CacheService] Error reading backup files: {e}. Starting fresh.")
                
        # Default fallback initialization state
        return faiss.IndexFlatIP(self.dimension), [], []

    def save_cache_to_disk(self):
        """Serializes and saves the memory vector structures safely to local storage.

        EDGE-06 FIX: Uses atomic write pattern (write to temp, then rename) to
        prevent FAISS index and metadata JSON from getting out of sync if the
        process crashes between the two write operations.
        """
        import shutil
        try:
            index_tmp = INDEX_FILE + ".tmp"
            meta_tmp = METADATA_FILE + ".tmp"

            # 1. Write both to temp files first
            faiss.write_index(self.index, index_tmp)
            with open(meta_tmp, "w", encoding="utf-8") as f:
                json.dump({"claims": self.cached_claims, "verdicts": self.cached_verdicts}, f)

            # 2. Atomically replace old files (rename is atomic on POSIX; os.replace on Windows)
            shutil.move(index_tmp, INDEX_FILE)
            shutil.move(meta_tmp, METADATA_FILE)

            log.info("[CacheService] [SAVED] Vector cache saved successfully to local persistent storage.")
        except Exception as e:
            log.error(f"[CacheService] Failed to back up cache components: {e}")
            # Clean up any temp files that might be left behind
            for tmp in [INDEX_FILE + ".tmp", METADATA_FILE + ".tmp"]:
                try:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                except Exception:
                    pass

    def lookup(self, user_claim: str, similarity_threshold: float = 0.85):
        """Checks if a matching claim exists in the local vector cache."""
        if self.index.ntotal == 0 or not self.encoder:
            return None
        
        try:
            # 1. Convert user text to vector and normalize it
            query_vector = self.encoder.encode([user_claim])
            faiss.normalize_L2(query_vector)
            
            # 2. Query FAISS index for the single closest match
            scores, indices = self.index.search(np.array(query_vector).astype('float32'), 1)
            
            best_score = scores[0][0]
            best_idx = indices[0][0]
            
            # 3. If similarity exceeds the threshold, return the cached answer
            if best_idx != -1 and best_score >= similarity_threshold:
                log.info(f"[CacheService] [CACHE HIT] Semantic Similarity Match: {best_score:.2f}")
                return {
                    "verdict": self.cached_verdicts[best_idx],
                    "matched_claim": self.cached_claims[best_idx],
                    "score": float(best_score)
                }
            
            log.info(f"[CacheService] [CACHE MISS] Max match score was: {best_score if best_idx != -1 else 0.0:.2f}")
        except Exception as e:
            log.error(f"[CacheService] Lookup error: {e}")
            
        return None

    def update_cache(self, claim: str, final_verdict_markdown: str):
        """Saves a newly compiled verification result into the FAISS structure and writes to disk."""
        if not self.encoder: return

        try:
            # 1. Vectorize and normalize the claim
            vector = self.encoder.encode([claim])
            faiss.normalize_L2(vector)
            
            # 2. Write to memory index arrays
            self.index.add(np.array(vector).astype('float32'))
            self.cached_claims.append(claim)
            self.cached_verdicts.append(final_verdict_markdown)
            
            log.info(f"[CacheService] 💾 Successfully cached new claim. Total entries: {self.index.ntotal}")
            
            # 3. Immediately persist to disk
            self.save_cache_to_disk()
            
        except Exception as e:
            log.error(f"[CacheService] Cache storage warning: {str(e)}")

# Singleton instance
semantic_cache = SemanticFactCache()
