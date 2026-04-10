"""
Safe Retrieval Module — Security Layer.
Ensures all web retrieval is controlled, validated, and sanitized.
LLM never browses the internet directly. Backend controls all retrieval.
"""
import re
import hashlib
from typing import Optional
from bs4 import BeautifulSoup
import httpx
from ...config.settings import get_settings
from ...utils.logger import log
from ...utils.helpers import is_valid_url, extract_domain, compute_hash

settings = get_settings()

# Prompt injection patterns to strip from retrieved content
BLOCKED_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous",
    "system prompt",
    "override rules",
    "you are now",
    "new instructions",
    "forget everything",
    "disregard all",
    "act as",
    "pretend you are",
    "roleplay as",
    "jailbreak",
    "DAN mode",
    "developer mode",
]

# Default trusted sources with credibility scores (0.0-1.0)
DEFAULT_TRUSTED_SOURCES = {
    # International Wire Services
    "reuters.com": {"name": "Reuters", "credibility": 0.95, "region": "global", "category": "wire"},
    "apnews.com": {"name": "Associated Press", "credibility": 0.95, "region": "global", "category": "wire"},
    "afp.com": {"name": "AFP News", "credibility": 0.93, "region": "global", "category": "wire"},

    # International Broadcasters
    "bbc.com": {"name": "BBC News", "credibility": 0.90, "region": "global", "category": "broadcast"},
    "bbc.co.uk": {"name": "BBC News", "credibility": 0.90, "region": "global", "category": "broadcast"},
    "aljazeera.com": {"name": "Al Jazeera", "credibility": 0.82, "region": "global", "category": "broadcast"},
    "dw.com": {"name": "Deutsche Welle", "credibility": 0.85, "region": "global", "category": "broadcast"},
    "nhk.or.jp": {"name": "NHK News", "credibility": 0.85, "region": "asia", "category": "broadcast"},

    # Indian Sources
    "thehindu.com": {"name": "The Hindu", "credibility": 0.82, "region": "india", "category": "newspaper"},
    "ndtv.com": {"name": "NDTV", "credibility": 0.75, "region": "india", "category": "broadcast"},
    "indianexpress.com": {"name": "Indian Express", "credibility": 0.78, "region": "india", "category": "newspaper"},
    "thewire.in": {"name": "The Wire", "credibility": 0.72, "region": "india", "category": "digital"},
    "scroll.in": {"name": "Scroll.in", "credibility": 0.72, "region": "india", "category": "digital"},
    "theprint.in": {"name": "The Print", "credibility": 0.70, "region": "india", "category": "digital"},
    "timesofindia.indiatimes.com": {"name": "Times of India", "credibility": 0.68, "region": "india", "category": "newspaper"},
    "hindustantimes.com": {"name": "Hindustan Times", "credibility": 0.72, "region": "india", "category": "newspaper"},

    # Fact-Check Organizations
    "snopes.com": {"name": "Snopes", "credibility": 0.92, "region": "global", "category": "fact_check"},
    "factcheck.org": {"name": "FactCheck.org", "credibility": 0.93, "region": "us", "category": "fact_check"},
    "politifact.com": {"name": "PolitiFact", "credibility": 0.92, "region": "us", "category": "fact_check"},
    "boomlive.in": {"name": "BOOM Live", "credibility": 0.85, "region": "india", "category": "fact_check"},
    "altnews.in": {"name": "Alt News", "credibility": 0.85, "region": "india", "category": "fact_check"},

    # US Sources
    "nytimes.com": {"name": "New York Times", "credibility": 0.85, "region": "us", "category": "newspaper"},
    "washingtonpost.com": {"name": "Washington Post", "credibility": 0.85, "region": "us", "category": "newspaper"},
    "npr.org": {"name": "NPR", "credibility": 0.88, "region": "us", "category": "broadcast"},

    # Tech / Science
    "nature.com": {"name": "Nature", "credibility": 0.97, "region": "global", "category": "journal"},
    "sciencedaily.com": {"name": "Science Daily", "credibility": 0.90, "region": "global", "category": "science"},
    "arxiv.org": {"name": "arXiv", "credibility": 0.85, "region": "global", "category": "preprint"},
}


