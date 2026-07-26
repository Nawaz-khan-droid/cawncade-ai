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

# -- Local Extractive NLP Summarization (No-LLM Fallback) --
try:
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.lex_rank import LexRankSummarizer
except ImportError:
    pass

def generate_local_nlp_summary(scraped_evidence_text: str, num_sentences: int = 3) -> str:
    """Generates an objective summary of web evidence locally on CPU via NLP."""
    if not scraped_evidence_text.strip() or len(scraped_evidence_text) < 50:
        return "Insufficient live web data retrieved to synthesize an empirical summary."
        
    try:
        parser = PlaintextParser.from_string(scraped_evidence_text, Tokenizer("english"))
        summarizer = LexRankSummarizer()
        summary_sentences = summarizer(parser.document, num_sentences)
        compiled_summary = " ".join([str(sentence) for sentence in summary_sentences])
        
        return (
            f"### 📊 Local Computational Analysis\n"
            f"*This baseline summary was computed locally on the container server via extractive statistical NLP metrics (LexRank).*\n\n"
            f"{compiled_summary}"
        )
    except Exception as e:
        return f"Local statistical synthesis bypassed due to structural anomaly: {str(e)}"



class Orchestrator:
    """Main pipeline orchestrator. Truth over Speed: Reports conflicts rather than picking winners."""

    def __init__(self):
        import os
        # Ensure the 'db' folder exists for FAISS vector storage on live containers
        os.makedirs("db", exist_ok=True)
        
        # Ensure NLTK punkt is downloaded for sumy LexRank tokenizer
        try:
            import nltk
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            import nltk
            nltk.download('punkt')
        except ImportError:
            pass


    async def process(self, input_text: str = "", input_type: str = "auto", max_sources: int = 10, user_query: str = None, image_base64: str = None) -> dict:
        start_time = time.time()
        image_metadata = ""
        query = input_text
        extraction_meta = {"method": "raw_input"}

        # Step 0: Image Pre-Processing (Phase 4)
        if image_base64:
            import base64
            from app.services.image_service import extract_image_evidence
            try:
                # Handle data URI scheme if present
                base64_data = image_base64.split(",")[1] if "," in image_base64 else image_base64
                img_bytes = base64.b64decode(base64_data)
                img_data = extract_image_evidence(img_bytes)
                
                query = img_data["ocr_text"]
                input_text = query
                input_type = "image"
                image_metadata = img_data["metadata_context"]
                extraction_meta = {"method": "image_ocr"}
                log.info(f"[Orchestrator] 📸 Image processed. OCR Text: '{query[:60]}...'")
            except Exception as e:
                log.error(f"[Orchestrator] Image decode/process failed: {e}")

        # Step 1: Detect input type if not image
        if input_type == "auto" and not image_base64:
            if is_youtube_url(input_text):
                input_type = "youtube"
            elif content_extractor.is_url(input_text):
                input_type = "url"
            else:
                input_type = "text"

        # Step 1.5: Extract content for URLs/YouTube
        if input_type == "url":
            # Check SSRF before scraping
            from app.services.safe_browsing_service import is_ssrf_safe_url
            is_safe, error_reason = is_ssrf_safe_url(input_text)
            if not is_safe:
                log.warning(f"[Orchestrator] SSRF Security Block: {input_text}")
                return self._empty_result(f"Security Block: The submitted URL target is prohibited ({error_reason}).")

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

        # Append user query if provided to guide the agent
        if user_query:
            query = f"{query}\n\nUSER SPECIFIC CONTEXT/QUESTION: {user_query}"

        log.info(f"[Orchestrator] Search query: '{query[:100]}'")

        # -----------------------------------------------------------------
        # TIER 0: Local Text-Similarity Dictionary Matcher (Phase 5)
        # -----------------------------------------------------------------
        from app.services.dictionary_matcher import dictionary_matcher
        tier0_hit = dictionary_matcher.lookup_viral_claim(query)
        if tier0_hit:
            compute_time = int((time.time() - start_time) * 1000)
            try:
                import json
                parsed_hit = json.loads(tier0_hit)
                parsed_hit["compute_time_ms"] = compute_time
                parsed_hit["answer"] = f"⚡ Instant Tier 0 Match: {parsed_hit.get('answer', '')}"
                return parsed_hit
            except Exception as e:
                log.warning(f"[Orchestrator] Failed to parse Tier 0 cached JSON: {e}")

        # -----------------------------------------------------------------
        # FAST-PASS: Semantic Cache Lookup
        # -----------------------------------------------------------------
        from app.services.cache_service import semantic_cache
        cached_match = semantic_cache.lookup(query, similarity_threshold=0.85)
        if cached_match:
            compute_time = int((time.time() - start_time) * 1000)
            log.info("[Orchestrator] ⚡ Instant Semantic Cache Hit!")
            return {
                "answer": f"⚡ Instant Semantic Cache Match: {cached_match['matched_claim'][:100]}",
                "context_summary": "This claim was previously analyzed and resolved locally.",
                "agent_deep_dive": cached_match['verdict'],
                "agreements": ["Local FAISS Cache"],
                "conflicts": [],
                "sources_cited": [],
                "confidence": cached_match['score'] * 100,
                "scores": {"confidence": cached_match['score'] * 100, "bias": 0.0, "conflict": 0.0, "sensitivity": 0.0, "ai_risk": 0.0, "recency": 0.0,
                    "confidence_label": "CACHED"},
                "compute_time_ms": compute_time, "status": "completed",
                "metadata": {"input_type": input_type, "extraction": extraction_meta,
                    "cache_hit": True, "sources_retrieved": 0},
            }

        # Step 2: Fact Check (pre-flight)
        fact_check_result = await check_claim(query)
        fact_verdict = get_verdict_from_claims(fact_check_result.get("claims", []))

        if fact_verdict["debunked"]:
            compute_time = int((time.time() - start_time) * 1000)
            log.info(f"[Orchestrator] Claim DEBUNKED: {fact_verdict['verdict']}")
            return {
                "answer": fact_verdict["verdict"], "context_summary": "This claim has been investigated by fact-checking organizations.",
                "agreements": [], "conflicts": [], "sources_cited": fact_verdict.get("sources", []),
                "confidence": 0.0, "scores": {"confidence": 0.0, "bias": 0.0, "conflict": 0.0, "sensitivity": 0.0, "ai_risk": 0.0, "recency": 0.0,
                    "confidence_label": "DEBUNKED"},
                "compute_time_ms": compute_time, "status": "debunked",
                "metadata": {"input_type": input_type, "extraction": extraction_meta,
                    "fact_check": fact_check_result, "fact_verdict": fact_verdict, "sources_retrieved": 0},
            }

        # Step 3: Research - Tiered Search
        try:
            # Attempt to pass max_sources
            search_result = await tiered_search(query, max_sources=max_sources)
        except TypeError as e:
            if "max_sources" in str(e):
                log.warning("[Orchestrator] tiered_search does not accept max_sources. Updating internal call.")
                # Fallback to standard call if the service hasn't been updated yet
                search_result = await tiered_search(query)
            else:
                raise e
        
        sources = search_result.get("sources", [])

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
        scores = scoring_engine.compute_score(query, sources)

        # Step 7: Build synthesis
        synthesis = self._build_synthesis(query, sources, scores, fact_verdict, extraction_meta, trusted_domains_found, search_result.get("tier_stats", {}))

        # Step 8: Phase 3 - Agent Deep Dive (optional, runs in parallel with synthesis)
        agent_report = ""
        try:
            clean_snippets = [re.sub(r'<[^>]+>', ' ', s.get('snippet', '')) for s in sources[:5]]
            evidence_context = "\n".join([f"- {s.get('title', '')}: {clean_snippets[i][:200]}" for i, s in enumerate(sources[:5])])
            
            # Phase 4: Inject Image OCR Text & Metadata Tampering Flags directly into the ReAct loop
            if image_metadata:
                image_injection = f"--- IMAGE ANALYSIS DATA ---\n{image_metadata}\n[EXTRACTED OCR TEXT]: {input_text}\n---------------------------\n\n"
                evidence_context = image_injection + evidence_context
                
            agent_report = await cawncade_agent.run_investigation(query, evidence_context)
            if agent_report and len(agent_report) > 100:
                synthesis["layer3_deep_dive"] = agent_report
                log.info(f"[Orchestrator] Agent deep-dive: {len(agent_report)} chars")
                
                # -----------------------------------------------------------------
                # CACHE LOGGING: Save the newly researched claim to FAISS
                # -----------------------------------------------------------------
                from app.services.cache_service import semantic_cache
                semantic_cache.update_cache(query, agent_report)
            else:
                log.info("[Orchestrator] LLM deep-dive returned empty. Engaging local Extractive NLP (Sumy).")
                agent_report = generate_local_nlp_summary(evidence_context, num_sentences=3)
                synthesis["layer3_deep_dive"] = agent_report
        except Exception as e:
            log.warning(f"[Orchestrator] Agent deep-dive failed: {e}. Engaging local NLP fallback.")
            agent_report = generate_local_nlp_summary(evidence_context, num_sentences=3)
            synthesis["layer3_deep_dive"] = agent_report

        compute_time = int((time.time() - start_time) * 1000)

        result = {
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
            "confidence": scores.get("confidence", 0.0), "scores": scores,
            "compute_time_ms": compute_time, "status": "completed",
            "metadata": {"input_type": input_type, "extraction": extraction_meta,
                "fact_check": fact_check_result, "fact_verdict": fact_verdict,
                "tier_stats": search_result.get("tier_stats", {}), "sources_retrieved": len(sources),
                "trusted_domains_found": list(trusted_domains_found),
                "agent_used": bool(agent_report and len(agent_report) > 100)},
        }
        
        # -----------------------------------------------------------------
        # TIER 0 COMMIT: Save the final result to the local dictionary
        # -----------------------------------------------------------------
        if result["status"] == "completed":
            import json
            from app.services.dictionary_matcher import dictionary_matcher
            dictionary_matcher.commit_viral_claim(query, json.dumps(result))
            
        return result

    async def process_image(self, image_base64: str, user_query: str = None) -> dict:
        """
        Routes the image through the standard Fact-Checking pipeline 
        by leveraging the new Phase 4 OCR Pre-Processor.
        """
        return await self.process(
            input_text="",
            input_type="image",
            user_query=user_query,
            image_base64=image_base64
        )

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
            "confidence": 0.0, "scores": {"confidence": 0.0, "bias": 0.0, "conflict": 0.0, "sensitivity": 0.0, "ai_risk": 0.0, "recency": 0.0,
                "confidence_label": "INSUFFICIENT"},
            "compute_time_ms": compute_time, "status": "no_sources",
            "metadata": {"extraction": extraction or {}, "fact_check": fact_check or {"claims": [], "total": 0},
                "fact_verdict": fact_verdict or {"debunked": False, "verdict": "N/A", "sources": []},
                "tier_stats": search_result.get("tier_stats", {}) if search_result else {}, "sources_retrieved": 0},
        }


orchestrator = Orchestrator()
