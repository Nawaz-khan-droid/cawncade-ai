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
import os
from datetime import datetime, timezone
from app.config.settings import get_settings
from app.core.cache import cache
from app.core.resilience import (
    circuit_google_search, circuit_tavily, circuit_newsapi,
    circuit_newsdata, circuit_gdelt, circuit_google_news,
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

# ═══════════════════════════════════════════════════════════════
# TIER 2: DuckDuckGo (Promoted)
# ═══════════════════════════════════════════════════════════════
async def search_duckduckgo(query: str) -> list:
    """Tier 2: Fast, unlimited fallback."""
    try:
        from duckduckgo_search import DDGS
        # Wrapper updated for v6+
        results = []
        with DDGS() as ddgs:
            raw_results = ddgs.text(query[:300], max_results=5)
            # ddgs.text returns a generator
            for r in raw_results:
                results.append(r)
                
        return [{
            "url": r["href"], 
            "title": r["title"], 
            "snippet": r["body"], 
            "source_name": "DuckDuckGo", 
            "channel": "duckduckgo", 
            "retrieval_tier": "tier_2"
        } for r in results]
    except Exception as e:
        log.error(f"[Search] DDG Failed: {e}")
        return []

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

async def search_newsapi(query: str) -> list:
    if not settings.NEWS_API_KEY: return []
    safe_query = query[:300]
    
    async def _call():
        async with _get_httpx_client(15.0) as client:
            params = {"q": safe_query, "apiKey": settings.NEWS_API_KEY, "language": "en"}
            resp = await client.get("https://newsapi.org/v2/everything", params=params)
            resp.raise_for_status()
            data = resp.json().get("articles", [])
            return [{
                "url": a["url"], 
                "title": a["title"], 
                "snippet": a["description"], 
                "source_name": a["source"]["name"], 
                "channel": "newsapi", 
                "retrieval_tier": "tier_3"
            } for a in data]
    return await circuit_newsapi.call(_call) or []

# ═══════════════════════════════════════════════════════════════
# TIER 4: Tavily AI Search (Demoted to preserve quota)
# ═══════════════════════════════════════════════════════════════
async def search_tavily(query: str, trusted_only: bool = False):
    if not settings.TAVILY_API_KEY:
        return []
    
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
# TIER 5: Google News RSS & GDELT
# ═══════════════════════════════════════════════════════════════
async def search_google_news_rss(query: str) -> list:
    """Tier 5: Google News RSS — now wrapped in circuit_google_news (BUG-02 fixed)."""
    encoded = urllib.parse.quote_plus(query[:300])
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"

    async def _call():
        async with _get_httpx_client(10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            return [{
                "url": e.link, "title": e.title, "snippet": e.summary,
                "source_name": "Google News", "channel": "google_news_rss",
                "retrieval_tier": "tier_5"
            } for e in feed.entries[:5]]

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
    return await circuit_tavily.call(_call) or []

# ═══════════════════════════════════════════════════════════════
# RESCUE PLAN ORCHESTRATION 
# ═══════════════════════════════════════════════════════════════
async def tiered_search(query: str, max_sources: int = 10, **kwargs) -> dict:
    log.info(f"[Search] Executing Rescue Plan search: '{query[:60]}'")

    # THE NEW LADDER: Most reliable APIs first.
    tasks = [
        search_serper(query),                           # Tier 1 (New, highly reliable)
        search_tavily(query, trusted_only=False),       # Tier 2 (Proven to work)
        search_you_com(query),                          # Tier 2 (New, highly reliable)
        search_newsdata(query),                         # Tier 3 (Proven to work)
        search_google_news_rss(query),                  # Tier 4 (Free, reliable)
        search_google_custom(query, trusted_only=True), # Tier 5 (IP bans likely)
        search_duckduckgo(query),                       # Tier 5 (Last resort, won't crash if 0)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_sources = []
    tier_stats = {}
    
    tier_names = ["serper", "tavily", "you_com", "newsdata", "rss", "google", "duckduckgo"]

    for i, result in enumerate(results):
        name = tier_names[i]
        if isinstance(result, Exception):
            tier_stats[name] = f"error: {str(result)[:50]}"
            continue
        if isinstance(result, list):
            tier_stats[name] = f"{len(result)} articles"
            all_sources.extend(result)

    # Deduplicate by domain
    seen_domains = set()
    deduped = []
    for src in all_sources:
        url = src.get("url", "")
        if not url: continue
        domain = url.split("//")[-1].split("/")[0].replace("www.", "")
        if domain not in seen_domains:
            seen_domains.add(domain)
            src["domain"] = domain
            deduped.append(src)

    return {
        "sources": deduped[:max_sources],
        "tier_stats": tier_stats,
        "total_found": len(all_sources)
    }

async def verify_against_trusted(query: str, max_results: int = 5) -> list:
    # Use serper proxy to bypass IP bans
    serper_results = await search_serper(query)
    if serper_results: return serper_results[:max_results]
    tavily_results = await search_tavily(query, trusted_only=True)
    return tavily_results[:max_results] if tavily_results else []