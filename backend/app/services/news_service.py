"""
CAWNCADE AI v3.1 — News Service (Phase 4 Production).
Tiered multi-source search with Webshare proxy, circuit breaker, and caching.

Search Priority (Intelligence Ladder):
  Tier 1: Google Custom Search -> Trusted 50-Site Walled Garden (precision)
  Tier 2: DuckDuckGo -> Unlimited fallback (speed/reliability)
  Tier 3: NewsData.io / NewsAPI.org (breadth)
  Tier 4: Tavily -> AI-enhanced search (preserved credits)
  Tier 5: Google News RSS + GDELT (free, always available)
"""

import asyncio
import httpx
import feedparser
import urllib.parse
from urllib.parse import urlparse  # EDGE-04 FIX: proper URL parsing
import os
from collections import defaultdict  # PERF-02 FIX: per-domain article count
from datetime import datetime, timezone
from app.config.settings import get_settings
from app.core.cache import cache
from app.core.resilience import (
    circuit_google_search, circuit_tavily, circuit_newsapi,
    circuit_newsdata, circuit_gdelt, circuit_google_news, circuit_you_com,
)
from app.core.trusted_domains import get_google_site_filter, ALL_TRUSTED_DOMAINS
from app.utils.logger import log

settings = get_settings()

def _get_browser_headers() -> dict:
    """Realistic browser User-Agent for all outbound requests."""
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        )
    }

def _get_httpx_client(timeout: float = 20.0) -> httpx.AsyncClient:
    """Create httpx client with standardized browser headers."""
    kwargs = {
        "timeout": timeout, 
        "follow_redirects": True, 
        "headers": _get_browser_headers(),
    }
    return httpx.AsyncClient(**kwargs)
