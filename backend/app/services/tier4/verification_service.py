"""
CAWNCADE AI v3.5 — Tier 4 Grounded Evidence Verification Service.
Coordinates claim parsing, hybrid evidence ranking (BM25 + MiniLM), entity matching,
and deterministic verdict generation.
"""

from typing import Dict, Any, List
from app.services.tier4.claim_parser import claim_parser
from app.services.tier4.evidence_ranker import evidence_ranker
from app.services.tier4.entity_matcher import entity_matcher
from app.services.tier4.verdict_engine import verdict_engine
from app.services.tier4.summarizer import extractive_summarizer


class Tier4VerificationService:
    """
    Tier 4 Grounded Evidence Verification Engine (No-LLM Mode).
    Performs deterministic NLP analysis, BM25 + MiniLM hybrid evidence ranking,
    and grounded rule-based verification.
    """

    def generate_report(self, query: str, evidence_text: str, sources_count: int = 0) -> str:
        """Generates a transparent, grounded evidence report."""
        if not evidence_text or len(evidence_text.strip()) < 30:
            return (
                "### ⚠️ Tier 4 Computational Analysis (No-LLM Mode)\n"
                "*No readable text evidence was retrieved from target. Verification performed strictly via search citations.*"
            )

        # 1. Claim Decomposition & Evidence Entity Parsing
        claim_parsed = claim_parser.parse_claim(query)
        evidence_parsed = claim_parser.parse_claim(evidence_text)

        # 2. Entity Overlap & Timeline Conflict Match
        match_stats = entity_matcher.compare_entities(claim_parsed, evidence_parsed)

        # 3. Grounded Deterministic Verdict Calculation
        verdict_res = verdict_engine.calculate_verdict(match_stats, sources_count, len(evidence_text))

        # 4. Hybrid Evidence Ranking (BM25 + MiniLM)
        raw_sentences = [s.strip() for s in evidence_text.split(".") if len(s.strip()) > 15]
        ranked_evidence = evidence_ranker.rank_evidence(query, raw_sentences, top_k=3)

        top_sentences_text = (
            "\n".join([f"- {item['sentence']} *(Match Score: {item['hybrid_score']})*" for item in ranked_evidence])
            if ranked_evidence
            else f"- {extractive_summarizer.summarize(evidence_text, 2)}"
        )

        people_str = ", ".join(evidence_parsed["people"][:5]) or "None detected"
        orgs_str = ", ".join(evidence_parsed["organizations"][:5]) or "None detected"
        locs_str = ", ".join(evidence_parsed["locations"][:5]) or "None detected"
        dates_str = ", ".join(evidence_parsed["dates"][:5]) or "None detected"

        return (
            f"### 📊 Local Computational Evidence Verification (Tier 4 No-LLM Mode)\n"
            f"*Notice: Online AI LLM reasoning was unavailable. This report was computed deterministically using CPU NLP (spaCy NER, LexRank, BM25 + MiniLM hybrid ranking, and Citation Alignment).* \n\n"
            f"**Grounded Deterministic Verdict**: `{verdict_res['verdict']}` (Confidence: **{verdict_res['confidence']}**)\n"
            f"- **Entity Overlap Match**: `{int(verdict_res['entity_overlap_score'] * 100)}%` | **Timeline Match**: `{'PASSED' if verdict_res['year_match'] else 'CONFLICT DETECTED'}`\n"
            f"- *Analysis*: {verdict_res['explanation']}\n\n"
            f"**Hybrid BM25 + MiniLM Ranked Evidence Sentences:**\n{top_sentences_text}\n\n"
            f"**Grounded Entities Detected:**\n"
            f"- 👤 **People**: {people_str}\n"
            f"- 🏢 **Organizations**: {orgs_str}\n"
            f"- 📍 **Locations**: {locs_str}\n"
            f"- 📅 **Timeline / Dates**: {dates_str}\n\n"
            f"**Evidence Grounding**: Cross-referenced across {sources_count} web citation(s)."
        )


tier4_verification_service = Tier4VerificationService()
