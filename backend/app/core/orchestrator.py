"""
CAWNCADE AI v3.0 — Pipeline Orchestrator.
Coordinates the full C.L.E.A.R. verification pipeline:
  1. Input -> Extract (URL/Text/YouTube/Image)
  2. Safety -> Safe Browsing check
  3. Fact-Check -> Google Fact Check API (historical debunks)
  4. Research -> Tiered Search (Google -> Tavily -> DDG -> RSS)
  5. Agent -> Llama 3.1 ReAct Agent for deep-dive synthesis (Phase 3)
  6. Score -> CAWNCADE multi-factor scoring
"""

import re
import time
import asyncio
from app.services.news_service import tiered_search, verify_against_trusted
from app.services.fact_check_service import check_claim, get_verdict_from_claims
from app.services.safe_browsing_service import check_url
from app.services.agent_service import cawncade_agent
from app.services.youtube_service import analyze_youtube, is_youtube_url
from app.services.vision_service import analyze_image
from app.modules.extraction.extractor import content_extractor
from app.modules.scoring.scorer import scoring_engine
from app.core.trusted_domains import get_trust_info
from app.utils.logger import log
from app.utils.helpers import compute_recency


class Orchestrator:
    """Main pipeline orchestrator. Truth over Speed: Reports conflicts rather than picking winners."""

    async def process(self, input_text: str, input_type: str = "auto", max_sources: int = 10) -> dict:
        start_time = time.time()

        # Step 0: Detect input type
        if input_type == "auto":
            if is_youtube_url(input_text):
                input_type = "youtube"
            elif content_extractor.is_url(input_text):
                input_type = "url"
            else:
                input_type = "text"

        # Step 1: Extract content
        query = input_text
        extraction_meta = {"method": "raw_input"}

        if input_type == "url":
            extraction = await content_extractor.extract_from_url(input_text)
            if extraction.get("title") or extraction.get("text"):
                query = f"{extraction.get('title', '')} {extraction.get('text', '')[:500]}".strip()
                extraction_meta = {"method": "url_extraction", "title": extraction.get("title", "")}
                log.info(f"[Orchestrator] URL extracted: '{extraction.get('title', 'N/A')[:60]}'")
            else:
                topic = content_extractor.extract_keywords_from_url(input_text)
                if topic:
                    query = topic
                    extraction_meta = {"method": "url_keyword_extraction", "topic": topic}

            safety = await check_url(input_text)
            if not safety.get("safe", True):
                extraction_meta["safety_warning"] = safety.get("threats", [])

        elif input_type == "youtube":
            yt_result = await analyze_youtube(input_text)
            extraction_meta = {
                "method": "youtube_dual_stream",
                "video_id": yt_result.get("video_id"),
                "title": yt_result.get("title", ""),
                "channel": yt_result.get("channel", ""),
                "duration": yt_result.get("duration", 0),
                "api_stream": yt_result.get("api_stream"),
                "scraper_stream": yt_result.get("scraper_stream"),
                "view_count": yt_result.get("view_count", 0),
            }
            if yt_result.get("success"):
                # Prefer transcript for fact-checking, fall back to description
                if yt_result.get("transcript"):
                    query = yt_result["transcript"][:2000]
                    extraction_meta["transcript_used"] = True
                elif yt_result.get("description"):
                    query = yt_result["description"][:2000]
                    extraction_meta["description_fallback"] = True
                log.info(f"[Orchestrator] YouTube Dual-Stream: API={yt_result.get('api_stream')}, Scraper={yt_result.get('scraper_stream')}, Title='{yt_result.get('title', 'N/A')[:60]}'")
            else:
                topic = content_extractor.extract_keywords_from_url(input_text)
                if topic:
                    query = topic
                extraction_meta["error"] = yt_result.get("error")

        if not query.strip():
            return self._empty_result("Could not extract meaningful content from input.")

        log.info(f"[Orchestrator] Search query: '{query[:100]}'")

        # Step 2: Fact Check (pre-flight)
        fact_check_result = await check_claim(query)
        fact_verdict = get_verdict_from_claims(fact_check_result.get("claims", []))

        if fact_verdict["debunked"]:
            compute_time = int((time.time() - start_time) * 1000)
            log.info(f"[Orchestrator] Claim DEBUNKED: {fact_verdict['verdict']}")
            return {
                "answer": fact_verdict["verdict"], "context_summary": "This claim has been investigated by fact-checking organizations.",
                "agreements": [], "conflicts": [], "sources_cited": fact_verdict.get("sources", []),
                "confidence": 0.0, "scores": {"confidence_score": 0.0,
                    "confidence_label": "DEBUNKED - Fact-checked organizations have flagged this claim",
                    "dynamic_disclaimers": ["Verified via Google Fact Check Tools API"]},
                "compute_time_ms": compute_time, "status": "debunked",
                "metadata": {"input_type": input_type, "extraction": extraction_meta,
                    "fact_check": fact_check_result, "fact_verdict": fact_verdict, "sources_retrieved": 0},
            }

        # Step 3: Research - Tiered Search
        search_result = await tiered_search(query, max_sources=max_sources)
        sources = search_result.get("sources", [])

        if not sources:
            short_query = " ".join(query.split()[:10])
            if short_query != query:
                log.info(f"[Orchestrator] Retrying with shorter query: '{short_query[:60]}'")
                retry = await tiered_search(short_query, max_sources=max_sources)
                sources = retry.get("sources", [])

        if not sources:
            compute_time = int((time.time() - start_time) * 1000)
            return self._empty_result(
                f"No relevant sources found for: '{query[:60]}'. Try rephrasing or entering the topic directly as text.",
                compute_time, extraction_meta, fact_check_result, fact_verdict, search_result)

        # Step 4: Score sources
        for src in sources:
            domain = src.get("domain", "")
            trust = get_trust_info(domain)
            src["trust_tier"] = trust["label"]
            src["trust_multiplier"] = trust["multiplier"]
            src["credibility_score"] = trust["multiplier"]
            src["recency_score"] = compute_recency(src.get("published_at"))

        # Step 5: Verify - Cross-source analysis
        trusted_results = await verify_against_trusted(query)
        trusted_domains_found = set()
        for src in trusted_results:
            d = src.get("domain", "")
            if d:
                trusted_domains_found.add(d)

        for src in sources:
            src["is_trusted_domain"] = src.get("domain", "") in trusted_domains_found

        # Step 6: Compute aggregate scores
        credibility_avg = sum(s.get("credibility_score", 0.5) for s in sources) / len(sources)
        recency_avg = sum(s.get("recency_score", 0.5) for s in sources) / len(sources)
        trusted_ratio = len([s for s in sources if s.get("is_trusted_domain")]) / len(sources)

        scores = scoring_engine.compute_score(
            credibility_avg=credibility_avg, agreement_score=trusted_ratio,
            diversity_score=min(len(set(s.get("channel", "") for s in sources)) / 5, 1.0),
            recency_score=recency_avg, grounding_score=min(len(sources) / 10, 1.0),
        )

        # Step 7: Build synthesis
        synthesis = self._build_synthesis(query, sources, scores, fact_verdict, extraction_meta, trusted_domains_found, search_result.get("tier_stats", {}))

        # Step 8: Phase 3 - Agent Deep Dive (optional, runs in parallel with synthesis)
        agent_report = ""
        try:
            evidence_context = "\n".join([f"- {s.get('title', '')}: {s.get('snippet', '')[:200]}" for s in sources[:5]])
            agent_report = await cawncade_agent.run_investigation(query, evidence_context)
            if agent_report and len(agent_report) > 100:
                synthesis["layer3_deep_dive"] = agent_report
                log.info(f"[Orchestrator] Agent deep-dive: {len(agent_report)} chars")
        except Exception as e:
            log.warning(f"[Orchestrator] Agent deep-dive failed: {e}")

        compute_time = int((time.time() - start_time) * 1000)

        return {
            "answer": synthesis.get("layer1_claim", ""),
            "context_summary": synthesis.get("layer2_verification", ""),
            "agent_deep_dive": synthesis.get("layer3_deep_dive", ""),
            "agreements": synthesis.get("agreements", []),
            "conflicts": synthesis.get("conflicts", []),
            "sources_cited": [
                {"url": s.get("url", ""), "title": s.get("title", ""), "snippet": s.get("snippet", "")[:200],
                 "source_name": s.get("source_name", ""), "channel": s.get("channel", ""),
                 "trust_tier": s.get("trust_tier", "unknown"), "is_trusted": s.get("is_trusted_domain", False),
                 "retrieval_tier": s.get("retrieval_tier", "")}
                for s in sources[:10]
            ],
            "confidence": scores.get("confidence_score", 0.0), "scores": scores,
            "compute_time_ms": compute_time, "status": "completed",
            "metadata": {"input_type": input_type, "extraction": extraction_meta,
                "fact_check": fact_check_result, "fact_verdict": fact_verdict,
                "tier_stats": search_result.get("tier_stats", {}), "sources_retrieved": len(sources),
                "trusted_domains_found": list(trusted_domains_found),
                "agent_used": bool(agent_report and len(agent_report) > 100)},
        }

    async def process_image(self, image_base64: str) -> dict:
        start_time = time.time()
        vision_result = await analyze_image(image_base64)
        from app.services.vision_service import extract_image_metadata
        metadata = await extract_image_metadata(image_base64)
        compute_time = int((time.time() - start_time) * 1000)
        return {
            "label": vision_result.get("label", "unknown"), "confidence": vision_result.get("confidence", 0.0),
            "model_used": vision_result.get("model_used", ""), "all_predictions": vision_result.get("all_predictions", []),
            "metadata": metadata, "error": vision_result.get("error"),
            "compute_time_ms": compute_time, "status": "completed" if vision_result.get("label") != "error" else "failed",
        }

    def _build_synthesis(self, query, sources, scores, fact_verdict, extraction_meta, trusted_domains, tier_stats):
        title = extraction_meta.get("title", query[:100])
        layer1 = f"Analysis of: {title}"

        trusted_count = len(trusted_domains)
        total = len(sources)

        if fact_verdict.get("verdict") and "No prior" not in fact_verdict.get("verdict", ""):
            layer2 = fact_verdict["verdict"]
        elif trusted_count > total * 0.5:
            layer2 = f"Claim corroborated by {trusted_count} trusted source(s) out of {total} sources reviewed. Trusted domains: {', '.join(list(trusted_domains)[:5])}."
        elif trusted_count > 0:
            layer2 = f"Partially verified. {trusted_count} trusted source(s) confirmed coverage, but {total - trusted_count} unverified source(s) also reported on this topic. Cross-referencing recommended."
        else:
            layer2 = f"No confirmation from trusted sources found across {total} results. This claim has not been verified by established fact-checkers or wire services."

        return {
            "layer1_claim": layer1, "layer2_verification": layer2, "layer3_deep_dive": "",
            "agreements": [s["source_name"] for s in sources if s.get("is_trusted_domain")][:5],
            "conflicts": [],
        }

    def _empty_result(self, message, compute_time=0, extraction=None, fact_check=None, fact_verdict=None, search_result=None):
        return {
            "answer": message, "context_summary": "Retrieval returned no results.",
            "agreements": [], "conflicts": [], "sources_cited": [],
            "confidence": 0.0, "scores": {"confidence_score": 0.0,
                "confidence_label": "INSUFFICIENT - Cannot reliably assess",
                "dynamic_disclaimers": ["No sources found for verification."]},
            "compute_time_ms": compute_time, "status": "no_sources",
            "metadata": {"extraction": extraction or {}, "fact_check": fact_check or {"claims": [], "total": 0},
                "fact_verdict": fact_verdict or {"debunked": False, "verdict": "N/A", "sources": []},
                "tier_stats": search_result.get("tier_stats", {}) if search_result else {}, "sources_retrieved": 0},
        }


orchestrator = Orchestrator()
