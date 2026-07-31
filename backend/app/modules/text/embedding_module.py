"""
Embedding Module.
Uses sentence-transformers for semantic similarity, dedup, and conflict detection.
Model: all-MiniLM-L6-v2 (384-dim, fast, free, runs on CPU).

PERF-01 FIX: This module previously lazy-loaded its own SentenceTransformer instance,
creating a potential THIRD copy of the same model in memory (alongside evidence_ranker.py
and cache_service.py). It now delegates to the shared embedding_singleton so all three
consumers share exactly one in-memory instance (~90MB).
"""
import numpy as np
from ...utils.logger import log


class EmbeddingModel:
    """
    Sentence embedding model for semantic operations.
    Delegates to the centralized embedding singleton (lazy-loaded on first use).
    All encode/similarity methods are API-compatible with the original implementation.
    """

    @property
    def model(self):
        """Returns the shared singleton model instance."""
        try:
            from app.services.embedding_singleton import get_embedding_model
            return get_embedding_model()
        except Exception as e:
            log.error(f"[EmbeddingModel] Could not retrieve embedding singleton: {e}")
            return None

    def encode(self, text: str) -> np.ndarray:
        """Encode a single text into embedding vector."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return np.array(embedding, dtype=np.float32)

    def encode_batch(self, texts: list[str]) -> np.ndarray:
        """Encode multiple texts into embedding matrix."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return np.array(embeddings, dtype=np.float32)

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def find_most_similar(self, query: str, candidates: list[str], top_k: int = 5) -> list[tuple[int, float]]:
        """
        Find the most similar candidates to a query.
        Returns list of (index, similarity_score) tuples.
        """
        if not candidates:
            return []

        query_embedding = self.encode(query)
        candidate_embeddings = self.encode_batch(candidates)

        similarities = [
            self.cosine_similarity(query_embedding, candidate_embeddings[i])
            for i in range(len(candidates))
        ]

        # Sort by similarity descending
        indexed_sims = list(enumerate(similarities))
        indexed_sims.sort(key=lambda x: x[1], reverse=True)

        return indexed_sims[:top_k]

    def dedup_by_similarity(self, texts: list[str], threshold: float = 0.9) -> list[int]:
        """
        Find indices of duplicate texts (above similarity threshold).
        Returns indices to REMOVE.
        """
        if len(texts) < 2:
            return []

        embeddings = self.encode_batch(texts)
        to_remove = set()
        n = len(texts)

        for i in range(n):
            if i in to_remove:
                continue
            for j in range(i + 1, n):
                if j in to_remove:
                    continue
                sim = self.cosine_similarity(embeddings[i], embeddings[j])
                if sim >= threshold:
                    to_remove.add(j)  # Keep first occurrence, remove later one

        return list(to_remove)


# Singleton
embedding_model = EmbeddingModel()