# ═══════════════════════════════════════════════════════════════
# TIER 1: Google Custom Search
# ═══════════════════════════════════════════════════════════════
async def search_google_custom(query: str, trusted_only: bool = False) -> list:
    if not settings.GOOGLE_API_KEY or not settings.GOOGLE_CSE_ID:
        return []

    safe_query = query[:300]
    cache_key = f"gcs:{safe_query}:trusted={trusted_only}"
    
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    url = "https://www.googleapis.com/customsearch/v1"
    search_query = safe_query

    if trusted_only:
        site_filter = get_google_site_filter(max_domains=50)
        search_query = f"({site_filter}) {safe_query}"

    params = {
        "key": settings.GOOGLE_API_KEY,
        "cx": settings.GOOGLE_CSE_ID,
        "q": search_query,
        "num": settings.MAX_SOURCES_PER_QUERY,
    }

    async def _call():
        async with _get_httpx_client(15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    result = await circuit_google_search.call(_call)
    if not result: return []

    articles = []
    for item in result.get("items", [])[:settings.MAX_SOURCES_PER_QUERY]:
        articles.append({
            "url": item.get("link", ""),
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "source_name": item.get("displayLink", "Google Search"),
            "published_at": None,
            "channel": "google_custom",
            "retrieval_tier": "tier_1",
        })

    cache.set(cache_key, articles, ttl=settings.SEARCH_CACHE_TTL)
    return articles

def extract_search_keywords(query: str) -> str:
    """Extracts key named entities and keywords from a claim for search query formulation."""
    import re
    if len(query) < 40:
        return query
    # Remove common filler phrases
    cleaned = re.sub(r'\b(is located in|was created by|announced that|according to|claims that|has been|was|is|are|were)\b', ' ', query, flags=re.I)
    cleaned = " ".join(cleaned.split())
    return cleaned[:150] if cleaned else query[:150]

async def resolve_destination_url(url: str, client: httpx.AsyncClient = None) -> str:
    """Unwraps google news redirect URLs (news.google.com) to extract the actual publisher URL."""
    if "news.google.com" not in url:
        return url
    # BUG-03 FIX: Always close a client we created ourselves, even on exception
    _own_client = client is None
    _client = client if client is not None else _get_httpx_client(8.0)
    try:
        resp = await _client.get(url, follow_redirects=True)
        final_url = str(resp.url)
        if "news.google.com" not in final_url:
            return final_url
    except Exception:
        pass
    finally:
        if _own_client:
            await _client.aclose()
    return url

# ═══════════════════════════════════════════════════════════════
# TIER 2: DuckDuckGo (Promoted)
# ═══════════════════════════════════════════════════════════════
async def search_duckduckgo(query: str) -> list:
    """Tier 5: Fast, unlimited fallback using ddgs / duckduckgo_search."""
    clean_q = extract_search_keywords(query)

    # BUG-04 FIX: DDGS.text() is a BLOCKING synchronous call.
    # Running it directly in an async function blocks the entire event loop.
    # Use run_in_executor to offload it to a thread pool.
    def _sync_ddg_search():
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            return list(ddgs.text(clean_q, max_results=5))

    try:
        loop = asyncio.get_running_loop()
        raw_results = await loop.run_in_executor(None, _sync_ddg_search)
        return [{
            "url": r.get("href") or r.get("link", ""),
            "title": r.get("title", ""),
            "snippet": r.get("body") or r.get("snippet", ""),
            "source_name": "DuckDuckGo",
            "channel": "duckduckgo",
            "retrieval_tier": "tier_2"
        } for r in raw_results if r.get("href") or r.get("link")]
    except Exception as e:
        log.error(f"[Search] DDG Failed: {e}")
        return []

# ═══════════════════════════════════════════════════════════════
# TIER 5: Google News RSS & GDELT
# ═══════════════════════════════════════════════════════════════
import re
import html

def clean_html(text: str) -> str:
    """Strips raw HTML tags and unescapes entities from web snippets."""
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = html.unescape(clean)
    return " ".join(clean.split())

async def search_google_news_rss(query: str) -> list:
    """Tier 5: Google News RSS with async destination URL unwrapping."""
    clean_q = extract_search_keywords(query)
    encoded = urllib.parse.quote_plus(clean_q)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"

    async def _call():
        async with _get_httpx_client(10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            entries = feed.entries[:5]
            
            # Resolve redirect URLs in parallel
            tasks = [resolve_destination_url(e.link, client) for e in entries]
            resolved_urls = await asyncio.gather(*tasks, return_exceptions=True)
            
            articles = []
            for i, e in enumerate(entries):
                res_url = resolved_urls[i] if isinstance(resolved_urls[i], str) else e.link
                # Extract publisher name from title if format is "Title - Publisher"
                title = clean_html(e.title)
                publisher = "Google News"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0]
                    publisher = parts[1]
                pub_lower = publisher.lower().strip()
                publisher_domain_map = {
                    "britannica": "britannica.com",
                    "encyclopedia britannica": "britannica.com",
                    "wikipedia": "wikipedia.org",
                    "reuters": "reuters.com",
                    "ap news": "apnews.com",
                    "associated press": "apnews.com",
                    "bbc": "bbc.com",
                    "bbc news": "bbc.com",
                    "nasa": "nasa.gov",
                    "the hindu": "thehindu.com",
                    "indian express": "indianexpress.com",
                    "hindustan times": "hindustantimes.com",
                    "ndtv": "ndtv.com",
                    "alt news": "altnews.in",
                    "boom live": "boomlive.in",
                    "politifact": "politifact.com",
                    "snopes": "snopes.com",
                    "forbes": "forbes.com",
                }
                
                matched_domain = None
                for k, d in publisher_domain_map.items():
                    if k in pub_lower or k in title.lower():
                        matched_domain = d
                        break

                if "news.google.com" in res_url and matched_domain:
                    res_url = f"https://www.{matched_domain}"

                articles.append({
                    "url": res_url, 
                    "title": title, 
                    "snippet": clean_html(e.summary),
                    "source_name": publisher, 
                    "channel": "google_news_rss",
                    "retrieval_tier": "tier_5"
                })
            return articles

    return await circuit_google_news.call(_call) or []

# ═══════════════════════════════════════════════════════════════
# NEW TIER 1: Serper.dev (Reliable Google Search Proxy)
# ═══════════════════════════════════════════════════════════════
async def search_serper(query: str) -> list:
    if not settings.SERPER_API_KEY: return []
    safe_query = query[:300]
    
    async def _call():
        async with _get_httpx_client(15.0) as client:
            headers = {"X-API-KEY": settings.SERPER_API_KEY, "Content-Type": "application/json"}
            payload = {"q": safe_query, "num": 5}
            resp = await client.post("https://google.serper.dev/search", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return [{
                "url": r.get("link", ""),
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "source_name": r.get("source", "Serper/Google"),
                "channel": "serper",
                "retrieval_tier": "tier_1"
            } for r in data.get("organic", [])]
    return await circuit_google_search.call(_call) or []

# ═══════════════════════════════════════════════════════════════
# VISUAL LENS: Serper.dev Lens
# ═══════════════════════════════════════════════════════════════
async def search_serper_lens(image_url: str):
    if not settings.SERPER_API_KEY: return {}
    async def _call():
        async with _get_httpx_client(15.0) as client:
            headers = {"X-API-KEY": settings.SERPER_API_KEY, "Content-Type": "application/json"}
            payload = {"url": image_url}
            resp = await client.post("https://google.serper.dev/lens", headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()
    return await circuit_google_search.call(_call) or {}

# ═══════════════════════════════════════════════════════════════
# NEW TIER 2: You.com (AI-Powered Web Search)
# ═══════════════════════════════════════════════════════════════
async def search_you_com(query: str) -> list:
    if not settings.YOU_API_KEY: return []
    safe_query = query[:300]
    
    async def _call():
        async with _get_httpx_client(15.0) as client:
            headers = {"X-API-Key": settings.YOU_API_KEY}
            params = {"query": safe_query, "num_web_results": 5}
            resp = await client.get("https://api.ydc-index.io/search", headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            return [{
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "source_name": r.get("name", "You.com"),
                "channel": "you_com",
                "retrieval_tier": "tier_2"
            } for r in data.get("hits", [])]
    # REFACTOR-04 FIX: Use dedicated circuit_you_com, not circuit_tavily.
    # You.com and Tavily are independent services; shared circuit breaker would
    # cause one service's outage to trip the other's breaker incorrectly.
    return await circuit_you_com.call(_call) or []

# ═══════════════════════════════════════════════════════════════
# TIER 3: NewsData.io & NewsAPI.org
# ═══════════════════════════════════════════════════════════════
async def search_newsdata(query: str) -> list:
    if not settings.NEWSDATA_API_KEY: return []
    safe_query = query[:300]
    
    async def _call():
        async with _get_httpx_client(15.0) as client:
            params = {"apikey": settings.NEWSDATA_API_KEY, "q": safe_query, "language": "en"}
            resp = await client.get("https://newsdata.io/api/1/news", params=params)
            resp.raise_for_status()
            data = resp.json().get("results", [])
            return [{
                "url": a.get("link", ""),
                "title": a.get("title", ""),
                "snippet": a.get("description", "")[:300] if a.get("description") else "",
                "source_name": a.get("source_id", "NewsData"),
                "channel": "newsdata",
                "retrieval_tier": "tier_3"
            } for a in data]
    return await circuit_newsdata.call(_call) or []

# ═══════════════════════════════════════════════════════════════
# TIER 4: Tavily AI Search
# ═══════════════════════════════════════════════════════════════
async def search_tavily(query: str, trusted_only: bool = False):
    if not settings.TAVILY_API_KEY: return []
    safe_query = query[:300]

    async def _call():
        async with _get_httpx_client(20.0) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.TAVILY_API_KEY,
                    "query": safe_query,
                    "search_depth": "advanced",
                    "max_results": 5
                }
            )
            resp.raise_for_status()
            data = resp.json().get("results", [])
            return [{
                "url": r["url"],
                "title": r["title"],
                "snippet": r["content"],
                "source_name": "Tavily AI",
                "channel": "tavily",
                "retrieval_tier": "tier_4"
            } for r in data]

    return await circuit_tavily.call(_call) or []

# ═══════════════════════════════════════════════════════════════
# GDELT v2 Project Global News Search
# ═══════════════════════════════════════════════════════════════
async def search_gdelt(query: str, max_results: int = 5):
    """Query GDELT v2 Project API for international news articles."""
    safe_query = query[:200].replace('"', '')

    async def _call():
        async with _get_httpx_client(15.0) as client:
            resp = await client.get(
                "https://api.gdeltproject.org/api/v2/doc/doc",
                params={
                    "query": safe_query,
                    "mode": "artlist",
                    "maxrecords": max_results,
                    "format": "json",
                    "sort": "date"
                }
            )
            if resp.status_code != 200:
                return []
            data = resp.json().get("articles", [])
            return [{
                "url": a.get("url", ""),
                "title": a.get("title", ""),
                "snippet": f"Source: {a.get('domain', '')} - Published: {a.get('seendate', '')}",
                "source_name": a.get("domain", "GDELT Global News"),
                "channel": "gdelt",
                "retrieval_tier": "tier_4"
            } for a in data if a.get("url")]

    return await circuit_gdelt.call(_call) or []

# ═══════════════════════════════════════════════════════════════
# RESCUE PLAN ORCHESTRATION 
# ═══════════════════════════════════════════════════════════════
async def tiered_search(query: str | list[str], max_sources: int = 10, **kwargs) -> dict:
    if isinstance(query, list):
        queries = query
    else:
        queries = [query]

    log.info(f"[Search] Executing Adaptive Multi-Query Search across {len(queries)} query variation(s)...")

    HIGH_TRUST_DOMAINS = {
        "reuters.com", "bbc.com", "bbc.co.uk", "nasa.gov", "who.int", "cdc.gov",
        "nih.gov", "nature.com", "sciencemag.org", "snopes.com", "politifact.com",
        "factcheck.org", "apnews.com", "nytimes.com", "theguardian.com", "ndtv.com"
    }

    all_sources = []
    seen_urls = set()
    seen_domains = set()
    queries_executed = []
    early_stopped = False

    for q_idx, q in enumerate(queries, 1):
        queries_executed.append(q)
        q_tasks = [
            search_serper(q),                           # Tier 1 (Google Serper API)
            search_tavily(q, trusted_only=False),       # Tier 2 (Tavily AI Search)
            search_you_com(q),                          # Tier 2 (You.com Index API)
            search_newsdata(q),                         # Tier 3 (NewsData)
            search_gdelt(q),                            # Tier 4 (GDELT v2 Global News API)
            search_google_news_rss(q),                  # Tier 4 (Free Google News RSS)
            search_duckduckgo(q),                       # Tier 5 (DuckDuckGo Fallback)
        ]

        q_results = await asyncio.gather(*q_tasks, return_exceptions=True)
        # PERF-02 FIX: Track per-domain article count; allow up to 3 per domain
        # instead of 1, so same-domain articles with different angles are preserved.
        domain_counts: dict = defaultdict(int)
        high_trust_count = 0

        for result in q_results:
            if isinstance(result, list):
                for src in result:
                    url = src.get("url", "")
                    if not url or url in seen_urls:
                        continue
                    # EDGE-04 FIX: Use urlparse for robust domain extraction
                    parsed_url = urlparse(url)
                    domain = (parsed_url.hostname or "").replace("www.", "").lower()
                    if not domain:
                        continue
                    if domain_counts[domain] >= 3:  # max 3 articles per domain
                        continue
                    seen_urls.add(url)
                    domain_counts[domain] += 1
                    src["domain"] = domain
                    all_sources.append(src)

                    if (domain in HIGH_TRUST_DOMAINS or domain.endswith(".gov") or domain.endswith(".edu")) and len(src.get("snippet", "")) > 40:
                        high_trust_count += 1

        # Stance & Relevance-Aware Adaptive Early Stopping Check
        if high_trust_count >= 3 and len(all_sources) >= 4:
            log.info(f"[Search] 🛡️ Stance & Relevance-Aware Early-Stopping satisfied at Query {q_idx}/{len(queries)}: Found {high_trust_count} high-trust Tier-1 sources with relevant snippets. Skipping remaining queries.")
            early_stopped = True
            break

    deduped = all_sources[:max_sources]

    return {
        "sources": deduped,
        "total_found": len(all_sources),
        "queries_executed": queries_executed,
        "early_stopped": early_stopped,
    }

async def verify_against_trusted(query: str, max_results: int = 5) -> list:
    # Use serper proxy to bypass IP bans
    serper_results = await search_serper(query)
    if serper_results: return serper_results[:max_results]
    tavily_results = await search_tavily(query, trusted_only=True)
    return tavily_results[:max_results] if tavily_results else []