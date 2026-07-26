"""
CAWNCADE AI v3.5 — Tier 4 Grounded Deterministic Verdict Engine.
Calculates grounded verdicts strictly based on evidence agreement, timeline alignment, and citation counts.
"""

from typing import Dict, Any


class VerdictEngine:
    """Calculates grounded deterministic verdicts without claiming generative AI reasoning."""

    def calculate_verdict(self, match_stats: Dict[str, Any], sources_count: int, evidence_length: int) -> Dict[str, Any]:
        overlap_score = match_stats.get("entity_overlap_score", 0.5)
        year_conflict = match_stats.get("year_conflict", False)
        year_match = match_stats.get("year_match", True)

        if sources_count == 0 or evidence_length < 50:
            verdict = "INSUFFICIENT EVIDENCE FOR DETERMINISTIC VERDICT"
            confidence = "LOW"
            explanation = "No readable text evidence was retrieved to perform deterministic alignment."
        elif year_conflict and overlap_score >= 0.4:
            verdict = "CONTRADICTED BY AVAILABLE EVIDENCE (DATE / TIMELINE MISMATCH)"
            confidence = "MEDIUM"
            explanation = f"Timeline conflict detected: Claim specified year {match_stats.get('claim_years')} whereas evidence indicates {match_stats.get('evidence_years')}."
        elif overlap_score >= 0.6 and year_match:
            verdict = "SUPPORTED BY AVAILABLE EVIDENCE"
            confidence = "HIGH" if sources_count >= 3 else "MEDIUM"
            explanation = f"Claim entities and timeline matched across {sources_count} retrieved web source(s)."
        elif overlap_score >= 0.3:
            verdict = "MIXED / PARTIALLY SUPPORTED EVIDENCE"
            confidence = "MEDIUM"
            explanation = "Partial entity alignment found; some claim details lack explicit source verification."
        else:
            verdict = "UNVERIFIED / NO STRONG EVIDENCE MATCH"
            confidence = "LOW"
            explanation = "Available web citations do not contain sufficient matching entity context."

        return {
            "verdict": verdict,
            "confidence": confidence,
            "explanation": explanation,
            "entity_overlap_score": overlap_score,
            "year_match": year_match,
            "year_conflict": year_conflict,
        }


verdict_engine = VerdictEngine()
