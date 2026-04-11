"""
CAWNCADE AI v3.0 — News Service (Phase 4 Production).
Tiered multi-source search with Webshare proxy, circuit breaker, and caching.

Search Priority (Intelligence Ladder):
  Tier 1: Google Custom Search -> Trusted 50-Site Walled Garden (precision)
  Tier 2: Tavily -> AI-enhanced search with include_domains (quality)
  Tier 3: NewsData.io / NewsAPI.org (breadth)
  Tier 4: DuckDuckGo via LangChain wrapper (unlimited fallback)
  Tier 5: Google News RSS + GDELT (free, always available)

PHASE 4 UPDATE:
  - Tier 1 CSE now uses site:domain.com syntax for ALL 50 trusted domains
  - Tier 2 Tavily uses include_domains with the full 50-domain list
  - DuckDuckGo via duckduckgo-search (AsyncDDGS) with time=None equivalent
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
# TIER 1: Google Custom Search — The Walled Garden (50 trusted sites)
# ═══════════════════════════════════════════════════════════════
async def search_google_custom(query: str, trusted_only: bool = False) -> list:
    """
    Search using Google Custom Search Engine.
    When trusted_only=True, restricts to the 50-domain list using site: syntax.
    This is the core of the 'Walled Garden' verification strategy.
    """
    if not settings.GOOGLE_API_KEY or not settings.GOOGLE_CSE_ID:
        return []

    cache_key = f"gcs:{query}:trusted={trusted_only}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    url = "https://www.googleapis.com/customsearch/v1"
    search_query = query

    if trusted_only:
        # PHASE 4: Use ALL 50 domains with site: filter for the Walled Garden
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
    log.info(f"[Tier 1 - Google CSE Walled Garden] {len(articles)} results for '{query[:50]}'")
    return articles


# ═══════════════════════════════════════════════════════════════
# TIER 2: Tavily — AI-enhanced search
# ═══════════════════════════════════════════════════════════════
async def search_tavily(query: str, trusted_only: bool = False) -> list:
    """
    Search using Tavily API.
    When trusted_only=True, restricts to the 50-domain list via include_domains.
    """
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

        # PHASE 4: Restrict to 50 trusted domains when in verification mode
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
        log.info(f"[Tier 2 - Tavily] {len(articles)} results for '{query[:50]}'")
        return articles

    except ImportError:
        log.warning("[Tier 2 - Tavily] tavily-python not installed. Skipping.")
        return []
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
    params = {
        "apikey": settings.NEWSDATA_API_KEY,
        "q": query,
        "language": "en",
        "size": settings.MAX_SOURCES_PER_QUERY,
    }

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
        published = None
        if article.get("pubDate"):
            try:
                published = datetime.fromisoformat(article["pubDate"].replace("Z", "+00:00"))
            except Exception:
                pass
        articles.append({
            "url": article.get("link", ""),
            "title": article.get("title", ""),
            "snippet": article.get("description", "")[:300],
            "source_name": article.get("source_id", "NewsData"),
            "published_at": published,
            "channel": "newsdata",
            "retrieval_tier": "tier_3",
        })

    cache.set(cache_key, articles, ttl=settings.SEARCH_CACHE_TTL)
    log.info(f"[Tier 3 - NewsData] {len(articles)} results for '{query[:50]}'")
    return articles


# ═══════════════════════════════════════════════════════════════
# TIER 3b: NewsAPI.org
# ═══════════════════════════════════════════════════════════════
async def search_newsapi(query: str) -> list:
    if not settings.NEWS_API_KEY:
        return []

    cache_key = f"newsapi:{query}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "apiKey": settings.NEWS_API_KEY,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": settings.MAX_SOURCES_PER_QUERY,
    }

    async def _call():
        async with _get_httpx_client(15.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code in (401, 429):
                return None
            resp.raise_for_status()
            return resp.json()

    result = await circuit_newsapi.call(_call)
    if result is None:
        return []

    articles = []
    for article in result.get("articles", [])[:settings.MAX_SOURCES_PER_QUERY]:
        published = None
        if article.get("publishedAt"):
            try:
                published = datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00"))
            except Exception:
                pass
        articles.append({
            "url": article.get("url", ""),
            "title": article.get("title", ""),
            "snippet": article.get("description", ""),
            "source_name": article.get("source", {}).get("name", "NewsAPI"),
            "published_at": published,
            "channel": "newsapi",
            "retrieval_tier": "tier_3",
        })

    cache.set(cache_key, articles, ttl=settings.SEARCH_CACHE_TTL)
    log.info(f"[Tier 3 - NewsAPI] {len(articles)} results for '{query[:50]}'")
    return articles


# ═══════════════════════════════════════════════════════════════
# TIER 4: DuckDuckGo (Free, Unlimited — no time restriction)
# ═══════════════════════════════════════════════════════════════
async def search_duckduckgo(query: str) -> list:
    """
    Search using DuckDuckGo via duckduckgo-search (AsyncDDGS).
    No time restriction — searches full web history.
    This is the same engine used by the LangChain DuckDuckGoSearchAPIWrapper in agent_service.py.
    """
    cache_key = f"ddg:{query}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        from duckduckgo_search import AsyncDDGS

        ddgs_kwargs = {}
        if settings.WEBSHARE_PROXY_URL:
            ddgs_kwargs["proxies"] = settings.WEBSHARE_PROXY_URL

        async def _call():
            results = []
            async with AsyncDDGS(**ddgs_kwargs) as ddgs:
                async for r in ddgs.text(query, max_results=settings.MAX_SOURCES_PER_QUERY):
                    results.append(r)
            return results

        raw_results = await _call()
        if not raw_results:
            return []

        articles = []
        for r in raw_results[:settings.MAX_SOURCES_PER_QUERY]:
            articles.append({
                "url": r.get("href", ""),
                "title": r.get("title", ""),
                "snippet": r.get("body", ""),
                "source_name": r.get("hostname", "DuckDuckGo"),
                "published_at": None,
                "channel": "duckduckgo",
                "retrieval_tier": "tier_4",
            })

        cache.set(cache_key, articles, ttl=settings.SEARCH_CACHE_TTL)
        log.info(f"[Tier 4 - DuckDuckGo] {len(articles)} results for '{query[:50]}'")
        return articles

    except ImportError:
        log.warning("[Tier 4 - DuckDuckGo] duckduckgo-search not installed. Skipping.")
        return []
    except Exception as e:
        log.error(f"[Tier 4 - DuckDuckGo] Error: {e}")
        return []


# ═══════════════════════════════════════════════════════════════
# TIER 5: Google News RSS (Free, No API key)
# ═══════════════════════════════════════════════════════════════
async def search_google_news_rss(query: str) -> list:
    cache_key = f"gnrss:{query}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    encoded = urllib.parse.quote_plus(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"

    async def _call():
        async with _get_httpx_client(settings.RSS_FEED_TIMEOUT) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return feedparser.parse(resp.text)

    feed = await circuit_google_news.call(_call)
    if feed is None:
        return []

    articles = []
    for entry in feed.entries[:settings.MAX_SOURCES_PER_QUERY]:
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        articles.append({
            "url": entry.get("link", ""),
            "title": entry.get("title", ""),
            "snippet": entry.get("summary", ""),
            "source_name": entry.get("source", {}).get("title", "Google News") if hasattr(entry, "source") else "Google News",
            "published_at": published,
            "channel": "google_news_rss",
            "retrieval_tier": "tier_5",
        })

    cache.set(cache_key, articles, ttl=settings.SEARCH_CACHE_TTL)
    log.info(f"[Tier 5 - Google News RSS] {len(articles)} results")
    return articles


# ═══════════════════════════════════════════════════════════════
# TIER 5b: GDELT (Free, No API key)
# ═══════════════════════════════════════════════════════════════
async def search_gdelt(query: str) -> list:
    cache_key = f"gdelt:{query}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    base_url = settings.GDELT_BASE_URL.rstrip("/") + "/"
    params = {
        "mode": "ArticleList",
        "maxrecords": str(settings.MAX_SOURCES_PER_QUERY),
        "format": "json",
        "query": query,
        "timespan": "7d",
    }

    async def _call():
        async with _get_httpx_client(20.0) as client:
            resp = await client.get(base_url, params=params)
            resp.raise_for_status()
            return resp.json()

    data = await circuit_gdelt.call(_call)
    if data is None:
        return []

    articles = []
    for a in data.get("articles", [])[:settings.MAX_SOURCES_PER_QUERY]:
        articles.append({
            "url": a.get("url", ""),
            "title": a.get("title", ""),
            "snippet": a.get("seendate", ""),
            "source_name": a.get("sourcecountry", "Global"),
            "published_at": None,
            "channel": "gdelt",
            "retrieval_tier": "tier_5",
        })

    cache.set(cache_key, articles, ttl=settings.SEARCH_CACHE_TTL)
    log.info(f"[Tier 5 - GDELT] {len(articles)} results")
    return articles


# ═══════════════════════════════════════════════════════════════
# MAIN ORCHESTRATION — Parallel Tier Execution
# ═══════════════════════════════════════════════════════════════
async def tiered_search(query: str, max_results: int = 10) -> dict:
    """
    Execute all search tiers in parallel, deduplicate results, and return unified output.
    Tier 1 (Google CSE) runs with trusted_only=True for the Walled Garden.
    """
    log.info(f"[Search] Starting tiered search for: '{query[:80]}'")

    tasks = [
        search_google_custom(query, trusted_only=True),   # Walled Garden
        search_tavily(query, trusted_only=False),          # Global web via Tavily
        search_newsdata(query),                            # NewsData breadth
        search_newsapi(query),                             # NewsAPI breadth
        search_duckduckgo(query),                          # DuckDuckGo unlimited
        search_google_news_rss(query),                     # Google News RSS
        search_gdelt(query),                               # GDELT global
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_sources = []
    tier_stats = {}
    tier_map = {
        0: "tier_1_google_cse_walled_garden",
        1: "tier_2_tavily_global",
        2: "tier_3_newsdata",
        3: "tier_3_newsapi",
        4: "tier_4_duckduckgo",
        5: "tier_5_google_news_rss",
        6: "tier_5_gdelt",
    }

    for i, result in enumerate(results):
        name = tier_map.get(i, f"tier_{i}")
        if isinstance(result, Exception):
            tier_stats[name] = f"error: {str(result)[:80]}"
            log.error(f"[Search] {name} failed: {result}")
            continue
        count = len(result) if isinstance(result, list) else 0
        tier_stats[name] = f"{count} articles"
        if isinstance(result, list) and count > 0:
            all_sources.extend(result)

    # Deduplicate by domain
    seen_domains = set()
    deduped = []
    for src in all_sources:
        url = src.get("url", "")
        domain = ""
        if url:
            try:
                domain = url.split("//")[-1].split("/")[0].replace("www.", "")
            except Exception:
                domain = url[:30]
        if domain and domain not in seen_domains:
            seen_domains.add(domain)
            src["domain"] = domain
            deduped.append(src)

    log.info(f"[Search] Total: {len(all_sources)} raw -> {len(deduped)} deduplicated. Tier stats: {tier_stats}")
    return {
        "sources": deduped[:max_results],
        "tier_stats": tier_stats,
        "total_raw": len(all_sources),
        "total_deduped": len(deduped),
    }


async def verify_against_trusted(query: str, max_results: int = 5) -> list:
    """
    Verify a claim against trusted sources only.
    First tries Google CSE Walled Garden, then Tavily with include_domains.
    """
    gcs_results = await search_google_custom(query, trusted_only=True)
    if gcs_results:
        return gcs_results[:max_results]
    tavily_results = await search_tavily(query, trusted_only=True)
    if tavily_results:
        return tavily_results[:max_results]
    return []
