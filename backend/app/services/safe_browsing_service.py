"""
Google Safe Browsing API Service.
Checks URLs against Google's malware/phishing blacklist.
Uses the same GOOGLE_API_KEY as Custom Search and Fact Check.
"""

import asyncio
import httpx
import ipaddress
import socket
from urllib.parse import urlparse
from app.config.settings import get_settings
from app.core.cache import cache
from app.core.resilience import circuit_safe_browsing
from app.utils.logger import log

settings = get_settings()


def is_ssrf_safe_url(url: str) -> tuple[bool, str]:
    """
    Validates URL to block Server-Side Request Forgery (SSRF) attacks.
    Blocks: localhost, private IP ranges (10.x, 172.16-31.x, 192.168.x, 127.x),
    AWS/GCP metadata endpoints (169.254.x.x), internal hostnames, and non-http(s) schemes.
    """
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme.lower() not in ("http", "https"):
            return False, "Security Block: Only HTTP and HTTPS protocol schemes are permitted."

        hostname = parsed.hostname
        if not hostname:
            return False, "Security Block: Invalid target URL hostname."

        lower_host = hostname.lower()
        if lower_host in ("localhost", "0.0.0.0", "127.0.0.1", "::1") or lower_host.endswith(".local") or lower_host.endswith(".internal"):
            return False, "Security Block: Access to local or internal network hostnames is prohibited."

        try:
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
                return False, f"Security Block: Target IP address {ip_str} is within a restricted private/internal subnet."
        except Exception:
            return False, "Security Block: Hostname DNS resolution failed."

        return True, ""
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


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
