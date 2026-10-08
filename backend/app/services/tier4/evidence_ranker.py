"""
CAWNCADE AI v3.5 ?" Tier 4 Hybrid Evidence Ranker.
Fuses Lexical BM25 (exact names/dates/numbers) with MiniLM Semantic Embeddings (paraphrases & meaning).
Includes a 90MB Zero-Shot Cross-Encoder for deep contextual precision.
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
    from app.services.embedding_singleton import get_embedding_model, get_multilingual_model
    HAS_MINILM = True
except Exception:
    get_embedding_model = lambda: None  # type: ignore
    get_multilingual_model = lambda: None  # type: ignore
    HAS_MINILM = False

# ==============================================================================
# INTEGRATION: Zero-Shot Cross-Encoder
# Why zero-shot? The MS-MARCO model is pre-trained on millions of Bing search 
# query-passage pairs. It already natively understands logical alignment and 
# information retrieval without needing CAWNCADE-specific training.
# ==============================================================================
try:
    from sentence_transformers import CrossEncoder
    # Only ~90MB. Automatically downloaded on first use if space is available.
    cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', max_length=512)
    HAS_CROSS_ENCODER = True
    log.info("[EvidenceRanker] Zero-Shot Cross-Encoder (MS-MARCO) loaded successfully.")
except Exception as e:
    cross_encoder = None
    HAS_CROSS_ENCODER = False
    log.warning(f"[EvidenceRanker] Cross-Encoder failed to load (Check Disk Space!): {e}")


class EvidenceRanker:
    """Hybrid ranker: BM25 + SentenceTransformer + CrossEncoder."""

    def rank_evidence(self, query: str, sentences: List[str], top_k: int = 3, **kwargs) -> List[Dict[str, Any]]:
        """Ranks evidence sentences using a dynamic pipeline (RRF -> CrossEncoder -> Stance)."""
        if not sentences or not query.strip():
            return []

        clean_sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
        if not clean_sentences:
            return []

        # ---------------------------------------------------------
        # STEP 1: Compute Base Scores (BM25 & Semantic)
        # ---------------------------------------------------------
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
            except Exception as e:
                log.warning(f"[EvidenceRanker] BM25 exception: {e}")

        semantic_scores = [0.0] * len(clean_sentences)
        lang = kwargs.get("lang", "en")
        
        if HAS_MINILM:
            try:
                active_model = get_multilingual_model() if lang != "en" else get_embedding_model()
                if active_model:
                    query_emb = active_model.encode(query, convert_to_tensor=True)
                    sentence_embs = active_model.encode(clean_sentences, convert_to_tensor=True)
                    cos_sim = util.cos_sim(query_emb, sentence_embs)[0]
                    semantic_scores = [(float(score) + 1.0) / 2.0 for score in cos_sim]
            except Exception as e:
                log.warning(f"[EvidenceRanker] MiniLM exception: {e}")

        entity_score = kwargs.get("entity_overlap", 0.5)

        # ---------------------------------------------------------
        # STEP 2: The Broad Net (Reciprocal Rank Fusion - RRF)
        # ---------------------------------------------------------
        bm25_ranks = {i: rank for rank, i in enumerate(sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True), 1)}
        semantic_ranks = {i: rank for rank, i in enumerate(sorted(range(len(semantic_scores)), key=lambda i: semantic_scores[i], reverse=True), 1)}
        K_RRF = 60
        
        # Build initial candidate list
        candidates = []
        for i, sentence in enumerate(clean_sentences):
            rrf_score = (1.0 / (K_RRF + bm25_ranks[i])) + (1.0 / (K_RRF + semantic_ranks[i]))
            hybrid_score = rrf_score * (1.0 + (0.20 * entity_score))
            candidates.append({
                "index": i,
                "sentence": sentence,
                "bm25_score": bm25_scores[i],
                "semantic_score": semantic_scores[i],
                "hybrid_score": hybrid_score
            })
            
        # Sort by RRF and keep top 20 for the Cross-Encoder
        candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
        top_candidates = candidates[:20]

        # ---------------------------------------------------------
        # STEP 3: The Precision Scalpel (Cross-Encoder)
        # ---------------------------------------------------------
        if HAS_CROSS_ENCODER and cross_encoder:
            try:
                pairs = [[query, c["sentence"]] for c in top_candidates]
                ce_scores = cross_encoder.predict(pairs)
                
                # Overwrite hybrid score with highly precise cross-encoder score
                for idx, c in enumerate(top_candidates):
                    # Cross-encoder logits can be negative/positive, we just use them for sorting
                    c["hybrid_score"] = float(ce_scores[idx])
                
                # Re-sort using Cross-Encoder scores
                top_candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
            except Exception as e:
                log.warning(f"[EvidenceRanker] Cross-Encoder prediction failed: {e}")

        # Keep only the absolute best (Top K) before heavy stance parsing
        golden_chunks = top_candidates[:top_k]

        # ---------------------------------------------------------
        # STEP 4: The Logical Filter (Stance Classification)
        # ---------------------------------------------------------
        NEGATION_TOKENS = {"not", "never", "no", "nor", "nt", "dont", "didnt", "isnt", "wasnt", 
                           "werent", "cant", "wont", "wouldnt", "couldnt", "shouldnt", "doesnt", 
                           "havent", "hasnt", "hadnt", "neednt", "cannot", "neither", "fake", 
                           "untrue", "false", "myth", "hoax", "debunked", "refutes", "denies", 
                           "disproven", "incorrect", "misleading"}
                           
        NEGATION_SUBSTRINGS = ("didn't", "doesn't", "don't", "isn't", "wasn't", "weren't",
                               "can't", "cannot", "won't", "wouldn't", "couldn't", "shouldn't",
                               "hasn't", "haven't", "hadn't", "no cure", "no miracle", "no evidence",
                               "not a cure", "not proven", "not effective", "fails to", "unable to",
                               "did not cure", "does not cure", "will not cure",
                               "there is no", "there are no", "no scientific")

        final_results = []
        for c in golden_chunks:
            sentence = c["sentence"]
            s_score = c["semantic_score"]
            hybrid_score = c["hybrid_score"]
            
            sent_lower_raw = sentence.lower()
            query_lower_raw = query.lower()
            sent_words = set(re.findall(r'\b\w+\b', sent_lower_raw))
            query_words_set = set(re.findall(r'\b\w+\b', query_lower_raw))

            query_has_negation = bool(query_words_set & NEGATION_TOKENS) or any(ns in query_lower_raw for ns in NEGATION_SUBSTRINGS)
            sent_has_negation = bool(sent_words & NEGATION_TOKENS) or any(ns in sent_lower_raw for ns in NEGATION_SUBSTRINGS)
            
            # Stance Logic
            if s_score > 0.6 and (query_has_negation != sent_has_negation):
                stance = "CONTRADICTS"
            elif sent_has_negation and not query_has_negation and s_score > 0.45:
                stance = "CONTRADICTS"
            elif s_score > 0.65 or (not HAS_CROSS_ENCODER and hybrid_score > 0.6) or (HAS_CROSS_ENCODER and hybrid_score > 2.0):
                stance = "SUPPORTS"
            elif s_score > 0.45 or (not HAS_CROSS_ENCODER and hybrid_score > 0.4) or (HAS_CROSS_ENCODER and hybrid_score > 0.0):
                stance = "PARTIAL"
            else:
                stance = "NEUTRAL"
                
            final_results.append({
                "sentence": sentence,
                "bm25_score": round(c["bm25_score"], 3),
                "semantic_score": round(s_score, 3),
                "hybrid_score": round(hybrid_score, 3),
                "stance": stance
            })

        return final_results

evidence_ranker = EvidenceRanker()
