"""
CAWNCADE AI v3.5 — Tier 4 Hybrid Evidence Ranker.
Fuses Lexical BM25 (exact names/dates/numbers) with MiniLM Semantic Embeddings (paraphrases & meaning).
"""

import re
from typing import List, Dict, Any
from app.utils.logger import log

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

try:
    from sentence_transformers import SentenceTransformer, util
    # Shared CPU instance for semantic similarity scoring
    minilm_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    HAS_MINILM = True
except Exception:
    minilm_model = None
    HAS_MINILM = False


class EvidenceRanker:
    """Hybrid ranker: BM25 (exact names/dates) + SentenceTransformer MiniLM (semantic similarity)."""

    def rank_evidence(self, query: str, sentences: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
        """Ranks evidence sentences using a hybrid BM25 + MiniLM score."""
        if not sentences or not query.strip():
            return []

        clean_sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
        if not clean_sentences:
            return []

        # 1. Lexical BM25 Scores
        bm25_scores = [0.0] * len(clean_sentences)
        if HAS_BM25:
            try:
                tokenized_corpus = [s.lower().split() for s in clean_sentences]
                tokenized_query = query.lower().split()
                bm25 = BM25Okapi(tokenized_corpus)
                bm25_raw = bm25.get_scores(tokenized_query)
                max_b = max(bm25_raw) if max(bm25_raw) > 0 else 1.0
                bm25_scores = [s / max_b for s in bm25_raw]
            except Exception as e:
                log.warning(f"[EvidenceRanker] BM25 calculation exception: {e}")

        # 2. Semantic Similarity Scores (all-MiniLM-L6-v2)
        semantic_scores = [0.0] * len(clean_sentences)
        if HAS_MINILM and minilm_model:
            try:
                query_emb = minilm_model.encode(query, convert_to_tensor=True)
                sentence_embs = minilm_model.encode(clean_sentences, convert_to_tensor=True)
                cos_sim = util.cos_sim(query_emb, sentence_embs)[0]
                semantic_scores = [float(score) for score in cos_sim]
            except Exception as e:
                log.warning(f"[EvidenceRanker] MiniLM similarity exception: {e}")

        # 3. Hybrid Fusion (50% Lexical + 50% Semantic)
        ranked_results = []
        for i, sentence in enumerate(clean_sentences):
            b_score = bm25_scores[i]
            s_score = semantic_scores[i]
            hybrid_score = (0.5 * b_score) + (0.5 * s_score)
            ranked_results.append({
                "sentence": sentence,
                "bm25_score": round(b_score, 3),
                "semantic_score": round(s_score, 3),
                "hybrid_score": round(hybrid_score, 3),
            })

        ranked_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return ranked_results[:top_k]


evidence_ranker = EvidenceRanker()
