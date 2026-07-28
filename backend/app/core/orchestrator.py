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

def extract_local_entities(text: str) -> dict:
    """Extracts People, Organizations, Locations, & Dates locally via NLTK/regex."""
    entities = {"people": [], "organizations": [], "locations": [], "dates": []}
    try:
        import nltk
        words = nltk.word_tokenize(text[:2000])
        pos_tags = nltk.pos_tag(words)
        chunks = nltk.ne_chunk(pos_tags)
        
        for chunk in chunks:
            if hasattr(chunk, 'label'):
                name = " ".join(c[0] for c in chunk)
                label = chunk.label()
                if label in ("PERSON",) and name not in entities["people"]:
                    entities["people"].append(name)
                elif label in ("ORGANIZATION", "ORGANISATION") and name not in entities["organizations"]:
                    entities["organizations"].append(name)
                elif label in ("GPE", "LOCATION") and name not in entities["locations"]:
                    entities["locations"].append(name)
    except Exception:
        date_matches = re.findall(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b", text, re.I)
        entities["dates"] = list(set(date_matches[:5]))
    return entities


def generate_local_nlp_summary(scraped_evidence_text: str, num_sentences: int = 3) -> str:
    """Generates an objective summary + entity breakdown of web evidence locally on CPU via NLP."""
    if not scraped_evidence_text.strip() or len(scraped_evidence_text) < 50:
        return "Insufficient live web data retrieved to synthesize an empirical summary."
        
    try:
        parser = PlaintextParser.from_string(scraped_evidence_text, Tokenizer("english"))
        summarizer = LexRankSummarizer()
        summary_sentences = summarizer(parser.document, num_sentences)
        compiled_summary = " ".join([str(sentence) for sentence in summary_sentences])
        
        entities = extract_local_entities(scraped_evidence_text)
        people_str = ", ".join(entities["people"][:5]) or "None detected"
        orgs_str = ", ".join(entities["organizations"][:5]) or "None detected"
        locs_str = ", ".join(entities["locations"][:5]) or "None detected"

        return (
            f"### 📊 Local Computational Evidence Analysis (Tier 4 Offline Mode)\n"
            f"*Note: AI LLM reasoning was unavailable; showing local extractive NLP synthesis (LexRank).* \n\n"
            f"**Extracted Key Sentences:**\n{compiled_summary}\n\n"
            f"**Detected Entities:**\n"
            f"- 👤 **Key People**: {people_str}\n"
            f"- 🏢 **Organizations**: {orgs_str}\n"
            f"- 📍 **Locations**: {locs_str}"
        )
    except Exception as e:
        return f"Local statistical synthesis bypassed due to structural anomaly: {str(e)}"



class Orchestrator:
    """Main pipeline orchestrator. Evidence over Speed: Reports conflicts rather than picking winners."""

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

        # Step 0: Image Pre-Processing & Vision Model Forensics (Phase 4)
        if image_base64:
            import base64
            from app.services.image_service import extract_image_evidence
            from app.services.vision_service import analyze_image
            try:
                # Handle data URI scheme if present
                base64_data = image_base64.split(",")[1] if "," in image_base64 else image_base64
                img_bytes = base64.b64decode(base64_data)
                img_data = extract_image_evidence(img_bytes)

                # Execute Vision Model (HF SigLIP2 / ViT) for deepfake detection
                vision_res = await analyze_image(image_base64)
                
                ocr_text = img_data.get("ocr_text", "")
                query = ocr_text if ocr_text.strip() else (user_query or "Image Forensic Analysis")
                input_text = query
                input_type = "image"
                image_metadata = f"{img_data['metadata_context']}\n[DEEPFAKE ANALYSIS]: {vision_res.get('label', 'UNKNOWN')} (Confidence: {vision_res.get('confidence', 0.0)*100:.1f}%)"
                extraction_meta = {"method": "image_ocr_and_vision", "vision_analysis": vision_res, "ocr_text": ocr_text}
                log.info(f"[Orchestrator] 📸 Image processed. Vision: {vision_res.get('label')}, OCR Text: '{query[:60]}...'")
            except Exception as e:
                log.error(f"[Orchestrator] Image decode/process failed: {e}")

        # Step 1: Detect input type if not image (Auto-override frontend input_type if URL)
        if not image_base64:
            if is_youtube_url(input_text):
                input_type = "youtube"
            elif content_extractor.is_url(input_text):
                input_type = "url"
            elif input_type == "auto":
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
                "status": "SUCCESS" if yt_result.get("transcript") else "TRANSCRIPT_UNAVAILABLE",
            }
            if yt_result.get("success"):
                if yt_result.get("transcript"):
                    query = f"{yt_result.get('title', '')} {yt_result['transcript'][:2000]}".strip()
                    extraction_meta["transcript_used"] = True
                elif yt_result.get("description"):
                    query = f"{yt_result.get('title', '')} {yt_result['description'][:1000]}".strip()
                    extraction_meta["description_fallback"] = True
                else:
                    query = yt_result.get("title", "YouTube Video Claim Analysis")
                log.info(f"[Orchestrator] YouTube Dual-Stream: API={yt_result.get('api_stream')}, Scraper={yt_result.get('scraper_stream')}, Title='{yt_result.get('title', 'N/A')[:60]}'")
            else:
                topic = content_extractor.extract_keywords_from_url(input_text)
                query = topic if topic else "YouTube Video Claim Analysis"
                extraction_meta["error"] = yt_result.get("error", "Transcript extraction failed")

        # Ensure query is not a raw URL string before search
        if content_extractor.is_url(query.strip()):
            cleaned_topic = content_extractor.extract_keywords_from_url(query)
            query = cleaned_topic if cleaned_topic else query.replace("https://", "").replace("http://", "").replace("www.", "")

        if not query.strip():
            return self._empty_result("Could not extract meaningful content from input.")

        # Query Expansion Engine v2.0: Convert raw input/transcripts into 3-4 parallel expanded queries
        from app.services.tier4.claim_parser import claim_parser
        expanded_queries = claim_parser.generate_expanded_queries(query)

        # Append user query if provided to guide the agent
        if user_query:
            query = f"{query}\n\nUSER SPECIFIC CONTEXT/QUESTION: {user_query}"

        log.info(f"[Orchestrator] Multi-Query Expansion ({len(expanded_queries)} variations): {expanded_queries}")

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
                parsed_hit["answer"] = f"[TIER 0 MATCH]: {parsed_hit.get('answer', '')}"
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
            log.info("[Orchestrator] [CACHE HIT] Instant Semantic Cache Hit!")
            return {
                "answer": f"[CACHE MATCH]: {cached_match['matched_claim'][:100]}",
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

        # Step 3: Research - Tiered Search with Parallel Multi-Query Expansion
        try:
            search_result = await tiered_search(expanded_queries, max_sources=max_sources)
        except TypeError as e:
            if "max_sources" in str(e):
                search_result = await tiered_search(expanded_queries)
            else:
                raise e
        
        sources = search_result.get("sources", [])

        # Check for Infrastructure Retrieval Failure
        if not sources:
            compute_time = int((time.time() - start_time) * 1000)
            return {
                "answer": "INFRASTRUCTURE RETRIEVAL FAILURE: Unable to retrieve live web data across search tiers.",
                "context_summary": "All search connectors were unreachable or returned 0 results. This reflects a network or search provider outage, not an evidence verdict.",
                "agreements": [], "conflicts": [], "sources_cited": [],
                "confidence": 0.0,
                "scores": {"confidence": 0.0, "bias": 0.0, "conflict": 0.0, "sensitivity": 0.0, "ai_risk": 0.0, "recency": 0.0, "confidence_label": "INFRASTRUCTURE_FAILURE"},
                "compute_time_ms": compute_time, "status": "infrastructure_failure",
                "metadata": {"input_type": input_type, "extraction": extraction_meta, "sources_retrieved": 0}
            }

        # Step 4: Score sources & Direct Domain Trust Evaluation
        trusted_domains_found = set()
        trusted_keywords = ["britannica", "bbc", "reuters", "wikipedia", "nasa", "ap news", "associated press", "politifact", "snopes", "the hindu", "indian express", "ndtv", "hindustan times", "nytimes", "washington post"]
        for src in sources:
            domain = src.get("domain", "")
            source_name = src.get("source_name", "").lower()
            title_lower = src.get("title", "").lower()
            trust = get_trust_info(domain)
            
            is_publisher_trusted = any(kw in source_name or kw in title_lower for kw in trusted_keywords)
            is_trusted = trust["tier"] in (1, 2, 3, 4) or domain.endswith(".gov") or domain.endswith(".edu") or domain.endswith(".org") or is_publisher_trusted

            src["trust_tier"] = trust["label"] if trust["tier"] != 0 else ("trusted_publisher" if is_publisher_trusted else "unknown")
            src["trust_multiplier"] = max(trust["multiplier"], 0.85) if is_publisher_trusted else trust["multiplier"]
            src["credibility_score"] = src["trust_multiplier"]
            src["is_trusted_domain"] = is_trusted
            src["recency_score"] = compute_recency(src.get("published_at"))
            if is_trusted:
                trusted_domain_name = domain if domain and domain != "news.google.com" else (source_name.title() if source_name else "Trusted Publisher")
                trusted_domains_found.add(trusted_domain_name)

        # Step 5: Compute aggregate scores
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
                
                # Save researched claim to FAISS semantic cache
                from app.services.cache_service import semantic_cache
                semantic_cache.update_cache(query, agent_report)
            else:
                log.info("[Orchestrator] LLM deep-dive returned empty. Engaging offline_nlp_service.")
                from app.services.offline_nlp_service import offline_nlp_service
                agent_report = offline_nlp_service.generate_report(query, evidence_context, sources_count=len(sources))
                synthesis["layer3_deep_dive"] = agent_report
        except Exception as e:
            log.warning(f"[Orchestrator] Agent deep-dive failed: {e}. Engaging offline_nlp_service fallback.")
            from app.services.offline_nlp_service import offline_nlp_service
            agent_report = offline_nlp_service.generate_report(query, evidence_context, sources_count=len(sources))
            synthesis["layer3_deep_dive"] = agent_report

        compute_time = int((time.time() - start_time) * 1000)

        # Step 9: v3.5 Explainability, Dated Timeline & Smart Cost-Routing Integration
        from app.services.tier4.verification_service import tier4_verification_service
        from app.services.agent_service import smart_claim_router
        from app.core.resilience import get_all_circuit_breaker_telemetry

        explainable_data = tier4_verification_service.analyze_explainable_verification(query, sources)
        
        smart_route = smart_claim_router.evaluate_route(
            claim=query,
            entity_confidence=explainable_data["explainability"]["entity_alignment"]["score"],
            tier1_sources=explainable_data["explainability"]["source_quality"]["tier1_sources"],
            contradiction_count=explainable_data["explainability"]["conflict_breakdown"]["contradiction"],
            total_sources=len(sources)
        )

        circuit_telemetry = get_all_circuit_breaker_telemetry()

        # ── Telemetry Metadata Collection ──
        system_meta = {
            "model_used": getattr(cawncade_agent, "active_model", "local_lexrank_nlp"),
            "llm_tier": getattr(cawncade_agent, "llm_tier", "tier_4_local_nlp"),
            "fallback_used": getattr(cawncade_agent, "fallback_used", False),
            "latency_ms": compute_time,
            "smart_route": smart_route,
            "circuit_telemetry": circuit_telemetry
        }

        result = {
            "verdict": synthesis.get("verdict_code", explainable_data["verdict"]),
            "answer": synthesis.get("layer1_claim", ""),
            "context_summary": synthesis.get("layer2_verification", ""),
            "agent_deep_dive": synthesis.get("layer3_deep_dive", ""),
            "explainability": explainable_data["explainability"],
            "timeline": explainable_data["timeline"],
            "conflict_breakdown": explainable_data["explainability"]["conflict_breakdown"],
            "agreements": synthesis.get("agreements", []),
            "conflicts": synthesis.get("conflicts", []),
            "sources_cited": [
                {"url": s.get("url", ""), "title": s.get("title", ""), "snippet": s.get("snippet", "")[:200],
                 "source_name": s.get("source_name", ""), "channel": s.get("channel", ""),
                 "trust_tier": s.get("trust_tier", "unknown"), "is_trusted": s.get("is_trusted_domain", False),
                 "retrieval_tier": s.get("retrieval_tier", "")}
                for s in sources[:10]
            ],
            "confidence": scores.get("confidence", explainable_data["confidence_score"]), "scores": scores,
            "compute_time_ms": compute_time, "status": "completed",
            "system_metadata": system_meta,
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
        import re
        title = extraction_meta.get("title", query[:100])
        layer1 = f"Analysis of: {title}"

        # Extract core subject entity from query (e.g. "Modi" from "Modi Resigned")
        stop_words = {"the", "from", "post", "that", "this", "been", "was", "has", "have", "with", "for", "and", "about", "news", "today"}
        query_words = [w for w in re.findall(r'\b[A-Za-z]{3,}\b', query) if w.lower() not in stop_words]
        main_subject = query_words[0] if query_words else ""

        # Check if subject entity actually appears in retrieved evidence
        subject_matched_sources = []
        for s in sources:
            text = (s.get("title", "") + " " + s.get("snippet", "") + " " + s.get("source_name", "")).lower()
            if not main_subject or main_subject.lower() in text:
                subject_matched_sources.append(s)

        trusted_subject_sources = [s for s in subject_matched_sources if s.get("is_trusted_domain")]
        trusted_count = len(trusted_subject_sources)

        if fact_verdict.get("verdict") and "No prior" not in fact_verdict.get("verdict", ""):
            verdict_code = "FALSE_DEBUNKED" if fact_verdict.get("debunked") else "VERIFIED_TRUE"
            layer2 = fact_verdict["verdict"]
        elif trusted_count >= 1:
            verdict_code = "VERIFIED_TRUE"
            src_names = list(dict.fromkeys([s.get('source_name', s.get('domain', 'Reference Site')) for s in trusted_subject_sources]))
            layer2 = f"Claim corroborated across trusted sources reporting on {main_subject or 'this topic'} ({', '.join(src_names[:3])})."
        elif len(subject_matched_sources) > 0:
            verdict_code = "UNVERIFIED"
            layer2 = f"Mentioned in web sources, but lacks primary wire service or official news confirmation."
        else:
            verdict_code = "UNVERIFIED"
            layer2 = f"No corroborating evidence found for this specific claim. Retrieved web data discusses unrelated news and does not report that '{query}' occurred."

        return {
            "verdict_code": verdict_code,
            "layer1_claim": layer1, 
            "layer2_verification": layer2, 
            "layer3_deep_dive": "",
            "agreements": [s.get("source_name", "") for s in trusted_subject_sources][:5],
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
