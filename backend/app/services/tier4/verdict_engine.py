"""
CAWNCADE AI v3.5 — Tier 4 Grounded Deterministic Verdict Engine.
Calculates grounded verdicts strictly based on evidence agreement, timeline alignment, and citation counts.
"""

from typing import Dict, Any


class VerdictEngine:
    """Calculates grounded deterministic verdicts using mathematical confidence & sentence stance analysis."""

    def calculate_verdict(self, match_stats: Dict[str, Any], sources_count: int, evidence_length: int, trusted_count: int = 0, stance_counts: Dict[str, int] = None) -> Dict[str, Any]:
        overlap_score = match_stats.get("entity_overlap_score", 0.5)
        year_conflict = match_stats.get("year_conflict", False)
        year_match = match_stats.get("year_match", True)

        n_sup = stance_counts.get("SUPPORTS", 0) if stance_counts else 0
        n_con = stance_counts.get("CONTRADICTS", 0) if stance_counts else 0
        n_part = stance_counts.get("PARTIAL", 0) if stance_counts else 0
        n_neu = stance_counts.get("NEUTRAL", 0) if stance_counts else 0
        total_sentences = n_sup + n_con + n_part + n_neu

        if sources_count == 0 or evidence_length < 50:
            verdict = "INSUFFICIENT EVIDENCE FOR DETERMINISTIC VERDICT"
            confidence_label = "LOW"
            confidence_val = 0.10
            explanation = "No readable text evidence was retrieved to perform deterministic alignment."
        elif (n_con > 0 or year_conflict) and n_con >= n_sup:
            verdict = "CONTRADICTED BY AVAILABLE EVIDENCE"
            confidence_label = "HIGH" if (sources_count >= 2 or trusted_count > 0) else "MEDIUM"
            confidence_val = 0.85 if trusted_count > 0 else 0.65
            explanation = f"Contradicting evidence detected across sources. Explicit negation or timeline mismatch found."
        elif (n_sup > 0 or overlap_score >= 0.5) and year_match and n_con == 0:
            verdict = "SUPPORTED BY AVAILABLE EVIDENCE"
            confidence_label = "HIGH" if (sources_count >= 2 or trusted_count > 0) else "MEDIUM"
            confidence_val = 0.90 if trusted_count > 0 else 0.70
            explanation = f"Claim entities and stance corroborated across {sources_count} retrieved source(s)."
        elif n_sup > 0 and n_con > 0 or n_part > 0:
            verdict = "MIXED / PARTIALLY SUPPORTED EVIDENCE"
            confidence_label = "MEDIUM"
            confidence_val = 0.50
            explanation = "Partial entity alignment found; some claim details lack explicit source verification or show conflicting coverage."
        else:
            verdict = "UNVERIFIED / NO STRONG EVIDENCE MATCH"
            confidence_label = "LOW"
            confidence_val = 0.30
            explanation = "Available web citations do not contain sufficient matching entity context."
            
        # ── Mathematical Confidence Formula Specification ──
        # Confidence = 0.35 * StanceRatio + 0.25 * TrustMult_max + 0.20 * SourceDiversity + 0.20 * RetrievalCompleteness
        stance_ratio = (n_sup - n_con) / max(1, total_sentences) if total_sentences > 0 else 0.0
        trust_mult_max = 1.0 if trusted_count >= 2 else (0.75 if trusted_count == 1 else 0.40)
        source_diversity = min(1.0, sources_count / 4.0)
        retrieval_completeness = min(1.0, total_sentences / 5.0) if total_sentences > 0 else 0.2
        
        math_confidence = (0.35 * max(0.0, stance_ratio)) + (0.25 * trust_mult_max) + (0.20 * source_diversity) + (0.20 * retrieval_completeness)
        final_confidence = round(max(confidence_val, math_confidence) * 100, 1)

        return {
            "verdict": verdict,
            "confidence": f"{confidence_label} ({final_confidence}%)",
            "confidence_num": final_confidence,
            "explanation": explanation,
            "entity_overlap_score": overlap_score,
            "year_match": year_match,
            "year_conflict": year_conflict,
        }


verdict_engine = VerdictEngine()
