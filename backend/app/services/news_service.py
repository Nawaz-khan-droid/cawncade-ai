"""
CAWNCADE AI v3.0 — News Service (Phase 4 Production).
Tiered multi-source search with Webshare proxy, circuit breaker, and caching.

Search Priority (Intelligence Ladder):
  Tier 1: Google Custom Search -> Trusted 50-Site Walled Garden (precision)
  Tier 2: Tavily -> AI-enhanced search with include_domains (quality)
  Tier 3: NewsData.io / NewsAPI.org (breadth)
  Tier 4: DuckDuckGo via LangChain wrapper (unlimited fallback)
  Tier 5: Google News RSS + GDELT (free, always available)
"""

import asyncio
import httpx
import feedparser
import urllib.parse
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

def _get_proxy_headers() -> dict:
    """Realistic browser User-Agent for all outbound requests."""
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        )
    }

def _get_httpx_client(timeout: float = 20.0) -> httpx.AsyncClient:
    """Create httpx client with optional Webshare proxy and browser headers."""
    kwargs = {"timeout": timeout, "follow_redirects": True, "headers": _get_proxy_headers()}
    if settings.WEBSHARE_PROXY_URL:
        kwargs["proxy"] = settings.WEBSHARE_PROXY_URL
    return httpx.AsyncClient(**kwargs)

# ═══════════════════════════════════════════════════════════════
# TIER 1: Google Custom Search — The Walled Garden
# ═══════════════════════════════════════════════════════════════
async def search_google_custom(query: str, trusted_only: bool = False) -> list:
    if not settings.GOOGLE_API_KEY or not settings.GOOGLE_CSE_ID:
        return []

    cache_key = f"gcs:{query}:trusted={trusted_only}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    url = "https://www.googleapis.com/customsearch/v1"
    search_query = query

    if trusted_only:
        site_filter = get_google_site_filter(max_domains=50)
        search_query = f"({site_filter}) {query}"

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
    if result is None:
        return []

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
# TIER 2: Tavily — AI-enhanced search
# ═══════════════════════════════════════════════════════════════
async def search_tavily(query: str, trusted_only: bool = False) -> list:
    if not settings.TAVILY_API_KEY:
        return []

    cache_key = f"tavily:{query}:trusted={trusted_only}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        from tavily import TavilyClient
        tavily = TavilyClient(api_key=settings.TAVILY_API_KEY)

        kwargs = {
            "query": query,
            "max_results": settings.MAX_SOURCES_PER_QUERY,
            "search_depth": "basic",
        }
        if trusted_only:
            kwargs["include_domains"] = ALL_TRUSTED_DOMAINS

        async def _call():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: tavily.search(**kwargs))

        result = await circuit_tavily.call(_call)
        if result is None:
            return []

        articles = []
        for r in result.get("results", [])[:settings.MAX_SOURCES_PER_QUERY]:
            articles.append({
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "snippet": r.get("content", r.get("snippet", ""))[:500],
                "source_name": r.get("source", ""),
                "published_at": None,
                "channel": "tavily",
                "retrieval_tier": "tier_2",
                "score": r.get("score", 0),
            })

        cache.set(cache_key, articles, ttl=settings.SEARCH_CACHE_TTL)
        return articles
    except Exception as e:
        log.error(f"[Tier 2 - Tavily] Error: {e}")
        return []

