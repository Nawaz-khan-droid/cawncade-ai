"""
Main Retriever Module.
Orchestrates multi-source retrieval: Google News RSS, GDELT, direct URL fetch.
"""
import asyncio
import httpx
from typing import Optional
from ..text.embedding_module import embedding_model
from ..extraction.extractor import content_extractor
from .safe_retrieval import safe_retrieval
from ...services.news_service import news_service
from ...config.settings import get_settings
from ...utils.logger import log
from ...utils.helpers import compute_recency, extract_domain, normalize_score

settings = get_settings()

class Retriever:
    """
    Multi-source retriever. Combines RSS, GDELT, and direct fetches.
    """

    async def retrieve_for_query(self, query: str, max_sources: int = None) -> list[dict]:
        """
        Main retrieval method: fetch sources for a given query.
        """
        max_sources = max_sources or settings.MAX_SOURCES_PER_QUERY

        # Phase 1: Search multiple sources in parallel with redirect support
        # We ensure the underlying news_service uses follow_redirects=True
        search_tasks = [
            news_service.search_google_news_rss(query),
            news_service.search_gdelt(query),
        ]
        
        try:
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
        except Exception as e:
            log.error(f"Global search task failed: {e}")
            return []

        all_sources = []
        for result in results:
            if isinstance(result, Exception):
                log.error(f"Search source error: {result}")
                continue
            if isinstance(result, list):
                all_sources.extend(result)

        log.info(f"Raw retrieval: {len(all_sources)} sources found")

        if not all_sources:
            return []

        # Phase 2: Filter and Deduplicate
        filtered = self._filter_and_dedup(all_sources)

        # Phase 3: Score Relevance (Semantic + Credibility)
        scored = self._score_relevance(filtered, query)

        # Phase 4: Sort and Limit
        scored.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return scored[:max_sources]

    def _filter_and_dedup(self, sources: list[dict]) -> list[dict]:
        seen_domains = set()
        filtered = []

        for src in sources:
            url = src.get("url", "")
            if not url: continue
            
            domain = extract_domain(url) or url

            if domain in seen_domains:
                continue

            # Get credibility
            is_trusted, info = safe_retrieval.is_trusted_source(domain)
            credibility = info["credibility"] if info else 0.4

            # Minimal quality gate
            if credibility < 0.2 and len(filtered) >= settings.MIN_SOURCES_FOR_VERIFICATION:
                continue

            seen_domains.add(domain)
            src["domain"] = domain
            src["credibility_score"] = credibility
            src["is_trusted"] = is_trusted
            src["source_name"] = info["name"] if info else src.get("source_name", domain)

            filtered.append(src)

        return filtered

    def _score_relevance(self, sources: list[dict], query: str) -> list[dict]:
        """Score each source. Defaults to basic scoring if embeddings fail."""
        try:
            query_embedding = embedding_model.encode(query)

            for src in sources:
                combined = f"{src.get('title', '')} {src.get('snippet', '')}".strip()
                
                if combined:
                    src_embedding = embedding_model.encode(combined)
                    similarity = embedding_model.cosine_similarity(query_embedding, src_embedding)
                else:
                    similarity = 0.3

                credibility = src.get("credibility_score", 0.5)
                recency = compute_recency(src.get("published_at"))

                # Final Weighting: 50% AI Logic, 30% Trust, 20% Freshness
                src["relevance_score"] = normalize_score(
                    0.5 * similarity + 0.3 * credibility + 0.2 * recency
                )
                src["recency_score"] = recency

        except Exception as e:
            log.warning(f"Embedding scoring failed ({e}). Falling back to metadata scoring.")
            for src in sources:
                credibility = src.get("credibility_score", 0.5)
                recency = compute_recency(src.get("published_at"))
                src["relevance_score"] = normalize_score(0.6 * credibility + 0.4 * recency)
                src["recency_score"] = recency

        return sources

retriever = Retriever()