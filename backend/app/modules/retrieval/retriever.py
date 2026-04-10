"""
Main Retriever Module.
Orchestrates multi-source retrieval: Google News RSS, GDELT, direct URL fetch.
"""
import asyncio
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
    Filters and ranks results by relevance and credibility.
    """

    async def retrieve_for_query(self, query: str, max_sources: int = None) -> list[dict]:
        """
        Main retrieval method: fetch sources for a given query.
        Returns list of source dicts sorted by relevance score.
        """
        max_sources = max_sources or settings.MAX_SOURCES_PER_QUERY

        # Phase 1: Search multiple sources in parallel
        search_tasks = [
            news_service.search_google_news_rss(query),
            news_service.search_gdelt(query),
        ]
        results = await asyncio.gather(*search_tasks, return_exceptions=True)

        all_sources = []
        for result in results:
            if isinstance(result, Exception):
                log.error(f"Search error: {result}")
                continue
            if isinstance(result, list):
                all_sources.extend(result)

        log.info(f"Raw retrieval: {len(all_sources)} sources found")

        if not all_sources:
            return []

        # Phase 2: Filter by trusted sources and deduplicate
        filtered = self._filter_and_dedup(all_sources)

        # Phase 3: Compute relevance scores using embeddings
        scored = self._score_relevance(filtered, query)

        # Phase 4: Sort by relevance, limit to max_sources
        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored[:max_sources]

    async def retrieve_from_urls(self, urls: list[str]) -> list[dict]:
        """Retrieve content from specific URLs (direct fetch mode)."""
        safe_results = await safe_retrieval.retrieve_safe(urls)

        enriched = []
        for result in safe_results:
            result["recency_score"] = compute_recency(result.get("published_at"))
            result["relevance_score"] = result.get("credibility_score", 0.5)
            enriched.append(result)

        return enriched

    def _filter_and_dedup(self, sources: list[dict]) -> list[dict]:
        """
        Filter sources by credibility threshold and deduplicate.
        Unknown sources get a moderate score (0.4) — not blocked, just lower ranked.
        """
        seen_domains = set()
        seen_hashes = set()
        filtered = []

        for src in sources:
            url = src.get("url", "")
            domain = extract_domain(url) or url

            # Dedup by domain
            if domain in seen_domains:
                continue

            # Get credibility
            is_trusted, info = safe_retrieval.is_trusted_source(domain)
            credibility = info["credibility"] if info else 0.4

            # Skip very low credibility (< 0.2) unless we have too few sources
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
        """Score each source by semantic relevance to the query using embeddings."""
        try:
            query_embedding = embedding_model.encode(query)

            for src in sources:
                title = src.get("title", "")
                snippet = src.get("snippet", "")
                combined = f"{title} {snippet}"

                if combined.strip():
                    src_embedding = embedding_model.encode(combined)
                    similarity = embedding_model.cosine_similarity(query_embedding, src_embedding)
                else:
                    similarity = 0.3

                # Relevance = weighted combination of semantic similarity + credibility
                credibility = src.get("credibility_score", 0.5)
                recency = compute_recency(src.get("published_at"))

                src["relevance_score"] = normalize_score(
                    0.5 * similarity + 0.3 * credibility + 0.2 * recency
                )
                src["recency_score"] = recency

        except Exception as e:
            log.error(f"Embedding scoring failed: {e}. Using credibility-only scoring.")
            for src in sources:
                credibility = src.get("credibility_score", 0.5)
                recency = compute_recency(src.get("published_at"))
                src["relevance_score"] = normalize_score(0.6 * credibility + 0.4 * recency)
                src["recency_score"] = recency

        return sources


# Singleton
retriever = Retriever()
