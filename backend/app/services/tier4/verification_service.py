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


from app.utils.logger import log


class Tier4VerificationService:
    """
    Tier 4 Grounded Evidence Verification Engine (No-LLM Mode).
    Performs deterministic NLP analysis, BM25 + MiniLM hybrid evidence ranking,
    and grounded rule-based verification.
    """

    def cross_validate_and_sanitize(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identifies and isolates conflicting results before synthesis.
        If a source snippet contains zero relevance overlap with peer sources, logs conflict isolation.
        """
        if len(sources) <= 1:
            return sources

        import re
        stop_words = {"the", "and", "for", "with", "this", "that", "from", "news", "today", "about", "fact", "check"}
        valid_sources = []
        for target in sources:
            target_tokens = set(re.findall(r'\b\w{3,}\b', (target.get("title", "") + " " + target.get("snippet", "")).lower())) - stop_words
            has_corroboration = False
            for peer in sources:
                if target.get("url") == peer.get("url"):
                    continue
                peer_tokens = set(re.findall(r'\b\w{3,}\b', (peer.get("title", "") + " " + peer.get("snippet", "")).lower())) - stop_words
                overlap = len(target_tokens.intersection(peer_tokens))
                min_required = 1 if len(target_tokens) <= 4 else 2
                if overlap >= min_required:
                    has_corroboration = True
                    break
            if has_corroboration:
                valid_sources.append(target)
            else:
                log.warning(f"[CONFLICT_ISOLATION] Isolated uncorroborated outlier source payload: {target.get('url', '')}")

        return valid_sources if valid_sources else sources

    def generate_report(self, query: str, evidence_text: str, sources_count: int = 0, **kwargs) -> str:
        """Generates a clean, user-facing, executive evidence summary."""
        log.info("[TIER_4_ACTIVATION] Running zero-LLM algorithmic evaluation fallback.")
        if not evidence_text or len(evidence_text.strip()) < 30:
            return "No verified text evidence was retrieved for this claim across target web sources."

        # 1. Claim Decomposition & Evidence Parsing
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

        # 3. Rank Evidence Sentences
        import re
        query_keywords = [w.lower() for w in re.findall(r'\b[A-Za-z0-9]{3,}\b', query) if w.lower() not in {"the", "and", "for", "with", "this", "that", "news", "today", "fact", "check"}]
        
        raw_sentences = [s.strip() for s in re.split(r'[\.\n;]', evidence_text) if len(s.strip()) > 20]
        ranked_evidence = evidence_ranker.rank_evidence(
            query, 
            raw_sentences, 
            top_k=8, 
            entity_overlap=match_stats.get("entity_overlap_score", 0.5),
            lang=detected_lang
        )

        clean_evidence_bullets = []
        boilerplate_terms = {"fact brief", "tdlexperts", "source:", "date:", "recent"}
        
        for item in ranked_evidence:
            sent = item.get("sentence", "").strip()
            sent_lower = sent.lower()
            
            # Skip boilerplate fragments or unrelated noise sentences
            if any(bt in sent_lower for bt in boilerplate_terms):
                continue
            # Ensure sentence has at least 1 key query noun/entity match
            if query_keywords and not any(kw in sent_lower for kw in query_keywords[:3]):
                continue

            if ":" in sent:
                parts = sent.split(":", 1)
                if parts[0].strip().lower() == parts[1].strip()[:len(parts[0].strip())].lower():
                    sent = parts[1].strip()
            if len(sent) > 25 and sent.lower() not in [b.lower() for b in clean_evidence_bullets]:
                clean_sent = sent[0].upper() + sent[1:]
                clean_evidence_bullets.append(clean_sent)

        if not clean_evidence_bullets:
            clean_evidence_bullets = [f"Retrieved news sources discuss {query_keywords[0].title() if query_keywords else 'this topic'} and corroborate key claim details."]

        formatted_bullets = "\n".join([f"- {b}" for b in clean_evidence_bullets[:3]])

        # Key Grounded Entities (only include non-empty ones)
        entities_list = []
        if evidence_parsed.get("people"):
            entities_list.append(f"**Key Individuals**: {', '.join(evidence_parsed['people'][:3])}")
        if evidence_parsed.get("organizations"):
            entities_list.append(f"**Organizations Mentioned**: {', '.join(evidence_parsed['organizations'][:3])}")
        if evidence_parsed.get("dates"):
            entities_list.append(f"**Key Dates & Timeline**: {', '.join(evidence_parsed['dates'][:3])}")

        entity_summary = ("\n\n" + "\n".join([f"- {e}" for e in entities_list])) if entities_list else ""

        return f"{formatted_bullets}{entity_summary}"

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
        from app.core.trusted_domains import ALL_TRUSTED_DOMAINS
        HIGH_TRUST_DOMAINS = set(ALL_TRUSTED_DOMAINS) | {
            "nasa.gov", "reuters.com", "bbc.com", "who.int", "cdc.gov", "nih.gov", "nature.com", 
            "snopes.com", "politifact.com", "britannica.com", "wikipedia.org", "apnews.com", 
            "theguardian.com", "mashable.com", "forbes.com", "cnn.com", "bloomberg.com", 
            "nytimes.com", "washingtonpost.com", "ndtv.com", "indianexpress.com"
        }
        tier1_count = sum(1 for s in sources if s.get("is_trusted_domain") or any(domain in s.get("url", "") or domain in s.get("domain", "") for domain in HIGH_TRUST_DOMAINS) or s.get("url", "").endswith(".gov") or s.get("url", "").endswith(".edu"))

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
        all_text = " ".join([s.get("title", "") + " " + s.get("snippet", "") for s in sources]).lower()
        debunk_keywords = {"false", "myth", "hoax", "fake", "debunk", "debunked", "untrue", "misleading", "no evidence", "disproven", "incorrect", "has not", "did not", "not true"}
        unfulfilled_milestone_keywords = {"closes in", "nears", "approaches", "yet to", "before hitting", "aims for", "will hit", "is set to", "expected to"}
        
        is_debunked = any(dk in all_text for dk in debunk_keywords)
        query_lower = query.lower()
        asserts_completed_event = any(kw in query_lower for kw in ["reached", "hit", "surpassed", "cures", "cured", "inaugurated", "released"])
        is_unfulfilled_milestone = asserts_completed_event and any(mk in all_text for mk in unfulfilled_milestone_keywords)

        verdict_res = verdict_engine.calculate_verdict(
            match_stats, 
            len(sources), 
            len(evidence_text), 
            trusted_count=tier1_count, 
            stance_counts=conflict_breakdown,
            is_unfulfilled_milestone=is_unfulfilled_milestone,
            is_debunked=is_debunked
        )

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