# ═══════════════════════════════════════════════════════════════
# TIER 3: NewsData.io
# ═══════════════════════════════════════════════════════════════
async def search_newsdata(query: str) -> list:
    if not settings.NEWSDATA_API_KEY:
        return []

    cache_key = f"newsdata:{query}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    url = "https://newsdata.io/api/1/news"
    params = {"apikey": settings.NEWSDATA_API_KEY, "q": query, "language": "en", "size": settings.MAX_SOURCES_PER_QUERY}

    async def _call():
        async with _get_httpx_client(15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    result = await circuit_newsdata.call(_call)
    if result is None:
        return []

    articles = []
    for article in result.get("results", [])[:settings.MAX_SOURCES_PER_QUERY]:
        articles.append({
            "url": article.get("link", ""),
            "title": article.get("title", ""),
            "snippet": article.get("description", "")[:300],
            "source_name": article.get("source_id", "NewsData"),
            "published_at": None,
            "channel": "newsdata",
            "retrieval_tier": "tier_3",
        })
    cache.set(cache_key, articles, ttl=settings.SEARCH_CACHE_TTL)
    return articles

# ═══════════════════════════════════════════════════════════════
# TIER 3b: NewsAPI.org
# ═══════════════════════════════════════════════════════════════
async def search_newsapi(query: str) -> list:
    if not settings.NEWS_API_KEY:
        return []
    url = "https://newsapi.org/v2/everything"
    params = {"q": query, "apiKey": settings.NEWS_API_KEY, "language": "en", "pageSize": settings.MAX_SOURCES_PER_QUERY}
    async def _call():
        async with _get_httpx_client(15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    result = await circuit_newsapi.call(_call)
    if not result: return []
    return [{"url": a["url"], "title": a["title"], "snippet": a["description"], "source_name": a["source"]["name"], "channel": "newsapi", "retrieval_tier": "tier_3"} for a in result.get("articles", [])]

# ═══════════════════════════════════════════════════════════════
# TIER 4: DuckDuckGo
# ═══════════════════════════════════════════════════════════════
async def search_duckduckgo(query: str) -> list:
    try:
        from duckduckgo_search import AsyncDDGS
        async with AsyncDDGS() as ddgs:
            results = [r async for r in ddgs.text(query, max_results=settings.MAX_SOURCES_PER_QUERY)]
            return [{"url": r["href"], "title": r["title"], "snippet": r["body"], "source_name": "DuckDuckGo", "channel": "duckduckgo", "retrieval_tier": "tier_4"} for r in results]
    except Exception:
        return []

# ═══════════════════════════════════════════════════════════════
# TIER 5: Google News RSS
# ═══════════════════════════════════════════════════════════════
async def search_google_news_rss(query: str) -> list:
    encoded = urllib.parse.quote_plus(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
    async with _get_httpx_client(10.0) as client:
        resp = await client.get(url)
        feed = feedparser.parse(resp.text)
        return [{"url": e.link, "title": e.title, "snippet": e.summary, "source_name": "Google News", "channel": "google_news_rss", "retrieval_tier": "tier_5"} for e in feed.entries[:settings.MAX_SOURCES_PER_QUERY]]

# ═══════════════════════════════════════════════════════════════
# TIER 5b: GDELT
# ═══════════════════════════════════════════════════════════════
async def search_gdelt(query: str):
    """
    Search GDELT Project's Context API with strict JSON safety.
    """
    # 1. Prepare the URL and Proxy
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.gdeltproject.org/api/v2/context/context?query={encoded_query}&mode=artlist&format=json"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # GDELT can be picky; using standard headers is safer
            headers = {"User-Agent": "Mozilla/5.0"} 
            response = await client.get(url, headers=headers)
            
            # 2. Check for empty content BEFORE parsing JSON
            if not response.text or not response.text.strip():
                log.warning("[GDELT] Received empty response body")
                return []

            # 3. Handle HTTP errors before JSON parsing
            if response.status_code != 200:
                log.error(f"[GDELT] HTTP {response.status_code} error")
                return []

            # 4. Final safety check for JSON formatting
            try:
                data = response.json()
                # GDELT results are usually in an 'articles' list
                return data.get("articles", [])
            except ValueError:
                log.error(f"[GDELT] Invalid JSON received: {response.text[:100]}")
                return []

    except Exception as e:
        log.error(f"[GDELT] Search failed: {e}")
        return []

# ═══════════════════════════════════════════════════════════════
# MAIN ORCHESTRATION — FIX APPLIED HERE
# ═══════════════════════════════════════════════════════════════
async def tiered_search(query: str, max_sources: int = 10, **kwargs) -> dict:
    """
    Execute all search tiers in parallel. 
    Accepts max_sources and **kwargs to satisfy the Orchestrator's handshake.
    """
    log.info(f"[Search] Executing tiered search: '{query[:60]}' (limit: {max_sources})")

    tasks = [
        search_google_custom(query, trusted_only=True),
        search_tavily(query, trusted_only=False),
        search_newsdata(query),
        search_newsapi(query),
        search_duckduckgo(query),
        search_google_news_rss(query),
        search_gdelt(query),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_sources = []
    tier_stats = {}
    
    tier_names = ["tier_1_google", "tier_2_tavily", "tier_3_newsdata", "tier_3_newsapi", "tier_4_ddg", "tier_5_rss", "tier_5_gdelt"]

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
        domain = src.get("url", "").split("//")[-1].split("/")[0].replace("www.", "")
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
    gcs_results = await search_google_custom(query, trusted_only=True)
    if gcs_results: return gcs_results[:max_results]
    tavily_results = await search_tavily(query, trusted_only=True)
    return tavily_results[:max_results] if tavily_results else []