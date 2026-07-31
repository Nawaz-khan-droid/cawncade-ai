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
    from sentence_transformers import util
    # PERF-01 FIX: Use the shared singleton instead of loading a separate instance here.
    # Previously this loaded ~90MB of model weights a second time (cache_service.py loads
    # the same model). Now both modules share a single in-memory instance.
    from app.services.embedding_singleton import get_embedding_model, get_multilingual_model
    HAS_MINILM = True
except Exception:
    get_embedding_model = lambda: None  # type: ignore
    get_multilingual_model = lambda: None  # type: ignore
    HAS_MINILM = False


class EvidenceRanker:
    """Hybrid ranker: BM25 (exact names/dates) + SentenceTransformer MiniLM (semantic similarity)."""

    def rank_evidence(self, query: str, sentences: List[str], top_k: int = 3, **kwargs) -> List[Dict[str, Any]]:
        """Ranks evidence sentences using a hybrid BM25 + MiniLM score."""
        if not sentences or not query.strip():
            return []

        clean_sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
        if not clean_sentences:
            return []

        # 1. Lexical BM25 Scores (MinMax Normalized)
        bm25_scores = [0.0] * len(clean_sentences)
        if HAS_BM25:
            try:
                tokenized_corpus = [s.lower().split() for s in clean_sentences]
                tokenized_query = query.lower().split()
                bm25 = BM25Okapi(tokenized_corpus)
                bm25_raw = list(bm25.get_scores(tokenized_query))
                min_b = float(min(bm25_raw)) if bm25_raw else 0.0
                max_b = float(max(bm25_raw)) if bm25_raw else 1.0
                if max_b > min_b:
                    bm25_scores = [float((s - min_b) / (max_b - min_b)) for s in bm25_raw]
                else:
                    bm25_scores = [0.0] * len(bm25_raw)
            except Exception as e:
                log.warning(f"[EvidenceRanker] BM25 calculation exception: {e}")

        # 2. Semantic Similarity Scores
        semantic_scores = [0.0] * len(clean_sentences)
        lang = kwargs.get("lang", "en")
        
        if HAS_MINILM:
            try:
                # Select appropriate model via singleton (lazy-loaded, shared across app)
                if lang != "en":
                    active_model = get_multilingual_model()
                else:
                    active_model = get_embedding_model()

                if active_model:
                    query_emb = active_model.encode(query, convert_to_tensor=True)
                    sentence_embs = active_model.encode(clean_sentences, convert_to_tensor=True)
                    cos_sim = util.cos_sim(query_emb, sentence_embs)[0]
                    # Map from [-1, 1] to [0, 1] for easier fusion
                    semantic_scores = [(float(score) + 1.0) / 2.0 for score in cos_sim]
            except Exception as e:
                log.warning(f"[EvidenceRanker] MiniLM similarity exception: {e}")

        # 3. Entity Alignment Score (from verification_service context)
        # We assume entity_overlap is passed as a float. Default to 0.5.
        entity_score = kwargs.get("entity_overlap", 0.5)

        # 4. Sentence-Level Stance Classification (Negation & Similarity Logic)
        NEGATION_TERMS = {"not", "never", "no", "fake", "untrue", "denies", "debunked", "refutes", "false", "cannot", "doesn't", "don't", "didnt", "isn't", "wasnt"}
        
        ranked_results = []
        for i, sentence in enumerate(clean_sentences):
            b_score = bm25_scores[i]
            s_score = semantic_scores[i]
            hybrid_score = (0.45 * s_score) + (0.35 * b_score) + (0.20 * entity_score)
            
            # Stance classification logic
            sent_words = set(re.findall(r'\b\w+\b', sentence.lower()))
            query_has_negation = bool(set(re.findall(r'\b\w+\b', query.lower())) & NEGATION_TERMS)
            sent_has_negation = bool(sent_words & NEGATION_TERMS)
            
            # If high semantic similarity but one has negation and the other does not -> CONTRADICTS
            if s_score > 0.6 and (query_has_negation != sent_has_negation):
                stance = "CONTRADICTS"
            elif s_score > 0.65 or hybrid_score > 0.6:
                stance = "SUPPORTS"
            elif s_score > 0.45 or hybrid_score > 0.4:
                stance = "PARTIAL"
            else:
                stance = "NEUTRAL"
                
            ranked_results.append({
                "sentence": sentence,
                "bm25_score": round(b_score, 3),
                "semantic_score": round(s_score, 3),
                "hybrid_score": round(hybrid_score, 3),
                "stance": stance
            })

        ranked_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return ranked_results[:top_k]


evidence_ranker = EvidenceRanker()
