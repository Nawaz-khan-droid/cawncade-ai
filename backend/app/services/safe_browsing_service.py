"""
Google Safe Browsing API Service.
Checks URLs against Google's malware/phishing blacklist.
Uses the same GOOGLE_API_KEY as Custom Search and Fact Check.
"""

import asyncio
import httpx
from app.config.settings import get_settings
from app.core.cache import cache
from app.core.resilience import circuit_safe_browsing
from app.utils.logger import log

settings = get_settings()


async def check_url(url: str) -> dict:
    if not settings.GOOGLE_API_KEY:
        return {"safe": True, "threats": [], "cached": False, "note": "Safe Browsing not configured"}

    cache_key = f"safebrowse:{url}"
    cached = cache.get(cache_key)
    if cached is not None:
        return {**cached, "cached": True}

    endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={settings.GOOGLE_API_KEY}"
    payload = {
        "client": {"clientId": "cawncade-ai", "clientVersion": "3.0.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }

    async def _call():
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(endpoint, json=payload)
            resp.raise_for_status()
            return resp.json()

    result = await circuit_safe_browsing.call(_call)
    if result is None:
        return {"safe": True, "threats": [], "cached": False, "note": "Safe Browsing check failed"}

    matches = result.get("matches", [])
    output = {"safe": len(matches) == 0, "threats": [m.get("threatType", "Unknown") for m in matches], "cached": False}

    cache.set(cache_key, output, ttl=settings.SAFE_BROWSE_CACHE_TTL)

    if not output["safe"]:
        log.warning(f"[SafeBrowsing] THREAT detected: {url} -> {output['threats']}")

    return output


async def check_urls_batch(urls: list) -> dict:
    results = {}
    tasks = [check_url(url) for url in urls]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    for url, resp in zip(urls, responses):
        if isinstance(resp, Exception):
            results[url] = {"safe": True, "threats": [], "error": str(resp)}
        else:
            results[url] = resp
    return results
