"""
Google Fact Check Tools API Service.
Checks if a claim has already been debunked or verified by fact-checkers.
Uses the same GOOGLE_API_KEY as Custom Search and Safe Browsing.
"""

import httpx
from app.config.settings import get_settings
from app.core.cache import cache
from app.core.resilience import circuit_fact_check
from app.utils.logger import log

settings = get_settings()


async def check_claim(query: str) -> dict:
    if not settings.GOOGLE_API_KEY:
        return {"claims": [], "total": 0, "cached": False}

    cache_key = f"factcheck:{query}"
    cached = cache.get(cache_key)
    if cached is not None:
        return {**cached, "cached": True}

    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {
        "query": query,
        "key": settings.GOOGLE_API_KEY,
        "pageSize": 10,
        "languageCode": "en",
    }

    async def _call():
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 429:
                return None
            resp.raise_for_status()
            return resp.json()

    result = await circuit_fact_check.call(_call)
    if result is None:
        return {"claims": [], "total": 0, "cached": False}

    claims = []
    for claim in result.get("claims", []):
        reviews = []
        for review in claim.get("claimReview", []):
            reviews.append({
                "publisher": review.get("publisher", {}).get("name", "Unknown"),
                "url": review.get("url", ""),
                "textual_rating": review.get("textualRating", ""),
                "rating_date": review.get("reviewDate", ""),
            })
        claims.append({
            "text": claim.get("text", ""),
            "claimant": claim.get("claimant", ""),
            "date": claim.get("claimDate", ""),
            "reviews": reviews,
        })

    output = {"claims": claims, "total": len(claims), "cached": False}
    cache.set(cache_key, output, ttl=settings.FACT_CHECK_CACHE_TTL)
    log.info(f"[FactCheck] Found {len(claims)} existing fact-checks for '{query[:50]}'")
    return output


def get_verdict_from_claims(claims: list) -> dict:
    if not claims:
        return {"debunked": False, "verdict": "No prior fact-checks found", "sources": []}

    debunked_keywords = ["false", "misleading", "fake", "unverified", "incorrect", "not true", "distorted", "out of context"]
    verified_keywords = ["true", "correct", "accurate", "confirmed", "verified", "mostly true"]

    debunk_count = 0
    verify_count = 0
    sources = []

    for claim in claims:
        for review in claim.get("reviews", []):
            rating = review.get("textual_rating", "").lower()
            publisher = review.get("publisher", "")
            sources.append({"publisher": publisher, "rating": review.get("textual_rating", ""), "url": review.get("url", "")})

            if any(kw in rating for kw in debunked_keywords):
                debunk_count += 1
            elif any(kw in rating for kw in verified_keywords):
                verify_count += 1

    if debunk_count > verify_count:
        return {
            "debunked": True,
            "verdict": f"Claim flagged as FALSE/MISLEADING by {debunk_count} fact-checker(s)",
            "sources": sources,
        }
    elif verify_count > debunk_count:
        return {
            "debunked": False,
            "verdict": f"Claim verified as TRUE/CORRECT by {verify_count} fact-checker(s)",
            "sources": sources,
        }
    else:
        return {
            "debunked": False,
            "verdict": "Mixed or inconclusive fact-check results",
            "sources": sources,
        }
