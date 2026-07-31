"""
CAWNCADE AI — Shared Embedding Model Singleton (PERF-01 Fix).

Problem:
    `evidence_ranker.py` and `cache_service.py` both loaded
    `sentence-transformers/all-MiniLM-L6-v2` independently at module import time,
    consuming ~90 MB of RAM twice (~180 MB total) and doubling startup latency.

Solution:
    This module provides a single lazy-loaded instance shared across the whole
    application.  The model is only loaded on the first call to get_embedding_model(),
    not at import time, keeping startup fast for processes that never need it.

Usage:
    from app.services.embedding_singleton import get_embedding_model, get_multilingual_model
    model = get_embedding_model()
    embeddings = model.encode(["some text"])
"""

from app.utils.logger import log

_minilm_model = None
_multilingual_model = None


def get_embedding_model():
    """
    Returns the singleton all-MiniLM-L6-v2 SentenceTransformer instance.
    Loads it on first call; subsequent calls are O(1) dictionary lookups.
    Thread-safe in CPython due to the GIL protecting the assignment.
    """
    global _minilm_model
    if _minilm_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            log.info("[EmbeddingSingleton] Loading all-MiniLM-L6-v2 (shared instance)...")
            _minilm_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            log.info("[EmbeddingSingleton] ✅ all-MiniLM-L6-v2 loaded and cached.")
        except Exception as e:
            log.warning(f"[EmbeddingSingleton] Could not load all-MiniLM-L6-v2: {e}")
            _minilm_model = None
    return _minilm_model


def get_multilingual_model():
    """
    Returns the singleton paraphrase-multilingual-MiniLM-L12-v2 instance.
    Used for non-English claim analysis. Lazy-loaded on first call.
    """
    global _multilingual_model
    if _multilingual_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            log.info("[EmbeddingSingleton] Loading paraphrase-multilingual-MiniLM-L12-v2 (shared instance)...")
            _multilingual_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            log.info("[EmbeddingSingleton] ✅ multilingual model loaded and cached.")
        except Exception as e:
            log.warning(f"[EmbeddingSingleton] Could not load multilingual model: {e}")
            _multilingual_model = None
    return _multilingual_model