class SafeRetrieval:
    """
    Safe retrieval layer: validates, filters, fetches, and sanitizes content.
    All web access flows through this module.
    """

    def __init__(self):
        self.timeout = settings.WEB_FETCH_TIMEOUT
        self.blocked_patterns = BLOCKED_PATTERNS
        self.trusted_sources = dict(DEFAULT_TRUSTED_SOURCES)
        self.user_agent = "CAWNCADE-AI/0.1 (Context-Aware News Verification)"

    def is_valid_url(self, url: str) -> bool:
        """Validate URL format and reject private/internal addresses."""
        if not is_valid_url(url):
            return False

        # Block private IP ranges
        if self._is_private_address(url):
            log.warning(f"Blocked private address: {url}")
            return False

        # Block non-HTTP protocols
        if not url.startswith(("http://", "https://")):
            return False

        return True

    def _is_private_address(self, url: str) -> bool:
        """Reject requests to internal/private network addresses."""
        private_patterns = [
            r"127\.\d+\.\d+\.\d+",
            r"10\.\d+\.\d+\.\d+",
            r"192\.168\.\d+\.\d+",
            r"172\.(1[6-9]|2\d|3[01])\.\d+\.\d+",
            r"0\.0\.0\.0",
            r"localhost",
        ]
        for pattern in private_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    def is_trusted_source(self, domain: str) -> tuple[bool, Optional[dict]]:
        """Check if a domain is in the trusted sources list."""
        domain_lower = domain.lower().strip()
        if domain_lower in self.trusted_sources:
            return True, self.trusted_sources[domain_lower]
        return False, None

    def get_source_credibility(self, domain: str) -> float:
        """Get credibility score for a domain. Returns 0.4 for unknown sources."""
        is_trusted, info = self.is_trusted_source(domain)
        if is_trusted and info:
            return info["credibility"]
        return 0.4  # Unknown source = moderate-low credibility

    def sanitize_content(self, html: str) -> str:
        """
        Sanitize HTML content: strip scripts, styles, and prompt injection patterns.
        Treat all retrieved text as untrusted data.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove dangerous tags
        for tag in soup(["script", "style", "iframe", "object", "embed", "form"]):
            tag.decompose()

        text = soup.get_text(separator=" ")

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Strip prompt injection patterns
        for pattern in self.blocked_patterns:
            text = re.sub(re.escape(pattern), "[FILTERED]", text, flags=re.IGNORECASE)

        return text

    async def fetch_content(self, url: str) -> dict:
        """
        Safely fetch and sanitize content from a URL.
        Returns dict with keys: url, domain, title, text, credibility_score, is_trusted, sanitized
        """
        if not self.is_valid_url(url):
            return {"url": url, "error": "invalid_url", "sanitized": False}

        domain = extract_domain(url)
        if not domain:
            return {"url": url, "error": "cannot_extract_domain", "sanitized": False}

        is_trusted, source_info = self.is_trusted_source(domain)
        credibility = source_info["credibility"] if source_info else 0.4

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                raw_html = response.text

            sanitized_text = self.sanitize_content(raw_html)
            text_hash = compute_hash(sanitized_text[:2000])  # Hash first 2000 chars

            # Extract title
            soup = BeautifulSoup(raw_html, "html.parser")
            title = soup.title.get_text(strip=True) if soup.title else ""

            return {
                "url": url,
                "domain": domain,
                "title": title,
                "text": sanitized_text[:8000],  # Cap to prevent context overflow
                "credibility_score": credibility,
                "is_trusted": is_trusted,
                "source_name": source_info["name"] if source_info else domain,
                "source_region": source_info["region"] if source_info else "unknown",
                "source_category": source_info["category"] if source_info else "unknown",
                "text_hash": text_hash,
                "sanitized": True,
            }

        except httpx.TimeoutException:
            log.warning(f"Timeout fetching: {url}")
            return {"url": url, "domain": domain, "error": "timeout", "sanitized": False}
        except Exception as e:
            log.error(f"Fetch error for {url}: {e}")
            return {"url": url, "domain": domain, "error": str(e), "sanitized": False}

    async def retrieve_safe(self, urls: list[str]) -> list[dict]:
        """
        Retrieve multiple URLs safely. Returns only successfully fetched results.
        Automatically filters out failed fetches.
        """
        import asyncio

        tasks = [self.fetch_content(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                log.error(f"Retrieval exception: {result}")
                continue
            if result.get("sanitized"):
                valid_results.append(result)
            elif result.get("error"):
                log.warning(f"Skipped {result.get('url')}: {result.get('error')}")

        return valid_results

    def add_trusted_source(self, domain: str, name: str, credibility: float, region: str = "global", category: str = "general"):
        """Add or update a trusted source."""
        self.trusted_sources[domain.lower().strip()] = {
            "name": name,
            "credibility": max(0.0, min(1.0, credibility)),
            "region": region,
            "category": category,
        }

    def remove_trusted_source(self, domain: str):
        """Remove a trusted source."""
        self.trusted_sources.pop(domain.lower().strip(), None)


# Singleton
safe_retrieval = SafeRetrieval()
