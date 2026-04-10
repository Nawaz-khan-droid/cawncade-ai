"""
Verification Module.
Detects agreements, conflicts, and patterns across retrieved sources.
"""
import numpy as np
from ...modules.text.embedding_module import embedding_model
from ...utils.logger import log


class SourceVerifier:
    """
    Analyze retrieved sources to detect:
    - Agreement: sources that support the same narrative
    - Conflict: sources that contradict each other
    - Coverage gaps: important aspects not covered by any source
    """

    def __init__(self, agreement_threshold: float = 0.75, conflict_threshold: float = 0.4):
        self.agreement_threshold = agreement_threshold
        self.conflict_threshold = conflict_threshold

    def verify_sources(self, sources: list[dict], query: str) -> dict:
        """
        Main verification method. Analyzes all sources together.
        Returns: agreements, conflicts, coverage_score, diversity_score
        """
        if len(sources) < 2:
            return {
                "agreements": [],
                "conflicts": [],
                "coverage_score": 0.3,
                "diversity_score": 0.1,
                "agreement_score": 0.5,
                "conflict_score": 0.0,
            }

        # Extract text from each source
        texts = [f"{s.get('title', '')} {s.get('snippet', '')}".strip() for s in sources]
        valid_indices = [i for i, t in enumerate(texts) if len(t) > 20]

        if len(valid_indices) < 2:
            return {
                "agreements": [],
                "conflicts": [],
                "coverage_score": 0.3,
                "diversity_score": 0.2,
                "agreement_score": 0.5,
                "conflict_score": 0.0,
            }

        try:
            # Compute pairwise similarity matrix
            valid_texts = [texts[i] for i in valid_indices]
            embeddings = embedding_model.encode_batch(valid_texts)
            sim_matrix = self._cosine_similarity_matrix(embeddings)

            agreements = self._find_agreements(sim_matrix, sources, valid_indices)
            conflicts = self._find_conflicts(sim_matrix, sources, valid_indices)
            agreement_score = self._compute_agreement_score(sim_matrix)
            conflict_score = self._compute_conflict_score(sim_matrix)
            diversity_score = self._compute_diversity_score(sim_matrix)
            coverage_score = self._compute_coverage(sources, query)

        except Exception as e:
            log.error(f"Verification failed: {e}. Returning default scores.")
            agreements, conflicts = [], []
            agreement_score = 0.5
            conflict_score = 0.0
            diversity_score = 0.3
            coverage_score = 0.3

        return {
            "agreements": agreements,
            "conflicts": conflicts,
            "coverage_score": coverage_score,
            "diversity_score": diversity_score,
            "agreement_score": agreement_score,
            "conflict_score": conflict_score,
        }

    def _cosine_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        """Compute pairwise cosine similarity matrix."""
        norm = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norm = np.where(norm == 0, 1, norm)
        normalized = embeddings / norm
        return np.dot(normalized, normalized.T)

    def _find_agreements(self, sim_matrix: np.ndarray, sources: list[dict], indices: list[int]) -> list[dict]:
        """Find groups of sources that strongly agree."""
        agreements = []
        n = len(indices)

        for i in range(n):
            for j in range(i + 1, n):
                if sim_matrix[i][j] >= self.agreement_threshold:
                    agreements.append({
                        "source_1": sources[indices[i]].get("source_name", "Unknown"),
                        "source_2": sources[indices[j]].get("source_name", "Unknown"),
                        "similarity": float(sim_matrix[i][j]),
                        "type": "agreement",
                    })

        return agreements

    def _find_conflicts(self, sim_matrix: np.ndarray, sources: list[dict], indices: list[int]) -> list[dict]:
        """Find sources that potentially conflict (very different coverage)."""
        conflicts = []
        n = len(indices)

        for i in range(n):
            for j in range(i + 1, n):
                if sim_matrix[i][j] <= self.conflict_threshold:
                    conflicts.append({
                        "source_1": sources[indices[i]].get("source_name", "Unknown"),
                        "source_2": sources[indices[j]].get("source_name", "Unknown"),
                        "similarity": float(sim_matrix[i][j]),
                        "type": "conflict",
                    })

        return conflicts

    def _compute_agreement_score(self, sim_matrix: np.ndarray) -> float:
        """Average pairwise similarity (higher = more agreement)."""
        n = sim_matrix.shape[0]
        if n < 2:
            return 0.5

        # Get upper triangle (excluding diagonal)
        mask = np.triu(np.ones_like(sim_matrix, dtype=bool), k=1)
        upper_values = sim_matrix[mask]

        return float(np.mean(upper_values)) if len(upper_values) > 0 else 0.5

    def _compute_conflict_score(self, sim_matrix: np.ndarray) -> float:
        """Proportion of source pairs with low similarity."""
        n = sim_matrix.shape[0]
        if n < 2:
            return 0.0

        mask = np.triu(np.ones_like(sim_matrix, dtype=bool), k=1)
        upper_values = sim_matrix[mask]

        if len(upper_values) == 0:
            return 0.0

        low_sim_count = np.sum(upper_values <= self.conflict_threshold)
        return float(low_sim_count / len(upper_values))

    def _compute_diversity_score(self, sim_matrix: np.ndarray) -> float:
        """Inverse of average similarity = diversity. Higher = more diverse sources."""
        agreement = self._compute_agreement_score(sim_matrix)
        return float(1.0 - agreement)

    def _compute_coverage(self, sources: list[dict], query: str) -> float:
        """
        Estimate how well the sources cover the query aspects.
        Simple heuristic: based on number of sources and their text lengths.
        """
        if not sources:
            return 0.0

        total_text = sum(len(s.get("snippet", "")) + len(s.get("title", "")) for s in sources)
        avg_text = total_text / len(sources)

        # More sources + more text = better coverage
        source_factor = min(len(sources) / 5.0, 1.0)
        text_factor = min(avg_text / 200.0, 1.0)

        return float(min(source_factor * 0.6 + text_factor * 0.4, 1.0))


# Singleton
source_verifier = SourceVerifier()
