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

    def generate_report(self, query: str, evidence_text: str, sources_count: int = 0, **kwargs) -> str:
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

        # 2.5 Language Detection
        detected_lang = "en"
        try:
            from langdetect import detect
            detected_lang = detect(query)
        except Exception:
            pass

        # 4. Hybrid Evidence Ranking & Stance Detection (BM25 + MiniLM + Lexical Negation)
        raw_sentences = [s.strip() for s in evidence_text.split(".") if len(s.strip()) > 15]
        ranked_evidence = evidence_ranker.rank_evidence(
            query, 
            raw_sentences, 
            top_k=5, 
            entity_overlap=match_stats.get("entity_overlap_score", 0.5),
            lang=detected_lang
        )

        stance_counts = {"SUPPORTS": 0, "CONTRADICTS": 0, "PARTIAL": 0, "NEUTRAL": 0}
        for item in ranked_evidence:
            st = item.get("stance", "NEUTRAL")
            stance_counts[st] = stance_counts.get(st, 0) + 1

        # 3. Grounded Deterministic Verdict Calculation
        trusted_count = kwargs.get("trusted_count", 0)
        verdict_res = verdict_engine.calculate_verdict(match_stats, sources_count, len(evidence_text), trusted_count=trusted_count, stance_counts=stance_counts)

        top_sentences_text = (
            "\n".join([f"- [{item['stance']}] {item['sentence']} *(Match Score: {item['hybrid_score']})*" for item in ranked_evidence[:3]])
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

    def analyze_explainable_verification(self, query: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evidence-Derived Explainability & Dated Timeline Generator v3.5
        Produces structured evidence-derived signals, evidence conflict breakdowns, and dated timeline events with confidence.
        """
        import re
        claim_parsed = claim_parser.parse_claim(query)
        evidence_text = "\n".join([f"{s.get('title', '')}: {s.get('snippet', '')}" for s in sources])

        evidence_parsed = claim_parser.parse_claim(evidence_text)
        match_stats = entity_matcher.compare_entities(claim_parsed, evidence_parsed)

        # 1. Evidence Stance & Conflict Analysis
        raw_sentences = [s.strip() for s in evidence_text.split(".") if len(s.strip()) > 15]
        ranked_evidence = evidence_ranker.rank_evidence(
            query, 
            raw_sentences, 
            top_k=8, 
            entity_overlap=match_stats.get("entity_overlap_score", 0.5)
        )

        conflict_breakdown = {"supporting": 0, "contradicting": 0, "neutral": 0}
        for item in ranked_evidence:
            st = item.get("stance", "NEUTRAL")
            if st == "SUPPORTS": conflict_breakdown["supporting"] += 1
            elif st == "CONTRADICTS": conflict_breakdown["contradicting"] += 1
            else: conflict_breakdown["neutral"] += 1

        # 2. Source Trust Metrics
        HIGH_TRUST_DOMAINS = {"nasa.gov", "reuters.com", "bbc.com", "who.int", "cdc.gov", "nih.gov", "nature.com", "snopes.com", "politifact.com"}
        tier1_count = sum(1 for s in sources if any(domain in s.get("url", "") or domain in s.get("domain", "") for domain in HIGH_TRUST_DOMAINS) or s.get("url", "").endswith(".gov") or s.get("url", "").endswith(".edu"))

        # 3. Dated Timeline Generator with Confidence Metrics
        timeline_events = []
        date_pattern = r"\b(19\d{2}|20\d{2})(?:-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))?\b|\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2},?\s+)?(19\d{2}|20\d{2})\b"

        for s in sources:
            text = f"{s.get('title', '')} {s.get('snippet', '')}"
            matches = re.finditer(date_pattern, text, re.IGNORECASE)
            for m in matches:
                matched_date = m.group(0)
                # Compute date precision confidence
                has_exact_day = bool(re.search(r"\d{1,2}", matched_date))
                conf = 0.95 if has_exact_day else 0.70
                timeline_events.append({
                    "date": matched_date,
                    "event": s.get("title", "")[:80],
                    "source": s.get("source_name", s.get("domain", "Web Source")),
                    "confidence": conf
                })

        # Deduplicate timeline events by date
        unique_timeline = []
        seen_dates = set()
        for te in sorted(timeline_events, key=lambda x: x["confidence"], reverse=True):
            if te["date"] not in seen_dates:
                seen_dates.add(te["date"])
                unique_timeline.append(te)

        # 4. Calculate Final Grounded Verdict
        verdict_res = verdict_engine.calculate_verdict(match_stats, len(sources), len(evidence_text), trusted_count=tier1_count, stance_counts=conflict_breakdown)

        return {
            "verdict": verdict_res["verdict"],
            "confidence_score": verdict_res.get("confidence_num", 0.0),  # EDGE-02 FIX: use numeric key, not label string
            "explainability": {
                "entity_alignment": {
                    "matched_entities": match_stats.get("matched_entities", []),
                    "score": round(match_stats.get("entity_overlap_score", 0.0), 2)
                },
                "source_quality": {
                    "tier1_sources": tier1_count,
                    "total_sources": len(sources)
                },
                "timeline_alignment": {
                    "claim_years": claim_parsed.get("years", []),
                    "evidence_years": evidence_parsed.get("years", []),
                    "match_passed": match_stats.get("year_match", True)
                },
                "conflict_breakdown": conflict_breakdown
            },
            "timeline": unique_timeline[:5],
            "top_supporting_evidence": [e["sentence"] for e in ranked_evidence if e["stance"] == "SUPPORTS"][:3],
            "top_contradicting_evidence": [e["sentence"] for e in ranked_evidence if e["stance"] == "CONTRADICTS"][:3]
        }


tier4_verification_service = Tier4VerificationService()
